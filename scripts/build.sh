#!/usr/bin/env bash
# Régénère les fichiers de data/ à partir des sources ouvertes.
# Usage : scripts/build.sh  (depuis la racine du repo)
# Prérequis : bash, curl, unzip, awk, python3 (bibliothèque standard uniquement).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT

# Communes du Pays de Fayence (codes INSEE)
COMMUNES="83008 83029 83055 83080 83081 83117 83124 83133 83138"
DEP=83

# 1. Fichier DGFiP des parcelles des personnes morales (situation 2025, départements 57 à 976)
DGFIP_URL="https://data.economie.gouv.fr/api/v2/catalog/datasets/fichiers-des-locaux-et-des-parcelles-des-personnes-morales/attachments/fichier_des_parcelles_situation_2025_dpts_57_a_976_zip"
curl -sSL --retry 4 -o "$WORK/pm.zip" "$DGFIP_URL"
unzip -j -o -q "$WORK/pm.zip" "*PM_25_NB_${DEP}0.csv" -d "$WORK"
SRC="$WORK/PM_25_NB_${DEP}0.csv"

# 2. Filtre : communes du territoire + propriétaires publics
#    (groupes 1 État, 3 Département, 4 Commune, 5 Office HLM, 9 Établissement public)
CODES=$(for c in $COMMUNES; do printf '%s ' "${c:2}"; done)
{
  printf '\xef\xbb\xbf'
  head -1 "$SRC"
  awk -F';' -v codes="$CODES" 'BEGIN{n=split(codes,a," ");for(i=1;i<=n;i++)ok[a[i]]=1}
    NR>1 && ($3 in ok) && $21 ~ /^(1|3|4|5|9) /' "$SRC"
} > "$ROOT/data/parcelles_publiques_2025.csv"

# 3. Tracés cadastraux (Etalab) : parcelles et limites de communes
mkdir -p "$WORK/geo"
for c in $COMMUNES; do
  for kind in parcelles communes; do
    curl -sSL --retry 6 --retry-all-errors -o "$WORK/geo/${kind}_$c.json.gz" \
      "https://cadastre.data.gouv.fr/data/etalab-cadastre/latest/geojson/communes/$DEP/$c/cadastre-$c-$kind.json.gz"
  done
done
mkdir -p "$WORK/parc" && mv "$WORK"/geo/parcelles_*.json.gz "$WORK/parc/"
python3 -I "$ROOT/scripts/join.py" "$ROOT/data/parcelles_publiques_2025.csv" "$WORK/parc" "$ROOT/data/parcelles.geojson"
python3 -I "$ROOT/scripts/communes.py" "$WORK/geo" "$ROOT/data/communes.geojson"

# 4. Routes (BD TOPO IGN via le WFS de la Géoplateforme), puis simplification
python3 -I "$ROOT/scripts/roads.py" "$WORK/routes_raw.geojson"
python3 -I "$ROOT/scripts/simplify.py" "$WORK/routes_raw.geojson" "$ROOT/data/routes.geojson"

# 5. Distance de chaque parcelle à l'habitation la plus proche (bâtiments résidentiels BD TOPO,
#    zone élargie de 10 km autour du territoire)
python3 -I "$ROOT/scripts/habitations.py" "$WORK/habitations.json" "43.41,6.39,43.85,7.04"
python3 -I "$ROOT/scripts/distance.py" "$ROOT/data/parcelles.geojson" "$WORK/habitations.json"

echo "Données régénérées dans $ROOT/data"
