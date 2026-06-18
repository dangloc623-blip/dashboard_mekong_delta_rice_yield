from __future__ import annotations

import pandas as pd
import streamlit as st

from ..metrics_config import WEATHER_COLUMNS
from ..theme import render_empty_state

INTERNAL_OUTLIER_COLUMNS = {
    "is_yield_extreme_outlier",
    "is_area_outlier",
    "is_yield_low_warning",
}

DEFAULT_COLUMNS = [
    "nam",
    "tinh_thanh",
    "mua_vu",
    "region",
    "dien_tich",
    "san_luong",
    "nang_suat",
    *WEATHER_COLUMNS,
    "is_missing_target",
]


def _missing_target_rows(df: pd.DataFrame) -> pd.DataFrame:
    return df[df["is_missing_target"].fillna(False)].copy()


def _export_columns(df: pd.DataFrame) -> list[str]:
    return [col for col in df.columns if col not in INTERNAL_OUTLIER_COLUMNS]


def _render_downloads(
    df_filtered: pd.DataFrame,
    missing_source_df: pd.DataFrame,
    raw_source_df: pd.DataFrame | None,
    export_columns: list[str],
    year: int | tuple[int, int] | None,
    season: str | None,
) -> None:
    year_str = f"{year[0]}-{year[1]}" if isinstance(year, tuple) else str(year or "all")
    season_str = str(season).replace("/", "_") if season else "all"
    missing_rows = _missing_target_rows(missing_source_df)

    dl_col1, dl_col2, dl_col3 = st.columns(3)
    with dl_col1:
        st.download_button(
            label="Download filtered CSV",
            data=df_filtered[export_columns].to_csv(index=False).encode("utf-8-sig"),
            file_name=f"filtered_eda_{year_str}_{season_str}.csv",
            mime="text/csv",
            use_container_width=True,
        )

    with dl_col2:
        st.download_button(
            label="Download missing target rows CSV",
            data=missing_rows[export_columns].to_csv(index=False).encode("utf-8-sig"),
            file_name=f"missing_target_rows_{year_str}_{season_str}.csv",
            mime="text/csv",
            use_container_width=True,
        )
        if missing_rows.empty:
            st.caption("No missing target rows under current filters.")
        elif df_filtered.empty:
            st.caption(f"{len(missing_rows):,} missing target row(s) are hidden by the current display toggle.")

    with dl_col3:
        if raw_source_df is not None:
            st.download_button(
                label="Download full raw CSV",
                data=raw_source_df.to_csv(index=False).encode("utf-8-sig"),
                file_name="merged_dataset_raw.csv",
                mime="text/csv",
                use_container_width=True,
            )


def render_data_table(
    df_filtered: pd.DataFrame,
    year: int | tuple[int, int] | None = None,
    season: str | None = None,
    missing_source_df: pd.DataFrame | None = None,
    raw_source_df: pd.DataFrame | None = None,
) -> None:
    missing_source_df = df_filtered if missing_source_df is None else missing_source_df
    all_columns = [col for col in DEFAULT_COLUMNS if col in df_filtered.columns]
    export_columns = _export_columns(df_filtered)

    preview_limit = 100
    st.caption(f"**{len(df_filtered):,}** rows")

    selected_columns = st.multiselect(
        "Columns to display",
        options=all_columns,
        default=all_columns,
        key="table_columns",
    )

    if not selected_columns:
        render_empty_state("Select at least one column to display.", "table")
        _render_downloads(df_filtered, missing_source_df, raw_source_df, export_columns, year, season)
        return

    if df_filtered.empty:
        render_empty_state("No rows match current filters.", "table")
        _render_downloads(df_filtered, missing_source_df, raw_source_df, export_columns, year, season)
        return

    preview_df = df_filtered[selected_columns].head(preview_limit)
    if len(df_filtered) > preview_limit:
        st.caption(f"Previewing first {preview_limit:,} rows. CSV downloads include all matching rows.")
    st.dataframe(preview_df, use_container_width=True, hide_index=True)
    _render_downloads(df_filtered, missing_source_df, raw_source_df, export_columns, year, season)
