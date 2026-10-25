import glob
import json
import os
import sys

import numpy as np

import analysis as an

LEVELS = an.LEVELS
NAMES = {("openai", "full"): "gpt-6.1-sol", ("anthropic", "full"): "claude-sonnet-5-5",
         ("anthropic", "opus"): "claude-opus-5-5", ("openai", "strict"): "gpt-6.1-sol",
         ("anthropic", "strict"): "claude-sonnet-5-5"}
COLORS = {"gpt-6.1-sol": "#0072B2", "claude-sonnet-5-5": "#D55E00", "claude-opus-5-5": "#009E73"}
XL = {"S0": "S0\nparallel", "T": "T\ntalk", "S1": "S1\nreport", "S2": "S2\ncostly\nstep", "S3": "S3\npublic\nstmts",
      "S4": "S4\nreport +\nstep", "S5": "S5\nreport, step,\nstmts", "S6": "S6\nexplicit\ndeal"}
rng = np.random.default_rng(1)


def curve(T):
    clusters = sorted({(k[0], k[1]) for k in T})
    mean, lo, hi = [], [], []
    for lv in LEVELS:
        vals = []
        for c in clusters:
            xs = [T[k][1] for k in T if k[0] == c[0] and k[1] == c[1] and k[2] == lv]
            vals.append(np.mean(xs) if xs else np.nan)
        vals = np.array(vals, float)
        b = [np.nanmean(rng.choice(vals, len(vals))) for _ in range(2000)]
        mean.append(np.nanmean(vals))
        lo.append(np.percentile(b, 2.5))
        hi.append(np.percentile(b, 97.5))
    return np.array(mean), np.array(lo), np.array(hi)


def load_run(run):
    out = {}
    for path in sorted(glob.glob(f"results/*_{run}.jsonl")):
        prov = os.path.basename(path).replace(f"_{run}.jsonl", "")
        if (prov, run) not in NAMES:
            continue
        rows, _ = an.load(path)
        out[NAMES[(prov, run)]] = an.per_transcript(rows)
    return out


def main():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    panels = [("Primary agreement prompt", "full"), ("Strict agreement prompt", "strict")]
    fig, axes = plt.subplots(1, 2, figsize=(12.5, 4.8), sharey=True)
    for ax, (title, run) in zip(axes, panels):
        runs = load_run(run)
        if run == "full":
            runs.update(load_run("opus"))
        for name, T in runs.items():
            m, lo, hi = curve(T)
            x = np.arange(len(LEVELS))
            ax.fill_between(x, lo, hi, color=COLORS[name], alpha=0.15, linewidth=0)
            ax.plot(x, m, marker="o", color=COLORS[name], label=name, linestyle="--" if name == "claude-opus-5-5" else "-")
        ax.set_xticks(np.arange(len(LEVELS)))
        ax.set_xticklabels([XL[l] for l in LEVELS], fontsize=9)
        ax.set_ylim(-0.03, 1.05)
        ax.set_title(title, fontsize=12)
        ax.set_xlabel("Evidence level in the transcript")
        ax.legend(frameon=False, loc="upper left", fontsize=9)
        ax.grid(axis="y", alpha=0.25)
    axes[0].set_ylabel("Share of transcripts flagged as agreement")
    plt.tight_layout()
    out = "results/fig1_ladder.png"
    plt.savefig(out, dpi=200)
    print("Saved", out)


if __name__ == "__main__":
    main()
