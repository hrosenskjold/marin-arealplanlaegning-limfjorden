"""
Genererer syntetiske (dummy) GIS-testdata for Limfjorden ved Aalborg.

Formaal: give web-loesningen noget realistisk udseende testdata at arbejde med,
foer der leveres rigtige data. Alle vaerdier er tilfaeldigt genererede og har
IKKE nogen faglig/videnskabelig vaegt.

Output:
  - data/source/marin_kriterier.gpkg   (GeoPackage, to lag: kriterier_grid + studieomraade)
  - data/source/shapefile/*.shp        (samme to lag som shapefiles)
  - web/data/*.geojson                 (WGS84 GeoJSON til brug i webkortet)

Koer scriptet igen for at regenerere data:
    python data/generate_dummy_data.py
"""

import sqlite3
from pathlib import Path

import geopandas as gpd
import numpy as np
import shapely
from shapely.geometry import LineString, Point, box

# ---------------------------------------------------------------------------
# Opsaetning
# ---------------------------------------------------------------------------

RANDOM_SEED = 42
CELL_SIZE_M = 350  # gitterstoerrelse i meter
SOURCE_CRS = "EPSG:4326"   # lon/lat, til at definere den grove fjordform
WORK_CRS = "EPSG:25832"    # ETRS89 / UTM zone 32N - dansk standard, meter
WEB_CRS = "EPSG:4326"      # til Leaflet/GeoJSON

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parent
GPKG_PATH = HERE / "source" / "marin_kriterier.gpkg"
SHP_DIR = HERE / "source" / "shapefile"
WEB_DATA_DIR = REPO_ROOT / "web" / "data"

CRITERIA = {
    # feltnavn (<=10 tegn, shapefile-kompatibelt): (n_seeds, sigma_min_m, sigma_max_m, rng_seed)
    "bund":   dict(n_seeds=9, sigma=(700, 2600), seed=1),   # bundforhold / substrat
    "dybde":  dict(n_seeds=6, sigma=(1200, 4000), seed=2),  # vanddybde
    "stroem": dict(n_seeds=10, sigma=(500, 2000), seed=3),  # stroemforhold
    "natur":  dict(n_seeds=7, sigma=(800, 3000), seed=4),   # eksisterende naturvaerdi
}


# ---------------------------------------------------------------------------
# 1. Byg en grov, syntetisk "fjordform" omkring Aalborg (IKKE rigtig kystlinje)
# ---------------------------------------------------------------------------

def build_water_polygon() -> gpd.GeoSeries:
    """Simplificeret fjordform: en bugtet kanal med to bassiner i hver ende.

    Koordinaterne er haandtegnede for at ligne Limfjordens forloeb forbi
    Aalborg/Noerresundby (smal midt paa, bredere bassiner mod vest og oest).
    Det er en dummy-geometri til test - ikke en autoritativ kystlinje.
    """
    centerline = LineString(
        [
            (9.78, 57.050),
            (9.83, 57.058),
            (9.87, 57.053),
            (9.905, 57.048),
            (9.920, 57.045),  # "Aalborg-snaevringen"
            (9.940, 57.046),
            (9.965, 57.052),
            (10.00, 57.046),
            (10.05, 57.040),
        ]
    )
    west_basin = Point(9.795, 57.062)
    east_basin = Point(10.015, 57.043)

    line_gs = gpd.GeoSeries([centerline], crs=SOURCE_CRS).to_crs(WORK_CRS)
    west_gs = gpd.GeoSeries([west_basin], crs=SOURCE_CRS).to_crs(WORK_CRS)
    east_gs = gpd.GeoSeries([east_basin], crs=SOURCE_CRS).to_crs(WORK_CRS)

    channel = line_gs.iloc[0].buffer(950)
    west = west_gs.iloc[0].buffer(4800)
    east = east_gs.iloc[0].buffer(3600)

    water = channel.union(west).union(east).buffer(120).buffer(-120)  # gloed hjoerner
    return gpd.GeoSeries([water], crs=WORK_CRS)


# ---------------------------------------------------------------------------
# 2. Lav et kvadratisk gitter og klip det til fjordformen
# ---------------------------------------------------------------------------

def build_grid(water_geom, cell_size: float) -> gpd.GeoDataFrame:
    xmin, ymin, xmax, ymax = water_geom.bounds
    xs = np.arange(xmin, xmax, cell_size)
    ys = np.arange(ymin, ymax, cell_size)

    rows = []
    cell_area = cell_size * cell_size
    for x in xs:
        for y in ys:
            cell = box(x, y, x + cell_size, y + cell_size)
            if not cell.intersects(water_geom):
                continue
            clipped = cell.intersection(water_geom)
            if clipped.is_empty or clipped.area < 0.15 * cell_area:
                continue
            rows.append(clipped)

    gdf = gpd.GeoDataFrame(geometry=rows, crs=WORK_CRS)
    gdf.insert(0, "cell_id", range(1, len(gdf) + 1))
    gdf["area_m2"] = gdf.geometry.area.round(1)
    return gdf


# ---------------------------------------------------------------------------
# 3. Generer glatte, rumligt sammenhaengende "tilfaeldige" kriterievaerdier
# ---------------------------------------------------------------------------

def gaussian_random_field(xy: np.ndarray, n_seeds: int, sigma_range, seed: int) -> np.ndarray:
    """Summerer tilfaeldige Gauss-bump'er -> glatte, plausible rumlige moenstre
    (i stedet for hvid stoej, som ville se helt urealistisk ud paa et kort)."""
    rng = np.random.default_rng(seed)
    xmin, ymin = xy.min(axis=0)
    xmax, ymax = xy.max(axis=0)

    seed_xy = rng.uniform([xmin, ymin], [xmax, ymax], size=(n_seeds, 2))
    sigmas = rng.uniform(sigma_range[0], sigma_range[1], size=n_seeds)
    amps = rng.uniform(-1.0, 1.0, size=n_seeds)

    values = np.zeros(len(xy))
    for (sx, sy), sigma, amp in zip(seed_xy, sigmas, amps):
        d2 = (xy[:, 0] - sx) ** 2 + (xy[:, 1] - sy) ** 2
        values += amp * np.exp(-d2 / (2 * sigma ** 2))

    values -= values.min()
    if values.max() > 0:
        values = values / values.max()
    return np.round(values * 100, 1)


def add_criteria(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    centroids = np.column_stack([gdf.geometry.centroid.x, gdf.geometry.centroid.y])
    for field, cfg in CRITERIA.items():
        gdf[field] = gaussian_random_field(
            centroids, n_seeds=cfg["n_seeds"], sigma_range=cfg["sigma"], seed=cfg["seed"]
        )
    return gdf


# ---------------------------------------------------------------------------
# 4. Skriv output: GeoPackage (multi-lag), Shapefiles, og web-GeoJSON (WGS84)
# ---------------------------------------------------------------------------

def pin_gpkg_timestamps(gpkg_path: Path) -> None:
    """GDAL stamper gpkg_contents.last_change med selve skrivetidspunktet,
    saa to koersler med 100% identiske data alligevel giver forskellige
    filer byte-for-byte. Saet en fast dummy-vaerdi, saa output er
    reproducerbart (og CI's diff-tjek giver mening)."""
    con = sqlite3.connect(gpkg_path)
    con.execute("UPDATE gpkg_contents SET last_change = '2026-01-01T00:00:00.000Z'")
    con.commit()
    con.close()


def main():
    GPKG_PATH.parent.mkdir(parents=True, exist_ok=True)
    SHP_DIR.mkdir(parents=True, exist_ok=True)
    WEB_DATA_DIR.mkdir(parents=True, exist_ok=True)

    water = build_water_polygon()
    study_area = gpd.GeoDataFrame(
        {
            "navn": ["Limfjorden ved Aalborg (testomraade)"],
            "beskriv": ["Syntetisk/forenklet afgraensning - kun til test, ikke autoritativ kystlinje."],
        },
        geometry=water.values,
        crs=WORK_CRS,
    )

    grid = build_grid(water.iloc[0], CELL_SIZE_M)
    grid = add_criteria(grid)

    print(f"Studieomraade areal: {study_area.geometry.area.iloc[0] / 1e6:.1f} km2")
    print(f"Gitterceller genereret: {len(grid)}")

    # --- GeoPackage: to lag i samme fil ---
    if GPKG_PATH.exists():
        GPKG_PATH.unlink()
    study_area.to_file(GPKG_PATH, layer="studieomraade", driver="GPKG")
    grid.to_file(GPKG_PATH, layer="kriterier_grid", driver="GPKG")
    pin_gpkg_timestamps(GPKG_PATH)  # goer output byte-for-byte reproducerbart
    print(f"Skrev GeoPackage: {GPKG_PATH.relative_to(REPO_ROOT)}")

    # --- Shapefiles: et lag pr. fil ---
    study_area.to_file(SHP_DIR / "studieomraade.shp", driver="ESRI Shapefile", encoding="utf-8")
    grid.to_file(SHP_DIR / "kriterier_grid.shp", driver="ESRI Shapefile", encoding="utf-8")
    print(f"Skrev shapefiles: {SHP_DIR.relative_to(REPO_ROOT)}")

    # --- Web GeoJSON: reprojiceret til WGS84, koordinater afrundet til ~11 cm
    #     (6 decimaler) for at holde filstoerrelsen nede i browseren ---
    study_area_web = study_area.to_crs(WEB_CRS)
    study_area_web.geometry = shapely.set_precision(study_area_web.geometry.values, grid_size=1e-6)
    study_area_web.to_file(WEB_DATA_DIR / "studieomraade.geojson", driver="GeoJSON")

    grid_web = grid.to_crs(WEB_CRS)
    grid_web.geometry = shapely.set_precision(grid_web.geometry.values, grid_size=1e-6)
    grid_web.to_file(WEB_DATA_DIR / "kriterier_grid.geojson", driver="GeoJSON")
    print(f"Skrev web-GeoJSON: {WEB_DATA_DIR.relative_to(REPO_ROOT)}")


if __name__ == "__main__":
    main()
