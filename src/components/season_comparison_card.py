from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

from ..filters import FilterState, apply_filters
from ..metrics_config import metric_label
from ..theme import apply_plotly_theme, render_empty_state, render_mini_stats


@st.cache_data(show_spinner=False)
def _season_comparison_data(df: pd.DataFrame, filters: FilterState) -> pd.DataFrame:
    metric = filters.selected_metric
    filtered = apply_filters(df, filters)
    if filtered.empty or metric not in filtered.columns:
        return pd.DataFrame(columns=["mua_vu", "metric_value"])

    return (
        filtered.dropna(subset=[metric])
        .groupby("mua_vu", as_index=False)[metric]
        .mean()
        .rename(columns={metric: "metric_value"})
        .sort_values("metric_value", ascending=True)
    )


def render_season_comparison_card(df: pd.DataFrame, filters: FilterState) -> None:
    st.markdown("#### Season comparison")
    chart_type = st.selectbox(
        "Chart",
        options=["Compact bar", "Two-value card"],
        index=0,
        key="season_comparison_chart",
    )

    season_df = _season_comparison_data(df, filters)
    if season_df.empty:
        render_empty_state("No season data for current filters.", "chart")
        return

    if chart_type == "Two-value card":
        render_mini_stats(
            [
                (str(row["mua_vu"]), f"{row['metric_value']:.3f}")
                for _, row in season_df.sort_values("mua_vu").iterrows()
            ]
        )
        return

    fig = px.bar(
        season_df,
        x="metric_value",
        y="mua_vu",
        orientation="h",
        color="mua_vu",
        labels={"metric_value": metric_label(filters.selected_metric), "mua_vu": "Season"},
        color_discrete_sequence=["#14B8A6", "#22C7D6"],
    )
    fig.update_traces(texttemplate="%{x:.3f}", textposition="outside", cliponaxis=False)
    apply_plotly_theme(fig, height=170)
    fig.update_layout(showlegend=False, margin=dict(l=4, r=30, t=8, b=0))
    fig.update_xaxes(title_text="")
    st.plotly_chart(fig, use_container_width=True, config={"displaylogo": False})
