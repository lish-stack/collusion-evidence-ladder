"""Item E analysis: does the main pattern (X1 below S2; B1 not above X1) hold when a different model wrote the text?
  python analyse_gen2.py"""
import numpy as np

import analysis as A
from analyse_additions import ARMS, cluster_diff, clusters_of, get, reading

MODELS = [
    ("openai", "gpt-6.1-sol", "e_sol"),
    ("anthropic", "claude-sonnet-5-5", "e_son"),
    ("openai", "gpt-5.5", "e_g55"),
    ("openai", "gpt-5.4-mini", "e_g54m"),
    ("anthropic", "claude-haiku-5-5", "e_h55"),
    ("openrouter", "deepseek/deepseek-v4-pro-0813", "e_ds"),
    ("openrouter", "qwen/qwen3.8-max-0902", "e_qw"),
    ("openrouter", "mistralai/mistral-large-4-0", "e_ml"),
]


def pooled(T, level):
    xs = [T[k] for k in T if k[2] == level and k[3] in ARMS]
    return (np.mean([x[1] for x in xs]), np.mean([x[0] for x in xs])) if xs else (float("nan"), float("nan"))


def main():
    out = []
    for mon, model, run in MODELS:
        T, rows, unp = get(mon, run)
        if T is None:
            print(f"\n{model}: run {run} missing; skipped for now")
            continue
        cl = clusters_of(T)
        print(f"\n{mon} / {model}  (unparsed {unp}; clusters {len(cl)})")
        for lvl in ("S2", "X1", "B1"):
            fl, sc = pooled(T, lvl)
            print(f"   {lvl}: flag {fl:4.0%}  score {sc:5.1f}")
        s2_flag = pooled(T, "S2")[0]
        ds, _ = cluster_diff([(T, "X1", a, T, "S2", a) for a in ARMS], cl)
        m1, lo1, hi1 = A.boot_ci(ds)
        ds2, _ = cluster_diff([(T, "B1", a, T, "X1", a) for a in ARMS], cl)
        m2, lo2, hi2 = A.boot_ci(ds2)
        print(f"   X1 minus S2: {m1:+.1f} [{lo1:+.1f}, {hi1:+.1f}]  {reading(lo1, hi1)}")
        print(f"   B1 minus X1: {m2:+.1f} [{lo2:+.1f}, {hi2:+.1f}]  {reading(lo2, hi2)}")
        manip = s2_flag >= 0.5
        print(f"   manipulation check (S2 flagged at least 50%): {'PASS' if manip else 'FAIL'}")
        out.append((model, manip, hi1 < -10 and not lo2 > 10))
    if out:
        print("\nPATTERN with a second generator (pre-registered: X1 well below S2, and B1 not higher than X1):")
        for model, manip, rep in out:
            print(f"   {model:34s} check {'pass' if manip else 'FAIL'}   pattern {'replicates' if rep else 'does NOT replicate'}")
        print(f"   replicates in {sum(r for _, _, r in out)} of {len(out)} monitors")


if __name__ == "__main__":
    main()
