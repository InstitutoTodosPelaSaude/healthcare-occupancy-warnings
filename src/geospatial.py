"""Great-circle distances between the monitored units."""

from math import atan2, cos, radians, sin, sqrt

import pandas as pd

EARTH_RADIUS_KM = 6371.0


def haversine(lat1, lon1, lat2, lon2):
    """Great-circle distance in kilometres between two coordinate pairs."""
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = (
        sin(dlat / 2) ** 2
        + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
    )
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    return EARTH_RADIUS_KM * c


def create_distance_matrix(df):
    """Pairwise Haversine distance matrix, indexed and labelled by unit name.

    `df` must carry the columns `name`, `lat` and `lon`.
    """
    units = df['name'].tolist()
    matrix = pd.DataFrame(index=units, columns=units, dtype=float)

    for _, row_i in df.iterrows():
        for _, row_j in df.iterrows():
            matrix.at[row_i['name'], row_j['name']] = haversine(
                row_i['lat'], row_i['lon'], row_j['lat'], row_j['lon']
            )

    return matrix
