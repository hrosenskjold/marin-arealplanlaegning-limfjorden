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

## Versionering

Projektet følger [Semantic Versioning](https://semver.org/lang/da/)
(`MAJOR.MINOR.PATCH`) og [Keep a Changelog](https://keepachangelog.com/da/1.0.0/):

- Alle mærkbare ændringer beskrives i [`CHANGELOG.md`](CHANGELOG.md) under
  `[Unreleased]`, efterhånden som de laves.
- Versionsnummeret er den ene sandhedskilde i
  `web/data/kriterier_config.json` (`"version"`) — appen viser det selv
  nederst i sidebaren, med link til changeloggen.
- Ved en udgivelse: flyt `[Unreleased]`-punkterne til et nyt afsnit
  `[X.Y.Z] - YYYY-MM-DD` i `CHANGELOG.md`, opdatér `version` i
  `kriterier_config.json` tilsvarende, commit, og tag:

  ```bash
  git tag -a vX.Y.Z -m "vX.Y.Z"
  git push origin vX.Y.Z
  ```

  Brug MAJOR ved brud på datastruktur/felt- eller lagnavne (alt der kan
  ødelægge en integration), MINOR ved nye kriterier/funktioner, og PATCH
  ved rettelser eller rene data-opdateringer.
- Overvej at oprette et [GitHub Release](../../releases) pr. tag, så der
  er et klart historisk overblik ud over selve commit-loggen.

## Best practice / arkitekturvalg i dette udkast

- **Statisk site, ingen server/build-step.** Ren HTML/CSS/vanilla JS +
  Leaflet fra CDN. Minimerer angrebsflade og driftsbyrde — hele
  løsningen kan hostes gratis på GitHub Pages.
- **CDN-afhængigheder er pinnet med SRI-hash** (`integrity="sha256-..."`
  i `index.html`) og fast versionsnummer (Leaflet 1.9.4), så en
  kompromitteret eller ændret CDN-fil ikke kan injicere kode uden at
  browseren blokerer den.
- **Skarp adskillelse af data-lag:**
  - `data/source/` = kildedata (GeoPackage/Shapefiles), det man redigerer i QGIS/ArcGIS.
  - `web/data/*.geojson` = webklar eksport (WGS84, afrundet præcision) — genereret, aldrig redigeret i hånden.
  - `web/data/kriterier_config.json` = UI-konfiguration (titel, kriterier, vægte) — redigeres direkte, ingen kodeændring nødvendig.
- **`generate_dummy_data.py` er deterministisk** (faste random-seeds), så
  outputtet er reproducerbart — CI genkører scriptet og fejler, hvis
  resultatet afviger fra det committede (se `validate.yml`).
- **`noindex`** (`<meta name="robots">` + `web/robots.txt`) så testudkastet
  ikke dukker op i søgemaskiner, mens det stadig er et udkast.
- **Farver er tilgængelighedsvalideret** via en sekventiel enkelt-hue-rampe
  (lav→høj egnethed), ikke en vilkårlig regnbue — holder det læsbart for
  farveblinde og i gråtoneprint.
- **`.gitattributes`** tvinger LF-linjeskift på tekstfiler på tværs af
  Windows/macOS/Linux-bidragydere, så diffs ikke fyldes med
  linjeskifts-støj.
- **To CI-workflows** (`.github/workflows/`):
  `deploy.yml` deployer `web/` til Pages ved push til `master`;
  `validate.yml` kører på pull requests og tjekker gyldig JSON/GeoJSON
  samt data-reproducerbarhed, så fejl fanges før merge.
- **Anbefalet git-workflow fremadrettet:** lav ændringer på en
  feature-branch og pull request i stedet for at pushe direkte til
  `master`, da `master` auto-deployer til den offentlige URL. For et
  solo-testudkast er direkte push til `master` acceptabelt, men skift til
  PR-baseret workflow så snart flere bidrager, eller aktivér branch
  protection under Settings → Branches.
- **Ikke inkluderet endnu (kandidater til senere):** automatisk
  Playwright-smoke-test i CI (skærmbillede + konsol-tjek ved hver PR),
  license-fil (afklares med kommunens retningslinjer), og
  adgangsstyring hvis/når siden skal vise ikke-offentlige data.

## Kendte begrænsninger (testudkast)

- Fjordformen er håndtegnet/forenklet — **ikke** en autoritativ kystlinje.
- Kriterieværdierne er tilfældigt genereret (glatte Gauss-felter for at
  se rumligt plausible ud) og har ingen faglig betydning.
- Ingen adgangsstyring/login — statisk offentligt site.
- Ingen automatisk konvertering fra GeoPackage → GeoJSON i CI endnu;
  `web/data/*.geojson` skal genereres lokalt og committes.
