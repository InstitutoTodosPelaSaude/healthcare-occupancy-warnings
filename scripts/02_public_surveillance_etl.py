# %%
"""Step 02: public surveillance ETL (SIVEP-SRAG and InfoDengue).

Documents how the weekly São Paulo state series shipped in
`data/public_cases/` were produced. Those files correspond to the
6 April 2025 retrieval used in the manuscript.

Both sources are revised retrospectively, so a fresh download will not
reproduce the April 2025 numbers. To avoid overwriting the data behind the
published results, this script writes to `data/public_cases/refreshed/`.
Point OUTPUT_DIR at PUBLIC_CASES_DIR only if you intend to replace them.

Downloads (not versioned here; the SIVEP dump is several hundred MB):
    data/public_cases/sivep_all_data.csv
    data/public_cases/infodengue_all_data.csv

Outputs
    <OUTPUT_DIR>/sivep_cases_SP_state.tsv
    <OUTPUT_DIR>/sivep_vrisp_cases_SP_state.tsv
    <OUTPUT_DIR>/infodengue_cases_SP_state.tsv
"""

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.paths import PUBLIC_CASES_DIR, ensure_dir
from src.sivep_kit import INFODENGUE_URL, SIVEP_URL, epiweek_enddate, get_data_public

OUTPUT_DIR = ensure_dir(PUBLIC_CASES_DIR / "refreshed")

SIVEP_RAW = PUBLIC_CASES_DIR / "sivep_all_data.csv"
INFODENGUE_RAW = PUBLIC_CASES_DIR / "infodengue_all_data.csv"

# %%
# ----------------------------- SIVEP-SRAG -----------------------------
if not SIVEP_RAW.exists():
    get_data_public(path_url=SIVEP_URL, out_path_file_name=SIVEP_RAW)

sivep = pd.read_csv(SIVEP_RAW, sep=';')

# %%
target = [
    'test_kit',
    'location',
    'state',
    'date_pri_sin',
    'VSR_test_result',
    'SC2_test_result',
    'FLUA_test_result',
    'FLUB_test_result',
]

# Respiratory viruses of public health importance (RV):
# SARS-CoV-2, RSV, and Influenza A and B
tests = [
    'vsr_pcr', 'vsr_antigen',
    'covid_pcr', 'covid_antigen',
    'flua_pcr', 'flua_antigen',
    'flub_pcr', 'flub_antigen',
]

result_columns = [
    'VSR_test_result',
    'SC2_test_result',
    'FLUA_test_result',
    'FLUB_test_result',
]

sample_targets = sivep[target]
sample_targets = sample_targets[sample_targets['test_kit'].isin(tests)]

# %%
sample_targets['date_pri_sin'] = pd.to_datetime(sample_targets['date_pri_sin'])
sample_targets['year'] = sample_targets['date_pri_sin'].dt.year
sample_targets['virus'] = (
    sample_targets['test_kit']
    .str.replace('_pcr', '', regex=False)
    .str.replace('_antigen', '', regex=False)
)
sample_targets['epiweek_end'] = epiweek_enddate(sample_targets['date_pri_sin'])

# %%
melted_data = sample_targets.melt(
    id_vars=['state', 'location', 'year', 'virus', 'epiweek_end', 'date_pri_sin'],
    value_vars=result_columns,
    var_name='virus_test_result',
    value_name='result',
)

# Only confirmed detections are counted (Methods)
melted_data = melted_data[melted_data['result'] == 'Pos']
filtered_data = melted_data[melted_data['state'] == 'SAO PAULO']

# %%
summary_table = (
    filtered_data
    .groupby(['state', 'year', 'virus', 'epiweek_end'])
    .size()
    .reset_index(name='result_count')
)
summary_table['epiweek_end'] = summary_table['epiweek_end'].dt.strftime('%Y-%m-%d')
summary_table.to_csv(OUTPUT_DIR / 'sivep_cases_SP_state.tsv', index=False, sep='\t')

# %%
# RV panel: all four pathogens summed per epidemiological week
summary_vrisp = (
    summary_table
    .groupby(['epiweek_end'])
    .agg(positives=('result_count', 'sum'))
    .reset_index()
)
summary_vrisp.to_csv(
    OUTPUT_DIR / 'sivep_vrisp_cases_SP_state.tsv', sep='\t', index=False
)

# %%
# ----------------------------- InfoDengue -----------------------------
if not INFODENGUE_RAW.exists():
    get_data_public(path_url=INFODENGUE_URL, out_path_file_name=INFODENGUE_RAW)

infodengue = pd.read_csv(INFODENGUE_RAW, sep=',')
infodengue = infodengue[infodengue['state'] == 'São Paulo']
infodengue = infodengue[
    ['state', 'region', 'disease', 'data_fimSE', 'casos_confirmados', 'casos_estimados']
]
infodengue.to_csv(OUTPUT_DIR / 'infodengue_cases_SP_state.tsv', index=False, sep='\t')

print(f"Public surveillance series written to {OUTPUT_DIR}")
