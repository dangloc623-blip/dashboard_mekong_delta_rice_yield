from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from ..filters import FilterState, apply_history_filters, metric_aggregation
from ..metrics_config import metric_label
from ..theme import apply_plotly_theme, render_empty_state

TREND_VIEW_OPTIONS = ["Season average", "Overall mean", "By region", "Selected provinces"]


@st.cache_data(show_spinner=False)
def _aggregate(df: pd.DataFrame, filters: FilterState) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame()
    agg = metric_aggregation(filters.selected_metric)
    grouped = df.groupby(["nam", "mua_vu"], as_index=False)[filters.selected_metric]
    if agg == "sum":
        return grouped.sum(min_count=1)
    return grouped.mean()


@st.cache_data(show_spinner=False)
def _trend_dataframe(
    df: pd.DataFrame,
    filters: FilterState,
    metric: str,
    view_mode: str,
    show_selected_provinces: bool,
) -> pd.DataFrame:
    history = apply_history_filters(df, filters)
    if isinstance(filters.selected_year, tuple):
        start_year, end_year = filters.selected_year
        history = history[(history["nam"] >= start_year) & (history["nam"] <= end_year)]
    if history.empty or metric not in history.columns:
        return pd.DataFrame()

    if view_mode == "Selected provinces":
        group_cols = ["nam", "mua_vu", "tinh_thanh"]
    elif view_mode == "By region":
        group_cols = ["nam", "region"]
    elif view_mode == "Overall mean":
        group_cols = ["nam"]
    else:
        group_cols = ["nam", "mua_vu"]

    grouped = history.dropna(subset=[metric]).groupby(group_cols, as_index=False)[metric]
    result = grouped.sum(min_count=1) if metric_aggregation(metric) == "sum" else grouped.mean()

    if show_selected_provinces and view_mode != "Selected provinces":
        selected = history.dropna(subset=[metric]).groupby(["nam", "tinh_thanh"], as_index=False)[metric].mean()
        selected["overlay"] = True
        result["overlay"] = False
        return pd.concat([result, selected], ignore_index=True, sort=False)

    return result


def _add_year_marker(fig: go.Figure, selected_year: int | tuple[int, int], *, compact: bool = False) -> None:
    if isinstance(selected_year, tuple):
        start_year, end_year = selected_year
        if compact:
            fig.add_vrect(
                x0=start_year,
                x1=end_year,
                fillcolor="#0F766E",
                opacity=0.08,
                line_width=0,
            )
            fig.add_vline(x=start_year, line_dash="dot", line_color="#0F766E", line_width=1, opacity=0.45)
            fig.add_vline(x=end_year, line_dash="dot", line_color="#0F766E", line_width=1, opacity=0.45)
            return

        fig.add_vrect(
            x0=start_year,
            x1=end_year,
            fillcolor="#0F766E",
            opacity=0.08,
            line_width=0,
        )
        fig.add_vline(x=start_year, line_dash="dot", line_color="#0F766E", line_width=1, opacity=0.45)
        fig.add_vline(x=end_year, line_dash="dot", line_color="#0F766E", line_width=1, opacity=0.45)
        return

    if compact:
        fig.add_vline(
            x=selected_year,
            line_dash="dot",
            line_color="#0F766E",
            line_width=1,
            opacity=0.5,
        )
        return

    fig.add_vline(
        x=selected_year,
        line_dash="dash",
        line_color="#0F766E",
        line_width=2,
        opacity=1,
    )


def render_trend_chart(df: pd.DataFrame, filters: FilterState) -> None:
    st.markdown("#### Trend")
    ctrl_col1, ctrl_col2 = st.columns(2, gap="small")
    with ctrl_col1:
        view_mode = st.selectbox(
            "View mode",
            options=TREND_VIEW_OPTIONS,
            index=0,
            key="trend_view_mode",
        )
    with ctrl_col2:
        show_selected_provinces = st.toggle(
            "Show selected provinces",
            value=False,
            key="trend_show_selected_provinces",
        )

    metric = filters.selected_metric
    if metric not in df.columns:
        render_empty_state("Selected metric not available for trend chart.", "chart")
        return

    trend_df = _trend_dataframe(df, filters, metric, view_mode, show_selected_provinces)
    if trend_df.empty:
        render_empty_state("No rows for current filters.", "chart")
        return

    if view_mode == "Selected provinces":
        fig = px.line(
            trend_df,
            x="nam",
            y=metric,
            color="tinh_thanh",
            line_dash="mua_vu",
            markers=True,
            labels={
                "nam": "Year",
                metric: metric_label(metric),
                "mua_vu": "Season",
                "tinh_thanh": "Province",
            },
        )
    elif view_mode == "By region":
        fig = px.line(
            trend_df,
            x="nam",
            y=metric,
            color="region",
            markers=True,
            labels={
                "nam": "Year",
                metric: metric_label(metric),
                "region": "Region",
            },
        )
    elif view_mode == "Overall mean":
        fig = px.line(
            trend_df,
            x="nam",
            y=metric,
            markers=True,
            labels={
                "nam": "Year",
                metric: metric_label(metric),
            },
        )
    else:
        fig = px.line(
            trend_df,
            x="nam",
            y=metric,
            color="mua_vu",
            markers=True,
            labels={
                "nam": "Year",
                metric: metric_label(metric),
                "mua_vu": "Season",
            },
        )
    _add_year_marker(fig, filters.selected_year)
    apply_plotly_theme(fig, height=360)
    fig.update_layout(margin=dict(l=0, r=0, t=12, b=0))
    st.plotly_chart(fig, use_container_width=True)


def render_small_multiples(df: pd.DataFrame, filters: FilterState) -> None:
    with st.expander("Province small multiples"):
        sm_col1, sm_col2 = st.columns([1, 1])
        with sm_col1:
            variable = st.selectbox(
                "Small multiple variable",
                options=["nang_suat", "dien_tich"],
                format_func=metric_label,
            )
        with sm_col2:
            shared_y = st.toggle("Shared y-axis", value=False)

        history = apply_history_filters(df, filters).dropna(subset=[variable])
        if history.empty:
            render_empty_state("No rows for current filters.", "chart")
            return

        y_min = float(history[variable].min()) if shared_y else None
        y_max = float(history[variable].max()) if shared_y else None

        provinces = sorted(history["tinh_thanh"].unique().tolist())
        cols = st.columns(4)
        for idx, province in enumerate(provinces):
            province_df = history[history["tinh_thanh"] == province]
            chart_df = province_df.groupby(["nam", "mua_vu"], as_index=False)[variable].mean()
            fig = px.line(
                chart_df,
                x="nam",
                y=variable,
                color="mua_vu",
                labels={"nam": "Year", variable: metric_label(variable), "mua_vu": "Season"},
            )
            _add_year_marker(fig, filters.selected_year, compact=True)
            apply_plotly_theme(fig, height=210)
            fig.update_layout(
                title=dict(text=province, font=dict(size=12, color="#111827")),
                showlegend=idx == 0,
                margin=dict(l=0, r=0, t=35, b=0),
            )
            if shared_y and y_min is not None and y_max is not None:
                fig.update_yaxes(range=[y_min * 0.9, y_max * 1.1])

            cols[idx % 4].plotly_chart(fig, use_container_width=True)
