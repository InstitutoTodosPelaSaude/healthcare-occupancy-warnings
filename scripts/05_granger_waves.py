# %%
"""Step 05: stationarity testing and Granger causality across epidemic waves.

Runs the Augmented Dickey-Fuller test on every series, applies first-order
differencing where it is needed, then tests whether each laboratory indicator
Granger-causes the change in mean occupancy, separately within three
partially overlapping wave windows.

This is the source of Table S3.

Outputs
    results/granger/adf_stationarity.tsv
    results/granger/granger_results_by_wave.tsv
"""

import sys
from pathlib import Path

import pandas as pd
from statsmodels.tsa.stattools import adfuller, grangercausalitytests

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src import units
from src.paths import CONSOLIDATED_DATA_INTERMEDIATE, GRANGER_DIR, ensure_dir

ensure_dir(GRANGER_DIR)

# Maximum lag tested within each wave, bounded by the number of weeks available
MAX_LAG = 5
SIGNIFICANCE = 0.05

# %%
df = pd.read_csv(CONSOLIDATED_DATA_INTERMEDIATE, sep="\t")
df['epidemiological_weeks'] = pd.to_datetime(df['epidemiological_weeks'])

# %%
# ------------------------- ADF stationarity test -------------------------
adf_targets = [
    'detecta_percentage_mean',
    'sivep_cases_sc2_norm',
    'infodengue_cases_denv_norm',
    'radim_posrate_sc2',
    'radim_posrate_denv',
    'radim_posrate_vrisp',
    'sivep_vrisp_cases_norm',
]

adf_rows = []
for var_name in adf_targets:
    series = df[var_name].dropna()
    statistic, p_value = adfuller(series)[:2]
    adf_rows.append({
        'series': var_name,
        'adf_statistic': statistic,
        'p_value': p_value,
        'stationary': p_value <= SIGNIFICANCE,
    })

adf_df = pd.DataFrame(adf_rows)
adf_df.to_csv(GRANGER_DIR / "adf_stationarity.tsv", sep="\t", index=False)
print(adf_df.to_string(index=False))

# %%
# First-order differencing for the series that failed the ADF test
df['detecta_diff'] = df['detecta_percentage_mean'].diff()
df['infodengue_diff'] = df['infodengue_cases_denv_norm'].diff()
df['radim_denv_diff'] = df['radim_posrate_denv'].diff()

# Each laboratory indicator is tested against the differenced occupancy series
GRANGER_PAIRS = {
    'sivep_cases_sc2_norm': 'detecta_diff',
    'radim_posrate_sc2': 'detecta_diff',
    'infodengue_diff': 'detecta_diff',
    'radim_denv_diff': 'detecta_diff',
    'radim_posrate_vrisp': 'detecta_diff',
    'sivep_vrisp_cases_norm': 'detecta_diff',
}

# Partially overlapping windows, offset to accommodate the pathogen-specific
# lag structures (Methods: waves 1-3)
WAVES = units.GRANGER_WAVES

# %%
results = []

for i, (start_date, end_date) in enumerate(WAVES, start=1):
    wave_df = df[
        (df['epidemiological_weeks'] >= start_date)
        & (df['epidemiological_weeks'] <= end_date)
    ]

    for target, predictor in GRANGER_PAIRS.items():
        df_pair = wave_df[[target, predictor]].dropna()

        if len(df_pair) < MAX_LAG + 1:
            results.append({
                'wave': f'wave{i}', 'target': target, 'predictor': predictor,
                'lag': None, 'p_value': None, 'error': 'Not enough data points',
            })
            continue

        try:
            test_result = grangercausalitytests(df_pair, maxlag=MAX_LAG, verbose=False)
            for lag in range(1, MAX_LAG + 1):
                results.append({
                    'wave': f'wave{i}',
                    'target': target,
                    'predictor': predictor,
                    'lag': lag,
                    'p_value': test_result[lag][0]['ssr_ftest'][1],
                })
        except Exception as exc:  # noqa: BLE001 - recorded, not swallowed
            results.append({
                'wave': f'wave{i}', 'target': target, 'predictor': predictor,
                'lag': None, 'p_value': None, 'error': str(exc),
            })

# %%
results_df = pd.DataFrame(results)
results_df.to_csv(GRANGER_DIR / "granger_results_by_wave.tsv", sep="\t", index=False)

significant = results_df[results_df['p_value'] < SIGNIFICANCE]
print(f"Granger tests: {len(results_df)} | significant (p < {SIGNIFICANCE}): "
      f"{len(significant)}")
