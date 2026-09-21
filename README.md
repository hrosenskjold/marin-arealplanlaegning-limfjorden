# Marin arealplanlægning – Limfjorden ved Aalborg (testudkast)

Første udkast til en webløsning der viser GIS-polygoner på et kort og lader
brugeren vægte flere kriterier mod hinanden med skydere. Den samlede
egnethedsscore pr. polygon genberegnes og kortet omfarves live, uden
sideindlæsning. Layoutet trækker på den rolige, institutionelle stil fra
[marinnatur.dk](https://marinnatur.dk).

**Alle data i dette repo er syntetiske dummy-data uden faglig værdi** —
formålet er at afprøve layout, datastruktur og interaktion, før der
kobles rigtige data på.

## Sådan ser det ud

Kort med et klippet gitter af testceller over en forenklet "Limfjorden ved
Aalborg"-form, en sidebar med fire vægtningsskydere, en signaturforklaring
og et detaljepanel der åbner ved klik på en celle.

## Projektstruktur

```
data/
  generate_dummy_data.py     Genererer alle dummy-data (kør igen for nye tal)
  source/
    marin_kriterier.gpkg     GeoPackage m. 2 lag: kriterier_grid + studieomraade
    shapefile/                Samme 2 lag som Shapefiles (.shp/.dbf/.shx/.prj)

web/                          Selve webløsningen (statisk site, ingen build-step)
  index.html
  css/style.css
  js/app.js
  data/
    kriterier_config.json    Titel, undertitel og kriterieliste (se nedenfor)
    kriterier_grid.geojson   Gitterceller m. kriterieværdier, WGS84
    studieomraade.geojson    Omrids af testområdet, WGS84

.github/workflows/deploy.yml GitHub Actions: deployer web/ til GitHub Pages
```

`data/source/*` er "kildedata" (det man ville redigere i QGIS/ArcGIS).
`web/data/*.geojson` er den webklare eksport i WGS84 (EPSG:4326), genereret
af samme script. Webløsningen indlæser **kun** filerne i `web/data/` — den
læser aldrig GeoPackage eller Shapefile direkte (browsere kan ikke det).

## Kør lokalt

Webløsningen er et rent statisk site (HTML/CSS/vanilla JS + Leaflet fra
CDN). Den bruger `fetch()` til at hente sine JSON/GeoJSON-filer, så den skal
serveres over HTTP — at åbne `index.html` direkte som fil (`file://`)
blokeres af browserens CORS-regler.

```bash
cd web
python -m http.server 8765
# åbn http://localhost:8765
```

## Gendan/regenerér dummy-data

```bash
pip install geopandas numpy shapely pyogrio
python data/generate_dummy_data.py
```

Scriptet bygger en forenklet fjordform, lægger et 350 m gitter ned over
den, klipper det til fjordformen og genererer fire rumligt sammenhængende
"tilfældige" kriterieværdier (0–100) pr. celle. Det skriver derefter både
GeoPackage, Shapefiles og web-GeoJSON i én kørsel — ret `CELL_SIZE_M` eller
`CRITERIA` øverst i scriptet for at justere opløsning/antal kriterier.

## Sådan styres siden via GitHub

Meningen er at indhold kan opdateres ved at redigere filer i repoet og
pushe/merge til `main` — GitHub Actions deployer automatisk til GitHub
Pages, uden serverdrift.

- **Titel, undertitel, kriterienavne, beskrivelser og standardvægte:**
  redigér `web/data/kriterier_config.json` direkte (fx via GitHubs
  webeditor). Sliderne i sidebaren bygges dynamisk ud fra denne fil, så
  ændringer kræver ikke kodeændringer.
- **Selve GIS-dataene:** erstat `data/source/marin_kriterier.gpkg` (eller
  shapefilene) med rigtige data — behold felt-/lagnavnene, eller opdatér
  `kriterier_config.json`'s `felt`-værdier tilsvarende — kør
  `generate_dummy_data.py`-logikken (eller din egen eksport) for at
  producere nye `web/data/*.geojson`, og commit resultatet.
- **Hosting:** aktivér Pages under Settings → Pages → Source:
  *GitHub Actions* i det GitHub-repo, dette bliver pushet til.
  Workflowet i `.github/workflows/deploy.yml` deployer `web/`-mappen ved
  hvert push til `main`.

## Kendte begrænsninger (testudkast)

- Fjordformen er håndtegnet/forenklet — **ikke** en autoritativ kystlinje.
- Kriterieværdierne er tilfældigt genereret (glatte Gauss-felter for at
  se rumligt plausible ud) og har ingen faglig betydning.
- Ingen adgangsstyring/login — statisk offentligt site.
- Ingen automatisk konvertering fra GeoPackage → GeoJSON i CI endnu;
  `web/data/*.geojson` skal genereres lokalt og committes.
