import json, sys, math

def rdp(pts, eps):
    if len(pts) < 3:
        return pts
    (x1, y1), (x2, y2) = pts[0], pts[-1]
    dx, dy = x2 - x1, y2 - y1
    L = math.hypot(dx, dy)
    dmax, idx = 0, 0
    for i in range(1, len(pts) - 1):
        x, y = pts[i]
        d = abs(dy * x - dx * y + x2 * y1 - y2 * x1) / L if L else math.hypot(x - x1, y - y1)
        if d > dmax:
            dmax, idx = d, i
    if dmax > eps:
        return rdp(pts[: idx + 1], eps)[:-1] + rdp(pts[idx:], eps)
    return [pts[0], pts[-1]]

src, dst = sys.argv[1], sys.argv[2]
fc = json.load(open(src))
out = []
for f in fc["features"]:
    g = f["geometry"]
    eps = 0.00004 if f["properties"]["i"] <= 3 else 0.00007
    lines = [g["coordinates"]] if g["type"] == "LineString" else g["coordinates"]
    lines = [[[round(x, 5), round(y, 5)] for x, y in rdp(l, eps)] for l in lines]
    geom = {"type": "LineString", "coordinates": lines[0]} if len(lines) == 1 else {"type": "MultiLineString", "coordinates": lines}
    out.append({"type": "Feature", "geometry": geom, "properties": f["properties"]})
json.dump({"type": "FeatureCollection", "features": out}, open(dst, "w"), separators=(",", ":"))
print(len(out))
