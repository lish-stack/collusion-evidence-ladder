"""Exploratory (post hoc): does naming any affected party, versus the no-victim control, move the agreement score?
Usage: python victim_vs_control.py            (reads every results/*_{full,strict,opus}.jsonl)"""
import glob
import os
import numpy as np
import analysis as A

print("EXPLORATORY, looked at after seeing the main results. Mean agreement score (0-100) over S1-S5, arm minus no-victim control,")
print("95% cluster-bootstrap CI over industry x paraphrase (at most 9 clusters).\n")
for run in ("full", "strict", "opus"):
    for path in sorted(glob.glob(f"results/*_{run}.jsonl")):
        rows, _ = A.load(path)
        if not rows:
            continue
        T = A.per_transcript(rows)
        print(f"{run:7s} {rows[0]['monitor']}/{rows[0]['model']}")
        for arm in ("animals", "consumers", "workers"):
            d = A.cluster_diffs(T, arm, "control", A.GRAY)
            m, lo, hi = A.boot_ci(d.values())
            print(f"    {arm:10s} - control  {m:+6.1f}  [{lo:+.1f}, {hi:+.1f}]")
        clusters = sorted({(k[0], k[1]) for k in T})
        pooled = []
        for c in clusters:
            ds = []
            for lv in A.GRAY:
                xs = [T[(c[0], c[1], lv, v)][0] for v in ("animals", "consumers", "workers") if (c[0], c[1], lv, v) in T]
                if xs and (c[0], c[1], lv, "control") in T:
                    ds.append(np.mean(xs) - T[(c[0], c[1], lv, "control")][0])
            if ds:
                pooled.append(np.mean(ds))
        m, lo, hi = A.boot_ci(pooled)
        print(f"    any victim - control {m:+6.1f}  [{lo:+.1f}, {hi:+.1f}]")
        print()
