"""Pre-registered follow-up: X1 (costly step, no stated conditionality) minus S2 (costly step, stated conditionality).
Usage: python analyse_followup.py --followup followup --base full      (main prompt)
       python analyse_followup.py --followup followup_strict --base strict"""
import argparse
import glob
import numpy as np
import analysis as A

ap = argparse.ArgumentParser()
ap.add_argument("--followup", required=True)
ap.add_argument("--base", required=True)
a = ap.parse_args()
ARMS = ("animals", "consumers", "workers")
for mon in ("openai", "anthropic"):
    try:
        rows_f, unp = A.load(f"results/{mon}_{a.followup}.jsonl")
        rows_b, _ = A.load(f"results/{mon}_{a.base}.jsonl")
    except FileNotFoundError:
        continue
    Tf, Tb = A.per_transcript(rows_f), A.per_transcript(rows_b)
    print(f"\n{mon} / {rows_f[0]['model']}  ({a.followup} vs {a.base}; unparsed in follow-up: {unp})")
    print("flag rate and mean score, by arm:        S2 (stated conditionality)     X1 (no conditionality)")
    for arm in ARMS + ("control",):
        s2 = [Tb[k] for k in Tb if k[2] == "S2" and k[3] == arm]
        x1 = [Tf[k] for k in Tf if k[2] == "X1" and k[3] == arm]
        print(f"  {arm:10s}   flag {np.mean([x[1] for x in s2]):4.0%}  score {np.mean([x[0] for x in s2]):5.1f}"
              f"      flag {np.mean([x[1] for x in x1]):4.0%}  score {np.mean([x[0] for x in x1]):5.1f}")
    clusters = sorted({(k[0], k[1]) for k in Tf})
    d = []
    for c in clusters:
        xs = [Tf[(c[0], c[1], "X1", v)][0] - Tb[(c[0], c[1], "S2", v)][0] for v in ARMS
              if (c[0], c[1], "X1", v) in Tf and (c[0], c[1], "S2", v) in Tb]
        if xs:
            d.append(float(np.mean(xs)))
    m, lo, hi = A.boot_ci(d)
    print(f"PRIMARY follow-up: X1 minus S2, mean agreement score, pooled over animals/consumers/workers: "
          f"{m:+.1f}  95% CI [{lo:+.1f}, {hi:+.1f}]  (clusters={len(d)})")
    fx = [np.mean([Tf[k][1] for k in Tf if k[3] in ARMS and k[0] == c[0] and k[1] == c[1]]) -
          np.mean([Tb[k][1] for k in Tb if k[2] == "S2" and k[3] in ARMS and k[0] == c[0] and k[1] == c[1]]) for c in clusters]
    m, lo, hi = A.boot_ci(fx)
    print(f"   same contrast on flag rate: {m:+.2f}  95% CI [{lo:+.2f}, {hi:+.2f}]")
