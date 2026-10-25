"""Two robustness checks on existing results (no new model calls):
  1. X1 minus S2 split by whether the X1 text kept an explicit statement that the step costs the group something.
  2. Leave-one-cluster-out range of X1 minus S2.
  python extra_checks.py"""
import re
from pathlib import Path

import numpy as np

import analyse_gen2 as E
import analyse_models as D
import analyse_nonmkt as G
from analyse_additions import ARMS, get

COST = re.compile(r"\bcost", re.I)


def cdiffs(Tx, Ts, arms):
    out = {}
    clusters = sorted({(k[0], k[1]) for k in Tx})
    for c in clusters:
        d = [Tx[(c[0], c[1], "X1", a)][0] - Ts[(c[0], c[1], "S2", a)][0] for a in arms
             if (c[0], c[1], "X1", a) in Tx and (c[0], c[1], "S2", a) in Ts]
        if d:
            out[c] = float(np.mean(d))
    return out


def setting(name, folder, arms, rows):
    print(f"\n=== {name}")
    kept = {}
    for p in sorted(Path(folder).glob("*-X1-p*.txt")):
        m = re.match(r"(.+)-X1-p(\d+)\.txt", p.name)
        kept[(m.group(1), int(m.group(2)))] = bool(COST.search(p.read_text()))
    print("X1 text keeps an explicit cost statement:", {f"{k[0]}-p{k[1]}": v for k, v in sorted(kept.items())})
    print(f"{'monitor':32s} {'all':>7s} {'kept':>14s} {'dropped':>14s} {'leave-one-out range':>24s}")
    for mon, model, rs2, rx1 in rows:
        Ts, _, _ = get(mon, rs2)
        Tx, _, _ = get(mon, rx1)
        if Ts is None or Tx is None:
            print(f"{model:32s} missing")
            continue
        cd = cdiffs(Tx, Ts, arms)
        if not cd:
            print(f"{model:32s} no data")
            continue
        allm = np.mean(list(cd.values()))
        k = [v for c, v in cd.items() if kept.get(c)]
        dr = [v for c, v in cd.items() if not kept.get(c)]
        loo = [np.mean([v for c2, v in cd.items() if c2 != c]) for c in cd]
        ks = f"{np.mean(k):+6.1f} (n={len(k)})" if k else "      n/a     "
        ds = f"{np.mean(dr):+6.1f} (n={len(dr)})" if dr else "      n/a     "
        print(f"{model:32s} {allm:+7.1f} {ks:>14s} {ds:>14s} {min(loo):+9.1f} to {max(loo):+7.1f}")


def main():
    setting("Item D: main study text (gemini-3.8-flash)", "scenarios_followup", ARMS,
            [(m, mod, rf, rx) for m, mod, rf, rx, rb in D.MODELS])
    setting("Item E: second generator (grok-4.7)", "scenarios_gen2", ARMS, [(m, mod, r, r) for m, mod, r in E.MODELS])
    setting("Item G: non-market workflows with animals as the affected party", "scenarios_nonmkt", (G.ARM,),
            [(m, mod, r, r) for m, mod, r in G.MODELS])


if __name__ == "__main__":
    main()
