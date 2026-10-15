import csv, gzip, json, sys, glob, os

pm_csv, geo_dir, out = sys.argv[1], sys.argv[2], sys.argv[3]
GROUPS = {"1": "État", "3": "Département", "4": "Commune", "5": "Office HLM", "9": "Établissement public"}

owners = {}
with open(pm_csv, encoding="utf-8-sig", newline="") as f:
    r = csv.reader(f, delimiter=";")
    next(r)
    for row in r:
        g = row[20].strip()[:1]
        if g not in GROUPS:
            continue
        pref = (row[4].strip() or "000").zfill(3)
        sec = row[5].strip().rjust(2, "0")
        num = row[6].strip().zfill(4)
        pid = f"{row[0].strip()}{row[2]}{pref}{sec}{num}"
        p = owners.setdefault(pid, {"g": GROUPS[g], "d": row[23].strip(), "c": row[3].strip(),
                                    "s": row[5].strip(), "n": row[6].strip().lstrip("0"),
                                    "a": int(row[13] or 0), "cult": set()})
        if row[15].strip():
            p["cult"].add(row[15].split(" - ")[-1].strip())

def rnd(c):
    if isinstance(c[0], (int, float)):
        return [round(c[0], 5), round(c[1], 5)]
    return [rnd(x) for x in c]

feats, found = [], set()
for fp in sorted(glob.glob(os.path.join(geo_dir, "*.json.gz"))):
    with gzip.open(fp, "rt", encoding="utf-8") as f:
        fc = json.load(f)
    for ft in fc["features"]:
        pid = ft["properties"]["id"]
        o = owners.get(pid)
        if not o:
            continue
        found.add(pid)
        geom = ft["geometry"]
        geom["coordinates"] = rnd(geom["coordinates"])
        feats.append({"type": "Feature", "geometry": geom,
                      "properties": {"g": o["g"], "d": o["d"], "c": o["c"], "s": o["s"], "n": o["n"],
                                     "a": o["a"], "k": ", ".join(sorted(o["cult"]))}})

with open(out, "w", encoding="utf-8") as f:
    json.dump({"type": "FeatureCollection", "features": feats}, f, ensure_ascii=False, separators=(",", ":"))
print("owners", len(owners), "matched", len(found), "missing", len(set(owners) - found))
print("sample missing", list(set(owners) - found)[:5])
