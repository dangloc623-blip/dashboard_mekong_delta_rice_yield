from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

from ..eda_metrics import (
    QUALITY_SCOPE_LABEL_TO_VALUE,
    build_quality_scope_df,
    compute_missing_by_province,
    compute_quality_summary,
)
from ..filters import FilterState
from ..theme import apply_plotly_theme, kpi_card_html, render_empty_state, render_kpi_row, render_mini_stats

DETAIL_COLUMNS = [
    "nam",
    "tinh_thanh",
    "mua_vu",
    "region",
    "dien_tich",
    "san_luong",
    "nang_suat",
    "is_missing_target",
]

QUALITY_SCOPE_HELP = {
    "Current snapshot": "Uses selected year, season, region, and province. Row display toggles are ignored.",
    "Selected space, all years": "Ignores selected year; keeps selected season, region, and province. Row display toggles are ignored.",
    "Full raw dataset": "Ignores all dashboard filters.",
}


def _filters_to_dict(filters: FilterState) -> dict:
    return {
        "year_mode": filters.year_mode,
        "selected_year": filters.selected_year,
        "selected_season": filters.selected_season,
        "selected_regions": filters.selected_regions,
        "selected_provinces": filters.selected_provinces,
    }


def _missing_mask(df: pd.DataFrame) -> pd.Series:
    return df.get("is_missing_target", pd.Series(False, index=df.index)).fillna(False)


def _sort_heatmap_rows(heatmap_data: pd.DataFrame, missing_by_province: pd.DataFrame) -> pd.DataFrame:
    if heatmap_data.empty:
        return heatmap_data
    if missing_by_province.empty:
        return heatmap_data.reindex(sorted(heatmap_data.index))

    sorted_provinces = missing_by_province["tinh_thanh"].tolist()
    sorted_provinces.extend(sorted(province for province in heatmap_data.index if province not in sorted_provinces))
    return heatmap_data.reindex(sorted_provinces)


def render_missing_quality_panel(
    df_base: pd.DataFrame,
    filters: FilterState,
    validation_summary: dict | None = None,
    validation_warnings: list[str] | None = None,
    missing_regions: list[str] | None = None,
) -> None:
    with st.expander("Data QA Status", expanded=False):
        if validation_summary is not None:
            summary_df = pd.DataFrame([{"check": key, "value": value} for key, value in validation_summary.items()])
            st.dataframe(summary_df, use_container_width=True, hide_index=True)
        if validation_warnings:
            st.warning("; ".join(validation_warnings))
        if missing_regions:
            st.warning(f"Missing region mapping: {', '.join(missing_regions)}")

    scope_label = st.radio(
        "Quality Scope",
        options=list(QUALITY_SCOPE_LABEL_TO_VALUE.keys()),
        index=1,
        horizontal=True,
        key="quality_scope",
    )
    st.caption(QUALITY_SCOPE_HELP[scope_label])
    df_scope = build_quality_scope_df(
        df_base,
        _filters_to_dict(filters),
        QUALITY_SCOPE_LABEL_TO_VALUE[scope_label],
    )

    if df_scope.empty:
        render_empty_state("No rows for current quality scope.", "data")
        return

    summary = compute_quality_summary(df_scope)
    render_kpi_row(
        [
            kpi_card_html("Missing target rows", str(summary["missing_target_rows"])),
            kpi_card_html("Affected provinces", str(summary["affected_provinces"])),
            kpi_card_html("Target completeness", summary["target_completeness"]),
            kpi_card_html("Affected years", str(summary["affected_years"])),
        ]
    )

    missing_by_province = compute_missing_by_province(df_scope)
    col1, col2 = st.columns([1, 1.5])

    with col1:
        st.markdown("**Missing by Province**")
        if missing_by_province.empty:
            render_empty_state("No missing target rows under this quality scope.", "ok")
        else:
            fig_bar = px.bar(
                missing_by_province,
                y="tinh_thanh",
                x="missing_count",
                orientation="h",
                labels={"tinh_thanh": "Province", "missing_count": "Missing target rows"},
            )
            fig_bar.update_layout(yaxis={"categoryorder": "total ascending"}, margin=dict(l=0, r=0, t=0, b=0))
            fig_bar.update_traces(marker_color="#EA580C")
            apply_plotly_theme(fig_bar, height=350)
            st.plotly_chart(fig_bar, use_container_width=True)

    with col2:
        mode = st.radio(
            "Heatmap mode",
            options=["Missing target", "Target completeness"],
            index=0,
            horizontal=True,
            key="heatmap_mode",
            label_visibility="collapsed",
        )

        if mode == "Missing target" and missing_by_province.empty:
            render_empty_state("No missing target rows under this quality scope.", "ok")
        else:
            if mode == "Missing target":
                heatmap_data = (
                    df_scope.assign(missing_value=_missing_mask(df_scope).astype(int))
                    .pivot_table(
                        index="tinh_thanh",
                        columns="nam",
                        values="missing_value",
                        aggfunc="sum",
                        fill_value=0,
                    )
                )
                color_label = "Missing target"
                colorscale = ["#FFF7ED", "#FDBA74", "#EA580C", "#7C2D12"]
                zmin, zmax = 0, max(1, int(heatmap_data.to_numpy().max()))
            else:
                heatmap_data = (
                    df_scope.assign(completeness=(~_missing_mask(df_scope)).astype(float))
                    .pivot_table(
                        index="tinh_thanh",
                        columns="nam",
                        values="completeness",
                        aggfunc="mean",
                        fill_value=0,
                    )
                )
                color_label = "Completeness"
                colorscale = "Greens"
                zmin, zmax = 0, 1

            heatmap_data = _sort_heatmap_rows(heatmap_data, missing_by_province)
            fig_heat = px.imshow(
                heatmap_data,
                aspect="auto",
                color_continuous_scale=colorscale,
                zmin=zmin,
                zmax=zmax,
                labels=dict(x="Year", y="Province", color=color_label),
            )
            apply_plotly_theme(fig_heat, height=350)
            fig_heat.update_layout(margin=dict(l=0, r=0, t=20, b=0))
            st.plotly_chart(fig_heat, use_container_width=True)

    st.markdown("### Details")
    available_cols = [col for col in DETAIL_COLUMNS if col in df_scope.columns]

    with st.expander("Missing target rows", expanded=False):
        missing_rows = df_scope[_missing_mask(df_scope)]
        if missing_rows.empty:
            render_empty_state("No missing target rows under this quality scope.", "ok")
        else:
            st.dataframe(missing_rows[available_cols], use_container_width=True, hide_index=True)


def render_missing_quality_card(df_base: pd.DataFrame, filters: FilterState) -> None:
    st.markdown("#### Data completeness")
    df_scope = build_quality_scope_df(
        df_base,
        _filters_to_dict(filters),
        "selected_space_all_years",
    )
    if df_scope.empty:
        render_empty_state("No rows for current filters.", "data")
        return

    summary = compute_quality_summary(df_scope)
    render_mini_stats(
        [
            ("Missing", str(summary["missing_target_rows"])),
            ("Complete", str(summary["target_completeness"])),
            ("Affected", str(summary["affected_provinces"])),
        ]
    )

    missing_by_province = compute_missing_by_province(df_scope)
    if missing_by_province.empty:
        render_empty_state("No missing target rows under current space.", "ok")
    else:
        fig_bar = px.bar(
            missing_by_province.head(8),
            y="tinh_thanh",
            x="missing_count",
            orientation="h",
            labels={"tinh_thanh": "Province", "missing_count": "Missing target rows"},
        )
        fig_bar.update_layout(yaxis={"categoryorder": "total ascending"}, margin=dict(l=0, r=0, t=0, b=0))
        fig_bar.update_traces(marker_color="#EA580C")
        apply_plotly_theme(fig_bar, height=180)
        st.plotly_chart(fig_bar, use_container_width=True)

    available_cols = [col for col in DETAIL_COLUMNS if col in df_scope.columns]
    with st.expander("Missing target rows", expanded=False):
        missing_rows = df_scope[_missing_mask(df_scope)]
        if missing_rows.empty:
            render_empty_state("No missing target rows under current space.", "ok")
        else:
            st.dataframe(missing_rows[available_cols], use_container_width=True, hide_index=True)
