from __future__ import annotations

import math

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from ..filters import FilterState, apply_common_filters, apply_filters, metric_value_column
from ..geo_loader import (
    find_context_geojson_path,
    find_geojson_path,
    load_geojson,
    normalize_geojson_province_property,
)
from ..metrics_config import metric_label, WEATHER_COLUMNS
from ..selection import extract_selected_province_from_plotly_event
from ..theme import apply_plotly_theme, METRIC_COLORSCALES, REGION_COLORS, render_empty_state


MAP_SELECTION_ENABLED = False
MAP_METRIC_OPTIONS = ["nang_suat", "dien_tich", "san_luong", *WEATHER_COLUMNS]
MAP_AGGREGATION_OPTIONS = ["Selected range mean", "Selected year", "Full period mean"]
RANKING_CHART_OPTIONS = ["Dot plot", "Horizontal bar"]
RANKING_SORT_OPTIONS = ["Descending", "Ascending"]


def _walk_coordinate_pairs(coordinates):
    if isinstance(coordinates, list) and coordinates and isinstance(coordinates[0], (int, float)):
        yield coordinates
        return
    if isinstance(coordinates, list):
        for item in coordinates:
            yield from _walk_coordinate_pairs(item)


def _combined_geojson(*geojsons: dict | None) -> dict:
    features = []
    for geojson in geojsons:
        if geojson:
            features.extend(geojson.get("features", []))
    return {"type": "FeatureCollection", "features": features}


def _geojson_bounds(geojson: dict) -> tuple[list[float], list[float]] | None:
    longitudes: list[float] = []
    latitudes: list[float] = []
    for feature in geojson.get("features", []):
        geometry = feature.get("geometry") or {}
        for lon, lat, *_ in _walk_coordinate_pairs(geometry.get("coordinates", [])):
            longitudes.append(float(lon))
            latitudes.append(float(lat))
    if not longitudes or not latitudes:
        return None

    lon_pad = max((max(longitudes) - min(longitudes)) * 0.06, 0.15)
    lat_pad = max((max(latitudes) - min(latitudes)) * 0.06, 0.15)
    return [min(longitudes) - lon_pad, max(longitudes) + lon_pad], [min(latitudes) - lat_pad, max(latitudes) + lat_pad]


def _point_in_ring(lon: float, lat: float, ring: list[list[float]]) -> bool:
    inside = False
    points = ring if ring[0] == ring[-1] else [*ring, ring[0]]
    for current, following in zip(points, points[1:]):
        x0, y0 = float(current[0]), float(current[1])
        x1, y1 = float(following[0]), float(following[1])
        intersects = (y0 > lat) != (y1 > lat)
        if intersects:
            x_intersection = (x1 - x0) * (lat - y0) / (y1 - y0 + 1e-15) + x0
            if lon < x_intersection:
                inside = not inside
    return inside


def _point_in_polygon(lon: float, lat: float, polygon: list[list[list[float]]]) -> bool:
    if not polygon or not _point_in_ring(lon, lat, polygon[0]):
        return False
    return not any(_point_in_ring(lon, lat, hole) for hole in polygon[1:])


def _polygon_signed_area(ring: list[list[float]]) -> float:
    if len(ring) < 3:
        return 0.0
    points = ring if ring[0] == ring[-1] else [*ring, ring[0]]
    total = 0.0
    for current, following in zip(points, points[1:]):
        total += float(current[0]) * float(following[1]) - float(following[0]) * float(current[1])
    return total / 2


def _point_segment_distance_sq(px: float, py: float, ax: float, ay: float, bx: float, by: float) -> float:
    dx = bx - ax
    dy = by - ay
    if dx == 0 and dy == 0:
        return (px - ax) ** 2 + (py - ay) ** 2
    t = max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy)))
    nearest_x = ax + t * dx
    nearest_y = ay + t * dy
    return (px - nearest_x) ** 2 + (py - nearest_y) ** 2


def _distance_to_ring_sq(lon: float, lat: float, ring: list[list[float]]) -> float:
    points = ring if ring[0] == ring[-1] else [*ring, ring[0]]
    distances = [
        _point_segment_distance_sq(
            lon,
            lat,
            float(current[0]),
            float(current[1]),
            float(following[0]),
            float(following[1]),
        )
        for current, following in zip(points, points[1:])
    ]
    return min(distances) if distances else 0.0


def _fallback_centroid(ring: list[list[float]]) -> tuple[float, float]:
    area_twice = 0.0
    centroid_x = 0.0
    centroid_y = 0.0
    points = ring if ring[0] == ring[-1] else [*ring, ring[0]]
    for current, following in zip(points, points[1:]):
        x0, y0 = float(current[0]), float(current[1])
        x1, y1 = float(following[0]), float(following[1])
        cross = x0 * y1 - x1 * y0
        area_twice += cross
        centroid_x += (x0 + x1) * cross
        centroid_y += (y0 + y1) * cross

    if area_twice == 0:
        xs = [float(point[0]) for point in ring]
        ys = [float(point[1]) for point in ring]
        return sum(xs) / len(xs), sum(ys) / len(ys)
    return centroid_x / (3 * area_twice), centroid_y / (3 * area_twice)


def _largest_polygon(geometry: dict) -> list[list[list[float]]] | None:
    coordinates = geometry.get("coordinates", [])
    polygons = coordinates if geometry.get("type") == "MultiPolygon" else [coordinates]
    candidates = [polygon for polygon in polygons if polygon]
    if not candidates:
        return None
    return max(candidates, key=lambda polygon: abs(_polygon_signed_area(polygon[0])))


def _representative_point(geometry: dict) -> tuple[float, float] | None:
    polygon = _largest_polygon(geometry)
    if not polygon:
        return None

    exterior = polygon[0]
    xs = [float(point[0]) for point in exterior]
    ys = [float(point[1]) for point in exterior]
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)

    candidates = [_fallback_centroid(exterior)]
    grid_size = 18
    for x_step in range(1, grid_size):
        lon = min_x + (max_x - min_x) * x_step / grid_size
        for y_step in range(1, grid_size):
            lat = min_y + (max_y - min_y) * y_step / grid_size
            candidates.append((lon, lat))

    best: tuple[float, float, float] | None = None
    for lon, lat in candidates:
        if not _point_in_polygon(lon, lat, polygon):
            continue
        distance = _distance_to_ring_sq(lon, lat, exterior)
        if best is None or distance > best[0]:
            best = (distance, lon, lat)

    if best is None:
        return _fallback_centroid(exterior)
    return best[1], best[2]


def _wrap_label(label: str) -> str:
    if len(label) <= 9:
        return label
    parts = label.split()
    if len(parts) == 2:
        return "<br>".join(parts)
    if len(parts) >= 3:
        midpoint = math.ceil(len(parts) / 2)
        return f"{' '.join(parts[:midpoint])}<br>{' '.join(parts[midpoint:])}"
    return label


def _label_points(geojson: dict, property_name: str, output_col: str = "label") -> pd.DataFrame:
    rows = []
    for feature in geojson.get("features", []):
        props = feature.get("properties") or {}
        label = props.get(property_name)
        point = _representative_point(feature.get("geometry") or {})
        if point is None:
            continue
        lon, lat = point
        rows.append({output_col: label, "lon": lon, "lat": lat, "text": _wrap_label(str(label))})
    return pd.DataFrame(rows).dropna(subset=[output_col, "lon", "lat"])


def _line_segments_from_geometry(geometry: dict):
    coordinates = geometry.get("coordinates", [])
    polygons = coordinates if geometry.get("type") == "MultiPolygon" else [coordinates]

    for polygon in polygons:
        for ring in polygon:
            lons = [float(point[0]) for point in ring]
            lats = [float(point[1]) for point in ring]
            yield lons, lats


def _boundary_trace(geojson: dict, property_name: str, names: set[str] | None = None, width: float = 1.2, color: str = "#273142"):
    lon_values: list[float | None] = []
    lat_values: list[float | None] = []

    for feature in geojson.get("features", []):
        props = feature.get("properties") or {}
        name = props.get(property_name)
        if names is not None and name not in names:
            continue
        for lons, lats in _line_segments_from_geometry(feature.get("geometry") or {}):
            lon_values.extend(lons)
            lon_values.append(None)
            lat_values.extend(lats)
            lat_values.append(None)

    if not lon_values:
        return None

    return go.Scattergeo(
        lon=lon_values,
        lat=lat_values,
        mode="lines",
        line=dict(color=color, width=width),
        hoverinfo="skip",
        showlegend=False,
    )


def _aggregate_series(series: pd.Series, aggregation: str) -> float:
    if aggregation == "sum":
        return float(series.sum(min_count=1))
    return float(series.mean())


@st.cache_data(show_spinner=False)
def _aggregate_map_data(
    df: pd.DataFrame,
    filters: FilterState,
    metric: str = "nang_suat",
    aggregation: str = "Selected range mean",
) -> pd.DataFrame:
    if aggregation == "Full period mean":
        selected = apply_common_filters(df, filters)
    elif aggregation == "Selected year":
        selected = apply_common_filters(df, filters)
        selected_year = filters.selected_year[1] if isinstance(filters.selected_year, tuple) else filters.selected_year
        selected = selected[selected["nam"] == selected_year]
    else:
        selected = apply_filters(df, filters)
    if selected.empty:
        return selected

    agg_dict = {
        "nang_suat": ("nang_suat", "mean"),
        "dien_tich": ("dien_tich", "sum"),
        "san_luong": ("san_luong", "sum"),
        "is_missing_target": ("is_missing_target", "sum"),
    }
    for wcol in WEATHER_COLUMNS:
        if wcol in selected.columns:
            agg_dict[wcol] = (wcol, "mean")

    grouped = (
        selected.groupby(["tinh_thanh", "region"], as_index=False)
        .agg(**agg_dict)
        .rename(
            columns={
                "is_missing_target": "Missing target",
            }
        )
    )
    metric_col = metric_value_column(metric)
    metric_source_col = metric_col
    if metric == "region":
        grouped["metric_value"] = grouped["region"].astype("category").cat.codes
    elif metric_source_col in selected.columns:
        values = (
            selected.groupby("tinh_thanh")[metric_source_col]
            .apply(lambda values: _aggregate_series(values, "mean"))
            .reset_index(name="metric_value")
        )
        grouped = grouped.merge(values, on="tinh_thanh", how="left")
    else:
        grouped["metric_value"] = 0

    year_val = filters.selected_year
    if isinstance(year_val, tuple):
        grouped["nam"] = f"{year_val[0]}-{year_val[1]}"
    else:
        grouped["nam"] = year_val
    grouped["mua_vu"] = filters.selected_season
    grouped["aggregation_scope"] = aggregation

    return grouped.sort_values("metric_value", ascending=False)


def _get_colorscale(metric: str):
    return METRIC_COLORSCALES.get(metric, "YlGnBu")


def _render_ranking(map_df: pd.DataFrame, filters: FilterState) -> None:
    fig = px.bar(
        map_df.sort_values("metric_value", ascending=True),
        x="metric_value",
        y="tinh_thanh",
        color="region",
        orientation="h",
        color_discrete_map=REGION_COLORS,
        labels={
            "metric_value": metric_label(filters.selected_metric),
            "tinh_thanh": "Tỉnh",
            "region": "Region",
        },
        hover_data=[
            "nam",
            "mua_vu",
            "nang_suat",
            "dien_tich",
            "san_luong",
            "Missing target",
        ],
    )
    apply_plotly_theme(fig, height=460)
    fig.update_layout(margin=dict(l=0, r=0, t=10, b=0))
    st.plotly_chart(fig, use_container_width=True)


@st.cache_data(show_spinner=False)
def _aggregate_ranking_data(df: pd.DataFrame, filters: FilterState) -> pd.DataFrame:
    selected = apply_filters(df, filters)
    if selected.empty:
        return pd.DataFrame(columns=["tinh_thanh", "region", "metric_value", "nang_suat", "Missing target"])
    metric = filters.selected_metric
    if metric not in selected.columns:
        metric = "nang_suat"

    grouped = (
        selected.groupby(["tinh_thanh", "region"], as_index=False)
        .agg(
            metric_value=(metric, "mean"),
            nang_suat=("nang_suat", "mean"),
            dien_tich=("dien_tich", "sum"),
            san_luong=("san_luong", "sum"),
            is_missing_target=("is_missing_target", "sum"),
        )
        .rename(columns={"is_missing_target": "Missing target"})
    )
    return grouped.dropna(subset=["metric_value"]).copy()


def _ranking_figure(
    ranking_df: pd.DataFrame,
    chart_type: str,
    sort_order: str,
    selected_provinces: tuple[str, ...],
    metric: str,
) -> go.Figure:
    ascending = sort_order == "Ascending"
    plot_df = ranking_df.sort_values("metric_value", ascending=ascending).copy()
    selected = set(selected_provinces)
    marker_colors = [
        "#0F766E" if province in selected else REGION_COLORS.get(region, "#94A3B8")
        for province, region in zip(plot_df["tinh_thanh"], plot_df["region"])
    ]
    marker_lines = ["#111827" if province in selected else "rgba(17,24,39,0.28)" for province in plot_df["tinh_thanh"]]
    marker_widths = [2.6 if province in selected else 0.8 for province in plot_df["tinh_thanh"]]
    customdata = [[province] for province in plot_df["tinh_thanh"]]

    if chart_type == "Dot plot":
        fig = go.Figure(
            go.Scatter(
                x=plot_df["metric_value"],
                y=plot_df["tinh_thanh"],
                mode="markers",
                marker=dict(
                    size=12,
                    color=marker_colors,
                    line=dict(color=marker_lines, width=marker_widths),
                ),
                customdata=customdata,
                hovertemplate="<b>%{customdata[0]}</b><br>Value=%{x:.3f}<extra></extra>",
            )
        )
    else:
        fig = go.Figure(
            go.Bar(
                x=plot_df["metric_value"],
                y=plot_df["tinh_thanh"],
                orientation="h",
                marker=dict(color=marker_colors, line=dict(color=marker_lines, width=marker_widths)),
                customdata=customdata,
                hovertemplate="<b>%{customdata[0]}</b><br>Value=%{x:.3f}<extra></extra>",
            )
        )

    fig.update_layout(
        xaxis_title=metric_label(metric),
        yaxis_title="Province",
        showlegend=False,
    )
    apply_plotly_theme(fig, height=285)
    fig.update_layout(margin=dict(l=0, r=0, t=10, b=0))
    return fig


def render_ranking_panel(
    df: pd.DataFrame,
    filters: FilterState,
    selected_provinces: tuple[str, ...] = (),
    source: str = "ranking",
) -> str | None:
    st.markdown("#### Province ranking")
    ctrl_col1, ctrl_col2 = st.columns(2, gap="small")
    with ctrl_col1:
        chart_type = st.selectbox(
            "Chart type",
            options=RANKING_CHART_OPTIONS,
            index=0,
            key="ranking_chart_type",
        )
    with ctrl_col2:
        sort_order = st.selectbox(
            "Sort order",
            options=RANKING_SORT_OPTIONS,
            index=0,
            key="ranking_sort_order",
        )

    ranking_df = _aggregate_ranking_data(df, filters)
    if ranking_df.empty:
        render_empty_state("No rows for current filters.", "chart")
        return None

    st.session_state["_selection_valid_provinces_by_source"] = {
        **st.session_state.get("_selection_valid_provinces_by_source", {}),
        source: tuple(ranking_df["tinh_thanh"].dropna().unique().tolist()),
    }
    fig = _ranking_figure(ranking_df, chart_type, sort_order, selected_provinces, filters.selected_metric)
    event = st.plotly_chart(
        fig,
        use_container_width=True,
        key="ranking_selection_chart",
        on_select="rerun",
        selection_mode="points",
        config={"displaylogo": False},
    )
    return extract_selected_province_from_plotly_event(event, source)


@st.cache_data(show_spinner=False)
def _load_context_geojson() -> dict | None:
    context_path = find_context_geojson_path()
    if context_path is None:
        return None
    return load_geojson(context_path)


def _add_context_layer(fig: go.Figure, context_geojson: dict | None) -> None:
    if not context_geojson or not context_geojson.get("features"):
        return

    context_names = [feature.get("properties", {}).get("context_name") for feature in context_geojson["features"]]
    context_labels = [feature.get("properties", {}).get("context_label") for feature in context_geojson["features"]]
    countries = [feature.get("properties", {}).get("country_code") for feature in context_geojson["features"]]

    fig.add_trace(
        go.Choropleth(
            geojson=context_geojson,
            locations=context_names,
            featureidkey="properties.context_name",
            z=[0] * len(context_names),
            colorscale=[[0, "#eef1f5"], [1, "#eef1f5"]],
            showscale=False,
            marker_line_color="#9aa3af",
            marker_line_width=0.7,
            hovertemplate="%{customdata[0]} (%{customdata[1]})<extra></extra>",
            customdata=list(zip(context_labels, countries)),
        )
    )

    context_boundaries = _boundary_trace(context_geojson, "context_name", width=0.8, color="#9aa3af")
    if context_boundaries is not None:
        fig.add_trace(context_boundaries)

    context_labels_df = _label_points(context_geojson, "context_label")
    if not context_labels_df.empty:
        fig.add_trace(
            go.Scattergeo(
                lon=context_labels_df["lon"],
                lat=context_labels_df["lat"],
                text=context_labels_df["text"],
                mode="text",
                textfont=dict(color="#6b7280", size=8, family="Arial"),
                textposition="middle center",
                hoverinfo="skip",
                showlegend=False,
            )
        )


def _build_hover_customdata(map_df: pd.DataFrame) -> tuple[pd.DataFrame, str]:
    """Build customdata array and hovertemplate with all required fields."""
    hover_cols = ["nam", "mua_vu", "region", "nang_suat", "dien_tich", "san_luong"]
    # Add weather columns if present
    weather_present = [w for w in WEATHER_COLUMNS if w in map_df.columns]
    hover_cols.extend(weather_present)
    hover_cols.extend(["Missing target"])

    # Build template
    parts = [
        "<b>%{location}</b><br>",
        "Năm=%{customdata[0]}<br>",
        "Mùa vụ=%{customdata[1]}<br>",
        "Region=%{customdata[2]}<br>",
        "Năng suất (tấn/ha)=%{customdata[3]:.3f}<br>",
        "Diện tích (nghìn ha)=%{customdata[4]:.1f}<br>",
        "Sản lượng (nghìn tấn)=%{customdata[5]:.1f}<br>",
    ]
    idx = 6
    weather_labels = {
        "tổng số giờ nắng": "Giờ nắng",
        "tổng lượng mưa": "Lượng mưa",
        "độ ẩm trung bình": "Độ ẩm TB",
        "nhiệt độ trung bình": "Nhiệt độ TB",
    }
    for w in weather_present:
        label = weather_labels.get(w, w)
        parts.append(f"{label}=%{{customdata[{idx}]:.1f}}<br>")
        idx += 1
    parts.append(f"Missing target=%{{customdata[{idx}]}}<extra></extra>")

    template = "".join(parts)
    valid_cols = [c for c in hover_cols if c in map_df.columns]
    return map_df[valid_cols], template


def _build_hover_customdata(map_df: pd.DataFrame) -> tuple[pd.DataFrame, str]:
    """Build customdata with province as item 0 for native selection."""
    hover_cols = [
        "tinh_thanh",
        "nam",
        "mua_vu",
        "region",
        "nang_suat",
        "dien_tich",
        "san_luong",
        "metric_value",
        "aggregation_scope",
    ]
    weather_present = [col for col in WEATHER_COLUMNS if col in map_df.columns]
    hover_cols.extend(weather_present)
    hover_cols.extend(["Missing target"])

    parts = [
        "<b>%{customdata[0]}</b><br>",
        "Year=%{customdata[1]}<br>",
        "Season=%{customdata[2]}<br>",
        "Region=%{customdata[3]}<br>",
        "Yield=%{customdata[4]:.3f}<br>",
        "Area=%{customdata[5]:.1f}<br>",
        "Production=%{customdata[6]:.1f}<br>",
        "Selected value=%{customdata[7]:.3f}<br>",
        "Aggregation=%{customdata[8]}<br>",
    ]
    idx = 9
    for weather_col in weather_present:
        parts.append(f"{weather_col}=%{{customdata[{idx}]:.1f}}<br>")
        idx += 1
    parts.append(f"Missing target=%{{customdata[{idx}]}}<extra></extra>")

    valid_cols = [col for col in hover_cols if col in map_df.columns]
    return map_df[valid_cols], "".join(parts)


def render_map_or_fallback(df: pd.DataFrame, filters: FilterState) -> None:
    map_df = _aggregate_map_data(df, filters)
    if map_df.empty:
        render_empty_state("No rows for current filters.", "🗺️")
        return

    geo_path = find_geojson_path()
    if geo_path is None:
        st.caption("⚠️ GeoJSON layer not loaded — showing province ranking fallback")
        _render_ranking(map_df, filters)
        return

    geojson, geo_names = normalize_geojson_province_property(load_geojson(geo_path))
    expected_names = set(df["tinh_thanh"].dropna().unique().tolist())
    if not expected_names.issubset(geo_names):
        st.caption("⚠️ GeoJSON province mismatch — showing province ranking fallback")
        _render_ranking(map_df, filters)
        return

    context_geojson = _load_context_geojson()
    metric_values = map_df["metric_value"].dropna()
    zmin = float(metric_values.min()) if not metric_values.empty else None
    zmax = float(metric_values.max()) if not metric_values.empty else None

    colorscale = _get_colorscale(filters.selected_metric)

    fig = go.Figure()
    _add_context_layer(fig, context_geojson)

    customdata_df, hovertemplate = _build_hover_customdata(map_df)

    fig.add_trace(
        go.Choropleth(
            geojson=geojson,
            locations=map_df["tinh_thanh"].tolist(),
            featureidkey="properties.tinh_thanh",
            z=map_df["metric_value"].tolist(),
            zmin=zmin,
            zmax=zmax,
            colorscale=colorscale,
            marker_line_color="#111827",
            marker_line_width=1.15,
            colorbar=dict(
                title=metric_label(filters.selected_metric),
                bgcolor="rgba(0,0,0,0)",
                outlinecolor="#d5d9e2",
                outlinewidth=1,
            ),
            customdata=customdata_df,
            hovertemplate=hovertemplate,
        )
    )

    boundary = _boundary_trace(geojson, "tinh_thanh", width=1.65, color="#111827")
    if boundary is not None:
        fig.add_trace(boundary)

    label_df = _label_points(geojson, "tinh_thanh")
    if not label_df.empty:
        fig.add_trace(
            go.Scattergeo(
                lon=label_df["lon"],
                lat=label_df["lat"],
                text=label_df["text"],
                mode="text",
                textfont=dict(color="#111827", size=8, family="Arial"),
                textposition="middle center",
                hoverinfo="skip",
                showlegend=False,
            )
        )

    bounds_geojson = _combined_geojson(geojson, context_geojson)
    bounds = _geojson_bounds(bounds_geojson)
    geo_config = dict(
        projection_type="mercator",
        visible=False,
        bgcolor="rgba(0,0,0,0)",
        showland=False,
        showocean=False,
        showlakes=False,
        showcountries=False,
        showcoastlines=False,
        showframe=False,
    )
    if bounds:
        lon_range, lat_range = bounds
        geo_config.update(lonaxis_range=lon_range, lataxis_range=lat_range)
    fig.update_geos(**geo_config)

    fig.update_layout(
        height=560,
        margin=dict(l=0, r=0, t=8, b=0),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, system-ui, sans-serif", color="#172033"),
        dragmode=False,
    )

    st.plotly_chart(
        fig,
        use_container_width=True,
        config={
            "displaylogo": False,
            "scrollZoom": False,
        },
    )


def render_spatial_panel(
    df: pd.DataFrame,
    filters: FilterState,
    selected_provinces: tuple[str, ...] = (),
    enable_selection: bool = MAP_SELECTION_ENABLED,
) -> str | None:
    st.markdown("#### Spatial view")
    ctrl_col1, ctrl_col2 = st.columns(2, gap="small")
    with ctrl_col1:
        map_metric_options = [option for option in MAP_METRIC_OPTIONS if option in df.columns]
        default_metric = filters.selected_metric if filters.selected_metric in map_metric_options else "nang_suat"
        metric = st.selectbox(
            "Metric",
            options=map_metric_options,
            index=map_metric_options.index(default_metric),
            format_func=metric_label,
            key="map_metric",
        )
    with ctrl_col2:
        aggregation = st.selectbox(
            "Aggregation",
            options=MAP_AGGREGATION_OPTIONS,
            index=0,
            key="map_aggregation",
        )

    map_df = _aggregate_map_data(df, filters, metric, aggregation)
    if map_df.empty:
        render_empty_state("No rows for current filters.", "map")
        return None

    geo_path = find_geojson_path()
    if geo_path is None:
        st.caption("GeoJSON layer not loaded; showing province ranking fallback.")
        return render_ranking_panel(df, filters, selected_provinces=selected_provinces, source="map_fallback")

    geojson, geo_names = normalize_geojson_province_property(load_geojson(geo_path))
    expected_names = set(df["tinh_thanh"].dropna().unique().tolist())
    if not expected_names.issubset(geo_names):
        st.caption("GeoJSON province mismatch; showing province ranking fallback.")
        return render_ranking_panel(df, filters, selected_provinces=selected_provinces, source="map_fallback")

    context_geojson = _load_context_geojson()
    metric_values = map_df["metric_value"].dropna()
    zmin = float(metric_values.min()) if not metric_values.empty else None
    zmax = float(metric_values.max()) if not metric_values.empty else None

    fig = go.Figure()
    _add_context_layer(fig, context_geojson)
    customdata_df, hovertemplate = _build_hover_customdata(map_df)
    fig.add_trace(
        go.Choropleth(
            geojson=geojson,
            locations=map_df["tinh_thanh"].tolist(),
            featureidkey="properties.tinh_thanh",
            z=map_df["metric_value"].tolist(),
            zmin=zmin,
            zmax=zmax,
            colorscale=_get_colorscale(metric),
            marker_line_color="#111827",
            marker_line_width=1.15,
            colorbar=dict(
                title=metric_label(metric),
                bgcolor="rgba(0,0,0,0)",
                outlinecolor="#d5d9e2",
                outlinewidth=1,
            ),
            customdata=customdata_df,
            hovertemplate=hovertemplate,
        )
    )

    boundary = _boundary_trace(geojson, "tinh_thanh", width=1.65, color="#111827")
    if boundary is not None:
        fig.add_trace(boundary)

    if selected_provinces:
        selected_boundary = _boundary_trace(
            geojson,
            "tinh_thanh",
            names=set(selected_provinces),
            width=3.1,
            color="#0F766E",
        )
        if selected_boundary is not None:
            fig.add_trace(selected_boundary)

    label_df = _label_points(geojson, "tinh_thanh")
    if not label_df.empty:
        fig.add_trace(
            go.Scattergeo(
                lon=label_df["lon"],
                lat=label_df["lat"],
                text=label_df["text"],
                mode="text",
                textfont=dict(color="#111827", size=8, family="Arial"),
                textposition="middle center",
                hoverinfo="skip",
                showlegend=False,
            )
        )

    bounds = _geojson_bounds(_combined_geojson(geojson, context_geojson))
    geo_config = dict(
        projection_type="mercator",
        visible=False,
        bgcolor="rgba(0,0,0,0)",
        showland=False,
        showocean=False,
        showlakes=False,
        showcountries=False,
        showcoastlines=False,
        showframe=False,
    )
    if bounds:
        lon_range, lat_range = bounds
        geo_config.update(lonaxis_range=lon_range, lataxis_range=lat_range)
    fig.update_geos(**geo_config)
    fig.update_layout(
        height=560,
        margin=dict(l=0, r=0, t=8, b=0),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, system-ui, sans-serif", color="#172033"),
        dragmode=False,
    )

    config = {"displaylogo": False, "scrollZoom": False}
    if enable_selection:
        source = "map"
        st.session_state["_selection_valid_provinces_by_source"] = {
            **st.session_state.get("_selection_valid_provinces_by_source", {}),
            source: tuple(map_df["tinh_thanh"].dropna().unique().tolist()),
        }
        event = st.plotly_chart(
            fig,
            use_container_width=True,
            key="map_selection_chart",
            on_select="rerun",
            selection_mode="points",
            config=config,
        )
        return extract_selected_province_from_plotly_event(event, source)

    st.plotly_chart(fig, use_container_width=True, config=config)
    return None
