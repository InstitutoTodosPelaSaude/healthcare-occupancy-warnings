# %%
"""Step 01: build the occupancy panel and its weekly aggregates.

Reads the hourly occupancy TSVs for the 17 monitored units, aggregates them
to daily and then to weekly means, computes moving averages at four window
lengths, and draws the clustered weekly heatmap (Figure 2A).

Outputs
    results/unit_overview/by_unit/daily_percentage_by_unit.tsv
    results/unit_overview/by_unit/weekly_percentage_by_unit.tsv
    results/unit_overview/weekly_means_{7,14,21,28}.tsv
    results/unit_overview/plots/daily_moving_average_mean.{png,svg}
    results/unit_overview/plots/weekly_moving_average_mean.{png,svg}
    results/unit_overview/plots/weekly_heatmap.{png,svg}
"""

import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib.colors import LinearSegmentedColormap

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src import occupancy, units
from src.paths import OCCUPANCY_DIR, UNIT_OVERVIEW_DIR, ensure_dir

PATH_OUTPUT = UNIT_OVERVIEW_DIR
ensure_dir(PATH_OUTPUT / "by_unit", PATH_OUTPUT / "plots")

# %%
merged_data, week_days = occupancy.get_gold_standard_data(
    units.GOLD_STANDARD_LIST, units.DATES_TO_REMOVE, OCCUPANCY_DIR
)
# Single missing hourly records are filled linearly (Methods)
merged_data = merged_data.interpolate(method='linear')

merged_data.to_csv(
    PATH_OUTPUT / 'by_unit' / 'daily_percentage_by_unit.tsv', sep='\t', index=True
)

# %%
# Moving averages at four window lengths
merged_means = {}
for window in (7, 14, 21, 28):
    moving_stds, moving_average = occupancy.moving_average_or_zscores(
        merged_data, window=window
    )
    merged_means[window] = occupancy.concat_means(
        merged_data, moving_stds, moving_average
    )

occupancy.plot_combined_data(
    [merged_means[w] for w in (7, 14, 21, 28)],
    windows=[7, 14, 21, 28],
    path_output=PATH_OUTPUT,
    column_data="moving_average_mean",
    title_name='Daily moving average',
    period='days',
    output_file_name='daily_moving_average_mean',
)

# %%
# Daily to weekly (epidemiological weeks, ending on Saturday)
merged_data_weekly = occupancy.get_weekly_data_from_daily(merged_data)
merged_means_weekly = {
    w: occupancy.get_weekly_data_from_daily(merged_means[w]) for w in (7, 14, 21, 28)
}

occupancy.plot_combined_test(
    [merged_means_weekly[w] for w in (7, 14, 21, 28)],
    windows=[7, 14, 21, 28],
    path_output=PATH_OUTPUT,
    column_data="moving_average_mean",
    title_name='Weekly moving average',
    period='weeks',
    output_file_name='weekly_moving_average_mean',
)

# %%
merged_data_weekly.to_csv(
    PATH_OUTPUT / 'by_unit' / 'weekly_percentage_by_unit.tsv', sep='\t', index=True
)
for window in (7, 14, 21, 28):
    merged_means_weekly[window].to_csv(
        PATH_OUTPUT / f'weekly_means_{window}.tsv', sep='\t', index=True
    )

# %%
# Figure 2A: weekly occupancy heatmap, units clustered by temporal similarity
sns.set_theme()

heatmap_data = merged_data_weekly.copy()
heatmap_data.index = pd.to_datetime(heatmap_data.index)

# Reinstate the excluded weeks so they render as explicit gaps
for date in pd.to_datetime(units.EXCLUDED_WEEKS):
    if date not in heatmap_data.index:
        heatmap_data.loc[date] = np.nan

heatmap_data = heatmap_data.sort_index()
heatmap_data.index = heatmap_data.index.date

custom_cmap = LinearSegmentedColormap.from_list(
    'custom_cmap', ['#3A5FCD', '#FFFFFF', '#EE0000'], N=256
)

plot_data = heatmap_data.T
cluster_data = plot_data.fillna(50)  # placeholder value, clustering only

g = sns.clustermap(
    data=cluster_data,
    cmap=custom_cmap,
    linewidths=0.3,
    linecolor='white',
    center=50,
    row_cluster=True,
    col_cluster=False,
    figsize=(20, 5.5),
    cbar_pos=None,
)

# Paint the missing weeks grey rather than letting the placeholder show through
ax = g.ax_heatmap
for (i, j), value in np.ndenumerate(plot_data.values):
    if pd.isna(value):
        ax.add_patch(
            plt.Rectangle((j, i), 1, 1, fill=True, color='lightgrey', linewidth=0)
        )

g.ax_row_dendrogram.set_visible(False)

g.savefig(PATH_OUTPUT / 'plots' / 'weekly_heatmap.png',
          facecolor='white', bbox_inches='tight')
g.savefig(PATH_OUTPUT / 'plots' / 'weekly_heatmap.svg',
          facecolor='white', bbox_inches='tight')
plt.close('all')

print(f"Units: {merged_data.shape[1]} | days: {merged_data.shape[0]} | "
      f"weeks: {merged_data_weekly.shape[0]}")
