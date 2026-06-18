from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from .metrics_config import METRIC_CONFIG

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


@dataclass(frozen=True)
class FilterState:
    year_mode: str
    selected_year: int | tuple[int, int]
    selected_season: str
    selected_metric: str
    selected_regions: tuple[str, ...]
    selected_provinces: tuple[str, ...]
    show_missing: bool


@st.cache_data(show_spinner=False)
def apply_common_filters(df: pd.DataFrame, filters: FilterState) -> pd.DataFrame:
    result = df.copy()
    if filters.selected_season != "All":
        result = result[result["mua_vu"] == filters.selected_season]
    if filters.selected_regions:
        result = result[result["region"].isin(filters.selected_regions)]
    if filters.selected_provinces:
        result = result[result["tinh_thanh"].isin(filters.selected_provinces)]
    if not filters.show_missing:
        result = result[~result["is_missing_target"]]
    return result.copy()


@st.cache_data(show_spinner=False)
def apply_filters(df: pd.DataFrame, filters: FilterState) -> pd.DataFrame:
    result = apply_common_filters(df, filters)
    if isinstance(filters.selected_year, tuple):
        result = result[(result["nam"] >= filters.selected_year[0]) & (result["nam"] <= filters.selected_year[1])]
    else:
        result = result[result["nam"] == filters.selected_year]
    return result.copy()


@st.cache_data(show_spinner=False)
def apply_history_filters(df: pd.DataFrame, filters: FilterState) -> pd.DataFrame:
    return apply_common_filters(df, filters)


def metric_aggregation(metric: str) -> str:
    return str(METRIC_CONFIG.get(metric, {}).get("aggregation", "mean"))


def aggregate_metric(df: pd.DataFrame, metric: str, group_cols: list[str]) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(columns=[*group_cols, metric])
    agg = metric_aggregation(metric)
    if agg == "sum":
        return df.groupby(group_cols, as_index=False)[metric].sum(min_count=1)
    return df.groupby(group_cols, as_index=False)[metric].mean()


# Map filter metric key → actual DataFrame column name
_METRIC_COL_MAP: dict[str, str] = {
    "nang_suat": "nang_suat",
    "dien_tich": "dien_tich",
    "san_luong": "san_luong",
    "missing_target": "is_missing_target",
    "region": "region",
}


def metric_value_column(metric: str) -> str:
    """Return the DataFrame column that stores values for *metric*."""
    return _METRIC_COL_MAP.get(metric, metric)
