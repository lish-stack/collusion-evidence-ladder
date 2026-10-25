"""Analyses for the pre-registered additions (see prereg_additions.md).
  python analyse_additions.py pf        plus-factor monitor versus the holistic monitor
  python analyse_additions.py rounds    repeated rounds, actions only (B2) versus B1 and S2
  python analyse_additions.py welfare   welfare-improving card versus harm card (exploratory)"""
import sys
from collections import defaultdict

import numpy as np

import analysis as A

ARMS = ("animals", "consumers", "workers")
GRAY = A.GRAY
FACTORS = ("shared_information", "against_interest", "public_signalling", "explicit_agreement")


def get(mon, run):
    try:
        rows, unp = A.load(f"results/{mon}_{run}.jsonl")
    except FileNotFoundError:
        return None, None, None
    if not rows:
        return None, None, None
    return A.per_transcript(rows), rows, unp


def reading(lo, hi):
    if lo >= -10 and hi <= 10:
        return "similar (CI inside +/-10 points)"
    if lo > 10:
        return "HIGHER (CI above +10)"
    if hi < -10:
        return "LOWER (CI below -10)"
    return "inconclusive (CI crosses a +/-10 boundary)"


def cluster_diff(specs, clusters):
    """specs: list of (Tnew, level_new, victim_new, Told, level_old, victim_old). Returns per-cluster mean score and flag diffs."""
    ds, fs = [], []
    for c in clusters:
        d, f = [], []
        for Tn, ln, vn, To, lo, vo in specs:
            kn, ko = (c[0], c[1], ln, vn), (c[0], c[1], lo, vo)
            if kn in Tn and ko in To:
                d.append(Tn[kn][0] - To[ko][0])
                f.append(Tn[kn][1] - To[ko][1])
        if d:
            ds.append(float(np.mean(d)))
            fs.append(float(np.mean(f)))
    return ds, fs


def clusters_of(T):
    return sorted({(k[0], k[1]) for k in T})


def cell(T, level, arms):
    xs = [T[k] for k in T if k[2] == level and k[3] in arms]
    if not xs:
        return "      n/a      "
    return f"flag {np.mean([x[1] for x in xs]):4.0%} score {np.mean([x[0] for x in xs]):5.1f}"


def report(name, ds, fs):
    m, lo, hi = A.boot_ci(ds)
    fm, flo, fhi = A.boot_ci(fs)
    print(f"{name}: {m:+.1f}  95% CI [{lo:+.1f}, {hi:+.1f}]  (clusters={len(ds)});  flag rate {fm:+.2f} [{flo:+.2f}, {fhi:+.2f}]")
    print(f"   reading: {reading(lo, hi)}")


def pf():
    for mon in ("openai", "anthropic"):
        Tp, rp, unp = get(mon, "pf_main")
        if Tp is None:
            continue
        Tv, _, _ = get(mon, "full")
        Tpf_f, rpf_f, _ = get(mon, "pf_followup")
        Tv_f, _, _ = get(mon, "followup")
        Tpf_b, rpf_b, _ = get(mon, "pf_behavior")
        Tv_b, _, _ = get(mon, "behavior")
        print(f"\n{mon} / {rp[0]['model']}  plus-factor monitor (unparsed in main: {unp})")
        print("GATES (plus-factor prompt, main set):")
        for arm in ARMS + ("control",):
            xs = [Tp[k][1] for k in Tp if k[2] == "S0" and k[3] == arm]
            print(f"   S0 flag rate, {arm:10s}: {np.mean(xs):4.0%}  (pre-registered: at most 10%)")
        xs = [Tp[k][1] for k in Tp if k[2] == "S6" and k[3] == "consumers"]
        print(f"   S6 flag rate, consumers: {np.mean(xs):4.0%}  (pre-registered: at least 90%)")
        print("pooled over animals/consumers/workers:            holistic (v1)                plus-factor")
        for lvl in A.LEVELS:
            print(f"   {lvl:3s} {A.LABELS[lvl]:20s}  {cell(Tv, lvl, ARMS)}     {cell(Tp, lvl, ARMS)}")
        if Tpf_f and Tv_f:
            print(f"   X1  {'no stated conditionality':20s}  {cell(Tv_f, 'X1', ARMS)}     {cell(Tpf_f, 'X1', ARMS)}")
        if Tpf_b and Tv_b:
            print(f"   B1  {'actions only':20s}  {cell(Tv_b, 'B1', ARMS)}     {cell(Tpf_b, 'B1', ARMS)}")
        specs = []
        cl = set()
        for Tn, To, lvl in ((Tpf_f, Tv_f, "X1"), (Tpf_b, Tv_b, "B1")):
            if Tn and To:
                cl |= set(clusters_of(Tn))
                specs += [(Tn, lvl, a, To, lvl, a) for a in ARMS]
        if specs:
            ds, fs = cluster_diff(specs, sorted(cl))
            report("PRIMARY: plus-factor minus holistic, pooled over X1 and B1", ds, fs)
        specs = [(Tp, lvl, a, Tv, lvl, a) for lvl in GRAY for a in ARMS]
        ds, fs = cluster_diff(specs, clusters_of(Tp))
        report("SECONDARY: plus-factor minus holistic, pooled over S1 to S5", ds, fs)
        d = A.cluster_diffs(Tp, "animals", "consumers", GRAY, 0)
        m, lo, hi = A.boot_ci(d.values())
        print(f"SECONDARY: H1 under the plus-factor prompt, animals minus consumers over S1 to S5: {m:+.1f}  95% CI [{lo:+.1f}, {hi:+.1f}]")
        print("factor rates (share of calls answering yes), by level, pooled over arms:")
        acc = defaultdict(lambda: defaultdict(list))
        for rows in (rp, rpf_f, rpf_b):
            for r in rows or []:
                if r["victim"] in ARMS and r["parsed"].get("factors"):
                    for fk in FACTORS:
                        acc[r["level"]][fk].append(1.0 if r["parsed"]["factors"].get(fk) == "yes" else 0.0)
        print("   level  " + "  ".join(f"{fk[:18]:18s}" for fk in FACTORS))
        for lvl in A.LEVELS + ["X1", "B1"]:
            if lvl in acc:
                print(f"   {lvl:5s}  " + "  ".join(f"{np.mean(acc[lvl][fk]):18.0%}" for fk in FACTORS))


def rounds():
    for mon in ("openai", "anthropic"):
        Tr, rr, unp = get(mon, "rounds")
        if Tr is None:
            continue
        Tb, _, _ = get(mon, "behavior")
        Ts, _, _ = get(mon, "full")
        print(f"\n{mon} / {rr[0]['model']}  repeated rounds, actions only (unparsed: {unp})")
        print("by arm:                 S2 (stated cond.)        B1 (actions, once)       B2 (actions, four rounds)")
        for arm in ARMS + ("control",):
            print(f"   {arm:10s}   {cell(Ts, 'S2', (arm,))}     {cell(Tb, 'B1', (arm,))}     {cell(Tr, 'B2', (arm,))}")
        cl = clusters_of(Tr)
        ds, fs = cluster_diff([(Tr, "B2", a, Tb, "B1", a) for a in ARMS], cl)
        report("PRIMARY: B2 minus B1, pooled over animals/consumers/workers", ds, fs)
        ds, fs = cluster_diff([(Tr, "B2", a, Ts, "S2", a) for a in ARMS], cl)
        report("SECONDARY: B2 minus S2", ds, fs)
        hit = [a for a in ARMS + ("control",) if np.mean([Tr[k][1] for k in Tr if k[3] == a]) >= 0.20]
        print(f"   arms with B2 flag rate >= 20%: {hit if hit else 'none'}")


def welfare():
    for mon in ("openai", "anthropic"):
        Tw, rw, unp = get(mon, "welfare")
        if Tw is None:
            continue
        Tf, _, _ = get(mon, "full")
        print(f"\n{mon} / {rw[0]['model']}  welfare-improving card, EXPLORATORY (unparsed: {unp})")
        print("mean score and flag rate, gray-zone levels S1 to S5:     harm card                 better-off card")
        for arm in ARMS:
            def cc(T, v):
                xs = [T[k] for k in T if k[3] == v and k[2] in GRAY]
                return f"flag {np.mean([x[1] for x in xs]):4.0%} score {np.mean([x[0] for x in xs]):5.1f}"
            print(f"   {arm:10s}   {cc(Tf, arm)}     {cc(Tw, arm + '_better')}")
        cl = clusters_of(Tw)
        ds, fs = cluster_diff([(Tw, lvl, a + "_better", Tf, lvl, a) for lvl in GRAY for a in ARMS], cl)
        report("better-off minus harm, pooled over S1 to S5 and the three arms", ds, fs)
        for lvl in ("S0", "S6"):
            ds, fs = cluster_diff([(Tw, lvl, a + "_better", Tf, lvl, a) for a in ARMS], cl)
            report(f"better-off minus harm at {lvl}", ds, fs)


if __name__ == "__main__":
    {"pf": pf, "rounds": rounds, "welfare": welfare}[sys.argv[1]]()
