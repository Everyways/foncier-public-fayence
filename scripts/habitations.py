"""Télécharge les bâtiments résidentiels de la BD TOPO (IGN) et enregistre leur centre.

Usage : python3 habitations.py SORTIE.json [lat_min,lon_min,lat_max,lon_max]

Un bâtiment est retenu si son usage principal ou secondaire est « Résidentiel »
et s'il est en service. La zone par défaut couvre le Pays de Fayence élargi de
10 km, pour que les maisons situées hors du territoire comptent aussi.
"""
import json, subprocess, sys, urllib.parse

out = sys.argv[1]
bbox = sys.argv[2] if len(sys.argv) > 2 else "43.41,6.39,43.85,7.04"
base = "https://data.geopf.fr/wfs/ows"
cql = (f"BBOX(geometrie,{bbox}) AND (usage_1='Résidentiel' OR usage_2='Résidentiel') "
       "AND etat_de_l_objet='En service'")

def centroid(geom):
    # Moyenne des sommets de l'anneau extérieur : suffisant pour un bâtiment (erreur de quelques mètres).
    polys = [geom["coordinates"]] if geom["type"] == "Polygon" else geom["coordinates"]
    ring = max((p[0] for p in polys), key=len)
    xs = [c[0] for c in ring[:-1]] or [ring[0][0]]
    ys = [c[1] for c in ring[:-1]] or [ring[0][1]]
    return [round(sum(xs) / len(xs), 6), round(sum(ys) / len(ys), 6)]

pts, start = [], 0
while True:
    q = urllib.parse.urlencode({"SERVICE": "WFS", "VERSION": "2.0.0", "REQUEST": "GetFeature",
        "TYPENAMES": "BDTOPO_V3:batiment", "OUTPUTFORMAT": "application/json",
        "PROPERTYNAME": "geometrie", "CQL_FILTER": cql,
        "COUNT": "5000", "STARTINDEX": str(start), "SORTBY": "cleabs"})
    r = subprocess.run(["curl", "-sS", "--retry", "5", "--retry-all-errors", "-m", "300", base + "?" + q],
                       capture_output=True, text=True)
    try:
        fs = json.loads(r.stdout)["features"]
    except Exception:
        sys.exit(f"Réponse invalide à l'index {start} : {r.stdout[:300]} {r.stderr[:300]}")
    pts += [centroid(f["geometry"]) for f in fs if f.get("geometry")]
    print(f"{len(pts)} bâtiments", flush=True)
    if len(fs) < 5000:
        break
    start += 5000

with open(out, "w") as f:
    json.dump(pts, f, separators=(",", ":"))
