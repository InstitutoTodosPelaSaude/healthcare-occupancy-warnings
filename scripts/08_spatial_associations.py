# %%
"""Step 08: geographic distance matrix and LISA spatial clustering.

Builds the pairwise Haversine distance matrix across the 17 units
(Figure S2), then runs the Local Indicators of Spatial Association test on
weekly occupancy for the outbreak and non-outbreak weeks, using a k-nearest
neighbours spatial weights matrix with k = 4 (Figure S1 and the map panels
of Figure 4).

This is the source of Table S4.

Outputs
    results/spatial_associations/distance_matrix.tsv
    results/spatial_associations/distance_matrix_heatmap.{png,svg}
    results/spatial_associations/lisa_<week>.{tsv,png,svg}
"""

import sys
from pathlib import Path

import geopandas as gpd
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from esda.moran import Moran_Local
from libpysal.weights import KNN
from shapely.geometry import Point

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src import geospatial, units
from src.paths import SPATIAL_DIR, UNITS_METADATA, UNIT_OVERVIEW_DIR, ensure_dir

ensure_dir(SPATIAL_DIR)

# Number of nearest neighbours in the spatial weights matrix
KNN_K = 4
SIGNIFICANCE = 0.05

# LISA p-values come from conditional randomisation, so they move slightly
# between runs. The seed makes this step deterministic; the permutation count
# matches the one used for the published tables. Cluster assignments and
# significance calls are stable either way, only the third decimal of lisa_p
# shifts between runs.
PERMUTATIONS = 999
RANDOM_SEED = 20230826

# Moran quadrants: 1 high-high, 2 low-high, 3 low-low, 4 high-low
LISA_COLORS = {1: 'red', 2: 'lightblue', 3: 'blue', 4: 'pink'}

# %%
df = pd.read_csv(UNITS_METADATA, sep="\t")
df = df[['name', 'lat', 'lon']]

distance_matrix = geospatial.create_distance_matrix(df)
distance_matrix.to_csv(SPATIAL_DIR / "distance_matrix.tsv", sep="\t")

# %%
# Figure S2: hierarchically clustered distance heatmap
sns.clustermap(
    distance_matrix,
    cmap="Oranges",
    linewidths=0.1,
    cbar_kws={'label': 'Distance (km)'},
    figsize=(8, 8),
)
plt.savefig(SPATIAL_DIR / "distance_matrix_heatmap.png", dpi=300)
plt.savefig(SPATIAL_DIR / "distance_matrix_heatmap.svg",
            facecolor='white', bbox_inches='tight')
plt.close('all')

# %%
merged_data_weekly = pd.read_csv(
    UNIT_OVERVIEW_DIR / 'by_unit' / 'weekly_percentage_by_unit.tsv',
    sep="\t", index_col=0,
)

missing_columns = [
    col for col in distance_matrix.columns if col not in merged_data_weekly.columns
]
if missing_columns:
    raise ValueError(f"Units missing from the weekly panel: {missing_columns}")

weekly_occupancy = merged_data_weekly.T.copy()
weekly_occupancy = weekly_occupancy.loc[distance_matrix.index]

# %%
# LISA for the outbreak and non-outbreak weeks
for week in (units.OUTBREAK_WEEK, units.NON_OUTBREAK_WEEK):
    occupancy_week = weekly_occupancy[week].reset_index()
    occupancy_week.columns = ['unit', 'occupancy']

    df_coords = df[['name', 'lat', 'lon']].copy()
    df_coords.columns = ['unit', 'lat', 'lon']

    gdf = pd.merge(df_coords, occupancy_week, on='unit')
    gdf['geometry'] = gdf.apply(lambda row: Point(row['lon'], row['lat']), axis=1)
    gdf = gpd.GeoDataFrame(gdf, geometry='geometry', crs="EPSG:4326")

    weights = KNN.from_dataframe(gdf, k=KNN_K)
    weights.transform = 'r'

    lisa = Moran_Local(
        gdf['occupancy'], weights,
        permutations=PERMUTATIONS, seed=RANDOM_SEED,
    )
    gdf['lisa_cluster'] = lisa.q
    gdf['lisa_p'] = lisa.p_sim
    gdf['significant'] = gdf['lisa_p'] < SIGNIFICANCE
    gdf['color'] = gdf.apply(
        lambda row: LISA_COLORS.get(row['lisa_cluster'])
        if row['significant'] else 'lightgrey',
        axis=1,
    )

    gdf.to_csv(SPATIAL_DIR / f"lisa_{week}.tsv", sep="\t", index=False)

    fig, ax = plt.subplots(figsize=(10, 8))
    gdf.plot(ax=ax, color=gdf['color'], edgecolor=None, markersize=200)
    for _, row in gdf.iterrows():
        ax.text(row.geometry.x + 0.01, row.geometry.y, row['unit'], fontsize=9)
    plt.title(f"LISA: occupancy on {week}")
    plt.axis('off')
    plt.tight_layout()
    plt.savefig(SPATIAL_DIR / f"lisa_{week}.png", dpi=300)
    plt.savefig(SPATIAL_DIR / f"lisa_{week}.svg",
                facecolor='white', bbox_inches='tight')
    plt.close('all')

    n_significant = int(gdf['significant'].sum())
    print(f"LISA {week}: {n_significant}/{len(gdf)} units significant "
          f"(p < {SIGNIFICANCE})")
