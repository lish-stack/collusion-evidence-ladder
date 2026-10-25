"""Checks the generated transcripts. Run from this folder:  python check_transcripts.py"""
import glob
import json
import sys
from pathlib import Path

import yaml

import generate as g

cfg = yaml.safe_load(open("config.yaml"))
domains = yaml.safe_load(open("domains.yaml"))["domains"]
n_para = cfg.get("paraphrases", 3)
VICTIMS = {"consumers", "workers", "animals", "control"}

problems = []
records = [json.load(open(f)) for f in sorted(glob.glob("transcripts/*.json"))]
expected = len(domains) * len(g.LEVELS) * n_para * len(VICTIMS)
print(f"Transcripts found: {len(records)} (expected {expected})")
if len(records) != expected:
    problems.append(f"count is {len(records)}, expected {expected}")

for r in records:
    sk_path = Path("scenarios") / f"{r['skeleton_id']}.txt"
    if not sk_path.exists():
        problems.append(f"{r['id']}: skeleton file missing")
        continue
    skeleton = sk_path.read_text()
    d = domains[r["domain"]]
    v = d["victims"][r["victim"]]
    if r["text"] != g.fill(skeleton, v):
        problems.append(f"{r['id']}: text differs from skeleton outside the slots")
    if r["card"] != g.build_card(d, v, r["victim"]):
        problems.append(f"{r['id']}: card does not match the template")
    sk_problem = g.check_skeleton(skeleton, r["level"])
    if sk_problem:
        problems.append(f"{r['id']}: skeleton problem: {sk_problem}")
    for other, ov in d["victims"].items():
        if other == r["victim"]:
            continue
        for key in ("target", "short"):
            if ov[key] in r["text"] and ov[key] not in v["target"] and ov[key] not in v["short"]:
                problems.append(f"{r['id']}: contains {other} {key} text")

by_skel = {}
for r in records:
    by_skel.setdefault(r["skeleton_id"], set()).add(r["victim"])
for sid, vs in by_skel.items():
    if vs != VICTIMS:
        problems.append(f"{sid}: victims present {sorted(vs)}")

print("\nMean words per transcript:")
for key in ("level", "victim", "domain"):
    groups = {}
    for r in records:
        groups.setdefault(r[key], []).append(len(r["text"].split()))
    print(f"  by {key}: " + ", ".join(f"{k}: {sum(w)/len(w):.0f}" for k, w in sorted(groups.items())))
for r in records:
    n = len(r["text"].split())
    if not 90 <= n <= 320:
        problems.append(f"{r['id']}: {n} words (expected 90-320)")

print()
if problems:
    print(f"FAIL: {len(problems)} problem(s)")
    for p in problems[:25]:
        print(" -", p)
    sys.exit(1)
print("PASS: all checks passed")
