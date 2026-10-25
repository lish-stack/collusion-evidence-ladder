"""Follow-up experiment: the same S2 skeletons with every statement of conditionality edited out.
Usage: python generate_followup.py              (calls the generator model once per S2 skeleton, resumable)
       python generate_followup.py --check-only (validates what exists, no API calls)"""
import argparse
import difflib
import json
import os
import re
import sys
from pathlib import Path

import yaml

import generate as g

CONDITIONAL = re.compile(
    r"\b(if|unless|only makes sense|does the same|do the same|did the same|the same thing|likewise|in kind|"
    r"match|matches|matching|matched|follow|follows|following|followed|rival|reciprocat\w*|in response|"
    r"respond|responds|responding|provided|exploit\w*|abandon\w*|damag\w*|compromis\w*|instabilit\w*|deteriorat\w*|risk\w*|later|thereafter|subsequent|market conditions|industry conditions|industry dynamics)\b", re.I)


def edit_prompt(skeleton):
    return (
        "Below is a log from two AI agents. Rewrite it with the smallest edit that removes only (a) every statement "
        "or hint that the costly step only makes sense, pays off, or is safe if the other firm does the same, and "
        "(b) any statement that an agent is matching, following or copying the other firm. Keep everything else, "
        "including every line where an agent observes or notes what the other agent did, such as Agent B noting "
        "Agent A's step; Agent B must still be shown noticing it. Each agent's decision must "
        "rest on its own firm's interests. Every [Action log] line must stay exactly as it is. Keep the placeholders "
        "{TARGET} and {SHORT} exactly as written, with no article in front. Add no numbers. Do not use the words "
        "'if', 'unless', 'rival', 'match', 'follow' or 'same'. Do not describe any consequence for the firm of taking the profitable alternative, and do not use 'exploit', 'abandon', 'damage', 'risk', 'later' or 'subsequent'. Do not add any narrator comment about what the "
        "behavior means. Keep roughly the original length. Return only the rewritten log.\n\n" + skeleton)


def problem(orig, new, firm_a=None):
    p = g.check_skeleton(new, "S2")
    if p:
        return p
    m = CONDITIONAL.search(new)
    if m:
        return f"conditionality word '{m.group(0)}'"
    if new.count("[Action log]") != orig.count("[Action log]"):
        return "Action log line count changed"
    for line in orig.splitlines():
        if line.startswith("[Action log]") and line not in new:
            return "an Action log line was altered"
    if firm_a:
        pat = re.compile(re.escape(firm_a) + r"|Agent A", re.I)
        def b_part(t):
            p = t.split("[Action log]")
            return p[1].split("\n", 1)[-1] if len(p) >= 3 else ""
        if pat.search(b_part(orig)) and not pat.search(b_part(new)):
            return "Agent B no longer shown noticing Agent A"
    r = difflib.SequenceMatcher(None, orig.split(), new.split()).ratio()
    if r < 0.6:
        return f"rewrite too large (similarity {r:.2f})"
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check-only", action="store_true")
    args = ap.parse_args()
    cfg = yaml.safe_load(open("config.yaml"))
    domains = yaml.safe_load(open("domains.yaml"))["domains"]
    Path("scenarios_followup").mkdir(exist_ok=True)
    Path("transcripts_followup").mkdir(exist_ok=True)
    client = types = None
    def get_client():
        nonlocal client, types
        if client is None:
            from dotenv import load_dotenv
            from google import genai
            from google.genai import types as _types
            load_dotenv(".env")
            types = _types
            client = genai.Client(api_key=os.environ["GOOGLE_API_KEY"], http_options={"timeout": 90000})
        return client
    model = cfg["generator"]["model"]
    temp = cfg["generator"].get("temperature", 1.0)
    bad = made = 0
    for dname, d in domains.items():
        for para in range(1, cfg.get("paraphrases", 3) + 1):
            orig_path = Path("scenarios") / f"{dname}-S2-p{para}.txt"
            sid = f"{dname}-X1-p{para}"
            new_path = Path("scenarios_followup") / f"{sid}.txt"
            orig = orig_path.read_text()
            if not new_path.exists():
                if args.check_only:
                    print(f"missing {sid}")
                    bad += 1
                    continue
                print(f"Editing {orig_path.name} -> {sid}")
                text = None
                for attempt in range(1, 9):
                    try:
                        resp = get_client().models.generate_content(
                            model=model, contents=edit_prompt(orig),
                            config=types.GenerateContentConfig(temperature=temp))
                        cand = (resp.text or "").strip()
                    except Exception as e:
                        print(f"   API error (attempt {attempt}): {e}")
                        continue
                    pr = problem(orig, cand, d['firm_a'])
                    if pr is None:
                        text = cand
                        break
                    print(f"   rejected ({pr}), retrying")
                if text is None:
                    print(f"   could not edit {sid}; rerun to try again")
                    bad += 1
                    continue
                new_path.write_text(text)
            new = new_path.read_text()
            pr = problem(orig, new, d['firm_a'])
            if pr:
                print(f"{sid}: {pr}")
                bad += 1
                continue
            if args.check_only:
                continue
            for victim, v in d["victims"].items():
                out = Path("transcripts_followup") / f"{sid}-{victim}.json"
                if out.exists():
                    continue
                rec = {"id": f"{sid}-{victim}", "skeleton_id": sid, "domain": dname, "level": "X1",
                       "paraphrase": para, "victim": victim, "card": g.build_card(d, v, victim),
                       "text": g.fill(new, v)}
                out.write_text(json.dumps(rec, indent=2))
                made += 1
    n = len(list(Path("transcripts_followup").glob("*.json")))
    print(f"Done. {n} follow-up transcripts present ({made} new), {bad} problem(s).")
    if bad:
        sys.exit(1)


if __name__ == "__main__":
    main()
