from __future__ import annotations

ID_COLUMNS = ["nam", "tinh_thanh", "mua_vu"]

WEATHER_COLUMNS = [
    "tổng số giờ nắng",
    "tổng lượng mưa",
    "độ ẩm trung bình",
    "nhiệt độ trung bình",
]

CORE_NUMERIC_COLUMNS = [
    "nang_suat",
    "dien_tich",
    "san_luong",
    *WEATHER_COLUMNS,
]

DISTRIBUTION_COLUMNS = CORE_NUMERIC_COLUMNS.copy()

METRIC_CONFIG = {
    "nang_suat": {
        "label": "Năng suất",
        "unit": "tấn/ha",
        "format": ".3f",
        "aggregation": "mean",
        "target_based": True,
    },
    "dien_tich": {
        "label": "Diện tích",
        "unit": "nghìn ha",
        "format": ".1f",
        "aggregation": "sum",
        "target_based": True,
    },
    "san_luong": {
        "label": "Sản lượng",
        "unit": "nghìn tấn",
        "format": ".1f",
        "aggregation": "sum",
        "target_based": True,
    },
    "missing_target": {
        "label": "Missing target",
        "unit": "rows",
        "aggregation": "sum",
        "target_based": False,
    },
    "region": {
        "label": "Region",
        "unit": "",
        "aggregation": "category",
        "target_based": False,
    },
}


def metric_label(metric: str, include_unit: bool = True) -> str:
    config = METRIC_CONFIG.get(metric, {"label": metric, "unit": ""})
    unit = config.get("unit", "")
    if include_unit and unit:
        return f"{config['label']} ({unit})"
    return str(config["label"])


def metric_format(metric: str) -> str:
    return str(METRIC_CONFIG.get(metric, {}).get("format", ".2f"))
