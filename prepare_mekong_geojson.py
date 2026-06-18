#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Prepare local ADM1 GeoJSON layers for the Streamlit dashboard.

Outputs:
    dashboard/data/mekong_delta_adm1.geojson
    dashboard/data/mekong_delta_context_adm1.geojson

The Streamlit app reads these local files only; it does not call boundary APIs
at runtime.
"""

from __future__ import annotations

import json
import re
import unicodedata
from pathlib import Path
from typing import Any

import pandas as pd
import requests


COUNTRY_API_URLS = {
    "VNM": "https://www.geoboundaries.org/api/current/gbOpen/VNM/ADM1/",
    "KHM": "https://www.geoboundaries.org/api/current/gbOpen/KHM/ADM1/",
}

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
OUTPUT_DIR = SCRIPT_DIR / "data"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

OUT_GEOJSON = OUTPUT_DIR / "mekong_delta_adm1.geojson"
OUT_CONTEXT_GEOJSON = OUTPUT_DIR / "mekong_delta_context_adm1.geojson"
OUT_FULL_GEOJSON = OUTPUT_DIR / "vietnam_adm1_geoboundaries_simplified.geojson"
OUT_CAMBODIA_GEOJSON = OUTPUT_DIR / "cambodia_adm1_geoboundaries_simplified.geojson"
OUT_NAME_MAP = OUTPUT_DIR / "province_name_mapping.csv"
OUT_REGION_MAP = OUTPUT_DIR / "province_region_mapping.csv"
OUT_METADATA = OUTPUT_DIR / "geoboundaries_vnm_adm1_metadata.json"
OUT_CONTEXT_METADATA = OUTPUT_DIR / "geoboundaries_context_metadata.json"

DATASET_CANDIDATES = [
    SCRIPT_DIR / "merged_dataset.csv",
    SCRIPT_DIR / "data" / "merged_dataset.csv",
    REPO_ROOT / "dataset" / "merged_dataset.csv",
    REPO_ROOT / "merged_dataset.csv",
    Path("/mnt/data/merged_dataset.csv"),
]

MEKONG_PROVINCES = [
    "An Giang",
    "Bạc Liêu",
    "Bến Tre",
    "Cà Mau",
    "Cần Thơ",
    "Hậu Giang",
    "Kiên Giang",
    "Long An",
    "Sóc Trăng",
    "Tiền Giang",
    "Trà Vinh",
    "Vĩnh Long",
    "Đồng Tháp",
]

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

# Neighboring ADM1 units with a land boundary or major river/inland boundary
# against the Mekong Delta provinces. Sea-only contacts are intentionally left out.
CONTEXT_ADM1 = {
    "VNM": {
        "Ho Chi Minh": "TP. Hồ Chí Minh",
        "Tây Ninh": "Tây Ninh",
    },
    "KHM": {
        "Svay Rieng": "Svay Rieng",
        "Prey Veng": "Prey Veng",
        "Kandal": "Kandal",
        "Takeo": "Takeo",
        "Kampot": "Kampot",
    },
}

ALIASES = {
    "an giang": "An Giang",
    "bac lieu": "Bạc Liêu",
    "bạc liêu": "Bạc Liêu",
    "ben tre": "Bến Tre",
    "bến tre": "Bến Tre",
    "ca mau": "Cà Mau",
    "cà mau": "Cà Mau",
    "can tho": "Cần Thơ",
    "cần thơ": "Cần Thơ",
    "hau giang": "Hậu Giang",
    "hậu giang": "Hậu Giang",
    "kien giang": "Kiên Giang",
    "kiên giang": "Kiên Giang",
    "long an": "Long An",
    "soc trang": "Sóc Trăng",
    "sóc trăng": "Sóc Trăng",
    "tien giang": "Tiền Giang",
    "tiền giang": "Tiền Giang",
    "tra vinh": "Trà Vinh",
    "trà vinh": "Trà Vinh",
    "vinh long": "Vĩnh Long",
    "vĩnh long": "Vĩnh Long",
    "dong thap": "Đồng Tháp",
    "đồng tháp": "Đồng Tháp",
    "tp can tho": "Cần Thơ",
    "tp cần thơ": "Cần Thơ",
    "thanh pho can tho": "Cần Thơ",
    "thành phố cần thơ": "Cần Thơ",
}

NAME_PROPERTY_CANDIDATES = [
    "shapeName",
    "NAME_1",
    "name",
    "Name",
    "NAME",
    "VARNAME_1",
    "province",
    "Province",
    "ADM1_NAME",
]


def strip_accents(text: str) -> str:
    normalized = unicodedata.normalize("NFD", text)
    return "".join(ch for ch in normalized if unicodedata.category(ch) != "Mn")


def normalize_name(value: Any) -> str:
    text = str(value or "").strip()
    text = re.sub(
        r"\b(tinh|tỉnh|province|city|thanh pho|thành phố|tp\.?)\b",
        " ",
        text,
        flags=re.IGNORECASE,
    )
    text = strip_accents(text).replace("Đ", "D").replace("đ", "d")
    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


NORMALIZED_TO_CANONICAL = {normalize_name(name): name for name in MEKONG_PROVINCES}
NORMALIZED_TO_CANONICAL.update({normalize_name(key): value for key, value in ALIASES.items()})


def find_dataset_path() -> Path | None:
    for path in DATASET_CANDIDATES:
        if path.exists():
            return path
    return None


def expected_provinces() -> list[str]:
    dataset_path = find_dataset_path()
    if dataset_path is None:
        return MEKONG_PROVINCES
    df = pd.read_csv(dataset_path)
    if "tinh_thanh" not in df.columns:
        return MEKONG_PROVINCES
    values = sorted(df["tinh_thanh"].dropna().unique().tolist())
    return values if values else MEKONG_PROVINCES


def fetch_json(url: str) -> dict[str, Any]:
    response = requests.get(url, timeout=90)
    response.raise_for_status()
    return response.json()


def fetch_country_geojson(country_code: str) -> tuple[dict[str, Any], dict[str, Any]]:
    api_url = COUNTRY_API_URLS[country_code]
    print(f"[INFO] Fetching metadata: {api_url}")
    metadata = fetch_json(api_url)
    geojson_url = metadata.get("simplifiedGeometryGeoJSON") or metadata.get("gjDownloadURL")
    if not geojson_url:
        raise RuntimeError(f"No GeoJSON URL found for {country_code}.")
    print(f"[INFO] Downloading {country_code} GeoJSON: {geojson_url}")
    return metadata, fetch_json(geojson_url)


def guess_name_property(features: list[dict[str, Any]]) -> str | None:
    if not features:
        return None
    all_keys = set()
    for feature in features[:10]:
        all_keys.update(feature.get("properties", {}).keys())

    for key in NAME_PROPERTY_CANDIDATES:
        if key in all_keys:
            return key

    for key in sorted(all_keys):
        sample_values = [feature.get("properties", {}).get(key) for feature in features[:20]]
        if any(isinstance(value, str) and 2 <= len(value) <= 80 for value in sample_values):
            return key
    return None


def canonical_from_geo_name(raw_name: Any) -> str | None:
    return NORMALIZED_TO_CANONICAL.get(normalize_name(raw_name))


def build_mekong_layer(geojson: dict[str, Any], expected: list[str]) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    features = geojson.get("features", [])
    name_prop = guess_name_property(features)
    print(f"[INFO] Vietnam name property: {name_prop}")

    expected_set = set(expected)
    kept = []
    rows = []
    unmatched = []

    for feature in features:
        props = feature.get("properties", {})
        raw_name = props.get(name_prop) if name_prop else None
        canonical = canonical_from_geo_name(raw_name)

        if canonical in expected_set:
            new_feature = dict(feature)
            new_feature["properties"] = dict(props)
            new_feature["properties"]["tinh_thanh"] = canonical
            new_feature["properties"]["region"] = REGION_MAP[canonical]
            new_feature["properties"]["geojson_name_observed"] = raw_name
            kept.append(new_feature)
            rows.append(
                {
                    "tinh_thanh": canonical,
                    "geojson_name_observed": raw_name,
                    "normalized_key": normalize_name(raw_name),
                    "match_status": "matched",
                    "region": REGION_MAP[canonical],
                }
            )
        else:
            unmatched.append(raw_name)

    found = {row["tinh_thanh"] for row in rows}
    missing = sorted(expected_set - found)
    print(f"[INFO] Matched Mekong provinces: {len(found)}/{len(expected_set)}")
    if missing:
        print("[ERROR] Missing provinces:")
        for name in missing:
            print(f"  - {name}")
        print("[DEBUG] Sample unmatched GeoJSON names:")
        for name in unmatched[:40]:
            print(f"  - {name}")
        raise RuntimeError("Province matching failed.")

    out_geojson = dict(geojson)
    out_geojson["features"] = kept
    return out_geojson, rows


def build_context_layer(country_geojsons: dict[str, dict[str, Any]]) -> dict[str, Any]:
    context_features = []
    for country_code, geojson in country_geojsons.items():
        wanted = CONTEXT_ADM1.get(country_code, {})
        if not wanted:
            continue

        features = geojson.get("features", [])
        name_prop = guess_name_property(features)
        print(f"[INFO] {country_code} context name property: {name_prop}")

        matched = set()
        wanted_norm = {normalize_name(source): label for source, label in wanted.items()}
        for feature in features:
            props = feature.get("properties", {})
            raw_name = props.get(name_prop) if name_prop else None
            label = wanted_norm.get(normalize_name(raw_name))
            if not label:
                continue

            new_feature = dict(feature)
            new_feature["properties"] = dict(props)
            new_feature["properties"]["context_name"] = f"{label} ({country_code})"
            new_feature["properties"]["context_label"] = label
            new_feature["properties"]["country_code"] = country_code
            new_feature["properties"]["geojson_name_observed"] = raw_name
            context_features.append(new_feature)
            matched.add(label)

        missing = sorted(set(wanted.values()) - matched)
        if missing:
            raise RuntimeError(f"Missing context ADM1 for {country_code}: {missing}")

    return {"type": "FeatureCollection", "features": context_features}


def main() -> int:
    metadata_vnm, geojson_vnm = fetch_country_geojson("VNM")
    OUT_METADATA.write_text(json.dumps(metadata_vnm, ensure_ascii=False, indent=2), encoding="utf-8")
    OUT_FULL_GEOJSON.write_text(json.dumps(geojson_vnm, ensure_ascii=False), encoding="utf-8")

    metadata_khm, geojson_khm = fetch_country_geojson("KHM")
    OUT_CAMBODIA_GEOJSON.write_text(json.dumps(geojson_khm, ensure_ascii=False), encoding="utf-8")
    OUT_CONTEXT_METADATA.write_text(
        json.dumps({"VNM": metadata_vnm, "KHM": metadata_khm}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    expected = expected_provinces()
    mekong_geojson, rows = build_mekong_layer(geojson_vnm, expected)
    context_geojson = build_context_layer({"VNM": geojson_vnm, "KHM": geojson_khm})

    OUT_GEOJSON.write_text(json.dumps(mekong_geojson, ensure_ascii=False), encoding="utf-8")
    OUT_CONTEXT_GEOJSON.write_text(json.dumps(context_geojson, ensure_ascii=False), encoding="utf-8")

    pd.DataFrame(rows).sort_values("tinh_thanh").to_csv(OUT_NAME_MAP, index=False, encoding="utf-8-sig")
    pd.DataFrame([{"tinh_thanh": p, "region": REGION_MAP[p]} for p in expected]).to_csv(
        OUT_REGION_MAP,
        index=False,
        encoding="utf-8-sig",
    )

    print(f"[OK] Saved: {OUT_GEOJSON}")
    print(f"[OK] Saved: {OUT_CONTEXT_GEOJSON}")
    print(f"[OK] Saved: {OUT_FULL_GEOJSON}")
    print(f"[OK] Saved: {OUT_CAMBODIA_GEOJSON}")
    print(f"[OK] Saved: {OUT_NAME_MAP}")
    print(f"[OK] Saved: {OUT_REGION_MAP}")
    print(f"[OK] Saved: {OUT_METADATA}")
    print(f"[OK] Saved: {OUT_CONTEXT_METADATA}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

