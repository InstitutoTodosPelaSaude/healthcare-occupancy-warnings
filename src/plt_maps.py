"""Folium maps of the monitored units over the São Paulo metropolitan area."""

import json

import folium

# Radius of the catchment circle drawn around each unit, in metres
UNIT_CIRCLE_RADIUS_M = 750

STATUS_COLORS = {
    'green': 'green',
    'orange': 'orange',
    'red': 'red',
    'lightgray': 'lightgray',
}


def _load_geojson(path_geojson):
    with open(path_geojson, 'r') as file:
        return json.load(file)


def folium_mapping(data, path_geojson):
    """Locator map of every monitored unit (Figure 1A).

    `data` must carry name, lat, lon, city, rating_score, n_reviews,
    open_24h and link.
    """

    map_center = [data['lat'].mean(), data['lon'].mean()]
    unit_map = folium.Map(
        location=map_center,
        zoom_start=10,
        tiles='CartoDB positron',
        min_zoom=10,
    )

    for _, row in data.iterrows():
        folium.Circle(
            radius=UNIT_CIRCLE_RADIUS_M,
            location=[row['lat'], row['lon']],
            color='black',
            weight=0.1,
            fill=True,
            fill_color='#ff9966',
            fill_opacity=0.75,
        ).add_to(unit_map)

    sp_geojson = _load_geojson(path_geojson)
    highlight_cities = set(data['city'].unique())

    def style_function(feature):
        if feature['properties']['name_muni'] in highlight_cities:
            return {'fillColor': '#000000', 'color': 'black',
                    'weight': 1, 'fillOpacity': 0}
        return {'fillColor': '#ffffff', 'color': '#ffffff',
                'weight': 0, 'fillOpacity': 1}

    folium.GeoJson(
        data=sp_geojson,
        name='Municipalities',
        style_function=style_function,
    ).add_to(unit_map)

    return unit_map


def map_status_by_date(date, metrics_by_unit, path_geojson, path_metadata,
                       background_color):
    """Per-unit occupancy status for one epidemiological week (Figure 4D/G)."""

    import pandas as pd

    location_data = pd.read_csv(path_metadata, sep="\t")
    location_data['city'] = location_data['city'].str.title()

    def get_zoom_level(min_lat, max_lat, min_lon, max_lon):
        """Pick a zoom level from the bounding box of the units."""
        lat_range = max_lat - min_lat
        lon_range = max_lon - min_lon
        span = max(lat_range, lon_range)

        if span > 2:
            return 7    # very broad area
        if span > 0.5:
            return 9    # moderate area
        if span > 0.1:
            return 11   # city level
        if span > 0.05:
            return 13   # city level, tighter
        return 14       # close-up

    min_lat, max_lat = location_data['lat'].min(), location_data['lat'].max()
    min_lon, max_lon = location_data['lon'].min(), location_data['lon'].max()

    zoom_start_value = get_zoom_level(min_lat, max_lat, min_lon, max_lon)
    min_zoom_value = zoom_start_value - 1

    map_center = [location_data['lat'].mean(), location_data['lon'].mean()]
    status_map = folium.Map(
        location=map_center,
        zoom_start=zoom_start_value,
        tiles='CartoDB positron',
        min_zoom=min_zoom_value,
    )

    for _, row in location_data.iterrows():
        unit_name = row['name']

        if unit_name not in metrics_by_unit:
            continue
        if date not in metrics_by_unit[unit_name].index:
            continue

        unit_status = metrics_by_unit[unit_name].loc[date, 'status']
        marker_color = STATUS_COLORS.get(unit_status, 'lightgray')

        popup = folium.Popup(
            f"""
            <h5><strong>{unit_name}</strong></h5>
            <br>Status: {unit_status.title()}
            <br><a href='{row['link']}' target='_blank'>More info</a>
            """,
            max_width=250,
        )
        tooltip = folium.Tooltip(
            f"""
            <h5><strong>{unit_name}</strong></h5>
            <h6>City: {row['city']}</h6>
            """
        )

        folium.Marker(
            [row['lat'], row['lon']],
            popup=popup,
            tooltip=tooltip,
            icon=folium.Icon(color=marker_color, icon='plus'),
        ).add_to(status_map)

        folium.Circle(
            radius=UNIT_CIRCLE_RADIUS_M,
            location=[row['lat'], row['lon']],
            color='black',
            weight=0.2,
            fill=True,
            fill_color='#ff9966',
            fill_opacity=0.5,
        ).add_to(status_map)

    sp_geojson = _load_geojson(path_geojson)
    highlight_cities = set(location_data['city'].unique())

    def style_function(feature):
        if feature['properties']['name_muni'] in highlight_cities:
            return {'fillColor': background_color, 'color': 'black',
                    'weight': 1.5, 'fillOpacity': 0.2}
        return {'fillColor': '#ffffff', 'color': 'black',
                'weight': 0.2, 'fillOpacity': 0.5}

    folium.GeoJson(
        data=sp_geojson,
        style_function=style_function,
    ).add_to(status_map)

    return status_map
