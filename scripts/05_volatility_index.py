# %%
"""Step 06: z-based epidemic volatility index over the occupancy signal.

Computes a 42-day (six-week) moving average and standard deviation of daily
occupancy, derives weekly z-scores, and classifies them as low (< 0),
moderate (0 to 0.65) or high (>= 0.65) volatility.

Produces the city-level panel of Figure 4A and the per-unit z-score barplots
and status maps for the outbreak and non-outbreak weeks (Figure 4B-C, E-F,
and the map panels).

Outputs
    results/outbreaks/occupancy_average_sao_paulo.{png,svg}
    results/outbreaks/by_unit_occupancy_zscore_at_{outbreak,non_outbreak}_period.{png,svg}
    results/outbreaks/map_by_unit_occupancy_zscore_at_{outbreak,non_outbreak}_period.html
    results/outbreaks/weekly_zscore_by_unit.tsv
"""

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src import occupancy, plt_maps, units
from src.paths import (
    MUNICIPALITY_GEOJSON,
    OCCUPANCY_DIR,
    OUTBREAKS_DIR,
    UNITS_METADATA,
    ensure_dir,
)

ensure_dir(OUTBREAKS_DIR)

# Six-week window: one week longer than the maximum Granger lag tested
VOLATILITY_WINDOW_DAYS = 42

CITY_NAME = 'São Paulo metropolitan area'

# %%
merged_data, week_days = occupancy.get_gold_standard_data(
    units.GOLD_STANDARD_LIST, units.DATES_TO_REMOVE, OCCUPANCY_DIR
)
merged_data = merged_data.interpolate(method='linear')

# %%
moving_stds, moving_average = occupancy.moving_average_or_zscores(
    merged_data, window=VOLATILITY_WINDOW_DAYS
)
merged_means_42 = occupancy.concat_means(merged_data, moving_stds, moving_average)
merged_data_weekly = occupancy.get_weekly_data_from_daily(merged_means_42)

# %%
# Figure 4A: city-level occupancy, 42-day moving average and weekly z-scores
occupancy.viz_metrics_by_city_sns(
    merged_data_weekly,
    city_name=CITY_NAME,
    output_file_name=str(OUTBREAKS_DIR / 'occupancy_average_sao_paulo'),
)

# %%
metrics_by_unit = occupancy.metrics_by_unit(merged_data, moving_average, moving_stds)

# Long-format export of the per-unit weekly z-scores
zscore_rows = []
for unit, frame in metrics_by_unit.items():
    unit_frame = frame.reset_index().rename(columns={'index': 'epi_week'})
    unit_frame.insert(0, 'unit_name', unit)
    zscore_rows.append(unit_frame)

pd.concat(zscore_rows, ignore_index=True).to_csv(
    OUTBREAKS_DIR / 'weekly_zscore_by_unit.tsv', sep='\t', index=False
)

# %%
# Two representative weeks: early outbreak stage and later stage
PERIODS = [
    (units.OUTBREAK_WEEK, 'outbreak', '#ff0000'),
    (units.NON_OUTBREAK_WEEK, 'non_outbreak', '#999966'),
]

for week, label, background_color in PERIODS:
    occupancy.plot_zscores_barplot_by_unit(
        metrics_by_unit,
        week_date=week,
        output_file_name=str(
            OUTBREAKS_DIR / f'by_unit_occupancy_zscore_at_{label}_period'
        ),
    )

    status_map = plt_maps.map_status_by_date(
        date=week,
        metrics_by_unit=metrics_by_unit,
        path_geojson=MUNICIPALITY_GEOJSON,
        path_metadata=UNITS_METADATA,
        background_color=background_color,
    )
    status_map.save(
        str(OUTBREAKS_DIR / f'map_by_unit_occupancy_zscore_at_{label}_period.html')
    )

print(f"Volatility index written for {len(metrics_by_unit)} units "
      f"({VOLATILITY_WINDOW_DAYS}-day window)")
