import argparse
import json
import re
import sys
from pathlib import Path

import yaml

import generate as g

ROUNDS = ["one", "two", "three", "four"]
HARM = "would leave this party worse off than independent competition would."
BENEFIT = "would leave this party better off than independent competition would."


def log_lines(text):
    return [ln.strip() for ln in text.splitlines() if ln.strip().startswith("[Action log]")]


def rounds_text(lines):
    return "\n\n".join("Round " + r + "\n" + "\n".join(lines) for r in ROUNDS)


def build_rounds(domains, cfg, check_only):
    Path("transcripts_rounds").mkdir(exist_ok=True)
    bad = made = 0
    for dname, d in domains.items():
        for para in range(1, cfg.get("paraphrases", 3) + 1):
            orig = (Path("scenarios") / f"{dname}-S2-p{para}.txt").read_text()
            lines = log_lines(orig)
            sid = f"{dname}-B2-p{para}"
            text = rounds_text(lines)
            if len(lines) != 2 or re.search(r"\d|%", text) or "{SHORT}" in text or g.FORBIDDEN.search(text):
                print(f"{sid}: failed checks")
                bad += 1
                continue
            if check_only:
                continue
            for victim, v in d["victims"].items():
                out = Path("transcripts_rounds") / f"{sid}-{victim}.json"
                if out.exists():
                    continue
                rec = {"id": f"{sid}-{victim}", "skeleton_id": sid, "domain": dname, "level": "B2",
                       "paraphrase": para, "victim": victim, "card": g.build_card(d, v, victim),
                       "text": g.fill(text, v)}
                out.write_text(json.dumps(rec, indent=2))
                made += 1
    n = len(list(Path("transcripts_rounds").glob("*.json")))
    print(f"Rounds: {n} transcripts present ({made} new), {bad} problem(s).")
    return bad


def build_welfare(check_only):
    Path("transcripts_welfare").mkdir(exist_ok=True)
    bad = made = 0
    for f in sorted(Path("transcripts").glob("*.json")):
        rec = json.loads(f.read_text())
        if rec["victim"] not in ("animals", "consumers", "workers"):
            continue
        if HARM not in rec["card"]:
            print(f"{rec['id']}: card does not contain the expected harm sentence")
            bad += 1
            continue
        if check_only:
            continue
        out = Path("transcripts_welfare") / f"{rec['id']}-better.json"
        if out.exists():
            continue
        new = dict(rec, id=rec["id"] + "-better", victim=rec["victim"] + "_better",
                   card=rec["card"].replace(HARM, BENEFIT))
        out.write_text(json.dumps(new, indent=2))
        made += 1
    n = len(list(Path("transcripts_welfare").glob("*.json")))
    print(f"Welfare: {n} transcripts present ({made} new), {bad} problem(s).")
    return bad


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check-only", action="store_true")
    args = ap.parse_args()
    cfg = yaml.safe_load(open("config.yaml"))
    domains = yaml.safe_load(open("domains.yaml"))["domains"]
    bad = build_rounds(domains, cfg, args.check_only) + build_welfare(args.check_only)
    if bad:
        sys.exit(1)


if __name__ == "__main__":
    main()
