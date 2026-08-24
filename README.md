# Healthcare Occupancy as an Early Warning Signal for Infectious Disease Surges

[![License: MIT](https://img.shields.io/badge/Code-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![License: CC-BY-4.0](https://img.shields.io/badge/Data-CC--BY--4.0-blue.svg)](https://creativecommons.org/licenses/by/4.0/)
[![Python 3.12+](https://img.shields.io/badge/Python-3.12%2B-blue.svg)](https://www.python.org/)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.22086238.svg)](https://doi.org/10.5281/zenodo.22086238)

Companion repository for:

> **Araújo JD†, Santos e Silva JC†**, Bragatte MAS, Sousa ER, Schrarstzhaupt IN, Sabino EC, Nakaya HI, Lázari CS, Pinho JRR, Penna GO, Kalil J, Simão M, Brito AF, Sampaio V. Healthcare occupancy data as an early warning indicator of infectious disease surges in São Paulo. *Communications Medicine* (under review).
>
> † These authors contributed equally to this work.

---

## Key Findings

- **Occupancy anticipates laboratory-confirmed surges by up to five weeks.** Granger causality identified significant directional associations at lags of 1 to 5 weeks across three epidemic waves.
- **The alert system caught every wave from its onset.** A weekly z-score above 0.65 on a six-week rolling baseline fired before the laboratory surge peak for 11 of the 12 Granger-significant pathogen-source combinations, reaching 22 weeks of lead time in wave 2. The exception is dengue positivity in wave 1, which peaked in the same week as the first alert. Per-combination lead times are in Supplementary Data 6.
- **Alignment is pathogen-dependent.** Dynamic time warping distances were lowest for SARS-CoV-2 (0.89 positivity, 1.00 case counts) and the respiratory panel (0.97, 1.01), and clearly higher for dengue (1.91, 2.12) — occupancy tracks respiratory surges more closely than arboviral ones.
- **Spatial pressure concentrates as a surge matures.** LISA found 2 of 17 units with significant local clustering in the early outbreak week and 7 of 17 in the later week, identifying a persistent hotspot cluster.
- **The signal is privacy-safe.** Occupancy comes from aggregated, anonymised Google Maps data. No individual-level record is used anywhere in this pipeline.

---

## Repository Structure

```
├── data/
│   ├── DATA_DICTIONARY.md                     # Source, coverage and columns for every input
│   ├── occupancy/                             # Hourly occupancy, one TSV per unit (17 units)
│   ├── units_metadata.tsv                     # Unit coordinates and attributes → Supplementary Data 1
│   ├── private_labs/                          # Weekly positivity rates, ITpS network (exploratory)
│   │   ├── respat_posrate_SP_state.tsv
│   │   ├── arbo_posrate_SP_state.tsv
│   │   └── vrisp_posrate_SP_state.tsv
│   ├── public_cases/                          # Weekly case counts (validation)
│   │   ├── sivep_cases_SP_state.tsv
│   │   ├── sivep_vrisp_cases_SP_state.tsv
│   │   └── infodengue_cases_SP_state.tsv
│   └── geo/sp_rj_municipality_crs.geojson     # Municipality boundaries for the maps
├── src/
│   ├── occupancy.py                           # Occupancy ETL, moving averages, z-scores, plots
│   ├── geospatial.py                          # Haversine distance matrix
│   ├── plt_maps.py                            # Folium maps
│   ├── units.py                               # Unit panel, excluded dates, wave windows
│   └── paths.py                               # Repository paths, anchored on __file__
├── scripts/                                   # The numbered pipeline, 01 through 09
├── results/
│   ├── consolidated_data_sp.tsv               # Weekly panel → Supplementary Data 2
│   ├── unit_overview/                         # Occupancy series and heatmap → Figure 2A
│   ├── dtw/                                   # Warping paths and distances → Figure 3
│   ├── granger/                               # ADF and Granger results → Supplementary Data 3
│   ├── outbreaks/                             # Volatility index and status maps → Figure 4A, 4B, 4E
│   ├── lead_time/                             # Alert weeks and lead times → Figure 5, Supplementary Data 5-6
│   ├── spatial_associations/                  # Distance matrix and LISA → Figures S1, S2, Supplementary Data 4
│   ├── maps/                                  # Unit locator map → Figure 1A
│   └── supp_data/                             # Supplementary Data 1-7 (TSV and XLSX)
├── CITATION.cff
├── requirements.txt
└── LICENSE
```

## Data

See [`data/DATA_DICTIONARY.md`](data/DATA_DICTIONARY.md) for column definitions,
coverage and checksums.

### Occupancy (included)

Occupancy percentages for 17 public urgent care units across seven municipalities
in the São Paulo metropolitan area, queried hourly from Google Maps between
5 July 2023 and 8 October 2024. The analyses cover the epidemiological weeks from
15 July 2023 to 12 October 2024. Google derives these values from aggregated,
anonymised location history and expresses them as a percentage of each location's
typical peak popularity. No individual-level information is accessed or stored.

Collection was live and hourly; the platform offers no retrospective or batch
retrieval. The TSVs in `data/occupancy/` are therefore the collected record
rather than a re-runnable extraction.

### Private laboratory data (included, aggregated)

Weekly positivity rates from seven private laboratories participating in a
prospective pathogen monitoring initiative coordinated by Instituto Todos pela
Saúde (ITpS), covering São Paulo state. These are the manuscript's exploratory
data and are shipped in `data/private_labs/` as weekly aggregates. The underlying
test-level records are not public.

### Public reference data (included, and publicly available at source)

The validation series in `data/public_cases/` were extracted on **6 April 2025**
from:

- **SIVEP-SRAG** (severe acute respiratory infections) — OPENDATASUS:
  https://opendatasus.saude.gov.br/ → SIVEP-Gripe → Síndrome Respiratória Aguda Grave
- **Dengue** — InfoDengue: https://info.dengue.mat.br/

Both systems revise their records retrospectively, so a fresh retrieval will not
reproduce the counts behind the published results. The 6 April 2025 extraction is
versioned here for that reason, aggregated to weekly totals for São Paulo state.

## Reproducing the Analysis

**Quick start:**

```sh
conda create --name occupancy python=3.12.9
conda activate occupancy
pip install -r requirements.txt

python scripts/01_unit_overview.py    # then 02 through 09, in order
```

Paths resolve relative to the repository, so the scripts run from any working
directory. Each file carries `# %%` cell markers and can also be stepped through
in an interactive window.

**Script guide:**

| Script | Purpose | Output |
|---|---|---|
| `01` | Occupancy panel: hourly → daily → weekly, moving averages, clustered heatmap | Figure 2A |
| `02` | Join occupancy with every laboratory indicator | Supplementary Data 2 |
| `03` | Dynamic time warping against each indicator | Figure 3 |
| `04` | ADF stationarity and Granger causality by wave | Supplementary Data 3 |
| `05` | Z-based epidemic volatility index, per-unit barplots and status maps | Figure 4A, 4B, 4E |
| `06` | Alert weeks, laboratory peaks and lead times | Figure 5, Supplementary Data 5-6 |
| `07` | Haversine distance matrix and LISA spatial clustering | Figures S1, S2, Supplementary Data 4 |
| `08` | Locator map of the 17 units | Figure 1A |
| `09` | Assemble Supplementary Data 1-7 (TSV and XLSX) | Supplementary Data 1-7 |

Final manuscript figures were composed from these outputs. Some elements were
added at composition time and are not produced by any script: panels 1B and 1C
are schematics; the surge shading and the lower average-occupancy panel of
Figure 2A; the line plots in Figures 2B and 2C (their underlying series is
`results/consolidated_data_sp.tsv`); and the absolute-occupancy panels 4C and 4F
(their values are in `results/supp_data/Supplementary Data 4.tsv`). Unit numbers
shown in the figures correspond to the unit index in Supplementary Data 1.

**Requirements:** Python >= 3.12, packages pinned in `requirements.txt`. If the
`dtaidistance` wheel ships without its compiled backend on your platform:
`pip install -vvv --upgrade --force-reinstall --no-deps --no-binary dtaidistance dtaidistance`.

## Reproducibility

Every numeric output is deterministic and reproduces the published values, with
one exception. LISA p-values come from conditional randomisation;
`07_spatial_associations.py` fixes the random seed so the step is repeatable, but
the p-values published in Supplementary Data 4 came from an unseeded run and differ in the
third decimal. Cluster assignments, significance calls and every other column are
unaffected.

PNG outputs are byte-reproducible within a given environment. SVG and HTML are
not: matplotlib embeds generated element identifiers in SVG, and folium assigns a
random map identifier on every run. Compare those by content, not by checksum.

## Citation

If you use this code or data, please cite:

```bibtex
@article{araujo2026healthcare,
  author  = {Araújo, Jose Deney and Santos e Silva, Juan Carlo and
             Bragatte, Marcelo A. S. and Sousa, Erick Rodrigues and
             Schrarstzhaupt, Isaac N. and Sabino, Ester C. and
             Nakaya, Helder I. and Lázari, Carolina dos Santos and
             Pinho, João Renato Rebello and Penna, Gerson Oliveira and
             Kalil, Jorge and Simão, Mariangela and
             Brito, Anderson Fernandes and Sampaio, Vanderson},
  title   = {Healthcare occupancy data as an early warning indicator of
             infectious disease surges in {São Paulo}},
  journal = {Communications Medicine},
  year    = {2026},
  note    = {Under review}
}
```

Each release is archived on Zenodo. The concept DOI
[10.5281/zenodo.22086238](https://doi.org/10.5281/zenodo.22086238) always resolves to
the latest version; cite the version DOI shown on the Zenodo record to reference a
specific release. Machine-readable metadata is in `CITATION.cff`.

## License

- **Code** (`scripts/`, `src/`): [MIT License](LICENSE)
- **Data and results** (`data/`, `results/`): [CC-BY-4.0](https://creativecommons.org/licenses/by/4.0/)

The occupancy values derive from Google Maps and the surveillance series from
SIVEP-SRAG and InfoDengue; see the provenance note in [`LICENSE`](LICENSE).

## Contact

Corresponding author and lead contact: Vanderson Sampaio (vandersons@gmail.com).

## Ethics

All public datasets used here come from repositories that carry no individually
identifiable information. SIVEP-SRAG and InfoDengue are publicly available, follow
open data principles, and do not require research ethics committee approval in
Brazil. Occupancy values are aggregated and anonymised at source by Google using
differential privacy techniques; no individual-level information was accessed or
stored by the authors. Private laboratory data are used only as weekly
state-level aggregates.
