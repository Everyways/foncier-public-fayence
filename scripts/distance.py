"""Ajoute à chaque parcelle la distance (en mètres) à l'habitation la plus proche.

Usage : python3 distance.py parcelles.geojson habitations.json

La distance est mesurée depuis le bord de la parcelle : 0 si une habitation est
à l'intérieur. Elle est écrite dans la propriété « h » de chaque parcelle,
plafonnée à 15 000 m. Le fichier de parcelles est réécrit sur place.
"""
import json, math, sys

parc_path, hab_path = sys.argv[1], sys.argv[2]
CAP = 15000
CELL = 250.0  # taille de maille de l'index spatial, en mètres

# Projection locale équirectangulaire (précise à mieux que 0,5 % sur ce territoire)
LAT0 = math.radians(43.63)
KX, KY = 111320.0 * math.cos(LAT0), 110574.0
proj = lambda lon, lat: (lon * KX, lat * KY)

grid = {}
for lon, lat in json.load(open(hab_path)):
    x, y = proj(lon, lat)
    grid.setdefault((int(x // CELL), int(y // CELL)), []).append((x, y))

def seg_dist(px, py, ax, ay, bx, by):
    dx, dy = bx - ax, by - ay
    L = dx * dx + dy * dy
    t = 0.0 if L == 0 else max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / L))
    return math.hypot(px - (ax + t * dx), py - (ay + t * dy))

def inside(px, py, ring):
    c = False
    for i in range(len(ring) - 1):
        (ax, ay), (bx, by) = ring[i], ring[i + 1]
        if (ay > py) != (by > py) and px < (bx - ax) * (py - ay) / (by - ay) + ax:
            c = not c
    return c

def polys(geom):
    raw = [geom["coordinates"]] if geom["type"] == "Polygon" else geom["coordinates"]
    return [[[proj(*c) for c in ring] for ring in poly] for poly in raw]

def dist_to(px, py, pl):
    best = math.inf
    for poly in pl:
        outer, holes = poly[0], poly[1:]
        if inside(px, py, outer) and not any(inside(px, py, h) for h in holes):
            return 0.0
        for ring in poly:
            for i in range(len(ring) - 1):
                d = seg_dist(px, py, *ring[i], *ring[i + 1])
                if d < best:
                    best = d
    return best

fc = json.load(open(parc_path))
for n, f in enumerate(fc["features"]):
    pl = polys(f["geometry"])
    xs = [x for p in pl for r in p for x, _ in r]
    ys = [y for p in pl for r in p for _, y in r]
    x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
    r, best = 250.0, math.inf
    while True:
        for i in range(int((x0 - r) // CELL), int((x1 + r) // CELL) + 1):
            for j in range(int((y0 - r) // CELL), int((y1 + r) // CELL) + 1):
                for px, py in grid.get((i, j), ()):
                    # Écart à la boîte englobante : borne inférieure, évite le calcul exact si inutile
                    gx = max(x0 - px, 0, px - x1)
                    gy = max(y0 - py, 0, py - y1)
                    if math.hypot(gx, gy) >= best:
                        continue
                    d = dist_to(px, py, pl)
                    if d < best:
                        best = d
        if best <= r or r >= CAP:
            break
        r *= 2
    f["properties"]["h"] = int(min(best, CAP))
    if n % 500 == 0:
        print(n, flush=True)

with open(parc_path, "w", encoding="utf-8") as fo:
    json.dump(fc, fo, ensure_ascii=False, separators=(",", ":"))
hs = [f["properties"]["h"] for f in fc["features"]]
for km in (0.5, 1, 2, 3, 5):
    print(f"> {km} km : {sum(h >= km * 1000 for h in hs)} parcelles")
