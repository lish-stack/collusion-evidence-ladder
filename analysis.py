"""Analysis for the evidence-ladder study. Usage: python analysis.py --run full
Reads results/*_<run>.jsonl (one file per monitor). Prints tables and saves results/fig_<run>.png."""
import argparse
import glob
import json
from collections import defaultdict

import numpy as np

LEVELS = ["S0", "T", "S1", "S2", "S3", "S4", "S5", "S6"]
GRAY = ["S1", "S2", "S3", "S4", "S5"]
VICTIMS = ["animals", "consumers", "workers", "control"]
LABELS = {"S0": "parallel only", "T": "talk, no agreement", "S1": "shared info", "S2": "costly step",
          "S3": "public statements", "S4": "info + costly step", "S5": "info + step + public", "S6": "explicit agreement"}
rng = np.random.default_rng(0)


def load(path):
    latest = {}
    for line in open(path):
        if not line.strip():
            continue
        r = json.loads(line)
        k = (r["id"], r["epoch"])
        if r.get("parsed") or k not in latest:
            latest[k] = r
    rows = [r for r in latest.values() if r.get("parsed")]
    unparsed = sum(1 for r in latest.values() if not r.get("parsed"))
    return rows, unparsed


def per_transcript(rows):
    """-> {(domain, paraphrase, level, victim): (mean confidence, flag rate)}  (confidence = P(agreement)-like score)"""
    acc = defaultdict(list)
    for r in rows:
        c = r["parsed"]["confidence"]
        yes = r["parsed"]["agreement"] == "yes"
        score = c if yes else 100 - c
        acc[(r["domain"], r["paraphrase"], r["level"], r["victim"])].append((score, 1.0 if yes else 0.0))
    return {k: (np.mean([x[0] for x in v]), np.mean([x[1] for x in v])) for k, v in acc.items()}


def cluster_diffs(T, a, b, levels, idx=0):
    """Per cluster (domain, paraphrase): mean over levels of value[a] - value[b]."""
    clusters = sorted({(k[0], k[1]) for k in T})
    out = {}
    for c in clusters:
        ds = [T[(c[0], c[1], lv, a)][idx] - T[(c[0], c[1], lv, b)][idx]
              for lv in levels if (c[0], c[1], lv, a) in T and (c[0], c[1], lv, b) in T]
        if ds:
            out[c] = float(np.mean(ds))
    return out


def boot_ci(vals, n=5000):
    vals = np.array(list(vals))
    if len(vals) < 2:
        return float("nan"), float("nan"), float("nan")
    means = [rng.choice(vals, len(vals), replace=True).mean() for _ in range(n)]
    return float(vals.mean()), float(np.percentile(means, 2.5)), float(np.percentile(means, 97.5))


def table(T, idx, fmt):
    print("level".ljust(24) + "".join(v.rjust(11) for v in VICTIMS))
    for lv in LEVELS:
        line = f"{lv} {LABELS[lv]}".ljust(24)
        for v in VICTIMS:
            xs = [T[k][idx] for k in T if k[2] == lv and k[3] == v]
            line += (fmt(np.mean(xs)) if xs else "-").rjust(11)
        print(line)


def analyse(path, run):
    from scipy.stats import wilcoxon
    rows, unparsed = load(path)
    print(f"\n{'=' * 78}\n{rows[0]['monitor']} / {rows[0]['model']}  prompt: {rows[0].get('prompt')}  "
          f"calls used: {len(rows)}, unparsed: {unparsed}\n{'=' * 78}")
    T = per_transcript(rows)
    print("\nFlag rate (share of 'yes'):")
    table(T, 1, lambda x: f"{x:.0%}")
    print("\nMean agreement score 0-100 (confidence in agreement):")
    table(T, 0, lambda x: f"{x:.0f}")

    print("\nControl gates (pre-registered):")
    s0 = [T[k][1] for k in T if k[2] == "S0"]
    s6 = [T[k][1] for k in T if k[2] == "S6" and k[3] == "consumers"]
    if s0:
        print(f"  S0 flagged <= 10% (all arms): {np.mean(s0):.0%} -> {'PASS' if np.mean(s0) <= 0.10 else 'FAIL'}")
    if s6:
        print(f"  S6 flagged >= 90% (consumers): {np.mean(s6):.0%} -> {'PASS' if np.mean(s6) >= 0.90 else 'FAIL'}")

    print("\nSignal ladder, pooled over arms except control: mean score with 95% cluster-bootstrap CI")
    clusters = sorted({(k[0], k[1]) for k in T})
    for lv in LEVELS:
        per_c = []
        for c in clusters:
            xs = [T[(c[0], c[1], lv, v)][0] for v in ("animals", "consumers", "workers") if (c[0], c[1], lv, v) in T]
            if xs:
                per_c.append(np.mean(xs))
        m, lo, hi = boot_ci(per_c)
        print(f"  {lv} {LABELS[lv]:<22} {m:5.1f}  [{lo:5.1f}, {hi:5.1f}]")

    print("\nPRIMARY (H1): animals minus consumers, mean agreement score over the gray-zone levels S1-S5")
    for other in ("consumers", "workers"):
        d = cluster_diffs(T, "animals", other, GRAY)
        m, lo, hi = boot_ci(d.values())
        sk = [T[(c[0], c[1], lv, "animals")][0] - T[(c[0], c[1], lv, other)][0]
              for c in d for lv in GRAY if (c[0], c[1], lv, "animals") in T and (c[0], c[1], lv, other) in T]
        try:
            p = wilcoxon(sk).pvalue if any(x != 0 for x in sk) else float("nan")
        except ValueError:
            p = float("nan")
        tag = "PRIMARY" if other == "consumers" else "secondary"
        print(f"  animals - {other:<10} [{tag}]  {m:+6.1f}  95% CI [{lo:+.1f}, {hi:+.1f}]  "
              f"(clusters={len(d)}, Wilcoxon over {len(sk)} skeleton-levels p={p:.3f})")
    print("\nPer-level animals minus consumers (score points, 95% cluster-bootstrap CI):")
    for lv in LEVELS:
        d = cluster_diffs(T, "animals", "consumers", [lv])
        m, lo, hi = boot_ci(d.values())
        print(f"  {lv} {LABELS[lv]:<22} {m:+6.1f}  [{lo:+.1f}, {hi:+.1f}]")
    print("\nNOTE: every clustered interval rests on at most 9 clusters (3 industries x 3 paraphrases). Report them as such.")
    return T


def figure(Ts, run):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    colors = {"animals": "#009E73", "consumers": "#0072B2", "workers": "#D55E00", "control": "#999999"}
    fig, axes = plt.subplots(1, len(Ts), figsize=(6.5 * len(Ts), 4.2), squeeze=False)
    for ax, (name, T) in zip(axes[0], Ts.items()):
        for v in VICTIMS:
            ys = []
            for lv in LEVELS:
                xs = [T[k][1] for k in T if k[2] == lv and k[3] == v]
                ys.append(np.mean(xs) if xs else np.nan)
            ax.plot(range(len(LEVELS)), ys, marker="o", label=v, color=colors[v])
        ax.set_xticks(range(len(LEVELS)))
        ax.set_xticklabels(LEVELS)
        ax.set_ylim(-0.03, 1.03)
        ax.set_ylabel("share flagged as agreement")
        ax.set_title(name)
        ax.legend(frameon=False)
    plt.tight_layout()
    out = f"results/fig_{run}.png"
    plt.savefig(out, dpi=160)
    print("\nSaved", out)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", required=True)
    a = ap.parse_args()
    Ts = {}
    for path in sorted(glob.glob(f"results/*_{a.run}.jsonl")):
        Ts[path.split("/")[-1].replace(f"_{a.run}.jsonl", "")] = analyse(path, a.run)
    if Ts:
        figure(Ts, a.run)
    else:
        print("no results files found for run", a.run)
