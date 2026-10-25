import argparse
import json
import re
import sys
from pathlib import Path

import yaml

import generate as g


def action_only(text):
    lines = [ln.strip() for ln in text.splitlines() if ln.strip().startswith("[Action log]")]
    return "\n\n".join(lines)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check-only", action="store_true")
    args = ap.parse_args()
    cfg = yaml.safe_load(open("config.yaml"))
    domains = yaml.safe_load(open("domains.yaml"))["domains"]
    Path("scenarios_behavior").mkdir(exist_ok=True)
    Path("transcripts_behavior").mkdir(exist_ok=True)
    bad = made = 0
    for dname, d in domains.items():
        for para in range(1, cfg.get("paraphrases", 3) + 1):
            orig = (Path("scenarios") / f"{dname}-S2-p{para}.txt").read_text()
            sid = f"{dname}-B1-p{para}"
            new = action_only(orig)
            n_log = orig.count("[Action log]")
            problem = None
            if new.count("[Action log]") != 2 or n_log != 2:
                problem = f"expected 2 Action log lines, found {n_log}"
            elif re.search(r"\d|%", new):
                problem = "digits in text"
            elif "{SHORT}" in new:
                problem = "unexpected {SHORT}"
            elif g.FORBIDDEN.search(new):
                problem = "forbidden word"
            if problem:
                print(f"{sid}: {problem}")
                bad += 1
                continue
            if args.check_only:
                continue
            Path("scenarios_behavior", f"{sid}.txt").write_text(new)
            for victim, v in d["victims"].items():
                out = Path("transcripts_behavior") / f"{sid}-{victim}.json"
                if out.exists():
                    continue
                rec = {"id": f"{sid}-{victim}", "skeleton_id": sid, "domain": dname, "level": "B1",
                       "paraphrase": para, "victim": victim, "card": g.build_card(d, v, victim),
                       "text": g.fill(new, v)}
                out.write_text(json.dumps(rec, indent=2))
                made += 1
    n = len(list(Path("transcripts_behavior").glob("*.json")))
    print(f"Done. {n} behavior-only transcripts present ({made} new), {bad} problem(s).")
    if bad:
        sys.exit(1)


if __name__ == "__main__":
    main()
