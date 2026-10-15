"""Construit le calque des terrains privés : toutes les parcelles cadastrales des communes
qui n'appartiennent pas à un propriétaire public.

Usage : python3 prives.py PM_25_NB_830.csv DOSSIER_PARCELLES_ETALAB SORTIE.geojson

- Parcelle d'une personne morale privée (fichier DGFiP, groupes 0, 6, 7, 8) :
  g = « Société ou SCI », avec la dénomination et la nature de culture.
- Parcelle absente du fichier DGFiP : propriétaire particulier (ou entreprise
  individuelle, SCI unipersonnelle), non publié. g = « Particulier », sans nom.
- Parcelles publiques (groupes 1 à 5 et 9) exclues : elles sont dans parcelles.geojson.
"""
import csv, glob, gzip, json, os, sys

pm_csv, geo_dir, out = sys.argv[1], sys.argv[2], sys.argv[3]

pm, names = {}, {}
with open(pm_csv, encoding="utf-8-sig", newline="") as f:
    r = csv.reader(f, delimiter=";")
    next(r)
    for row in r:
        pref = (row[4].strip() or "000").zfill(3)
        pid = f"{row[0].strip()}{row[2]}{pref}{row[5].strip().rjust(2, '0')}{row[6].strip().zfill(4)}"
        names[f"{row[0].strip()}{row[2]}"] = row[3].strip()
        grp = row[20].strip()[:1]
        p = pm.setdefault(pid, {"pub": False, "d": set(), "k": set()})
        if grp in "1234559":
            p["pub"] = True
        else:
            p["d"].add(row[23].strip())
        if row[15].strip():
            p["k"].add(row[15].split(" - ")[-1].strip())

def rnd(c):
    if isinstance(c[0], (int, float)):
        return [round(c[0], 5), round(c[1], 5)]
    return [rnd(x) for x in c]

feats, n_soc, n_part = [], 0, 0
for fp in sorted(glob.glob(os.path.join(geo_dir, "*.json.gz"))):
    with gzip.open(fp, "rt", encoding="utf-8") as f:
        fc = json.load(f)
    for ft in fc["features"]:
        pr = ft["properties"]
        o = pm.get(pr["id"])
        if o and o["pub"]:
            continue
        props = {"c": names.get(pr["commune"], pr["commune"]), "s": pr["section"],
                 "n": str(pr["numero"]).lstrip("0"), "a": int(pr.get("contenance") or 0)}
        if o:
            props.update(g="Société ou SCI", d=" / ".join(sorted(o["d"])), k=", ".join(sorted(o["k"])))
            n_soc += 1
        else:
            props.update(g="Particulier", d="", k="")
            n_part += 1
        g = ft["geometry"]
        feats.append({"type": "Feature", "geometry": {"type": g["type"], "coordinates": rnd(g["coordinates"])},
                      "properties": props})

with open(out, "w", encoding="utf-8") as f:
    json.dump({"type": "FeatureCollection", "features": feats}, f, ensure_ascii=False, separators=(",", ":"))
print(f"{n_soc} parcelles de sociétés ou SCI, {n_part} parcelles de particuliers")
