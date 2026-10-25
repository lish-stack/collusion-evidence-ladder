import json, sys
run = sys.argv[1] if len(sys.argv) > 1 else "full"
rows = {}
for m in ("openai", "anthropic"):
    try:
        for line in open("results/%s_%s.jsonl" % (m, run)):
            x = json.loads(line)
            if x.get("parsed"):
                rows.setdefault((x["skeleton_id"], m), []).append(x["parsed"]["agreement"] == "yes")
    except FileNotFoundError:
        pass
print("skeleton flag rate by monitor (all 4 arms x 3 epochs = 12 calls each), levels S2 to S5 only")
sids = sorted({k[0] for k in rows if k[0].split("-")[1] in ("S2", "S3", "S4", "S5")})
for sid in sids:
    cells = []
    for m in ("openai", "anthropic"):
        v = rows.get((sid, m), [])
        cells.append("%s %2d/%2d" % (m, sum(v), len(v)))
    print("%-12s" % sid, "   ".join(cells))
