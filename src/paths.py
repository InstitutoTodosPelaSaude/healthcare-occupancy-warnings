"""Repository paths, anchored on this file rather than the working directory.

Every script imports from here, so the pipeline runs the same way from the
repository root, from `scripts/`, or from a notebook.
"""

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

DATA_DIR = REPO_ROOT / "data"
OCCUPANCY_DIR = DATA_DIR / "occupancy"
PRIVATE_LABS_DIR = DATA_DIR / "private_labs"
PUBLIC_CASES_DIR = DATA_DIR / "public_cases"
GEO_DIR = DATA_DIR / "geo"

UNITS_METADATA = DATA_DIR / "units_metadata.tsv"
MUNICIPALITY_GEOJSON = GEO_DIR / "sp_rj_municipality_crs.geojson"

RESULTS_DIR = REPO_ROOT / "results"
UNIT_OVERVIEW_DIR = RESULTS_DIR / "unit_overview"
DTW_DIR = RESULTS_DIR / "dtw"
GRANGER_DIR = RESULTS_DIR / "granger"
OUTBREAKS_DIR = RESULTS_DIR / "outbreaks"
SPATIAL_DIR = RESULTS_DIR / "spatial_associations"
MAPS_DIR = RESULTS_DIR / "maps"
LEAD_TIME_DIR = RESULTS_DIR / "lead_time"
SUPP_TABLES_DIR = RESULTS_DIR / "supp_tables"

CONSOLIDATED_DATA = RESULTS_DIR / "consolidated_data_sp.tsv"
CONSOLIDATED_DATA_INTERMEDIATE = RESULTS_DIR / "consolidated_data_sp_intermediate.tsv"


def ensure_dir(*paths):
    """Create each directory (and its parents) if it does not exist yet."""
    for path in paths:
        Path(path).mkdir(parents=True, exist_ok=True)
    return paths[0] if len(paths) == 1 else paths
