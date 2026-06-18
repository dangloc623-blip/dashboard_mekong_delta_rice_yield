from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

from ..filters import FilterState, apply_common_filters, apply_filters
from ..metrics_config import DISTRIBUTION_COLUMNS, metric_label
from ..theme import apply_plotly_theme, render_empty_state, render_mini_stats

CURRENT_SNAPSHOT = "current_snapshot"
FULL_PERIOD = "full_period"
SELECTED_YEAR_RANGE = "selected_year_range"

DISTRIBUTION_SCOPE_LABELS = {
    CURRENT_SNAPSHOT: "Current filter",
    FULL_PERIOD: "Full period",
    SELECTED_YEAR_RANGE: "Selected year range",
}

DEFAULT_CHART_BY_DISTRIBUTION_SCOPE = {
    CURRENT_SNAPSHOT: "Histogram",
    FULL_PERIOD: "Histogram",
    SELECTED_YEAR_RANGE: "Histogram",
}

CHART_MODES_BY_DISTRIBUTION_SCOPE = {
    CURRENT_SNAPSHOT: [
        "Histogram",
        "Boxplot by season",
        "Boxplot by region",
        "Boxplot by province",
    ],
    FULL_PERIOD: [
        "Histogram",
        "Boxplot by season",
        "Boxplot by region",
        "Boxplot by province",
    ],
    SELECTED_YEAR_RANGE: [
        "Histogram",
        "Boxplot by season",
        "Boxplot by region",
        "Boxplot by province",
    ],
}

# Backward-compatible name used by the older validation script.
DEFAULT_MODE_BY_SCOPE = {
    label: DEFAULT_CHART_BY_DISTRIBUTION_SCOPE[scope]
    for scope, label in DISTRIBUTION_SCOPE_LABELS.items()
}


def _allowed_scopes(filters: FilterState) -> list[str]:
    return [FULL_PERIOD, CURRENT_SNAPSHOT, SELECTED_YEAR_RANGE]


def _sync_distribution_state(filters: FilterState) -> None:
    allowed_scopes = _allowed_scopes(filters)
    default_scope = allowed_scopes[0]
    previous_year_mode = st.session_state.get("_distribution_year_mode_seen")
    current_scope = st.session_state.get("distribution_scope", default_scope)

    if previous_year_mode != filters.year_mode or current_scope not in allowed_scopes:
        current_scope = default_scope
        st.session_state["distribution_scope"] = current_scope
        st.session_state["distribution_chart_mode"] = DEFAULT_CHART_BY_DISTRIBUTION_SCOPE[current_scope]
        st.session_state["_distribution_scope_seen"] = current_scope
        st.session_state["_distribution_year_mode_seen"] = filters.year_mode
        return

    st.session_state["_distribution_year_mode_seen"] = filters.year_mode

    if st.session_state.get("_distribution_scope_seen") != current_scope:
        st.session_state["distribution_chart_mode"] = DEFAULT_CHART_BY_DISTRIBUTION_SCOPE[current_scope]
        st.session_state["_distribution_scope_seen"] = current_scope

    allowed_modes = CHART_MODES_BY_DISTRIBUTION_SCOPE[current_scope]
    if st.session_state.get("distribution_chart_mode") not in allowed_modes:
        st.session_state["distribution_chart_mode"] = DEFAULT_CHART_BY_DISTRIBUTION_SCOPE[current_scope]


def _select_distribution_scope(filters: FilterState) -> tuple[str, str]:
    _sync_distribution_state(filters)
    allowed_scopes = _allowed_scopes(filters)

    ctrl_col1, ctrl_col2 = st.columns(2, gap="small")
    with ctrl_col1:
        scope = st.radio(
            "Distribution Scope",
            options=allowed_scopes,
            horizontal=True,
            key="distribution_scope",
            format_func=lambda value: DISTRIBUTION_SCOPE_LABELS[value],
        )

    if st.session_state.get("_distribution_scope_seen") != scope:
        st.session_state["distribution_chart_mode"] = DEFAULT_CHART_BY_DISTRIBUTION_SCOPE[scope]
        st.session_state["_distribution_scope_seen"] = scope

    modes = CHART_MODES_BY_DISTRIBUTION_SCOPE[scope]
    if st.session_state.get("distribution_chart_mode") not in modes:
        st.session_state["distribution_chart_mode"] = DEFAULT_CHART_BY_DISTRIBUTION_SCOPE[scope]

    with ctrl_col2:
        mode = st.selectbox(
            "Chart mode",
            options=modes,
            key="distribution_chart_mode",
        )

    return str(scope), str(mode)


@st.cache_data(show_spinner=False)
def _scope_dataframe(df_base: pd.DataFrame, filters: FilterState, scope: str) -> pd.DataFrame:
    if scope == CURRENT_SNAPSHOT:
        return apply_filters(df_base, filters)

    history = apply_common_filters(df_base, filters)
    if scope == SELECTED_YEAR_RANGE:
        if isinstance(filters.selected_year, tuple):
            start_year, end_year = filters.selected_year
            return history[(history["nam"] >= start_year) & (history["nam"] <= end_year)].copy()
        return apply_filters(df_base, filters)

    return history.copy()


@st.cache_data(show_spinner=False)
def _distribution_variables(df: pd.DataFrame) -> list[str]:
    return [
        col for col in DISTRIBUTION_COLUMNS
        if col in df.columns and pd.api.types.is_numeric_dtype(df[col])
    ]


@st.cache_data(show_spinner=False)
def _distribution_plot_data(df_base: pd.DataFrame, filters: FilterState, scope: str, variable: str) -> pd.DataFrame:
    plot_df = _scope_dataframe(df_base, filters, scope)
    if variable not in plot_df.columns:
        return plot_df.iloc[0:0].copy()
    return plot_df.dropna(subset=[variable]).copy()


def render_distribution_panel(df_base: pd.DataFrame, filters: FilterState) -> None:
    st.markdown("#### Distribution")
    variable = "nang_suat"
    if variable not in df_base.columns:
        render_empty_state("Yield is not available.", "chart")
        return

    allowed_scopes = _allowed_scopes(filters)
    if st.session_state.get("distribution_scope") not in allowed_scopes:
        st.session_state["distribution_scope"] = FULL_PERIOD
    current_scope = st.session_state["distribution_scope"]
    if st.session_state.get("distribution_chart_mode") not in CHART_MODES_BY_DISTRIBUTION_SCOPE[current_scope]:
        st.session_state["distribution_chart_mode"] = DEFAULT_CHART_BY_DISTRIBUTION_SCOPE[current_scope]

    ctrl_col1, ctrl_col2 = st.columns(2, gap="small")
    with ctrl_col1:
        scope = st.selectbox(
            "Scope",
            options=allowed_scopes,
            index=allowed_scopes.index(st.session_state["distribution_scope"]),
            key="distribution_scope",
            format_func=lambda value: DISTRIBUTION_SCOPE_LABELS[value],
        )
    if st.session_state.get("distribution_chart_mode") not in CHART_MODES_BY_DISTRIBUTION_SCOPE[scope]:
        st.session_state["distribution_chart_mode"] = DEFAULT_CHART_BY_DISTRIBUTION_SCOPE[scope]
    with ctrl_col2:
        mode = st.selectbox(
            "Chart type",
            options=CHART_MODES_BY_DISTRIBUTION_SCOPE[scope],
            index=0,
            key="distribution_chart_mode",
        )

    scope_df = _scope_dataframe(df_base, filters, scope)
    missing_count = int(scope_df[variable].isna().sum()) if variable in scope_df.columns else 0
    plot_df = _distribution_plot_data(df_base, filters, scope, variable)
    if plot_df.empty:
        render_empty_state("No rows for current distribution scope.", "chart")
        return

    stats = plot_df[variable].describe()
    render_mini_stats(
        [
            ("Mean", f"{stats.get('mean', 0):.3f}"),
            ("Median", f"{stats.get('50%', 0):.3f}"),
            ("Missing", str(missing_count)),
        ]
    )

    labels = {variable: metric_label(variable), "mua_vu": "Season", "tinh_thanh": "Province"}

    if mode == "Histogram":
        fig = px.histogram(plot_df, x=variable, color="mua_vu", marginal="box", nbins=18, labels=labels)
    elif mode == "Boxplot by region":
        fig = px.box(plot_df, x="region", y=variable, color="mua_vu", points=False, labels=labels)
    elif mode == "Boxplot by province":
        fig = px.box(plot_df, x=variable, y="tinh_thanh", points=False, labels=labels, orientation="h")
    else:
        fig = px.box(
            plot_df,
            x="mua_vu",
            y=variable,
            color="mua_vu",
            points=False,
            labels=labels,
        )

    apply_plotly_theme(fig, height=350)
    fig.update_layout(margin=dict(l=0, r=0, t=6, b=0))
    st.plotly_chart(fig, use_container_width=True)
