# %%
"""Step 03: join occupancy with the laboratory surveillance indicators.

Builds the weekly panel that every downstream analysis reads: mean occupancy
alongside exploratory (private laboratory positivity rates, ITpS network) and
validation (SIVEP-SRAG and InfoDengue case counts) indicators for SARS-CoV-2,
dengue and the respiratory virus panel.

This is the source of Table S2.

Outputs
    results/consolidated_data_sp.tsv
    results/consolidated_data_sp_intermediate.tsv   (interpolated + normalised)
"""

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src import units
from src.paths import (
    CONSOLIDATED_DATA,
    CONSOLIDATED_DATA_INTERMEDIATE,
    PRIVATE_LABS_DIR,
    PUBLIC_CASES_DIR,
    RESULTS_DIR,
    UNIT_OVERVIEW_DIR,
    ensure_dir,
)

ensure_dir(RESULTS_DIR)

# %%
occupancy_average = pd.read_csv(
    UNIT_OVERVIEW_DIR / 'weekly_means_7.tsv', sep='\t', index_col=0
)

# ------------------- Exploratory data: private laboratories -------------------
radim_respat = pd.read_csv(
    PRIVATE_LABS_DIR / 'radim_respat_posrate_SP_state.tsv', sep='\t', index_col=0
)
radim_respat_sc2 = radim_respat[radim_respat['virus'] == 'SC2']

radim_arbo = pd.read_csv(
    PRIVATE_LABS_DIR / 'radim_arbo_posrate_SP_state.tsv', sep='\t', index_col=0
)
radim_arbo_denv = radim_arbo[radim_arbo['virus'] == 'DENV']

radim_vrisp = pd.read_csv(
    PRIVATE_LABS_DIR / 'radim_vrisp_posrate_SP_state.tsv', sep='\t', index_col=0
)

# ------------------- Validation data: public surveillance -------------------
sivep_cases = pd.read_csv(PUBLIC_CASES_DIR / 'sivep_cases_SP_state.tsv', sep='\t')
sivep_cases_sc2 = sivep_cases[sivep_cases['virus'] == 'covid']
sivep_cases_sc2.index = sivep_cases_sc2['epiweek_end']
sivep_cases_sc2 = sivep_cases_sc2[['result_count']]
sivep_cases_sc2 = sivep_cases_sc2.groupby('epiweek_end', as_index=True).sum()

infodengue_cases = pd.read_csv(
    PUBLIC_CASES_DIR / 'infodengue_cases_SP_state.tsv', sep='\t'
)
infodengue_cases_denv = infodengue_cases[infodengue_cases['disease'] == 'dengue']
infodengue_cases_denv.index = infodengue_cases_denv['data_fimSE']

sivep_vrisp = pd.read_csv(
    PUBLIC_CASES_DIR / 'sivep_vrisp_cases_SP_state.tsv', sep='\t', index_col=0
)

# %%
# ------------------- Epidemiological week scaffold -------------------
saturdays = pd.date_range(
    start=pd.to_datetime(units.STUDY_START),
    end=pd.to_datetime(units.STUDY_END),
    freq='W-SAT',
)
consolidated = pd.DataFrame({'epidemiological_weeks': saturdays})
consolidated['epidemiological_weeks'] = (
    consolidated['epidemiological_weeks'].dt.strftime('%Y-%m-%d')
)

# %%
# Align every source on the same date string before joining
for frame in (occupancy_average, radim_respat_sc2, radim_arbo_denv,
              sivep_cases_sc2, infodengue_cases_denv, radim_vrisp, sivep_vrisp):
    frame.index = pd.to_datetime(frame.index).strftime('%Y-%m-%d')

weeks = consolidated['epidemiological_weeks']
consolidated['detecta_percentage_mean'] = weeks.map(occupancy_average['percentage_mean'])
consolidated['radim_posrate_sc2'] = weeks.map(radim_respat_sc2['positivity_rate'])
consolidated['sivep_cases_sc2'] = weeks.map(sivep_cases_sc2['result_count'])
consolidated['radim_posrate_denv'] = weeks.map(radim_arbo_denv['positivity_rate'])
consolidated['infodengue_cases_denv'] = weeks.map(infodengue_cases_denv['casos_estimados'])
consolidated['radim_posrate_vrisp'] = weeks.map(radim_vrisp['positivity_rate'])
consolidated['sivep_vrisp_cases'] = weeks.map(sivep_vrisp['positives'])

consolidated.to_csv(CONSOLIDATED_DATA, sep='\t', index=False)

# %%
# ------------------- Intermediate table for the time series analyses -------------------
consolidated = pd.read_csv(CONSOLIDATED_DATA, sep="\t")
consolidated['epidemiological_weeks'] = pd.to_datetime(
    consolidated['epidemiological_weeks']
)

# Only occupancy is interpolated; case counts keep their gaps
consolidated[['detecta_percentage_mean']] = (
    consolidated[['detecta_percentage_mean']].interpolate()
)

# Min-max rescale the case counts so they are comparable with occupancy
for col in ['sivep_cases_sc2', 'infodengue_cases_denv', 'sivep_vrisp_cases']:
    min_val = consolidated[col].min()
    max_val = consolidated[col].max()
    consolidated[f'{col}_norm'] = (
        (consolidated[col] - min_val) / (max_val - min_val)
    ) * 100

consolidated.to_csv(CONSOLIDATED_DATA_INTERMEDIATE, sep="\t", index=False)

print(f"Consolidated panel: {consolidated.shape[0]} epidemiological weeks")
