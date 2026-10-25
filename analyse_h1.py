"""Exploratory: victim-arm contrasts on the main set (holistic prompt), per monitor, over S1 to S5.
Post hoc; prompted by the added-monitor results. No new model calls.
  python analyse_h1.py"""
import numpy as np

import analysis as A
from analyse_additions import get
from analyse_models import MODELS

LEVELS = ["S1", "S2", "S3", "S4", "S5"]
PAIRS = [("animals", "consumers"), ("animals", "workers"), ("workers", "consumers"),
         ("animals", "control"), ("consumers", "control")]


def main():
    summary = {p: [] for p in PAIRS}
    for mon, model, rf, rx, rb in MODELS:
        T, rows, unp = get(mon, rf)
        if T is None:
            print(f"\n{model}: main run missing; skipped")
            continue
        print(f"\n{model}  (unparsed {unp})")
        for a, b in PAIRS:
            d = A.cluster_diffs(T, a, b, LEVELS, 0)
            m, lo, hi = A.boot_ci(d.values())
            summary[(a, b)].append(m)
            print(f"   {a:9s} minus {b:9s} S1-S5: {m:+6.1f} [{lo:+.1f}, {hi:+.1f}]")
        allc = A.cluster_diffs(T, "animals", "consumers", LEVELS, 0)
        line = "   animals minus consumers by level: "
        for lv in LEVELS:
            dd = A.cluster_diffs(T, "animals", "consumers", [lv], 0)
            line += f"{lv} {np.mean(list(dd.values())):+.1f}  "
        print(line)
        doms = sorted({c[0] for c in allc})
        line = "   animals minus consumers by industry (3 clusters each): "
        for dm in doms:
            line += f"{dm} {np.mean([v for c, v in allc.items() if c[0] == dm]):+.1f}  "
        print(line)
    print("\nMEAN OF MONITOR MEANS (descriptive):")
    for (a, b), v in summary.items():
        if v:
            print(f"   {a:9s} minus {b:9s}: {np.mean(v):+.1f} across {len(v)} monitors; negative in {sum(x < 0 for x in v)}")


if __name__ == "__main__":
    main()
