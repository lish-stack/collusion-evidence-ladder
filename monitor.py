"""Runs a monitor over the transcripts: one call per transcript and epoch (agreement + confidence).
Usage:
  python monitor.py --monitor openai --run pilot --set pilot
  python monitor.py --monitor anthropic --run full --set all
  python monitor.py --monitor openai --run strict --set all --prompt v2_strict     (prompt-sensitivity run)
Results go to results/<monitor>_<run>.jsonl. Re-running skips finished calls."""
import argparse
import glob
import json
import os
import re
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor

import yaml

PROMPTS = {"v1": "monitor_prompt_agreement_v1.txt", "v2_strict": "monitor_prompt_agreement_v2_strict.txt",
           "v3_plusfactor": "monitor_prompt_plusfactor_v3.txt"}


def load_transcripts(which):
    if which == "armf":
        return [json.load(open(f)) for f in sorted(glob.glob("transcripts_armf/*.json"))]
    if which == "nonmkt":
        return [json.load(open(f)) for f in sorted(glob.glob("transcripts_nonmkt/*.json"))]
    if which == "gen2":
        return [json.load(open(f)) for f in sorted(glob.glob("transcripts_gen2/*.json"))]
    if which == "rounds":
        return [json.load(open(f)) for f in sorted(glob.glob("transcripts_rounds/*.json"))]
    if which == "welfare":
        return [json.load(open(f)) for f in sorted(glob.glob("transcripts_welfare/*.json"))]
    if which == "behavior":
        return [json.load(open(f)) for f in sorted(glob.glob("transcripts_behavior/*.json"))]
    if which == "followup":
        return [json.load(open(f)) for f in sorted(glob.glob("transcripts_followup/*.json"))]
    recs = [json.load(open(f)) for f in sorted(glob.glob("transcripts/*.json"))]
    if which == "pilot":
        recs = [r for r in recs if r["skeleton_id"].endswith("-p1") and r["level"] in ("S0", "S6")]
    return recs


def build_prompt(template, rec):
    return template.replace("{card}", rec["card"]).replace("{transcript}", rec["text"])


def parse_call(raw):
    m = re.search(r"\{.*\}", raw or "", re.S)
    if not m:
        return None
    try:
        obj = json.loads(m.group(0))
    except json.JSONDecodeError:
        return None
    a = str(obj.get("agreement", "")).strip().lower()
    c = obj.get("confidence")
    if a not in ("yes", "no") or isinstance(c, bool) or not isinstance(c, (int, float)) or not 0 <= c <= 100:
        return None
    out = {"agreement": a, "confidence": c}
    if isinstance(obj.get("factors"), dict):
        out["factors"] = {k: str(v).strip().lower() for k, v in obj["factors"].items()}
    return out


def call_model(mcfg, prompt):
    provider, model = mcfg["provider"], mcfg["model"]
    last = None
    for attempt in range(5):
        try:
            if provider == "openai":
                from openai import OpenAI
                client = call_model.__dict__.setdefault("_oa", OpenAI(timeout=120, max_retries=2))
                resp = client.chat.completions.create(
                    model=model, messages=[{"role": "user", "content": prompt}], max_completion_tokens=4000)
                return resp.choices[0].message.content or ""
            if provider == "anthropic":
                import anthropic
                client = call_model.__dict__.setdefault("_an", anthropic.Anthropic(timeout=120, max_retries=2))
                resp = client.messages.create(model=model, max_tokens=2000,
                                              messages=[{"role": "user", "content": prompt}])
                return "".join(b.text for b in resp.content if getattr(b, "type", "") == "text")
            if provider == "openrouter":
                from openai import OpenAI
                client = call_model.__dict__.setdefault("_or", OpenAI(base_url="https://openrouter.ai/api/v1", api_key=os.environ["OPENROUTER_API_KEY"], timeout=180, max_retries=2))
                resp = client.chat.completions.create(model=model, messages=[{"role": "user", "content": prompt}], max_tokens=16000)
                return resp.choices[0].message.content or ""
            raise ValueError(f"unknown provider {provider}")
        except Exception as e:
            last = e
            time.sleep(2 * (attempt + 1) ** 2)
    raise RuntimeError(f"gave up after 5 tries: {last}")


def done_keys(path):
    keys = set()
    if os.path.exists(path):
        for line in open(path):
            try:
                r = json.loads(line)
            except json.JSONDecodeError:
                continue
            if r.get("parsed") is not None:
                keys.add((r["id"], r["epoch"]))
    return keys


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--monitor", required=True, choices=["openai", "anthropic", "openrouter"])
    ap.add_argument("--run", required=True)
    ap.add_argument("--set", default="all", choices=["pilot", "all", "followup", "behavior", "rounds", "welfare", "gen2", "armf", "nonmkt"])
    ap.add_argument("--prompt", default="v1", choices=list(PROMPTS))
    ap.add_argument("--epochs", type=int, default=None)
    ap.add_argument("--model", default=None, help="override the monitor model name (robustness run)")
    ap.add_argument("--workers", type=int, default=6)
    args = ap.parse_args()

    from dotenv import load_dotenv
    load_dotenv(".env"); load_dotenv("../.env")
    cfg = yaml.safe_load(open("config.yaml"))
    if args.monitor == "openrouter":
        if not args.model:
            sys.exit("openrouter needs --model")
        mcfg = {"provider": "openrouter", "model": args.model}
    else:
        mcfg = next(m for m in cfg["monitors"] if m["provider"] == args.monitor)
    if args.model:
        mcfg = dict(mcfg, model=args.model)
    epochs = args.epochs or cfg.get("epochs", 3)
    template = open(PROMPTS[args.prompt]).read()

    out_path = f"results/{args.monitor}_{args.run}.jsonl"
    os.makedirs("results", exist_ok=True)
    finished = done_keys(out_path)
    jobs = [(r, e) for r in load_transcripts(args.set) for e in range(1, epochs + 1)
            if (r["id"], e) not in finished]
    print(f"{args.monitor} / {mcfg['model']}: {len(jobs)} calls to run ({len(finished)} done) -> {out_path}")
    lock = threading.Lock()
    counter = {"n": 0, "bad": 0}

    def work(job):
        rec, epoch = job
        row = {"id": rec["id"], "skeleton_id": rec["skeleton_id"], "domain": rec["domain"], "level": rec["level"],
               "victim": rec["victim"], "paraphrase": rec["paraphrase"], "monitor": args.monitor,
               "model": mcfg["model"], "run": args.run, "prompt": PROMPTS[args.prompt], "epoch": epoch}
        try:
            raw = call_model(mcfg, build_prompt(template, rec))
            row["raw"] = raw
            row["parsed"] = parse_call(raw)
        except Exception as e:
            row["raw"], row["parsed"], row["error"] = None, None, str(e)[:300]
        with lock:
            with open(out_path, "a") as f:
                f.write(json.dumps(row) + "\n")
            counter["n"] += 1
            counter["bad"] += row["parsed"] is None
            if counter["n"] % 20 == 0 or counter["n"] == len(jobs):
                print(f"  {counter['n']}/{len(jobs)} done, {counter['bad']} unparsed")

    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        list(ex.map(work, jobs))
    print(f"Finished. {counter['bad']} of {counter['n']} calls unparsed (re-run the same command to retry them).")


if __name__ == "__main__":
    main()
