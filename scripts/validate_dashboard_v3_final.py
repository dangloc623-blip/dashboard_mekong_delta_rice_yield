from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.components.correlation_panel import _valid_columns
from src.components.data_table import _missing_target_rows
from src.components.distribution_panel import (
    CURRENT_SNAPSHOT,
    DEFAULT_CHART_BY_DISTRIBUTION_SCOPE,
    FULL_PERIOD,
    SELECTED_YEAR_RANGE,
)
from src.data_loader import find_dataset_path, load_raw_dataset
from src.eda_metrics import build_quality_scope_df, compute_missing_by_province, compute_quality_summary
from src.feature_flags import add_derived_features
from src.metrics_config import CORE_NUMERIC_COLUMNS, WEATHER_COLUMNS


def _base_filters(df: pd.DataFrame) -> dict:
    return {
        "year_mode": "Snapshot",
        "selected_year": int(df["nam"].max()),
        "selected_season": "dong_xuan",
        "selected_regions": tuple(sorted(df["region"].dropna().unique())),
        "selected_provinces": tuple(sorted(df["tinh_thanh"].dropna().unique())),
        "show_missing": False,
    }


def _pass(name: str, actual, expected) -> tuple[str, bool, object, object]:
    return name, actual == expected, actual, expected


def _approx(name: str, actual: float, expected: float, tolerance: float) -> tuple[str, bool, object, object]:
    return name, abs(actual - expected) <= tolerance, round(actual, 6), expected


def run_checks() -> int:
    df = add_derived_features(load_raw_dataset(find_dataset_path()))
    base_filters = _base_filters(df)

    full_raw = build_quality_scope_df(df, {**base_filters, "selected_provinces": ("An Giang",)}, "full_raw_dataset")
    full_raw_summary = compute_quality_summary(full_raw)

    snapshot_2024 = build_quality_scope_df(df, base_filters, "current_snapshot")
    snapshot_2024_summary = compute_quality_summary(snapshot_2024)

    coastal_region = "Ven biển / rủi ro mặn"
    selected_regions = tuple(region for region in base_filters["selected_regions"] if region != coastal_region)
    selected_provinces = tuple(sorted(df.loc[df["region"].isin(selected_regions), "tinh_thanh"].dropna().unique()))
    selected_space = build_quality_scope_df(
        df,
        {
            **base_filters,
            "selected_regions": selected_regions,
            "selected_provinces": selected_provinces,
        },
        "selected_space_all_years",
    )
    selected_space_missing = compute_missing_by_province(selected_space)
    selected_space_missing_provinces = selected_space_missing["tinh_thanh"].tolist()

    core_numeric = _valid_columns(df, CORE_NUMERIC_COLUMNS)
    weather_only = _valid_columns(df, WEATHER_COLUMNS)
    yield_drivers = [col for col in core_numeric if col != "nang_suat"]
    missing_target_download_rows = _missing_target_rows(df)

    checks = [
        _pass("row_count", len(df), 780),
        _pass("province_count", df["tinh_thanh"].nunique(), 13),
        _pass("year_count", df["nam"].nunique(), 30),
        _pass("season_count", df["mua_vu"].nunique(), 2),
        _pass("missing_target_count", int(df["is_missing_target"].sum()), 31),
        _pass("complete_target_count", int((~df["is_missing_target"]).sum()), 749),
        _approx("mean_nang_suat", float(df["nang_suat"].mean()), 5.318, 0.01),
        _pass("full_raw_missing_target_rows", full_raw_summary["missing_target_rows"], 31),
        _pass("full_raw_affected_provinces", full_raw_summary["affected_provinces"], 3),
        _pass("full_raw_completeness_pct", full_raw_summary["target_completeness_pct"], 96.03),
        _pass("snapshot_2024_dong_xuan_missing_rows", snapshot_2024_summary["missing_target_rows"], 0),
        _pass("snapshot_2024_dong_xuan_affected_provinces", snapshot_2024_summary["affected_provinces"], 0),
        _pass("selected_space_excludes_ca_mau", "Cà Mau" in selected_space_missing_provinces, False),
        _pass("selected_space_excludes_bac_lieu", "Bạc Liêu" in selected_space_missing_provinces, False),
        _pass(
            "distribution_snapshot_default",
            DEFAULT_CHART_BY_DISTRIBUTION_SCOPE[CURRENT_SNAPSHOT],
            "Histogram",
        ),
        _pass(
            "distribution_range_default",
            DEFAULT_CHART_BY_DISTRIBUTION_SCOPE[SELECTED_YEAR_RANGE],
            "Histogram",
        ),
        _pass(
            "distribution_full_period_default",
            DEFAULT_CHART_BY_DISTRIBUTION_SCOPE[FULL_PERIOD],
            "Histogram",
        ),
        _pass("correlation_core_numeric_var_count", len(core_numeric), 7),
        _pass("correlation_weather_only_var_count", len(weather_only), 4),
        _pass("correlation_weather_only_excludes_yield", "nang_suat" in weather_only, False),
        _pass("correlation_yield_driver_count", len(yield_drivers), 6),
        _pass("missing_target_download_row_count", len(missing_target_download_rows), 31),
        _pass("missing_target_download_only_missing", bool(missing_target_download_rows["is_missing_target"].all()), True),
    ]

    print("V3 Final Validation Results:")
    all_passed = True
    for name, passed, actual, expected in checks:
        status = "PASS" if passed else "FAIL"
        print(f"[{status}] {name}: actual={actual} expected={expected}")
        all_passed = all_passed and passed

    if all_passed:
        print("\nALL FINAL CHECKS PASSED!")
        return 0

    print("\nSOME FINAL CHECKS FAILED!")
    return 1


if __name__ == "__main__":
    raise SystemExit(run_checks())
