# Télécharge le réseau routier BD TOPO (IGN) sur la zone BBOX ci-dessous (lat_min,lon_min,lat_max,lon_max).
import json, sys, subprocess, urllib.parse

out = sys.argv[1]
base = "https://data.geopf.fr/wfs/ows"
cql = ("BBOX(geometrie,43.50,6.52,43.76,6.92) AND importance IN ('1','2','3','4','5') "
       "AND fictif=false AND etat_de_l_objet='En service' AND position_par_rapport_au_sol<>'-1'")
feats, start = [], 0
while True:
    q = urllib.parse.urlencode({"SERVICE": "WFS", "VERSION": "2.0.0", "REQUEST": "GetFeature",
        "TYPENAMES": "BDTOPO_V3:troncon_de_route", "OUTPUTFORMAT": "application/json",
        "PROPERTYNAME": "geometrie,importance,cpx_numero,nature", "CQL_FILTER": cql,
        "COUNT": "5000", "STARTINDEX": str(start), "SORTBY": "cleabs"})
    r = subprocess.run(["curl", "-sS", "--retry", "4", "--retry-all-errors", "-m", "180", base + "?" + q],
                       capture_output=True, text=True)
    try:
        fc = json.loads(r.stdout)
    except Exception:
        print("bad response", r.stdout[:500], r.stderr[:300]); sys.exit(1)
    fs = fc.get("features", [])
    for f in fs:
        p = f["properties"]
        g = f["geometry"]
        if g["type"] == "LineString":
            g["coordinates"] = [[round(c[0], 5), round(c[1], 5)] for c in g["coordinates"]]
        else:
            g["coordinates"] = [[[round(c[0], 5), round(c[1], 5)] for c in l] for l in g["coordinates"]]
        feats.append({"type": "Feature", "geometry": g,
                      "properties": {"i": int(p["importance"]), "r": p.get("cpx_numero") or ""}})
    print("got", len(fs), "total", len(feats), flush=True)
    if len(fs) < 5000:
        break
    start += 5000
json.dump({"type": "FeatureCollection", "features": feats}, open(out, "w"), separators=(",", ":"))
