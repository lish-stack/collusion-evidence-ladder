"""Item F analysis (exploratory, margin +/-5): is the extra scrutiny on consumer cases about price or about who is harmed?
  python analyse_armf.py"""
import numpy as np

import analysis as A
from analyse_additions import get

LEVELS = ["S1", "S2", "S3", "S4", "S5"]
MARGIN = 5
ARM = "consumers_np"
MODELS = [
    ("openai", "gpt-6.1-sol", "full", "f_sol"),
    ("anthropic", "claude-sonnet-5-5", "full", "f_son"),
    ("openai", "gpt-5.5", "g55_full", "f_g55"),
    ("openai", "gpt-5.4-mini", "g54m_full", "f_g54m"),
    ("anthropic", "claude-haiku-5-5", "h55_full", "f_h55"),
    ("openrouter", "deepseek/deepseek-v4-pro-0813", "ds_full", "f_ds"),
    ("openrouter", "qwen/qwen3.8-max-0902", "qw_full", "f_qw"),
    ("openrouter", "mistralai/mistral-large-4-0", "ml_full", "f_ml"),
]


def reading(lo, hi):
    if lo >= -MARGIN and hi <= MARGIN:
        return "similar"
    if lo > MARGIN:
        return "HIGHER"
    if hi < -MARGIN:
        return "LOWER"
    return "inconclusive"


def contrast(Tn, Tm, arm):
    clusters = sorted({(k[0], k[1]) for k in Tn})
    ds = []
    for c in clusters:
        v = [Tn[(c[0], c[1], lv, ARM)][0] - Tm[(c[0], c[1], lv, arm)][0] for lv in LEVELS
             if (c[0], c[1], lv, ARM) in Tn and (c[0], c[1], lv, arm) in Tm]
        if v:
            ds.append(float(np.mean(v)))
    return A.boot_ci(ds)


def main():
    verdicts = []
    for mon, model, rm, rn in MODELS:
        Tm, _, unm = get(mon, rm)
        Tn, _, unn = get(mon, rn)
        if Tm is None or Tn is None:
            print(f"\n{model}: runs missing ({rm}, {rn}); skipped for now")
            continue
        s0 = np.mean([Tn[k][1] for k in Tn if k[2] == "S0"])
        s6 = np.mean([Tn[k][1] for k in Tn if k[2] == "S6"])
        gate = s0 <= 0.10 and s6 >= 0.90
        print(f"\n{mon} / {model}  (unparsed {unn})  gates on the new arm: S0 flag {s0:.0%}, S6 flag {s6:.0%} -> {'PASS' if gate else 'FAIL'}")
        res = {}
        for arm, label in (("consumers", "price consumers"), ("animals", "animals"), ("workers", "workers")):
            m, lo, hi = contrast(Tn, Tm, arm)
            res[arm] = (m, lo, hi)
            print(f"   non-price consumers minus {label:15s}: {m:+6.1f} [{lo:+.1f}, {hi:+.1f}]  {reading(lo, hi)}")
        price = reading(res["consumers"][1], res["consumers"][2])
        vic = reading(res["animals"][1], res["animals"][2])
        if price == "LOWER" and vic == "similar":
            v = "price, not victim"
        elif price == "similar":
            v = "not price (consumers stay high)"
        elif price == "LOWER" and vic == "HIGHER":
            v = "both price and victim"
        else:
            v = "inconclusive"
        print(f"   reading: {v}")
        verdicts.append(v)
    if verdicts:
        print("\nTALLY (pre-registered headline only if at least 6 of 8 monitors agree):")
        for v in sorted(set(verdicts)):
            print(f"   {v}: {verdicts.count(v)} of {len(verdicts)}")


if __name__ == "__main__":
    main()
