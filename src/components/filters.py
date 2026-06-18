from __future__ import annotations

import pandas as pd
import streamlit as st

from ..filters import FilterState
from ..metrics_config import METRIC_CONFIG, metric_label

FILTER_PREFIX = "filter_"
APPLIED_FILTER_KEY = "_applied_filter_values"


def _clamp_year(value: int, min_year: int, max_year: int) -> int:
    return max(min_year, min(max_year, int(value)))


def _normalize_year_range(value: object, min_year: int, max_year: int) -> tuple[int, int]:
    if isinstance(value, (tuple, list)) and len(value) == 2:
        start = _clamp_year(int(value[0]), min_year, max_year)
        end = _clamp_year(int(value[1]), min_year, max_year)
        return (min(start, end), max(start, end))
    return (min_year, max_year)


def _default_values(
    min_year: int,
    max_year: int,
    region_options: list[str],
    province_options: list[str],
) -> dict:
    return {
        "year_mode": "Range",
        "snapshot_year": max_year,
        "year_range": (min_year, max_year),
        "selected_season": "All",
        "selected_metric": "nang_suat",
        "selected_regions": region_options,
        "selected_provinces": province_options,
        "show_missing": True,
    }


def _filter_state_from_values(values: dict) -> FilterState:
    selected_year: int | tuple[int, int]
    if values["year_mode"] == "Range":
        selected_year = tuple(values["year_range"])
    else:
        selected_year = int(values["snapshot_year"])

    return FilterState(
        year_mode=str(values["year_mode"]),
        selected_year=selected_year,
        selected_season=str(values["selected_season"]),
        selected_metric=str(values["selected_metric"]),
        selected_regions=tuple(values["selected_regions"]),
        selected_provinces=tuple(values["selected_provinces"]),
        show_missing=bool(values["show_missing"]),
    )


def _sanitize_values(
    values: dict,
    min_year: int,
    max_year: int,
    region_options: list[str],
    province_options: list[str],
) -> dict:
    result = dict(values)
    if result.get("year_mode") not in {"Snapshot", "Range"}:
        result["year_mode"] = "Snapshot"
    result["snapshot_year"] = _clamp_year(result.get("snapshot_year", max_year), min_year, max_year)
    result["year_range"] = _normalize_year_range(result.get("year_range", (min_year, max_year)), min_year, max_year)
    result["selected_season"] = result.get("selected_season", "All")
    if result["selected_season"] not in {"All", "dong_xuan", "he_thu-thu_dong"}:
        result["selected_season"] = "All"
    result["selected_metric"] = result.get("selected_metric", "nang_suat")
    if result["selected_metric"] not in METRIC_CONFIG:
        result["selected_metric"] = "nang_suat"
    result["selected_regions"] = [region for region in result.get("selected_regions", region_options) if region in region_options]
    if not result["selected_regions"]:
        result["selected_regions"] = region_options
    result["selected_provinces"] = [
        province for province in result.get("selected_provinces", province_options)
        if province in province_options
    ]
    if not result["selected_provinces"]:
        result["selected_provinces"] = province_options
    result["show_missing"] = bool(result.get("show_missing", True))
    return result


def _set_widget_defaults(values: dict) -> None:
    for key, value in values.items():
        st.session_state[f"{FILTER_PREFIX}{key}"] = value


def _read_widget_values() -> dict:
    return {
        "year_mode": st.session_state[f"{FILTER_PREFIX}year_mode"],
        "snapshot_year": st.session_state[f"{FILTER_PREFIX}snapshot_year"],
        "year_range": st.session_state[f"{FILTER_PREFIX}year_range"],
        "selected_season": st.session_state[f"{FILTER_PREFIX}selected_season"],
        "selected_metric": st.session_state[f"{FILTER_PREFIX}selected_metric"],
        "selected_regions": st.session_state[f"{FILTER_PREFIX}selected_regions"],
        "selected_provinces": st.session_state[f"{FILTER_PREFIX}selected_provinces"],
        "show_missing": st.session_state[f"{FILTER_PREFIX}show_missing"],
    }


def _sync_session_defaults(
    min_year: int,
    max_year: int,
    region_options: list[str],
    all_province_options: list[str],
    province_options: list[str],
) -> None:
    defaults = _default_values(min_year, max_year, region_options, all_province_options)

    if st.session_state.pop("_reset_filters_requested", False) or APPLIED_FILTER_KEY not in st.session_state:
        st.session_state[APPLIED_FILTER_KEY] = defaults
        _set_widget_defaults(defaults)

    applied = _sanitize_values(
        st.session_state[APPLIED_FILTER_KEY],
        min_year,
        max_year,
        region_options,
        all_province_options,
    )
    st.session_state[APPLIED_FILTER_KEY] = applied

    for key, default_value in defaults.items():
        widget_key = f"{FILTER_PREFIX}{key}"
        if widget_key not in st.session_state:
            st.session_state[widget_key] = applied.get(key, default_value)

    st.session_state[f"{FILTER_PREFIX}year_mode"] = (
        st.session_state[f"{FILTER_PREFIX}year_mode"]
        if st.session_state[f"{FILTER_PREFIX}year_mode"] in {"Snapshot", "Range"}
        else "Snapshot"
    )
    st.session_state[f"{FILTER_PREFIX}snapshot_year"] = _clamp_year(
        st.session_state[f"{FILTER_PREFIX}snapshot_year"],
        min_year,
        max_year,
    )
    st.session_state[f"{FILTER_PREFIX}year_range"] = _normalize_year_range(
        st.session_state[f"{FILTER_PREFIX}year_range"],
        min_year,
        max_year,
    )
    st.session_state[f"{FILTER_PREFIX}selected_regions"] = [
        region for region in st.session_state[f"{FILTER_PREFIX}selected_regions"]
        if region in region_options
    ] or region_options
    st.session_state[f"{FILTER_PREFIX}selected_provinces"] = [
        province for province in st.session_state[f"{FILTER_PREFIX}selected_provinces"]
        if province in province_options
    ] or province_options

    province_override = st.session_state.pop("_prov_default", None)
    if province_override is not None:
        clicked_provinces = [province for province in province_override if province in all_province_options]
        st.session_state[f"{FILTER_PREFIX}selected_provinces"] = clicked_provinces
        st.session_state[APPLIED_FILTER_KEY] = {
            **applied,
            "selected_provinces": clicked_provinces,
        }


def _province_options_for_regions(df: pd.DataFrame, regions: list[str]) -> list[str]:
    province_source = df[df["region"].isin(regions)] if regions else df
    return sorted(province_source["tinh_thanh"].dropna().unique().tolist())


def _mirror_explicit_state(values: dict) -> None:
    st.session_state["year_mode"] = values["year_mode"]
    st.session_state["selected_year"] = values["snapshot_year"]
    st.session_state["selected_year_range"] = values["year_range"]
    st.session_state["selected_season"] = values["selected_season"]
    st.session_state["active_metric"] = values["selected_metric"]
    st.session_state["selected_regions"] = tuple(values["selected_regions"])
    st.session_state["sidebar_selected_provinces"] = tuple(values["selected_provinces"])


def render_filters(df: pd.DataFrame) -> FilterState:
    min_year = int(df["nam"].min())
    max_year = int(df["nam"].max())
    region_options = sorted(df["region"].dropna().unique().tolist())
    all_province_options = sorted(df["tinh_thanh"].dropna().unique().tolist())

    draft_regions = st.session_state.get(f"{FILTER_PREFIX}selected_regions", region_options) or region_options
    province_options = _province_options_for_regions(df, draft_regions)

    _sync_session_defaults(min_year, max_year, region_options, all_province_options, province_options)

    with st.sidebar.form("filters_form"):
        st.markdown("### Time")
        year_mode = st.radio(
            "Year mode",
            options=["Snapshot", "Range"],
            horizontal=True,
            key=f"{FILTER_PREFIX}year_mode",
        )
        if year_mode == "Range":
            st.slider(
                "Year",
                min_value=min_year,
                max_value=max_year,
                step=1,
                key=f"{FILTER_PREFIX}year_range",
            )
        else:
            st.slider(
                "Year",
                min_value=min_year,
                max_value=max_year,
                step=1,
                key=f"{FILTER_PREFIX}snapshot_year",
            )

        st.selectbox(
            "Season",
            options=["All", "dong_xuan", "he_thu-thu_dong"],
            key=f"{FILTER_PREFIX}selected_season",
        )

        st.markdown("### Data")
        st.selectbox(
            "Primary metric",
            options=list(METRIC_CONFIG.keys()),
            format_func=lambda key: metric_label(key),
            key=f"{FILTER_PREFIX}selected_metric",
        )

        st.markdown("### Space")
        st.multiselect(
            "Region",
            options=region_options,
            key=f"{FILTER_PREFIX}selected_regions",
        )

        selected_count = len(st.session_state.get(f"{FILTER_PREFIX}selected_provinces", []))
        with st.expander(f"Provinces ({selected_count}/{len(province_options)} selected)", expanded=False):
            st.multiselect(
                "Select province",
                options=province_options,
                key=f"{FILTER_PREFIX}selected_provinces",
                label_visibility="collapsed",
            )

        st.markdown("### Actions")
        apply_clicked = st.form_submit_button("Apply filters", use_container_width=True)
        reset_clicked = st.form_submit_button("Reset filters", use_container_width=True)
        clear_clicked = st.form_submit_button("Clear selected provinces", use_container_width=True)

    if clear_clicked:
        st.session_state["interactive_selected_provinces"] = ()
        st.rerun()

    if reset_clicked:
        st.session_state["_reset_filters_requested"] = True
        st.session_state["interactive_selected_provinces"] = ()
        st.rerun()

    if apply_clicked:
        raw_values = _read_widget_values()
        apply_regions = [
            region for region in raw_values.get("selected_regions", region_options)
            if region in region_options
        ] or region_options
        apply_province_options = _province_options_for_regions(df, apply_regions)
        widget_values = _sanitize_values(
            raw_values,
            min_year,
            max_year,
            region_options,
            apply_province_options,
        )
        st.session_state[APPLIED_FILTER_KEY] = widget_values
        _mirror_explicit_state(widget_values)
        return _filter_state_from_values(widget_values)

    _mirror_explicit_state(st.session_state[APPLIED_FILTER_KEY])
    return _filter_state_from_values(st.session_state[APPLIED_FILTER_KEY])
