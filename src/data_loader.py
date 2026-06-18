from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from .metrics_config import ID_COLUMNS, WEATHER_COLUMNS

try:
    import streamlit as st
except ModuleNotFoundError:  # pragma: no cover - used only for local non-UI checks
    class _NoStreamlit:
        @staticmethod
        def cache_data(*args: Any, **kwargs: Any):
            def decorator(func):
                return func

            return decorator

    st = _NoStreamlit()


REQUIRED_COLUMNS = [
    "nam",
    "tinh_thanh",
    "mua_vu",
    "dien_tich",
    "san_luong",
    *WEATHER_COLUMNS,
]

EXPECTED_VALIDATION = {
    "row_count": 780,
    "year_count": 30,
    "province_count": 13,
    "season_count": 2,
    "duplicate_key_count": 0,
    "missing_target_count": 31,
    "complete_target_count": 749,
}


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _dashboard_root() -> Path:
    return Path(__file__).resolve().parents[1]


def find_dataset_path() -> Path:
    repo_root = _repo_root()
    dashboard_root = _dashboard_root()
    cwd = Path.cwd()
    candidates = [
        dashboard_root / "data" / "merged_dataset.csv",
        dashboard_root / "merged_dataset.csv",
        repo_root / "data" / "merged_dataset.csv",
        repo_root / "dataset" / "merged_dataset.csv",
        repo_root / "merged_dataset.csv",
        cwd / "dashboard" / "data" / "merged_dataset.csv",
        cwd / "dashboard" / "merged_dataset.csv",
        cwd / "data" / "merged_dataset.csv",
        cwd / "dataset" / "merged_dataset.csv",
        cwd / "merged_dataset.csv",
        Path("/mnt/data/merged_dataset.csv"),
        Path("/mnt/data/merged_dataset(1).csv"),
        dashboard_root / "data" / "merged_dataset(1).csv",
        dashboard_root / "merged_dataset(1).csv",
        repo_root / "merged_dataset(1).csv",
    ]
    for path in candidates:
        if path.exists():
            return path
    searched = "\n".join(str(path) for path in candidates)
    raise FileNotFoundError(f"merged_dataset.csv not found. Searched:\n{searched}")


def validate_required_columns(df: pd.DataFrame) -> None:
    missing = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing:
        raise ValueError(f"Raw dataset missing required columns: {missing}")


@st.cache_data(show_spinner=False)
def load_raw_dataset(path: str | Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    validate_required_columns(df)
    return df.copy()


def validation_summary(df: pd.DataFrame) -> dict[str, int | float | None]:
    summary: dict[str, int | float | None] = {
        "row_count": int(len(df)),
        "year_count": int(df["nam"].nunique(dropna=True)),
        "province_count": int(df["tinh_thanh"].nunique(dropna=True)),
        "season_count": int(df["mua_vu"].nunique(dropna=True)),
        "duplicate_key_count": int(df.duplicated(ID_COLUMNS).sum()),
        "missing_target_count": int(df.get("is_missing_target", pd.Series(dtype=bool)).sum()),
        "complete_target_count": int(df.get("is_complete_target", pd.Series(dtype=bool)).sum()),
        "mean_yield": None,
    }
    if "nang_suat" in df:
        mean_yield = df["nang_suat"].mean(skipna=True)
        summary["mean_yield"] = float(mean_yield) if pd.notna(mean_yield) else None
    return summary


def validation_warnings(summary: dict[str, int | float | None]) -> list[str]:
    warnings: list[str] = []
    for key, expected in EXPECTED_VALIDATION.items():
        actual = summary.get(key)
        if actual != expected:
            warnings.append(f"{key}: expected {expected}, got {actual}")

    mean_yield = summary.get("mean_yield")
    if mean_yield is not None and abs(float(mean_yield) - 5.318) > 0.01:
        warnings.append(f"mean_yield: expected about 5.318, got {float(mean_yield):.3f}")
    return warnings
