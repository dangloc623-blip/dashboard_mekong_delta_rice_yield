# Dashboard Tab 1 — Dataset overview / EDA

## Files

- `dashboard_tab1_eda.py`: Streamlit app triển khai Tab 1.
- `merged_dataset.csv`: raw dataset.
- `merged_dataset_fe.csv`: feature-engineered dataset.
- `eda_lua_dashboard_tab1.ipynb`: notebook gốc đã được bổ sung cell tạo dashboard.

## Run

```bash
pip install streamlit plotly pandas numpy
streamlit run dashboard_tab1_eda.py
```

## Nội dung Tab 1

- Overview: KPI, preview dữ liệu, data dictionary, coverage theo năm/mùa vụ.
- Data quality: missing report, heatmap thiếu target theo tỉnh-năm, thống kê numeric.
- Target & trend: năng suất, diện tích, sản lượng theo năm/mùa vụ/tỉnh.
- Weather & correlation: tương quan Pearson và scatter giữa thời tiết với năng suất.
- FE readiness: kiểm tra feature-engineered dataset, missing lag/rolling/cross, tương quan feature với target.
