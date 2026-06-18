from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

from ..filters import FilterState, apply_filters
from ..metrics_config import CORE_NUMERIC_COLUMNS, WEATHER_COLUMNS, metric_label
from ..theme import apply_plotly_theme, render_empty_state

DRIVER_MODE_OPTIONS = ["Yield vs drivers", "Weather only", "Core numeric"]
DRIVER_CHART_OPTIONS = ["Heatmap", "Correlation bar", "Scatter"]


def _valid_columns(df: pd.DataFrame, columns: list[str]) -> list[str]:
    return [col for col in columns if col in df.columns]


@st.cache_data(show_spinner=False)
def _relationship_dataframe(df: pd.DataFrame, filters: FilterState) -> pd.DataFrame:
    return apply_filters(df, filters)


@st.cache_data(show_spinner=False)
def _correlation_matrix(df: pd.DataFrame, columns: tuple[str, ...]) -> pd.DataFrame:
    corr_df = df[list(columns)].dropna()
    if len(corr_df) < 2:
        return pd.DataFrame()
    return corr_df.corr(method="pearson")


def _mode_columns(filtered: pd.DataFrame, mode: str) -> list[str]:
    if mode == "Weather only":
        return _valid_columns(filtered, WEATHER_COLUMNS)
    return _valid_columns(filtered, CORE_NUMERIC_COLUMNS)


def render_correlation_panel(df: pd.DataFrame, filters: FilterState) -> None:
    st.markdown("#### Driver relationship")
    filtered = _relationship_dataframe(df, filters)
    if filtered.empty:
        render_empty_state("No rows for current filters.", "chart")
        return

    ctrl_col1, ctrl_col2 = st.columns(2, gap="small")
    with ctrl_col1:
        mode = st.selectbox(
            "Mode",
            options=DRIVER_MODE_OPTIONS,
            index=0,
            key="corr_mode",
        )
    chart_options = DRIVER_CHART_OPTIONS
    if st.session_state.get("driver_chart_type") not in chart_options:
        st.session_state["driver_chart_type"] = chart_options[0]
    with ctrl_col2:
        chart_type = st.selectbox(
            "Chart type",
            options=chart_options,
            index=0,
            key="driver_chart_type",
        )

    corr_cols = _mode_columns(filtered, mode)
    corr = _correlation_matrix(filtered, tuple(corr_cols))

    if chart_type == "Correlation bar":
        if corr.empty or "nang_suat" not in corr.columns:
            render_empty_state("Need yield and at least 2 complete rows.", "chart")
            return
        corr_bar = (
            corr["nang_suat"]
            .drop("nang_suat")
            .dropna()
            .reset_index()
            .rename(columns={"index": "variable", "nang_suat": "corr"})
        )
        if corr_bar.empty:
            render_empty_state("No driver correlations available.", "chart")
            return
        fig = px.bar(
            corr_bar.sort_values("corr"),
            x="corr",
            y="variable",
            orientation="h",
            labels={"corr": "Pearson r", "variable": "Variable"},
            color="corr",
            color_continuous_scale="RdBu",
            range_color=[-1, 1],
        )
        apply_plotly_theme(fig, height=390)
        fig.update_layout(margin=dict(l=0, r=0, t=10, b=0))
        st.plotly_chart(fig, use_container_width=True)
        st.caption("Correlation is descriptive only.")
        return

    if chart_type == "Heatmap":
        if corr.empty:
            render_empty_state("Need at least 2 complete rows.", "chart")
            return
        fig = px.imshow(
            corr,
            text_auto=".2f",
            aspect="auto",
            color_continuous_scale="RdBu",
            zmin=-1,
            zmax=1,
            labels=dict(color="Pearson r"),
        )
        apply_plotly_theme(fig, height=400)
        fig.update_layout(margin=dict(l=0, r=0, t=10, b=0))
        st.plotly_chart(fig, use_container_width=True)
        st.caption("Correlation is descriptive only.")
        return

    drivers = [col for col in WEATHER_COLUMNS + ["dien_tich", "san_luong"] if col in filtered.columns]
    if not drivers:
        render_empty_state("No driver columns available.", "chart")
        return

    sc_col1, sc_col2 = st.columns(2, gap="small")
    with sc_col1:
        scatter_x = st.selectbox("Driver", options=drivers, format_func=metric_label, key="corr_scatter_x")
    with sc_col2:
        color_by = st.selectbox("Color", options=["mua_vu", "region"], index=0, key="corr_scatter_color")

    scatter_df = filtered.dropna(subset=[scatter_x, "nang_suat"])
    if scatter_df.empty:
        render_empty_state("No complete rows for scatter plot.", "chart")
        return

    fig = px.scatter(
        scatter_df,
        x=scatter_x,
        y="nang_suat",
        color=color_by,
        hover_data=["nam", "tinh_thanh", "mua_vu", "dien_tich", "san_luong"],
        labels={
            scatter_x: metric_label(scatter_x),
            "nang_suat": metric_label("nang_suat"),
            "mua_vu": "Season",
            "region": "Region",
        },
    )
    apply_plotly_theme(fig, height=390)
    fig.update_layout(margin=dict(l=0, r=0, t=10, b=0))
    st.plotly_chart(fig, use_container_width=True)
    st.caption("Correlation is descriptive only.")
