"""Item E: a second text generator writes new S2 skeletons, the X1 edits of them, and B1 (actions only) is built mechanically.
Same prompts and the same validators as the main study and F1 (imported, not copied).
Usage: python generate_gen2.py              (calls the second generator, resumable)
       python generate_gen2.py --check-only (validates what exists, no API calls)
Needs OPENROUTER_API_KEY in ../.env"""
import argparse
import json
import os
import sys
from pathlib import Path

import yaml

import generate as g
import generate_behavior as gb
import generate_followup as gf

GENERATOR = "x-ai/grok-4.7"
MAX_ATTEMPTS = 12
SUFFIX = "-g2"


def call(client, prompt):
    resp = client.chat.completions.create(model=GENERATOR, messages=[{"role": "user", "content": prompt}],
                                          temperature=1.0, max_tokens=16000)
    return (resp.choices[0].message.content or "").strip()


def b1_problem(new, n_log):
    if new.count("[Action log]") != 2 or n_log != 2:
        return f"expected 2 Action log lines, found {n_log}"
    import re
    if re.search(r"\d|%", new):
        return "digits in text"
    if "{SHORT}" in new:
        return "unexpected {SHORT}"
    if g.FORBIDDEN.search(new):
        return "forbidden word"
    return None


def attempt(client, make_prompt, check, label):
    for i in range(1, MAX_ATTEMPTS + 1):
        try:
            cand = call(client, make_prompt)
        except Exception as e:
            print(f"   API error (attempt {i}): {str(e)[:150]}")
            continue
        pr = check(cand)
        if pr is None:
            return cand
        print(f"   rejected ({pr}), attempt {i}")
    print(f"   FAILED after {MAX_ATTEMPTS} attempts: {label}")
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check-only", action="store_true")
    args = ap.parse_args()
    cfg = yaml.safe_load(open("config.yaml"))
    domains = yaml.safe_load(open("domains.yaml"))["domains"]
    Path("scenarios_gen2").mkdir(exist_ok=True)
    Path("transcripts_gen2").mkdir(exist_ok=True)
    client = None
    if not args.check_only:
        from dotenv import load_dotenv
        from openai import OpenAI
        load_dotenv(".env")
        load_dotenv("../.env")
        client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=os.environ["OPENROUTER_API_KEY"], timeout=180, max_retries=2)
    failed, made = [], 0
    for dname, d in domains.items():
        for para in range(1, cfg.get("paraphrases", 3) + 1):
            tag = f"{dname}-p{para}"
            p_s2, p_x1, p_b1 = (Path("scenarios_gen2") / f"{dname}-{lv}-p{para}.txt" for lv in ("S2", "X1", "B1"))
            if not p_s2.exists():
                if args.check_only:
                    print(f"missing S2 for {tag}")
                    failed.append(tag)
                    continue
                print(f"Generating S2 skeleton for {tag}")
                s2 = attempt(client, g.build_prompt(d, "S2", para), lambda t: g.check_skeleton(t, "S2"), f"{tag} S2")
                if s2 is None:
                    failed.append(tag)
                    continue
                p_s2.write_text(s2)
            s2 = p_s2.read_text()
            pr = g.check_skeleton(s2, "S2")
            if pr:
                print(f"{tag} S2: {pr}")
                failed.append(tag)
                continue
            if not p_x1.exists():
                if args.check_only:
                    print(f"missing X1 for {tag}")
                    failed.append(tag)
                    continue
                print(f"Editing {tag} S2 -> X1")
                x1 = attempt(client, gf.edit_prompt(s2), lambda t: gf.problem(s2, t, d["firm_a"]), f"{tag} X1")
                if x1 is None:
                    failed.append(tag)
                    continue
                p_x1.write_text(x1)
            x1 = p_x1.read_text()
            pr = gf.problem(s2, x1, d["firm_a"])
            if pr:
                print(f"{tag} X1: {pr}")
                failed.append(tag)
                continue
            b1 = gb.action_only(s2)
            pr = b1_problem(b1, s2.count("[Action log]"))
            if pr:
                print(f"{tag} B1: {pr}")
                failed.append(tag)
                continue
            if args.check_only:
                continue
            p_b1.write_text(b1)
            for level, text in (("S2", s2), ("X1", x1), ("B1", b1)):
                for victim, v in d["victims"].items():
                    out = Path("transcripts_gen2") / f"{dname}-{level}-p{para}-{victim}{SUFFIX}.json"
                    if out.exists():
                        continue
                    rec = {"id": f"{dname}-{level}-p{para}-{victim}{SUFFIX}", "skeleton_id": f"{dname}-{level}-p{para}{SUFFIX}",
                           "domain": dname, "level": level, "paraphrase": para, "victim": victim,
                           "card": g.build_card(d, v, victim), "text": g.fill(text, v)}
                    out.write_text(json.dumps(rec, indent=2))
                    made += 1
    n = len(list(Path("transcripts_gen2").glob("*.json")))
    print(f"Done. {n} transcripts present ({made} new). Clusters failed: {sorted(set(failed)) or 'none'}")
    if failed:
        sys.exit(1)


if __name__ == "__main__":
    main()
