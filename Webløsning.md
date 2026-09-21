En online platform der kan vise: 
- gis-polygoner
- sliders der vægter de data ift. hinanden

SKal kunne styres via GitHUB
Have et flot layout, som giver referencer til marinnatur.dk

---

## Status: første udkast er live

**Se det her:** https://hrosenskjold.github.io/marin-arealplanlaegning-limfjorden/
**Repo:** https://github.com/hrosenskjold/marin-arealplanlaegning-limfjorden

Sådan er de fire punkter i oplægget løst:

- **GIS-polygoner** — et 350 m gitter af testceller er klippet til en
  forenklet Limfjord-form ved Aalborg og vises på et Leaflet-kort.
  Cellerne er syntetiske dummy-data (se `data/generate_dummy_data.py`),
  leveret som både GeoPackage og Shapefiles under `data/source/`, samt
  som webklar GeoJSON under `web/data/`.
- **Sliders der vægter data ift. hinanden** — sidebaren har én skyder pr.
  kriterie (bundforhold, vanddybde, strømforhold, eksisterende
  naturværdi). Kortet genberegner og omfarver hver celles vægtede
  egnethedsscore live, når man flytter en skyder — uden at genindlæse
  siden. Klik på en celle viser bidraget fra hvert kriterie.
- **Styres via GitHub** — koden ligger i et git-repo, pushet til GitHub.
  Et GitHub Actions-workflow deployer automatisk til GitHub Pages ved
  hvert push til `master`. Titel, kriterienavne/-beskrivelser og
  standardvægte kan ændres direkte i `web/data/kriterier_config.json` —
  fx via GitHubs webeditor — uden at skulle røre koden.
- **Layout der refererer til marinnatur.dk** — hvidt/lyst institutionelt
  layout, mørk navy tekst, rolig blå farveskala til kortet, minimal
  navigation — samme rolige, "faglige" stil som marinnatur.dk.

Versionering, arkitekturvalg og best practice er dokumenteret i
[`README.md`](README.md) og [`CHANGELOG.md`](CHANGELOG.md). Nuværende
version: **v0.1.0** (se CHANGELOG for detaljer).

**Vigtigt:** alle data er syntetiske/tilfældigt genererede test-data uden
faglig værdi — kun til at afprøve layout og funktionalitet, før rigtige
data kobles på.