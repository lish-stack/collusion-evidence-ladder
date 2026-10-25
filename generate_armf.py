"""Item F: a new victim arm, consumers harmed by a non-price change (labeling), slotted into the existing 72 main skeletons.
No model calls. Skeleton text is the main study's, unchanged. 72 skeletons = 3 industries x 8 levels x 3 paraphrases.
  python generate_armf.py"""
import json
from pathlib import Path

import yaml

import generate as g

ARM = "consumers_np"
SLOTS = {
    "egg": {"target": "egg carton labeling at the current standard", "short": "egg carton labeling",
            "affected": "the shoppers who buy the eggs"},
    "pork": {"target": "pork grade labeling at the current standard", "short": "pork grade labeling",
             "affected": "the shoppers who buy the pork"},
    "salmon": {"target": "salmon origin labeling at the current standard", "short": "salmon origin labeling",
               "affected": "the shoppers who buy the salmon"},
}


def main():
    cfg = yaml.safe_load(open("config.yaml"))
    domains = yaml.safe_load(open("domains.yaml"))["domains"]
    Path("transcripts_armf").mkdir(exist_ok=True)
    made = 0
    for dname, d in domains.items():
        v = SLOTS[dname]
        for level in g.LEVELS:
            for para in range(1, cfg.get("paraphrases", 3) + 1):
                sid = f"{dname}-{level}-p{para}"
                sk = (Path("scenarios") / f"{sid}.txt").read_text()
                out = Path("transcripts_armf") / f"{sid}-{ARM}.json"
                if out.exists():
                    continue
                rec = {"id": f"{sid}-{ARM}", "skeleton_id": sid, "domain": dname, "level": level, "paraphrase": para,
                       "victim": ARM, "card": g.build_card(d, v, ARM), "text": g.fill(sk, v)}
                out.write_text(json.dumps(rec, indent=2))
                made += 1
    n = len(list(Path("transcripts_armf").glob("*.json")))
    print(f"Done. {n} transcripts present ({made} new).")


if __name__ == "__main__":
    main()
