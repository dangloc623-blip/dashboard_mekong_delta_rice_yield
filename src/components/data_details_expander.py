from __future__ import annotations

from dataclasses import replace

import pandas as pd
import streamlit as st

from ..filters import FilterState, apply_filters
from ..theme import render_empty_state
from .data_table import INTERNAL_OUTLIER_COLUMNS, render_data_table


def _export_columns(df: pd.DataFrame) -> list[str]:
    return [col for col in df.columns if col not in INTERNAL_OUTLIER_COLUMNS]


def _missing_rows(df: pd.DataFrame) -> pd.DataFrame:
    if "is_missing_target" not in df.columns:
        return df.iloc[0:0].copy()
    return df[df["is_missing_target"].fillna(False)].copy()


@st.cache_data(show_spinner=False)
def _missing_target_details(df_base: pd.DataFrame, filters: FilterState) -> pd.DataFrame:
    source = apply_filters(df_base, replace(filters, show_missing=True))
    return _missing_rows(source)


def render_data_details_expander(
    df_base: pd.DataFrame,
    raw_df: pd.DataFrame,
    df_filtered: pd.DataFrame,
    filters: FilterState,
) -> None:
    with st.expander("Data details & downloads", expanded=False):
        missing_rows = _missing_target_details(df_base, filters)
        export_columns = _export_columns(missing_rows)
        filtered_export_columns = _export_columns(df_filtered)
        st.markdown(f"**Missing target rows:** {len(missing_rows):,}")

        st.download_button(
            label="Download filtered CSV",
            data=df_filtered[filtered_export_columns].to_csv(index=False).encode("utf-8-sig"),
            file_name="filtered_eda.csv",
            mime="text/csv",
            use_container_width=True,
        )

        st.download_button(
            label="Download missing target CSV",
            data=missing_rows[export_columns].to_csv(index=False).encode("utf-8-sig"),
            file_name="missing_target_rows.csv",
            mime="text/csv",
            use_container_width=True,
        )

        load_missing = st.toggle("Load missing target details", value=False, key="load_missing_target_details")
        if load_missing:
            if missing_rows.empty:
                render_empty_state("No missing target rows under current filters.", "ok")
            else:
                st.dataframe(missing_rows[export_columns].head(100), use_container_width=True, hide_index=True)

        load_table = st.toggle("Load table preview", value=False, key="load_data_table")
        if load_table:
            render_data_table(
                df_filtered,
                year=filters.selected_year,
                season=filters.selected_season,
                missing_source_df=apply_filters(df_base, replace(filters, show_missing=True)),
                raw_source_df=raw_df,
            )
