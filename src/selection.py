from __future__ import annotations

from typing import Any, Optional

try:
    import streamlit as st
except ModuleNotFoundError:  # pragma: no cover - local non-UI checks
    st = None


def _read_value(obj: Any, key: str, default: Any = None) -> Any:
    if obj is None:
        return default
    if isinstance(obj, dict):
        return obj.get(key, default)
    return getattr(obj, key, default)


def _first_customdata_value(customdata: Any) -> Any:
    if customdata is None:
        return None
    if isinstance(customdata, dict):
        for key in ("province", "tinh_thanh", "name", "label"):
            if customdata.get(key):
                return customdata[key]
        return None
    if isinstance(customdata, (list, tuple)):
        return customdata[0] if customdata else None
    return customdata


def _valid_provinces_for_source(source: str) -> set[str]:
    if st is None:
        return set()
    configured = st.session_state.get("_selection_valid_provinces_by_source", {})
    values = configured.get(source, ()) if isinstance(configured, dict) else ()
    return {str(value) for value in values}


def _clean_candidate(value: Any) -> Optional[str]:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def extract_selected_province_from_plotly_event(event: Any, source: str) -> Optional[str]:
    """Return a selected province from a Streamlit Plotly selection payload.

    The function is intentionally defensive because Streamlit and Plotly can
    return empty or source-specific payloads during reruns.
    """
    try:
        selection = _read_value(event, "selection")
        points = _read_value(selection, "points", [])
        if not points:
            return None

        valid_provinces = _valid_provinces_for_source(source)
        for point in points:
            customdata_value = _clean_candidate(_first_customdata_value(_read_value(point, "customdata")))
            if customdata_value:
                return customdata_value

            for key in ("location", "label", "x", "y"):
                fallback = _clean_candidate(_read_value(point, key))
                if fallback and fallback in valid_provinces:
                    return fallback
    except Exception:
        return None
    return None
