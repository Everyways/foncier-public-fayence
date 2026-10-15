"""Fusionne les limites de communes Etalab (com_*.json.gz / communes_*.json.gz) en un seul GeoJSON léger."""
import glob, gzip, json, os, sys

src_dir, out = sys.argv[1], sys.argv[2]

def rnd(c):
    if isinstance(c[0], (int, float)):
        return [round(c[0], 4), round(c[1], 4)]
    return [rnd(x) for x in c]

feats = []
for p in sorted(glob.glob(os.path.join(src_dir, "communes_*.json.gz"))):
    with gzip.open(p, "rt", encoding="utf-8") as f:
        for ft in json.load(f)["features"]:
            g = ft["geometry"]
            feats.append({"type": "Feature",
                          "geometry": {"type": g["type"], "coordinates": rnd(g["coordinates"])},
                          "properties": {"nom": ft["properties"].get("nom")}})

with open(out, "w", encoding="utf-8") as f:
    json.dump({"type": "FeatureCollection", "features": feats}, f, ensure_ascii=False, separators=(",", ":"))
print(len(feats), "communes")
