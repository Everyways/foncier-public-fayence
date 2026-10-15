# Foncier public du Pays de Fayence

Carte interactive des parcelles non bâties détenues par des propriétaires publics (État, Département, communes, établissements publics, offices HLM) dans les 9 communes du Pays de Fayence (Var) : Bagnols-en-Forêt, Callian, Fayence, Mons, Montauroux, Saint-Paul-en-Forêt, Seillans, Tanneron, Tourrettes.

- Filtres par type de propriétaire, type de terrain (7 familles de natures cadastrales), commune, surface minimale et nom de propriétaire
- Mise en évidence des parcelles de 9 ha et plus et/ou situées à plus de N km (0,5 à 10 km) de toute habitation, critères cumulables
- Calque optionnel des terrains privés (masqué par défaut) : sociétés et SCI avec leur nom, parcelles de particuliers sans nom
- Fond routier simplifié (BD TOPO IGN)
- Pour chaque parcelle : liens vers la vue satellite Géoportail et Google Maps

## Publication

Le site est statique : `index.html` charge les fichiers de `data/`. Pour le publier, activez GitHub Pages sur la branche `main`, dossier racine (Settings → Pages).

Pour l'ouvrir en local, servez le dossier plutôt que d'ouvrir le fichier directement (le navigateur bloque les `fetch` en `file://`) :

```bash
python3 -m http.server 8000
```

## Données

| Fichier | Contenu | Source |
|---|---|---|
| `data/parcelles_publiques_2025.csv` | Parcelles des propriétaires publics, format DGFiP | [Fichiers des parcelles des personnes morales](https://www.data.gouv.fr/datasets/fichiers-des-locaux-et-des-parcelles-des-personnes-morales), situation au 1er janvier 2025 |
| `data/parcelles.geojson` | Tracés des parcelles ci-dessus, avec la distance à l'habitation la plus proche (propriété `h`, en mètres) | [Cadastre Etalab](https://cadastre.data.gouv.fr), millésime septembre 2026 ; bâtiments résidentiels [BD TOPO IGN](https://geoservices.ign.fr/bdtopo) |
| `data/prives.geojson` | Toutes les autres parcelles des 9 communes : sociétés et SCI (nom et nature de culture issus du fichier DGFiP), et parcelles de particuliers, dont le cadastre ne publie ni le nom ni la nature ; avec la distance aux habitations | Cadastre Etalab, DGFiP, BD TOPO IGN |
| `data/communes.geojson` | Limites des 9 communes | Cadastre Etalab |
| `data/routes.geojson` | Réseau routier simplifié | [BD TOPO IGN](https://geoservices.ign.fr/bdtopo) via la Géoplateforme |

Toutes les sources sont sous Licence Ouverte Etalab 2.0.

Environ 300 parcelles du fichier DGFiP 2025 n'ont pas de tracé dans le cadastre plus récent (parcelles divisées ou renumérotées) et n'apparaissent pas sur la carte. La surface affichée est la contenance cadastrale de chaque parcelle, sans regroupement des parcelles voisines.

La distance aux habitations est mesurée depuis le bord de la parcelle jusqu'au centre du bâtiment le plus proche dont l'usage principal ou secondaire est « Résidentiel » dans la BD TOPO (granges, hangars et bâtiments agricoles exclus). Les bâtiments situés jusqu'à 10 km hors du territoire sont pris en compte. Elle vaut 0 si une habitation se trouve dans la parcelle et est plafonnée à 15 km.

## Régénérer les données

```bash
scripts/build.sh
```

Le script télécharge les sources, filtre les communes et les propriétaires publics, joint les tracés et simplifie les routes. Pour un autre territoire, modifiez `COMMUNES` et `DEP` dans `scripts/build.sh` et la zone `BBOX` dans `scripts/roads.py`. Pour un autre millésime DGFiP, modifiez `DGFIP_URL` et le nom du fichier extrait.

Prérequis : `bash`, `curl`, `unzip`, `awk`, `python3` (bibliothèque standard uniquement).

## Avertissement

Une parcelle publique n'est pas forcément accessible ou disponible : forêts domaniales, terrains militaires, réserves et domaine privé des collectivités ont leurs propres règles.
