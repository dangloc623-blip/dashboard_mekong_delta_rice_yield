from __future__ import annotations

import json
from pathlib import Path
from typing import Any

try:
    import streamlit as st
except ModuleNotFoundError:  # pragma: no cover - local non-UI checks
    class _NoStreamlit:
        @staticmethod
        def cache_data(*args, **kwargs):
            def decorator(func):
                return func

            return decorator

    st = _NoStreamlit()


GEOJSON_CANDIDATES = [
    Path("dashboard/data/mekong_delta_adm1.geojson"),
    Path("dashboard/mekong_delta_adm1.geojson"),
    Path("data/mekong_delta_adm1.geojson"),
    Path("/mnt/data/mekong_delta_adm1.geojson"),
]

CONTEXT_GEOJSON_CANDIDATES = [
    Path("dashboard/data/mekong_delta_context_adm1.geojson"),
    Path("dashboard/mekong_delta_context_adm1.geojson"),
    Path("data/mekong_delta_context_adm1.geojson"),
    Path("/mnt/data/mekong_delta_context_adm1.geojson"),
]

PROVINCE_PROPERTY_CANDIDATES = [
    "tinh_thanh",
    "name",
    "NAME_1",
    "Name",
    "province",
    "Province",
]


def find_geojson_path() -> Path | None:
    repo_root = Path(__file__).resolve().parents[2]
    dashboard_root = Path(__file__).resolve().parents[1]
    paths = [
        dashboard_root / "data" / "mekong_delta_adm1.geojson",
        dashboard_root / "mekong_delta_adm1.geojson",
        repo_root / "data" / "mekong_delta_adm1.geojson",
        *[Path.cwd() / path for path in GEOJSON_CANDIDATES if not path.is_absolute()],
        *[path for path in GEOJSON_CANDIDATES if path.is_absolute()],
    ]
    for path in paths:
        if path.exists():
            return path
    return None


def find_context_geojson_path() -> Path | None:
    repo_root = Path(__file__).resolve().parents[2]
    dashboard_root = Path(__file__).resolve().parents[1]
    paths = [
        dashboard_root / "data" / "mekong_delta_context_adm1.geojson",
        dashboard_root / "mekong_delta_context_adm1.geojson",
        repo_root / "data" / "mekong_delta_context_adm1.geojson",
        *[Path.cwd() / path for path in CONTEXT_GEOJSON_CANDIDATES if not path.is_absolute()],
        *[path for path in CONTEXT_GEOJSON_CANDIDATES if path.is_absolute()],
    ]
    for path in paths:
        if path.exists():
            return path
    return None


@st.cache_data(show_spinner=False)
def load_geojson(path: Path) -> dict[str, Any]:
    geo = json.loads(path.read_text(encoding="utf-8"))
    
    # Plotly/D3 strict winding order fix: reverse polygon coordinates
    # to prevent them from being rendered as holes in a hemisphere-wrapping background.
    for f in geo.get("features", []):
        geom = f.get("geometry", {})
        coords = geom.get("coordinates")
        if not coords:
            continue
        geom_type = geom.get("type")
        if geom_type == "Polygon":
            # For Polygon, coords is a list of rings. Reverse the first (exterior) ring.
            coords[0] = coords[0][::-1]
        elif geom_type == "MultiPolygon":
            # For MultiPolygon, coords is a list of polygons. Reverse each exterior ring.
            for poly in coords:
                if poly:
                    poly[0] = poly[0][::-1]
    
    return geo


def normalize_geojson_province_property(geojson: dict[str, Any]) -> tuple[dict[str, Any], set[str]]:
    names: set[str] = set()
    for feature in geojson.get("features", []):
        props = feature.setdefault("properties", {})
        value = None
        for key in PROVINCE_PROPERTY_CANDIDATES:
            if props.get(key):
                value = props[key]
                break
        if value:
            props["tinh_thanh"] = value
            feature["id"] = value
            names.add(str(value))
    return geojson, names
