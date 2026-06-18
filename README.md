# Dataset Overview / EDA Dashboard

Interactive Streamlit dashboard for target completeness, province trends, spatial view, ranking selection, distribution views, driver relationship checks, and filtered/raw CSV downloads.

## Install

```bash
pip install streamlit pandas numpy plotly
```

## Data

Place the raw dataset at one of these paths:

```text
dashboard/data/merged_dataset.csv
dashboard/merged_dataset.csv
dataset/merged_dataset.csv
merged_dataset.csv
/mnt/data/merged_dataset.csv
```

`merged_dataset_fe.csv` is not used by Tab 1.

## Run

```bash
streamlit run app.py
```

Compatibility entrypoint:

```bash
streamlit run dashboard_tab1_eda.py
```

## GeoJSON

If `dashboard/data/mekong_delta_adm1.geojson` is missing or does not match all 13 provinces, the app uses the province ranking fallback.

## Native Selection

- Province ranking uses native Streamlit Plotly point selection.
- Map selection is disabled by default to keep fullscreen behavior stable.
- Sidebar province multiselect remains the stable fallback.

## V1 Limits

- No autoplay animation.
- No required map-click selection.
- No model performance tab.
- No residual or error explorer.
- No runtime boundary API call.
