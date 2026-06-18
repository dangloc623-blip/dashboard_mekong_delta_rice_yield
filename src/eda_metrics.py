from typing import Any

import pandas as pd

from .filters import FilterState, apply_common_filters

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


QUALITY_SCOPE_LABEL_TO_VALUE = {
    "Current snapshot": "current_snapshot",
    "Selected space, all years": "selected_space_all_years",
    "Full raw dataset": "full_raw_dataset",
}


def _filter_value(filters: dict[str, Any], key: str, default: Any = None) -> Any:
    return filters.get(key, default)


@st.cache_data(show_spinner=False)
def build_quality_scope_df(
    df_raw: pd.DataFrame,
    filters: dict[str, Any],
    scope: str,
) -> pd.DataFrame:
    """Return the exact dataframe used by Data Quality for a given scope.

    scope values:
    - current_snapshot
    - selected_space_all_years
    - full_raw_dataset

    Data Quality intentionally ignores row display toggles such as
    show_missing so summary metrics cannot hide incomplete target rows.
    """
    if scope == "full_raw_dataset":
        return df_raw.copy()

    result = df_raw.copy()

    if scope == "current_snapshot":
        selected_year = _filter_value(filters, "selected_year")
        if isinstance(selected_year, tuple):
            start_year, end_year = selected_year
            result = result[(result["nam"] >= start_year) & (result["nam"] <= end_year)]
        elif selected_year is not None:
            result = result[result["nam"] == selected_year]
    elif scope != "selected_space_all_years":
        return result.iloc[0:0].copy()

    selected_season = _filter_value(filters, "selected_season", "All")
    if selected_season != "All":
        result = result[result["mua_vu"] == selected_season]

    selected_regions = tuple(_filter_value(filters, "selected_regions", ()) or ())
    if selected_regions:
        result = result[result["region"].isin(selected_regions)]

    selected_provinces = tuple(_filter_value(filters, "selected_provinces", ()) or ())
    if selected_provinces:
        result = result[result["tinh_thanh"].isin(selected_provinces)]

    return result.copy()


def get_quality_scope_dataframe(
    df_base: pd.DataFrame,
    df_filtered: pd.DataFrame,
    filters: FilterState,
    scope: str,
) -> pd.DataFrame:
    """Backward-compatible wrapper for existing call sites."""
    del df_filtered
    scope_value = QUALITY_SCOPE_LABEL_TO_VALUE.get(scope, scope)
    return build_quality_scope_df(
        df_base,
        {
            "year_mode": filters.year_mode,
            "selected_year": filters.selected_year,
            "selected_season": filters.selected_season,
            "selected_regions": filters.selected_regions,
            "selected_provinces": filters.selected_provinces,
        },
        scope_value,
    )


def get_quality_dataframe(df_base: pd.DataFrame, df_filtered: pd.DataFrame, scope: str) -> pd.DataFrame:
    """Backward-compatible wrapper for older call sites."""
    if scope in {"Full dataset", "Full raw dataset"}:
        return df_base.copy()
    return df_filtered.copy()

@st.cache_data(show_spinner=False)
def compute_special_rows(df: pd.DataFrame) -> pd.DataFrame:
    """Return rows with missing target values."""
    mask = df.get("is_missing_target", pd.Series(False, index=df.index)).fillna(False)
    return df[mask].copy()

@st.cache_data(show_spinner=False)
def compute_quality_summary(df: pd.DataFrame) -> dict[str, str | int | float]:
    """Compute KPI metrics for data quality."""
    total_rows = len(df)
    missing_mask = df.get("is_missing_target", pd.Series([False] * total_rows, index=df.index)).fillna(False)
    missing_rows = df.loc[missing_mask]
    missing_count = int(missing_mask.sum())
    complete_rows = total_rows - missing_count
    completeness = 100.0 * complete_rows / total_rows if total_rows else 0.0

    return {
        "total_rows": int(total_rows),
        "missing_target_rows": missing_count,
        "complete_target_rows": int(complete_rows),
        "affected_provinces": int(missing_rows["tinh_thanh"].nunique()) if not missing_rows.empty else 0,
        "target_completeness": f"{completeness:.2f}%",
        "target_completeness_pct": round(completeness, 2),
        "affected_years": int(missing_rows["nam"].nunique()) if not missing_rows.empty else 0,
    }

@st.cache_data(show_spinner=False)
def compute_missing_by_province(df: pd.DataFrame) -> pd.DataFrame:
    """Compute number of missing target rows grouped by province, sorted descending."""
    missing_rows = df[df.get("is_missing_target", pd.Series(dtype=bool)).fillna(False)]
    if missing_rows.empty:
        return pd.DataFrame(columns=["tinh_thanh", "missing_count"])
    
    counts = missing_rows.groupby("tinh_thanh").size().reset_index(name="missing_count")
    return counts.sort_values(by="missing_count", ascending=False)
