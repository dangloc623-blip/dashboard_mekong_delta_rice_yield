from __future__ import annotations

import pandas as pd

from ..filters import FilterState, apply_filters, apply_history_filters
from ..metrics_config import metric_label
from ..theme import render_detail_card


def _fmt(value: float | int | str | None, digits: int = 3) -> str:
    if value is None or pd.isna(value):
        return "NA"
    if isinstance(value, str):
        return value
    return f"{float(value):.{digits}f}"


def render_province_detail(df: pd.DataFrame, df_filtered: pd.DataFrame, filters: FilterState) -> None:
    selected = list(filters.selected_provinces)

    if len(selected) != 1:
        n_prov = df_filtered["tinh_thanh"].nunique()
        metric_val = _fmt(df_filtered[filters.selected_metric].mean()) if filters.selected_metric in df_filtered.columns else "NA"
        missing_count = int(df_filtered["is_missing_target"].sum()) if not df_filtered.empty else 0

        render_detail_card(
            f"{n_prov} provinces selected",
            [
                ("Mean " + metric_label(filters.selected_metric, include_unit=False), metric_val),
                ("Missing target rows", str(missing_count)),
            ],
        )
        return

    province = selected[0]
    province_history = apply_history_filters(df[df["tinh_thanh"] == province], filters)
    province_selected = apply_filters(df[df["tinh_thanh"] == province], filters)
    region = df.loc[df["tinh_thanh"] == province, "region"].dropna().head(1)

    metric_col = filters.selected_metric
    if metric_col in df_filtered.columns:
        ranked = (
            df_filtered.groupby("tinh_thanh", as_index=False)[metric_col]
            .mean()
            .sort_values(metric_col, ascending=False)
            .reset_index(drop=True)
        )
        ranked["rank"] = range(1, len(ranked) + 1)
        rank_row = ranked[ranked["tinh_thanh"] == province]
        rank_str = f"{rank_row['rank'].iloc[0]}/{len(ranked)}" if not rank_row.empty else "NA"
    else:
        rank_str = "NA"

    latest = (
        province_history.dropna(subset=[filters.selected_metric]).sort_values("nam").tail(1)
        if filters.selected_metric in province_history.columns
        else pd.DataFrame()
    )
    latest_value = _fmt(latest.iloc[0][filters.selected_metric]) if not latest.empty else "NA"

    selected_metric_value = (
        _fmt(province_selected[filters.selected_metric].mean())
        if not province_selected.empty and filters.selected_metric in province_selected.columns
        else "NA"
    )
    rows = [
        ("Region", region.iloc[0] if not region.empty else "NA"),
        ("Selected year", str(filters.selected_year)),
        ("Season", filters.selected_season),
        (metric_label(filters.selected_metric), selected_metric_value),
        ("Mean yield (all years)", _fmt(province_history["nang_suat"].mean())),
        ("Missing target", str(int(province_history["is_missing_target"].sum()))),
        ("Latest available", latest_value),
        (f"Rank by {metric_label(filters.selected_metric, include_unit=False)}", rank_str),
    ]
    render_detail_card(province, rows)
