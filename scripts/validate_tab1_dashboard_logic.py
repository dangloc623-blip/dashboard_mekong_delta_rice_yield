from __future__ import annotations

from dataclasses import replace
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app import _effective_filters
from src.components.correlation_panel import DRIVER_CHART_OPTIONS, DRIVER_MODE_OPTIONS
from src.components.distribution_panel import DEFAULT_CHART_BY_DISTRIBUTION_SCOPE, FULL_PERIOD
from src.components.filters import _default_values, _province_options_for_regions
from src.components.map_panel import RANKING_CHART_OPTIONS, RANKING_SORT_OPTIONS
from src.components.trend_chart import TREND_VIEW_OPTIONS
from src.data_loader import find_dataset_path, load_raw_dataset
from src.eda_metrics import build_quality_scope_df, compute_quality_summary
from src.feature_flags import add_derived_features
from src.filters import FilterState, apply_filters
from src.selection import extract_selected_province_from_plotly_event


def _pass(name: str, condition: bool, detail: object = "") -> tuple[str, bool, object]:
    return name, bool(condition), detail


def _base_filters(df: pd.DataFrame) -> FilterState:
    return FilterState(
        year_mode="Range",
        selected_year=(int(df["nam"].min()), int(df["nam"].max())),
        selected_season="All",
        selected_metric="nang_suat",
        selected_regions=tuple(sorted(df["region"].dropna().unique())),
        selected_provinces=tuple(sorted(df["tinh_thanh"].dropna().unique())),
        show_missing=True,
    )


def run_checks() -> int:
    raw = load_raw_dataset(find_dataset_path())
    df = add_derived_features(raw)
    filters = _base_filters(df)
    defaults = _default_values(
        int(df["nam"].min()),
        int(df["nam"].max()),
        sorted(df["region"].dropna().unique().tolist()),
        sorted(df["tinh_thanh"].dropna().unique().tolist()),
    )

    full_raw = build_quality_scope_df(
        df,
        {
            "selected_year": (2020, 2024),
            "selected_season": "dong_xuan",
            "selected_regions": (),
            "selected_provinces": (),
        },
        "full_raw_dataset",
    )
    full_summary = compute_quality_summary(full_raw)

    snapshot_filters = replace(filters, year_mode="Snapshot", selected_year=2024, selected_season="dong_xuan")
    snapshot = apply_filters(df, snapshot_filters)

    regions = sorted(df["region"].dropna().unique().tolist())
    coastal_region = next((region for region in regions if "Ven" in region), regions[0])
    non_coastal_regions = [region for region in regions if region != coastal_region]
    non_coastal_options = set(_province_options_for_regions(df, non_coastal_regions))
    coastal_provinces = set(df.loc[df["region"] == coastal_region, "tinh_thanh"].dropna().unique())

    provinces = filters.selected_provinces
    focused = _effective_filters(filters, (provinces[0], "not a province"))

    malformed_cases = [
        None,
        {},
        {"selection": None},
        {"selection": {"points": []}},
        {"selection": {"points": [{"customdata": []}]}},
    ]

    checks = [
        _pass("row_count", len(df) == 780, len(df)),
        _pass("province_count", df["tinh_thanh"].nunique() == 13, df["tinh_thanh"].nunique()),
        _pass("year_min", int(df["nam"].min()) == 1995, int(df["nam"].min())),
        _pass("year_max", int(df["nam"].max()) == 2024, int(df["nam"].max())),
        _pass("year_count", df["nam"].nunique() == 30, df["nam"].nunique()),
        _pass("season_count", df["mua_vu"].nunique() == 2, df["mua_vu"].nunique()),
        _pass("missing_target_rows", int(df["is_missing_target"].sum()) == 31, int(df["is_missing_target"].sum())),
        _pass("complete_target_rows", int((~df["is_missing_target"]).sum()) == 749, int((~df["is_missing_target"]).sum())),
        _pass("default_year_mode_range", defaults["year_mode"] == "Range", defaults["year_mode"]),
        _pass("default_year_range_full", defaults["year_range"] == (1995, 2024), defaults["year_range"]),
        _pass("default_season_all", defaults["selected_season"] == "All", defaults["selected_season"]),
        _pass("default_metric_yield", defaults["selected_metric"] == "nang_suat", defaults["selected_metric"]),
        _pass("full_raw_missing_ignores_filters", full_summary["missing_target_rows"] == 31, full_summary["missing_target_rows"]),
        _pass("snapshot_2024_dong_xuan_missing_zero", int(snapshot["is_missing_target"].sum()) == 0, int(snapshot["is_missing_target"].sum())),
        _pass("coastal_region_removed_from_options", coastal_provinces.isdisjoint(non_coastal_options), coastal_provinces & non_coastal_options),
        _pass("interactive_intersects_sidebar", focused.selected_provinces == (provinces[0],), focused.selected_provinces),
        _pass(
            "malformed_plotly_events_return_none",
            all(extract_selected_province_from_plotly_event(event, "validation") is None for event in malformed_cases),
            "ok",
        ),
        _pass("ranking_default_dot_plot", RANKING_CHART_OPTIONS[0] == "Dot plot", RANKING_CHART_OPTIONS[0]),
        _pass("ranking_default_desc", RANKING_SORT_OPTIONS[0] == "Descending", RANKING_SORT_OPTIONS[0]),
        _pass(
            "distribution_default_full_period_histogram",
            DEFAULT_CHART_BY_DISTRIBUTION_SCOPE[FULL_PERIOD] == "Histogram",
            DEFAULT_CHART_BY_DISTRIBUTION_SCOPE[FULL_PERIOD],
        ),
        _pass("trend_default_season_average", TREND_VIEW_OPTIONS[0] == "Season average", TREND_VIEW_OPTIONS[0]),
        _pass("driver_default_mode_yield_vs_drivers", DRIVER_MODE_OPTIONS[0] == "Yield vs drivers", DRIVER_MODE_OPTIONS[0]),
        _pass("driver_default_heatmap", DRIVER_CHART_OPTIONS[0] == "Heatmap", DRIVER_CHART_OPTIONS[0]),
        _pass("interactive_default_empty", tuple() == (), ()),
    ]

    print("Tab 1 Dashboard Logic Validation:")
    all_passed = True
    for name, passed, detail in checks:
        status = "PASS" if passed else "FAIL"
        print(f"[{status}] {name}: {detail}")
        all_passed = all_passed and passed

    if all_passed:
        print("\nALL TAB 1 CHECKS PASSED!")
        return 0

    print("\nSOME TAB 1 CHECKS FAILED!")
    return 1


if __name__ == "__main__":
    raise SystemExit(run_checks())
