"""Helpers for the public surveillance sources (SIVEP-SRAG and InfoDengue)."""

import pandas as pd

SIVEP_URL = (
    "http://blob.monit.radim.org.br/public/"
    "data%2Frespat%2FSIVEP%2FSIVEP.csv"
)
INFODENGUE_URL = (
    "http://blob.monit.radim.org.br/public/"
    "data%2Farbo%2Finfodengue%2FInfo%20Dengue%20Casos%20por%20Estado.csv"
)


def get_data_public(path_url, out_path_file_name):
    """Download a public surveillance dump and cache it locally.

    The dumps are large (the SIVEP one is several hundred MB) and are not
    versioned in this repository.
    """
    data = pd.read_csv(path_url, sep=';')
    print(data.head())
    data.to_csv(out_path_file_name, index=False, sep=';')


def epiweek_enddate(date_column):
    """Map each date to the Saturday that closes its epidemiological week."""
    dates = pd.to_datetime(date_column, errors='coerce')
    return dates + pd.to_timedelta((5 - dates.dt.dayofweek) % 7, unit='D')
