# Data Dictionary

Every input dataset in this repository, with its source, coverage and column
definitions. All files are tab-separated (`\t`) with a header row.

Nothing here is individual-level. Occupancy values are aggregated and anonymised
at source by Google; laboratory data are weekly counts and positivity rates at
state level.

Checksums are the first 16 hex characters of the file's SHA-256.

---

## `occupancy/` — hourly healthcare unit occupancy

**Source:** Google Maps popular-times data, queried hourly during the study
period. Google derives it from aggregated, anonymised location history from
users who opted in, expressed as a percentage of the location's typical peak
popularity. No retrospective or batch retrieval is possible, so these files are
the collected record, not a re-runnable extraction.

**Coverage:** 5 July 2023 to 8 October 2024, one file per unit, 17 units.
Analyses start on 15 July 2023 (see `src/units.py`).
**Rows:** 452–462 per file (one row per calendar day).

| Column | Type | Description | Unit |
|---|---|---|---|
| `Date` | string | Calendar date, `DD/MM/YYYY` | — |
| `Local` | string | Establishment name as registered on Google Maps | — |
| `Day` | string | Day of week, in Portuguese | — |
| `4:00` … `3:00` | integer | Occupancy at that hour; the 24 columns run from 04:00 through 03:00 the next day. `-` marks a missing reading | % of peak capacity |

Missing readings are `-`; they become `NaN` on load. Single missing hourly
records are linearly interpolated. Days lost to connectivity outages are dropped
via `DATES_TO_REMOVE` in `src/units.py`, which removes five epidemiological
weeks from the analysis.

---

## `units_metadata.tsv` — healthcare unit attributes

**Source:** Google Maps establishment records, compiled by the authors.
**Rows:** 17 (one per monitored unit). Source of Supplementary Data 1.

| Column | Type | Description | Unit |
|---|---|---|---|
| `name` | string | Establishment name, matching `Local` in the occupancy files | — |
| `lat` | float | Latitude, EPSG:4326 | decimal degrees |
| `lon` | float | Longitude, EPSG:4326 | decimal degrees |
| `rating_score` | string | Google Maps average user rating (comma decimal separator) | 0–5 |
| `n_reviews` | integer | Number of Google Maps user reviews | count |
| `real_time` | string | Whether live occupancy was available (`yes`/`no`) | — |
| `open_24h` | string | Whether the unit operates 24 hours (`yes`/`no`) | — |
| `link` | string | Google Maps establishment URL | — |
| `address` | string | Street address | — |
| `city` | string | Municipality within the São Paulo metropolitan area | — |
| `state` | string | Federative unit (SP) | — |
| `cep` | string | Brazilian postal code | — |
| `distrito`, `bairro`, `search_term` | string | Internal lookup fields, dropped when Supplementary Data 1 is built | — |

`sha256: e4bef4cd376c7f6a`

---

## `private_labs/` — weekly positivity rates, private laboratory network

**Source:** prospective pathogen monitoring initiative coordinated by Instituto
Todos pela Saúde (ITpS), aggregating results from seven private laboratories
serving São Paulo state. These are the manuscript's **exploratory** data. The
weekly aggregates below are the starting point for this pipeline; the upstream
extraction is outside this repository and the underlying test-level records are
not public.

**Coverage:** December 2021 to April 2025, state level (São Paulo).

| File | Rows | Pathogens | Checksum |
|---|---|---|---|
| `respat_posrate_SP_state.tsv` | 2,100 | respiratory panel, one row per virus per week | `9b8021d952baedef` |
| `arbo_posrate_SP_state.tsv` | 342 | arboviruses, one row per virus per week | `1fb3acf69a9cd3ae` |
| `vrisp_posrate_SP_state.tsv` | 175 | respiratory panel combined into a single series | `6ec0784072e8e5e2` |

| Column | Type | Description | Unit |
|---|---|---|---|
| `epiweek_enddate` | date | Saturday closing the epidemiological week, `YYYY-MM-DD` | — |
| `nt` | integer | Non-tested / indeterminate results | count |
| `negatives` | integer | Negative results | count |
| `positives` | integer | Positive results | count |
| `positivity_rate` | float | `positives / (positives + negatives) × 100` | % |
| `virus` | string | Pathogen code: `SC2`, `FLUA`, `FLUB`, `VSR`, `DENV`, `CHIKV`. Absent from `vrisp_*`, which is already combined | — |

The pipeline uses `SC2` from `respat_*`, `DENV` from `arbo_*`, and the whole of
`vrisp_*` (SARS-CoV-2, RSV, Influenza A and B combined).

---

## `public_cases/` — weekly case counts, public surveillance

**Source:** SIVEP-SRAG via Open DataSUS, and InfoDengue. These are the
manuscript's **validation** data. Both are public; see the README's Data section
for how to reach them. **Retrieved 6 April 2025.** Both systems revise records
retrospectively, so a fresh retrieval will not reproduce these counts. The files
here are the extraction behind the published results and are versioned for that
reason.

### `sivep_cases_SP_state.tsv` — SARI cases by pathogen

826 rows, January 2021 to January 2025. `sha256: 50e68cac3f2afd16`

| Column | Type | Description | Unit |
|---|---|---|---|
| `state` | string | Federative unit (`SAO PAULO`) | — |
| `year` | integer | Calendar year of symptom onset | — |
| `virus` | string | Pathogen: `covid`, `flua`, `flub`, `vsr` | — |
| `epiweek_end` | date | Saturday closing the epidemiological week | — |
| `result_count` | integer | Confirmed detections that week | count |

### `sivep_vrisp_cases_SP_state.tsv` — respiratory panel combined

209 rows, January 2021 to January 2025. `sha256: 24915ecf719feb35`

| Column | Type | Description | Unit |
|---|---|---|---|
| `epiweek_end` | date | Saturday closing the epidemiological week | — |
| `positives` | integer | All four pathogens summed for that week | count |

### `infodengue_cases_SP_state.tsv` — dengue cases

453 rows, December 2021 to March 2025. `sha256: 3574f517ee6f7db4`

| Column | Type | Description | Unit |
|---|---|---|---|
| `state` | string | Federative unit (`São Paulo`) | — |
| `region` | string | Macro-region (`Sudeste`) | — |
| `disease` | string | `dengue`, `chikungunya` or `zika` | — |
| `data_fimSE` | date | Saturday closing the epidemiological week | — |
| `casos_confirmados` | integer | Laboratory-confirmed cases | count |
| `casos_estimados` | integer | Nowcast-corrected estimate, used in the analyses | count |

The analyses use `casos_estimados` for `disease == 'dengue'`, which corrects for
reporting delay.

---

## `geo/sp_rj_municipality_crs.geojson`

Municipality boundary polygons for São Paulo and Rio de Janeiro states,
EPSG:4326, used only to draw the maps. The `name_muni` property is matched
against the `city` column of `units_metadata.tsv` to highlight the municipalities
that host a monitored unit.

---

## Derived outputs

`results/` is fully regenerated by the pipeline and is not documented here. The
supplementary tables carry their own column dictionaries: each
`results/supp_data/Supplementary Data *.xlsx` has a **Data dictionary** sheet,
generated by `scripts/09_export_supp_data.py`.
