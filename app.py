from __future__ import annotations

from dataclasses import replace
import sys
from pathlib import Path

import streamlit as st

APP_DIR = Path(__file__).resolve().parent
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from src.components.correlation_panel import render_correlation_panel
from src.components.data_details_expander import render_data_details_expander
from src.components.distribution_panel import render_distribution_panel
from src.components.filters import render_filters
from src.components.kpi_cards import render_kpi_cards
from src.components.map_panel import MAP_SELECTION_ENABLED, render_ranking_panel, render_spatial_panel
from src.components.season_comparison_card import render_season_comparison_card
from src.components.trend_chart import render_trend_chart
from src.data_loader import find_dataset_path, load_raw_dataset
from src.feature_flags import add_derived_features
from src.filters import FilterState, apply_filters
from src.metrics_config import metric_label
from src.theme import inject_custom_css, render_filter_summary, render_header

INTERACTIVE_PROVINCES_KEY = "interactive_selected_provinces"


@st.cache_data(show_spinner=False)
def _load_dashboard_data() -> tuple:
    dataset_path = find_dataset_path()
    raw_df = load_raw_dataset(dataset_path)
    return raw_df.copy(), add_derived_features(raw_df)


def _selected_tuple(values: object) -> tuple[str, ...]:
    if not values:
        return ()
    if isinstance(values, str):
        return (values,)
    return tuple(str(value) for value in values if str(value).strip())


def _prune_interactive_selection(available_provinces: tuple[str, ...]) -> tuple[str, ...]:
    available = set(available_provinces)
    current = _selected_tuple(st.session_state.get(INTERACTIVE_PROVINCES_KEY, ()))
    pruned = tuple(province for province in current if province in available)
    if pruned != current:
        st.session_state[INTERACTIVE_PROVINCES_KEY] = pruned
    return pruned


def _effective_filters(filters: FilterState, interactive_provinces: tuple[str, ...]) -> FilterState:
    if not interactive_provinces:
        return filters
    focused = tuple(province for province in filters.selected_provinces if province in set(interactive_provinces))
    return replace(filters, selected_provinces=focused or filters.selected_provinces)


def _handle_chart_selection(source: str, province: str | None, available_provinces: tuple[str, ...]) -> None:
    if not province or province not in set(available_provinces):
        return

    signature_key = f"_last_processed_selection_{source}"
    signature = f"{source}:{province}"
    if st.session_state.get(signature_key) == signature:
        return

    current = list(_selected_tuple(st.session_state.get(INTERACTIVE_PROVINCES_KEY, ())))
    if province in current:
        current.remove(province)
    else:
        current.append(province)

    st.session_state[INTERACTIVE_PROVINCES_KEY] = tuple(current)
    st.session_state[signature_key] = signature
    st.rerun()


def _render_focus_controls(interactive_provinces: tuple[str, ...]) -> None:
    if not interactive_provinces:
        return
    if st.button("Clear selected provinces", use_container_width=False):
        st.session_state[INTERACTIVE_PROVINCES_KEY] = ()
        for key in list(st.session_state.keys()):
            if str(key).startswith("_last_processed_selection_"):
                del st.session_state[key]
        st.rerun()


def main() -> None:
    st.set_page_config(
        page_title="Mekong Delta Rice - Dashboard",
        layout="wide",
        page_icon="rice",
    )

    inject_custom_css()

    try:
        raw_df, df_base = _load_dashboard_data()
    except Exception as exc:
        st.error(f"Data load error: {exc}")
        st.stop()

    render_header(
        row_count=len(raw_df),
        province_count=int(raw_df["tinh_thanh"].nunique()),
        year_min=int(raw_df["nam"].min()),
        year_max=int(raw_df["nam"].max()),
        season_count=int(raw_df["mua_vu"].nunique()),
    )

    filters = render_filters(df_base)
    interactive_provinces = _prune_interactive_selection(filters.selected_provinces)
    effective_filters = _effective_filters(filters, interactive_provinces)
    df_filtered = apply_filters(df_base, effective_filters)

    render_filter_summary(
        year=filters.selected_year,
        season=filters.selected_season,
        metric_label=metric_label(filters.selected_metric, include_unit=False),
        region_count=len(filters.selected_regions),
        province_count=len(effective_filters.selected_provinces),
        region_total=int(df_base["region"].nunique()),
        province_total=int(df_base["tinh_thanh"].nunique()),
        focused_provinces=interactive_provinces,
    )
    _render_focus_controls(interactive_provinces)

    render_kpi_cards(df_filtered, effective_filters)

    map_col, side_col = st.columns([2.15, 0.95], gap="small")
    with map_col:
        with st.container(border=True):
            selected_from_map = render_spatial_panel(
                df_base,
                effective_filters,
                selected_provinces=interactive_provinces,
                enable_selection=MAP_SELECTION_ENABLED,
            )
            _handle_chart_selection("map", selected_from_map, filters.selected_provinces)

    with side_col:
        with st.container(border=True):
            selected_from_ranking = render_ranking_panel(
                df_base,
                effective_filters,
                selected_provinces=interactive_provinces,
            )
            _handle_chart_selection("ranking", selected_from_ranking, filters.selected_provinces)
        with st.container(border=True):
            render_season_comparison_card(df_base, effective_filters)

    trend_col, dist_col = st.columns([1.55, 1.0], gap="small")
    with trend_col:
        with st.container(border=True):
            render_trend_chart(df_base, effective_filters)
    with dist_col:
        with st.container(border=True):
            render_distribution_panel(df_base, effective_filters)

    with st.container(border=True):
        render_correlation_panel(df_base, effective_filters)

    render_data_details_expander(df_base, raw_df, df_filtered, effective_filters)


if __name__ == "__main__":
    main()
