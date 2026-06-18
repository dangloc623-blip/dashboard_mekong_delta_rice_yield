from __future__ import annotations

import pandas as pd
import streamlit as st

from ..filters import FilterState
from ..theme import kpi_card_html, render_kpi_row


def _format_int(value: int | float) -> str:
    if pd.isna(value):
        return "NA"
    return f"{int(value):,}"


def _format_float(value: int | float, digits: int = 3) -> str:
    if pd.isna(value):
        return "NA"
    return f"{float(value):.{digits}f}"


@st.cache_data(show_spinner=False)
def _compute_kpis(df_filtered: pd.DataFrame) -> dict[str, int | float | str]:
    complete = df_filtered[~df_filtered["is_missing_target"]]
    completeness = 1 - df_filtered["is_missing_target"].mean() if len(df_filtered) else 0
    year_value = "NA"
    if not df_filtered.empty:
        years = sorted(df_filtered["nam"].dropna().unique().tolist())
        year_value = str(years[0]) if len(years) == 1 else f"{years[0]}-{years[-1]}"

    return {
        "row_count": len(df_filtered),
        "year_value": year_value,
        "province_count": int(df_filtered["tinh_thanh"].nunique()) if not df_filtered.empty else 0,
        "completeness": completeness,
        "mean_yield": complete["nang_suat"].mean(),
        "missing_target": int(df_filtered["is_missing_target"].sum()) if not df_filtered.empty else 0,
        "mean_area": df_filtered["dien_tich"].mean(),
        "total_production": df_filtered["san_luong"].sum(),
    }


def render_kpi_cards(df_filtered: pd.DataFrame, filters: FilterState) -> None:
    kpis = _compute_kpis(df_filtered)
    year_value = (
        f"{filters.selected_year[0]}-{filters.selected_year[1]}"
        if isinstance(filters.selected_year, tuple)
        else str(filters.selected_year)
    )

    cards = [
        kpi_card_html("Filtered rows", _format_int(kpis["row_count"]), "rows"),
        kpi_card_html("Mean yield", _format_float(kpis["mean_yield"]), "tons/ha"),
        kpi_card_html("Target completeness", f"{float(kpis['completeness']):.1%}", "of filtered rows"),
        kpi_card_html("Provinces selected", _format_int(kpis["province_count"])),
        kpi_card_html("Year / range", year_value),
    ]
    render_kpi_row(cards)
