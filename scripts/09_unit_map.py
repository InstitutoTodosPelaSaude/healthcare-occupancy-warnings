# %%
"""Step 09: locator map of the monitored units (Figure 1A).

Draws the 17 units over the São Paulo metropolitan municipalities, with the
municipalities that host a unit highlighted.

Outputs
    results/maps/unit_map_sp.html
"""

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src import plt_maps
from src.paths import MAPS_DIR, MUNICIPALITY_GEOJSON, UNITS_METADATA, ensure_dir

ensure_dir(MAPS_DIR)

# %%
data = pd.read_csv(UNITS_METADATA, sep="\t")
data['city'] = data['city'].str.title()

unit_map = plt_maps.folium_mapping(
    data=data,
    path_geojson=MUNICIPALITY_GEOJSON,
)
unit_map.save(str(MAPS_DIR / 'unit_map_sp.html'))

print(f"Locator map for {len(data)} units written to {MAPS_DIR / 'unit_map_sp.html'}")
