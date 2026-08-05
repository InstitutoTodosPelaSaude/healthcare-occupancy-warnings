# %%
"""Step 10: assemble Supplementary Tables S1-S6.

These tables are the source data declared for Figures 1-5 and S1-S2. Each is
written as a TSV and, when openpyxl is available, as an XLSX carrying
human-readable headers plus a data dictionary.

Inputs come from the earlier steps:
    S1  data/units_metadata.tsv                          (static input)
    S2  results/consolidated_data_sp.tsv                 (step 02)
    S3  results/granger/granger_results_by_wave.tsv      (step 04)
    S4  results/spatial_associations/lisa_<week>.tsv     (step 07)
    S5  results/lead_time/weekly_zscores.tsv             (step 06)
    S6  results/lead_time/lead_time_table.tsv            (step 06)

Outputs
    results/supp_tables/TableS{1..6}.{tsv,xlsx}
"""

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src import units
from src.paths import (
    CONSOLIDATED_DATA,
    GRANGER_DIR,
    LEAD_TIME_DIR,
    SPATIAL_DIR,
    SUPP_TABLES_DIR,
    UNITS_METADATA,
    ensure_dir,
)

ensure_dir(SUPP_TABLES_DIR)

SIGNIFICANCE = 0.05
# Decimal places used in the submitted supplementary tables
ROUND_DP = 2

try:
    import openpyxl  # noqa: F401
    XLSX_AVAILABLE = True
except ImportError:
    XLSX_AVAILABLE = False
    print("openpyxl not installed: writing TSV only, skipping XLSX")


def write_table(df, name, readable_headers=None, dictionary=None):
    """Write one supplementary table as TSV and, if possible, as XLSX."""
    tsv_path = SUPP_TABLES_DIR / f"{name}.tsv"
    df.to_csv(tsv_path, sep="\t", index=False)

    if not XLSX_AVAILABLE:
        return

    export = df.rename(columns=readable_headers) if readable_headers else df.copy()

    with pd.ExcelWriter(SUPP_TABLES_DIR / f"{name}.xlsx", engine="openpyxl") as writer:
        export.to_excel(writer, sheet_name=name, index=False)
        if dictionary:
            pd.DataFrame(
                [{'Column': readable_headers.get(k, k) if readable_headers else k,
                  'Description': v}
                 for k, v in dictionary.items()]
            ).to_excel(writer, sheet_name="Data dictionary", index=False)


# %%
# ----------------------------- Table S1 -----------------------------
# Healthcare unit metadata
metadata = pd.read_csv(UNITS_METADATA, sep='\t')
metadata["unit_name"] = metadata["name"].map(units.NAME_MAPPING)
metadata["unit_index"] = metadata["unit_name"].map(units.UNIT_INDEX)
metadata = metadata.drop(columns=["search_term", "name", "distrito", "bairro"])
metadata = metadata[
    ["unit_index", "unit_name"]
    + [c for c in metadata.columns if c not in ("unit_index", "unit_name")]
]
table_s1 = metadata.sort_values(by="unit_index")

write_table(
    table_s1, "TableS1",
    readable_headers={
        'unit_index': 'Unit index', 'unit_name': 'Unit name',
        'lat': 'Latitude', 'lon': 'Longitude',
        'rating_score': 'Google Maps rating', 'n_reviews': 'Number of reviews',
        'real_time': 'Real-time data available', 'open_24h': '24-hour operation',
        'link': 'Google Maps link', 'address': 'Address',
        'city': 'Municipality', 'state': 'State', 'cep': 'Postal code',
    },
    dictionary={
        'unit_index': 'Stable identifier used across Tables S1 and S4.',
        'unit_name': 'Standardised unit name used in the manuscript figures.',
        'lat': 'Latitude in decimal degrees (EPSG:4326).',
        'lon': 'Longitude in decimal degrees (EPSG:4326).',
        'rating_score': 'Google Maps average user rating.',
        'n_reviews': 'Number of Google Maps user reviews.',
        'real_time': 'Whether live occupancy data was available for the unit.',
        'open_24h': 'Whether the unit operates 24 hours a day.',
        'link': 'Google Maps establishment link.',
        'address': 'Street address as registered on Google Maps.',
        'city': 'Municipality within the São Paulo metropolitan area.',
        'state': 'Federative unit (SP).',
        'cep': 'Brazilian postal code.',
    },
)

# %%
# ----------------------------- Table S2 -----------------------------
# Consolidated weekly occupancy and laboratory surveillance data
consolidated = pd.read_csv(CONSOLIDATED_DATA, sep='\t')
table_s2 = consolidated.rename(columns={
    'occupancy_percentage_mean': 'occupancy_percentage_mean',
    'exploratory_posrate_sc2': 'exploratory_private_posrate_sc2',
    'validation_cases_sc2': 'validation_public_cases_sc2',
    'exploratory_posrate_denv': 'exploratory_private_posrate_denv',
    'validation_cases_denv': 'validation_public_cases_denv',
    'exploratory_posrate_vrisp': 'exploratory_private_posrate_vrisp',
    'validation_vrisp_cases': 'validation_public_vrisp_cases',
})

write_table(
    table_s2, "TableS2",
    readable_headers={
        'epidemiological_weeks': 'Epidemiological week (ending Saturday)',
        'occupancy_percentage_mean': 'Mean Occupancy (%)',
        'exploratory_private_posrate_sc2': 'SARS-CoV-2 Positivity Rate - Private Labs (%)',
        'validation_public_cases_sc2': 'SARS-CoV-2 Cases - SIVEP-SRAG (#)',
        'exploratory_private_posrate_denv': 'Dengue Positivity Rate - Private Labs (%)',
        'validation_public_cases_denv': 'Dengue Cases - InfoDengue (#)',
        'exploratory_private_posrate_vrisp': 'Respiratory Viruses Positivity Rate - Private Labs (%)',
        'validation_public_vrisp_cases': 'Respiratory Viruses Cases - SIVEP-SRAG (#)',
    },
    dictionary={
        'epidemiological_weeks': 'Saturday closing each epidemiological week.',
        'occupancy_percentage_mean': 'Mean occupancy across the 17 monitored units.',
        'exploratory_private_posrate_sc2': 'SARS-CoV-2 positivity rate, ITpS private laboratory network (exploratory data).',
        'validation_public_cases_sc2': 'Confirmed SARS-CoV-2 cases, SIVEP-SRAG (validation data).',
        'exploratory_private_posrate_denv': 'Dengue positivity rate, ITpS private laboratory network (exploratory data).',
        'validation_public_cases_denv': 'Estimated dengue cases, InfoDengue (validation data).',
        'exploratory_private_posrate_vrisp': 'Positivity rate for the respiratory virus panel (SARS-CoV-2, RSV, Influenza A and B), private laboratories.',
        'validation_public_vrisp_cases': 'Confirmed cases for the respiratory virus panel, SIVEP-SRAG.',
    },
)

# %%
# ----------------------------- Table S3 -----------------------------
# Granger causality results, significant lags only
granger = pd.read_csv(GRANGER_DIR / "granger_results_by_wave.tsv", sep="\t")

SERIES_LABELS = {
    'validation_cases_sc2_norm': ('validation_cases_sc2_norm', 'SC2'),
    'exploratory_posrate_sc2': ('exploratory_posrate_sc2', 'SC2'),
    'validation_denv_diff': ('validation_denv_diff', 'DENV'),
    'exploratory_denv_diff': ('exploratory_denv_diff', 'DENV'),
    'exploratory_posrate_vrisp': ('exploratory_posrate_vrisp', 'RV'),
    'validation_vrisp_cases_norm': ('validation_vrisp_cases_norm', 'RV'),
}

table_s3 = granger[granger['p_value'] < SIGNIFICANCE].copy()
table_s3 = table_s3.sort_values(['wave', 'p_value'])
table_s3['shift_period'] = table_s3['wave'].str.replace('wave', 'shift', regex=False)
table_s3['timeseries1'] = table_s3['target'].map(lambda t: SERIES_LABELS[t][0])
table_s3['timeseries2'] = 'occupancy_diff'
table_s3['virus'] = table_s3['target'].map(lambda t: SERIES_LABELS[t][1])
table_s3['p-value'] = table_s3['p_value'].round(ROUND_DP)
table_s3 = table_s3[
    ['shift_period', 'timeseries1', 'timeseries2', 'lag', 'p-value', 'virus']
]
table_s3['lag'] = table_s3['lag'].astype(int)

write_table(
    table_s3, "TableS3",
    readable_headers={
        'shift_period': 'Shifted epidemic period', 'timeseries1': 'Laboratory series',
        'timeseries2': 'Occupancy series', 'lag': 'Lag (weeks)',
        'p-value': 'p-value', 'virus': 'Pathogen group',
    },
    dictionary={
        'shift_period': 'Overlapping epidemic window accounting for pathogen-specific lags.',
        'timeseries1': 'Laboratory surveillance series tested as the target.',
        'timeseries2': 'First-differenced mean occupancy series used as the predictor.',
        'lag': 'Number of weeks by which the laboratory signal precedes occupancy changes.',
        'p-value': 'Granger causality p-value (ssr F-test), rounded to two decimals.',
        'virus': 'Pathogen group: SC2, DENV or RV.',
    },
)

# %%
# ----------------------------- Table S4 -----------------------------
# LISA results for both representative weeks
lisa_frames = []
for week in (units.OUTBREAK_WEEK, units.NON_OUTBREAK_WEEK):
    frame = pd.read_csv(SPATIAL_DIR / f"lisa_{week}.tsv", sep='\t')
    frame['period_week'] = week
    lisa_frames.append(frame)

table_s4 = pd.concat(lisa_frames, ignore_index=True)
table_s4["unit_name"] = table_s4["unit"].map(units.NAME_MAPPING)
table_s4["unit_index"] = table_s4["unit_name"].map(units.UNIT_INDEX)
table_s4 = table_s4.drop(columns=['unit'])
table_s4 = table_s4[
    ['unit_index', 'unit_name']
    + [c for c in table_s4.columns if c not in ('unit_index', 'unit_name')]
]
table_s4 = table_s4.sort_values(by=['period_week', 'unit_index'])
# The submitted table carries the rounded numeric variant
table_s4['occupancy'] = table_s4['occupancy'].round(ROUND_DP)

write_table(
    table_s4, "TableS4",
    readable_headers={
        'unit_index': 'Unit index', 'unit_name': 'Unit name',
        'lat': 'Latitude', 'lon': 'Longitude', 'occupancy': 'Occupancy (%)',
        'geometry': 'Geometry (WKT)', 'lisa_cluster': 'LISA quadrant',
        'lisa_p': 'LISA p-value', 'significant': 'Significant (p < 0.05)',
        'color': 'Plot colour', 'period_week': 'Epidemiological week',
    },
    dictionary={
        'unit_index': 'Stable identifier, matching Table S1.',
        'unit_name': 'Standardised unit name.',
        'lat': 'Latitude in decimal degrees (EPSG:4326).',
        'lon': 'Longitude in decimal degrees (EPSG:4326).',
        'occupancy': 'Mean weekly occupancy for the unit.',
        'geometry': 'Point geometry in well-known text.',
        'lisa_cluster': 'Local Moran quadrant: 1 high-high, 2 low-high, 3 low-low, 4 high-low.',
        'lisa_p': 'Pseudo p-value from conditional randomisation.',
        'significant': 'Whether the local association reaches p < 0.05.',
        'color': 'Colour used in the LISA maps.',
        'period_week': 'Epidemiological week analysed.',
    },
)

# %%
# ----------------------------- Table S5 -----------------------------
# Weekly z-scores and alert flags, produced in step 06
table_s5 = pd.read_csv(LEAD_TIME_DIR / 'weekly_zscores.tsv', sep='\t')

write_table(
    table_s5, "TableS5",
    readable_headers={
        'epi_week': 'Epidemiological week', 'occupancy_%': 'Occupancy (%)',
        'occupancy_rolling_mean': 'Occupancy 6-week rolling mean',
        'occupancy_rolling_std': 'Occupancy 6-week rolling SD',
        'zscore_occupancy': 'Occupancy z-score', 'alert_fired': 'Alert fired (z > 0.65)',
    },
    dictionary={
        'epi_week': 'Saturday closing each epidemiological week.',
        'occupancy_%': 'Mean occupancy across the 17 monitored units.',
        'occupancy_rolling_mean': 'Six-week rolling mean of mean occupancy.',
        'occupancy_rolling_std': 'Six-week rolling standard deviation of mean occupancy.',
        'zscore_occupancy': 'Standardised deviation of occupancy from its rolling baseline.',
        'alert_fired': 'One when the occupancy z-score exceeds 0.65.',
    },
)

# %%
# ----------------------------- Table S6 -----------------------------
# Early warning lead time, produced in step 06
table_s6 = pd.read_csv(LEAD_TIME_DIR / 'lead_time_table.tsv', sep='\t')

write_table(
    table_s6, "TableS6",
    readable_headers={
        'wave': 'Wave', 'display_label': 'Indicator', 'source_type': 'Source type',
        'dataset_role': 'Dataset role', 'granger_significant': 'Granger significant',
        'first_alert_date': 'First alert date', 'n_alert_weeks': 'Number of alert weeks',
        'lab_peak_date': 'Laboratory peak date', 'lab_peak_value': 'Laboratory peak value',
        'lead_time_weeks': 'Lead time (weeks)', 'detected_before_peak': 'Detected before peak',
    },
    dictionary={
        'wave': 'Epidemiological wave period.',
        'display_label': 'Pathogen group and metric: (%) positivity rate, (#) case counts.',
        'source_type': 'Private (ITpS network) or public (SIVEP-SRAG, InfoDengue).',
        'dataset_role': 'Exploratory or validation data.',
        'granger_significant': 'Whether the pathogen group reached p < 0.05 in this wave.',
        'first_alert_date': 'First week with an occupancy z-score above 0.65.',
        'n_alert_weeks': 'Number of alert weeks within the wave.',
        'lab_peak_date': 'Week of the laboratory surge peak (two-week centred smooth).',
        'lab_peak_value': 'Raw indicator value at the peak week.',
        'lead_time_weeks': 'Weeks between the first alert and the laboratory peak.',
        'detected_before_peak': 'Whether the alert preceded the peak.',
    },
)

# %%
for name, table in (("TableS1", table_s1), ("TableS2", table_s2),
                    ("TableS3", table_s3), ("TableS4", table_s4),
                    ("TableS5", table_s5), ("TableS6", table_s6)):
    print(f"{name}: {table.shape[0]} rows x {table.shape[1]} columns")
