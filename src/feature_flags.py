from __future__ import annotations

import numpy as np
import pandas as pd

from .metrics_config import WEATHER_COLUMNS

try:
    import streamlit as st
except ModuleNotFoundError:  # pragma: no cover - local non-UI checks
    class _NoStreamlit:
        @staticmethod
        def cache_data(*args, **kwargs):
            def decorator(func):
                return func

            return decorator

    st = _NoStreamlit()

TARGET_COLUMNS = ["dien_tich", "san_luong", "nang_suat"]

REGION_MAP = {
    "An Giang": "Thượng nguồn / vựa lúa",
    "Đồng Tháp": "Thượng nguồn / vựa lúa",
    "Kiên Giang": "Ven biển / rủi ro mặn",
    "Sóc Trăng": "Ven biển / rủi ro mặn",
    "Bạc Liêu": "Ven biển / rủi ro mặn",
    "Trà Vinh": "Ven biển / rủi ro mặn",
    "Bến Tre": "Ven biển / rủi ro mặn",
    "Cà Mau": "Ven biển / rủi ro mặn",
    "Cần Thơ": "Trung tâm / nội đồng",
    "Hậu Giang": "Trung tâm / nội đồng",
    "Long An": "Trung tâm / nội đồng",
    "Tiền Giang": "Trung tâm / nội đồng",
    "Vĩnh Long": "Trung tâm / nội đồng",
}


def add_group_iqr_flag(
    df: pd.DataFrame,
    value_col: str,
    group_cols: list[str],
    output_col: str,
) -> pd.DataFrame:
    result = df.copy()
    grouped = result.groupby(group_cols, dropna=False)[value_col]
    q1 = grouped.transform(lambda values: values.quantile(0.25))
    q3 = grouped.transform(lambda values: values.quantile(0.75))
    count = grouped.transform("count")
    iqr = q3 - q1
    lower = q1 - 1.5 * iqr
    upper = q3 + 1.5 * iqr

    result[output_col] = (
        result[value_col].notna()
        & (count >= 4)
        & iqr.notna()
        & (iqr > 0)
        & ((result[value_col] < lower) | (result[value_col] > upper))
    )
    return result


@st.cache_data(show_spinner=False)
def add_derived_features(df: pd.DataFrame) -> pd.DataFrame:
    result = df.copy()
    valid_area = result["dien_tich"].notna() & (result["dien_tich"] != 0)
    result["nang_suat"] = np.where(
        valid_area & result["san_luong"].notna(),
        result["san_luong"] / result["dien_tich"],
        np.nan,
    )
    result["is_missing_target"] = result[TARGET_COLUMNS].isna().any(axis=1)
    result["is_complete_target"] = ~result["is_missing_target"]

    result = add_group_iqr_flag(
        result,
        value_col="nang_suat",
        group_cols=["tinh_thanh", "mua_vu"],
        output_col="is_yield_extreme_outlier",
    )
    result = add_group_iqr_flag(
        result,
        value_col="dien_tich",
        group_cols=["tinh_thanh", "mua_vu"],
        output_col="is_area_outlier",
    )
    result["is_yield_low_warning"] = result["nang_suat"] < 2
    result["region"] = result["tinh_thanh"].map(REGION_MAP)
    return result


def missing_region_values(df: pd.DataFrame) -> list[str]:
    if "region" not in df:
        return []
    return sorted(df.loc[df["region"].isna(), "tinh_thanh"].dropna().unique().tolist())


def numeric_columns_available(df: pd.DataFrame) -> list[str]:
    return [col for col in ["nang_suat", "dien_tich", "san_luong", *WEATHER_COLUMNS] if col in df.columns]
