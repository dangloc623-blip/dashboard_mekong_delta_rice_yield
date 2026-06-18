import os
import sys
import pandas as pd

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.data_loader import find_dataset_path, load_raw_dataset
from src.eda_metrics import compute_quality_summary, get_quality_scope_dataframe
from src.feature_flags import add_derived_features
from src.filters import FilterState, apply_filters
from src.geo_loader import load_geojson, find_geojson_path
from src.components.distribution_panel import DEFAULT_MODE_BY_SCOPE

def run_checks():
    dataset_path = find_dataset_path()
    raw_df = load_raw_dataset(dataset_path)
    df = add_derived_features(raw_df)
    
    geo_path = find_geojson_path()
    geojson = load_geojson(geo_path) if geo_path else None
    if geojson:
        from src.geo_loader import normalize_geojson_province_property
        geojson, geo_provinces = normalize_geojson_province_property(geojson)
    else:
        geo_provinces = set()
        
    matched = sum(1 for p in df['tinh_thanh'].unique() if p in geo_provinces)
    default_filters = FilterState(
        year_mode="Snapshot",
        selected_year=int(df["nam"].max()),
        selected_season="dong_xuan",
        selected_metric="nang_suat",
        selected_regions=tuple(sorted(df["region"].dropna().unique().tolist())),
        selected_provinces=tuple(sorted(df["tinh_thanh"].dropna().unique().tolist())),
        show_missing=True,
    )
    df_filtered = apply_filters(df, default_filters)
    quality_current = get_quality_scope_dataframe(df, df_filtered, default_filters, "Current snapshot")
    quality_space = get_quality_scope_dataframe(df, df_filtered, default_filters, "Selected space, all years")
    quality_full = get_quality_scope_dataframe(df, df_filtered, default_filters, "Full raw dataset")
    quality_full_summary = compute_quality_summary(quality_full)
    
    checks = {
        "rows = 780": len(df) == 780,
        "provinces = 13": df['tinh_thanh'].nunique() == 13,
        "years = 30": df['nam'].nunique() == 30,
        "seasons = 2": df['mua_vu'].nunique() == 2,
        "missing target rows = 31": df['is_missing_target'].sum() == 31,
        "complete target rows = 749": (~df['is_missing_target']).sum() == 749,
        "mean yield ~= 5.318": abs(df['nang_suat'].mean() - 5.318) < 0.01,
        "GeoJSON match = 13/13": matched == 13,
        "quality current snapshot = selected year only": quality_current['nam'].nunique() == 1 and quality_current['nam'].iloc[0] == int(df["nam"].max()),
        "quality selected space ignores year": quality_space['nam'].nunique() == 30,
        "quality selected space respects season": set(quality_space['mua_vu'].unique()) == {"dong_xuan"},
        "quality full raw rows = 780": len(quality_full) == 780,
        "quality full raw missing = 31": quality_full_summary["missing_target_rows"] == 31,
        "distribution current default = histogram": DEFAULT_MODE_BY_SCOPE.get("Current filter") == "Histogram",
        "distribution full default = histogram": DEFAULT_MODE_BY_SCOPE.get("Full period") == "Histogram",
        "distribution range default = histogram": DEFAULT_MODE_BY_SCOPE.get("Selected year range") == "Histogram",
    }
    
    print("Validation Results:")
    all_passed = True
    for name, passed in checks.items():
        status = "PASS" if passed else "FAIL"
        print(f"[{status}] {name}")
        if not passed:
            all_passed = False
            
    if all_passed:
        print("\nALL CHECKS PASSED!")
        sys.exit(0)
    else:
        print("\nSOME CHECKS FAILED!")
        sys.exit(1)

if __name__ == "__main__":
    run_checks()
