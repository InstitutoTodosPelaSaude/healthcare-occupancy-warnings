"""The monitored unit panel: file list, excluded dates and name standardisation.

Kept in one place because scripts 01, 06 and 10 all need the same 17 units
and the same exclusion window.
"""

# The 17 public urgent care units analysed in the manuscript.
# Each entry is a file name under data/detecta/.
GOLD_STANDARD_LIST = [
    'UPA Vila Assis.tsv',
    'UPA PEDREIRA - Dr. César Antunes da Rocha.tsv',
    'Unidade de Pronto Atendimento - UPA Zaíra.tsv',
    'AMA 24h Capão Redondo.tsv',
    'UPA Rudge Ramos.tsv',
    'UPA St. John - Lavras.tsv',
    'UPA VICENTE MISSIANO.tsv',
    'UPA Sacadura Cabral.tsv',
    'UPA Vila Mariana.tsv',
    'Unidade de Pronto Atendimento Akira Tada.tsv',
    'UPA - Pauliceia Taboão.tsv',
    'Unidade Avançada Carlos Chagas.tsv',
    'AMA SOROCABANA -PRONTO ATENDIMENTO.tsv',
    'UPA Paulista - Unidade de Pronto Atendimento.tsv',
    'UPA Vergueiro.tsv',
    'UPA Tito Lopes.tsv',
    'UPA Vila Santa Catarina.tsv',
]

# Days dropped from the panel: connectivity outages that left consecutive
# days without readings. 2023-12-23 is kept and linearly interpolated.
DATES_TO_REMOVE = [
    '2023-07-05', '2023-07-06', '2023-07-07', '2023-07-08',
    '2023-08-13', '2023-08-14', '2023-08-15', '2023-08-16', '2023-08-17',
    '2023-08-18', '2023-08-19',
    '2023-11-19', '2023-11-20', '2023-11-21', '2023-11-22', '2023-11-23',
    '2023-11-24', '2023-11-25', '2023-11-26', '2023-11-27', '2023-11-28',
    '2023-11-29', '2023-11-30',
    '2023-12-01', '2023-12-02', '2023-12-03', '2023-12-04', '2023-12-05',
    '2023-12-06', '2023-12-07', '2023-12-08', '2023-12-09',
    '2023-12-24', '2023-12-25', '2023-12-26', '2023-12-27', '2023-12-28',
    '2023-12-29', '2023-12-30',
]

# The five epidemiological weeks reported as excluded in the Methods.
EXCLUDED_WEEKS = [
    '2023-08-19', '2023-11-25', '2023-12-02', '2023-12-09', '2023-12-30',
]

# The two representative weeks compared in Figure 4 and Figure S1.
OUTBREAK_WEEK = '2023-08-26'
NON_OUTBREAK_WEEK = '2023-11-04'

# Study period (Methods: 15 July 2023 to 12 October 2024).
STUDY_START = '2023-07-15'
STUDY_END = '2024-10-12'

# Two sets of wave windows, deliberately different.
#
# GRANGER_WAVES are the shifted windows used for the causality tests: they are
# trimmed to whole epidemiological weeks with complete differenced series, so
# each test has enough observations for the lag structure being tested.
#
# LEAD_TIME_WAVES are the wider epidemic periods described in the Methods
# (July-December 2023, October 2023-June 2024, June-October 2024), used to
# locate the laboratory surge peak and the first occupancy alert.
GRANGER_WAVES = [
    ("2023-07-22", "2023-12-23"),
    ("2023-10-21", "2024-06-22"),
    ("2024-06-08", "2024-10-12"),
]

LEAD_TIME_WAVES = {
    'Wave 1': ('2023-07-15', '2023-12-31'),
    'Wave 2': ('2023-10-01', '2024-06-30'),
    'Wave 3': ('2024-06-01', '2024-10-12'),
}

# Maps each Granger test target back to its pathogen group, so the
# significance flags in Table S6 can be derived from the step 05 output
# instead of being transcribed by hand.
GRANGER_TARGET_TO_GROUP = {
    'sivep_cases_sc2_norm': 'SC2',
    'radim_posrate_sc2': 'SC2',
    'infodengue_diff': 'Denv',
    'radim_denv_diff': 'Denv',
    'radim_posrate_vrisp': 'RV',
    'sivep_vrisp_cases_norm': 'RV',
}

# Raw Google Maps establishment names mapped to the standardised names
# used in the manuscript figures and supplementary tables.
NAME_MAPPING = {
    "Unidade de Pronto Atendimento Akira Tada": "UPA Akira Tada",
    "UPA Paulista - Unidade de Pronto Atendimento": "UPA Paulista",
    "UPA PEDREIRA - Dr. César Antunes da Rocha": "UPA Pedreira - Dr. César Antunes da Rocha",
    "UPA Tito Lopes": "UPA Tito Lopes",
    "UPA VICENTE MISSIANO": "UPA Vicente Missiano",
    "UPA Vila Mariana": "UPA Vila Mariana",
    "UPA Sacadura Cabral": "UPA Sacadura Cabral",
    "Unidade de Pronto Atendimento - UPA Zaíra": "UPA Zaíra",
    "UPA Rudge Ramos": "UPA Rudge Ramos",
    "UPA St. John - Lavras": "UPA St. John - Lavras",
    "AMA SOROCABANA -PRONTO ATENDIMENTO": "AMA Sorocabana - Pronto atendimento",
    "UPA Vergueiro": "UPA Vergueiro",
    "Unidade Avançada Carlos Chagas": "Unidade Avançada Carlos Chagas",
    "UPA Vila Santa Catarina": "UPA Vila Santa Catarina",
    "AMA 24h Capão Redondo": "AMA Capão Redondo",
    "UPA - Pauliceia Taboão": "UPA Pauliceia Taboão",
    "UPA Vila Assis": "UPA Vila Assis",
}

# Stable unit numbering used across Tables S1 and S4.
UNIT_INDEX = {
    "UPA Vicente Missiano": 1,
    "UPA Vergueiro": 2,
    "UPA St. John - Lavras": 3,
    "UPA Tito Lopes": 4,
    "AMA Capão Redondo": 5,
    "UPA Paulista": 6,
    "UPA Vila Santa Catarina": 7,
    "UPA Pauliceia Taboão": 8,
    "UPA Rudge Ramos": 9,
    "UPA Sacadura Cabral": 10,
    "Unidade Avançada Carlos Chagas": 11,
    "UPA Pedreira - Dr. César Antunes da Rocha": 12,
    "UPA Akira Tada": 13,
    "AMA Sorocabana - Pronto atendimento": 14,
    "UPA Vila Assis": 15,
    "UPA Vila Mariana": 16,
    "UPA Zaíra": 17,
}
