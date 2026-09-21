# Changelog

Alle mærkbare ændringer i dette projekt dokumenteres i denne fil.

Formatet følger [Keep a Changelog](https://keepachangelog.com/da/1.0.0/),
og projektet følger [Semantic Versioning](https://semver.org/lang/da/)
(`MAJOR.MINOR.PATCH`): MAJOR ved brud på datastruktur/URL'er, MINOR ved nye
funktioner (fx nye kriterier/lag), PATCH ved rettelser og data-opdateringer.

Den kørende version vises i sidebarens footer på selve siden og i
`web/data/kriterier_config.json` (`version`-feltet).

## [Unreleased]

## [0.1.0] - 2026-09-21

### Tilføjet

- Første udkast af webløsningen: Leaflet-kort der viser GIS-polygoner
  farvet efter en vægtet egnethedsscore.
- Sidebar med live skydere til at vægte kriterier mod hinanden, bygget
  dynamisk ud fra `web/data/kriterier_config.json`.
- Klik-for-detaljer-panel og hover-tooltip pr. celle.
- Dummy-testdata for Limfjorden ved Aalborg: 350 m gitter klippet til en
  forenklet fjordform, fire syntetiske kriterier, leveret som GeoPackage,
  Shapefiles og web-GeoJSON (`data/generate_dummy_data.py`).
- GitHub Actions: deploy til GitHub Pages ved push til `master`, samt
  en valideringsworkflow der tjekker JSON/GeoJSON og data-reproducerbarhed
  på pull requests.
- Live eksempel: <https://hrosenskjold.github.io/marin-arealplanlaegning-limfjorden/>

[Unreleased]: https://github.com/hrosenskjold/marin-arealplanlaegning-limfjorden/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/hrosenskjold/marin-arealplanlaegning-limfjorden/releases/tag/v0.1.0
