# Codex Agent Plan — Dashboard V2 Upgrade  
## Streamlit Tab 1: Professional Interactive EDA Dashboard

## 0. Goal

Upgrade the current **Streamlit Tab 1 — Dataset Overview / EDA** from a functional V1 into a **professional, polished, map-centered interactive dashboard**.

The V2 dashboard must remain an **interactive EDA workspace**, not a report page.

It should help the presenter query and explore the data live through:

```text
filters
map interaction
linked charts
missing/outlier inspection
distribution exploration
correlation exploration
filtered data export
```

It must not contain long narrative explanations or causal claims.

---

## 1. Context from V1 live review

The current V1 already works and includes:

```text
sidebar filters
KPI cards
province ranking fallback
trend chart
missing heatmap
distribution chart
missing/outlier tables
correlation heatmap
scatter plot
filtered data table
download filtered CSV
```

However, V1 still feels like a technical Streamlit prototype. V2 should improve:

```text
visual polish
layout hierarchy
map-centered spatial exploration
filter UX
chart design
information density
interaction consistency
```

---

## 2. Non-negotiable V2 principles

### 2.1 Dashboard is not a report

Do not add long explanatory text.

Allowed text:

```text
section title
metric label
axis label
legend
tooltip
short technical caption
empty-state message
```

Not allowed:

```text
Bến Tre giảm do...
Mưa làm...
Kiên Giang cao vì...
```

Presenter explains those insights verbally.

### 2.2 Raw dataset remains the source of truth

Tab 1 uses:

```text
merged_dataset.csv
```

or equivalent:

```text
merged_dataset(1).csv
```

Do not use:

```text
merged_dataset_fe.csv
```

for Tab 1.

### 2.3 No runtime boundary API call

V2 must not call GeoJSON/boundary API during Streamlit runtime.

Use cached local files:

```text
data/mekong_delta_adm1.geojson
data/province_region_mapping.csv
data/province_name_mapping.csv
```

If GeoJSON is missing, show a polished fallback, but V2 target is to render the real map.

### 2.4 Map-centered design

V2 should prioritize the Mekong Delta map as the main visual object.

The map should not be a small secondary chart.

### 2.5 Professional UI over accessibility-specific design

The UI should look professional, modern, polished and presentation-ready.

Do not optimize specifically for color-blind palettes unless it improves general visual quality.

---

## 3. Current V1 issues to fix

## 3.1 Hide local data path

V1 shows a local path like:

```text
D:\DS107_TuDuyTinhToan\dashboard\merged_dataset.csv
```

This should not appear in production UI.

Replace with:

```text
Dataset: Raw rice dataset
Period: 1995–2024
Granularity: province × year × season
```

or a compact badge:

```text
Raw dataset · 780 rows · 13 provinces · 1995–2024
```

---

## 3.2 Rename confusing KPI labels

Current KPI:

```text
Years = 1999
```

This is confusing.

Replace with:

```text
Selected year
```

or if showing range:

```text
Year
```

Recommended KPI set:

```text
Filtered rows
Selected year
Provinces shown
Target completeness
Mean yield
Missing target rows
Yield outliers
Area outliers
```

---

## 3.3 Region filter must affect data consistently

In V1, region filter UI exists, but verify that it actually filters:

```text
KPI cards
province list
spatial view
trend chart
distribution panel
correlation panel
tables
downloaded CSV
```

If a region is removed, provinces belonging to that region should be removed from all dependent views unless they are manually reselected.

Implementation rule:

```text
region filter is applied before province filter
province options should update based on selected regions
```

---

## 3.4 Province selector needs better UX

Current multi-select shows many red tags and occupies too much sidebar space.

Improve with:

```text
searchable multiselect
Select all / Clear all buttons
compact selected count
optional expander for province list
```

Display:

```text
13 selected
```

instead of forcing all province tags to be visible.

---

## 3.5 Replace fallback-first spatial view with map-first design

V1 uses province ranking bar chart as the spatial view.

V2 should use:

```text
Interactive Mekong Delta choropleth map
```

Fallback ranking should remain only if GeoJSON is missing.

---

## 3.6 Improve chart hierarchy

V1 has many charts stacked vertically.

V2 should group them into clean analytic sections or sub-tabs:

```text
Overview
Map & Trend
Data Quality
Distribution
Correlation
Data Table
```

These are sub-sections within Tab 1, not dashboard-wide tabs.

---

## 3.7 Improve empty tables

When there are no missing/outlier rows, do not show only blank table headers.

Show short empty states:

```text
No missing target rows under current filters.
No yield warnings under current filters.
No area outliers under current filters.
```

---

## 4. V2 target layout

## 4.1 Page layout

Use wide layout:

```python
st.set_page_config(
    page_title="Dataset Overview / EDA",
    layout="wide"
)
```

### Recommended V2 layout

```text
┌─────────────────────────────────────────────────────────────┐
│ Header: Mekong Delta Rice Dataset — Interactive EDA          │
│ Badges: Raw dataset · 780 rows · 13 provinces · 1995–2024    │
├─────────────────────────────────────────────────────────────┤
│ Compact filter bar / polished sidebar                       │
├─────────────────────────────────────────────────────────────┤
│ KPI cards                                                    │
├───────────────────────────────┬─────────────────────────────┤
│ Interactive choropleth map     │ Selected province panel     │
│ Large central visual           │ Mini KPIs + current values  │
├───────────────────────────────┴─────────────────────────────┤
│ Trend chart                                                   │
├─────────────────────────────────────────────────────────────┤
│ Sub-tabs: Data Quality | Distribution | Correlation | Table   │
└─────────────────────────────────────────────────────────────┘
```

---

## 4.2 Recommended visual priority

Priority order:

```text
1. Map
2. KPI cards
3. Trend chart
4. Data quality / missing
5. Distribution
6. Correlation
7. Raw filtered table
```

Do not let the table dominate the dashboard.

---

## 5. Professional UI design system

## 5.1 CSS variables

Add a custom CSS block.

Recommended palette:

```css
:root {
  --bg-main: #F6F8FB;
  --panel-bg: #FFFFFF;
  --panel-border: #E5E7EB;
  --text-main: #111827;
  --text-muted: #6B7280;

  --primary: #0F766E;
  --primary-dark: #134E4A;
  --accent: #F59E0B;
  --danger: #DC2626;

  --upstream: #16A34A;
  --coastal: #0EA5E9;
  --center: #F97316;

  --shadow-card: 0 10px 25px rgba(15, 23, 42, 0.08);
  --radius-lg: 18px;
  --radius-md: 12px;
}
```

Use a premium light analytics look:

```text
soft gray page background
white cards
rounded corners
subtle shadows
strong typography
clean spacing
```

---

## 5.2 Typography

Use system fonts for stability:

```css
font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
```

If no custom font available, system font is fine.

---

## 5.3 KPI cards

KPI cards should look like dashboard cards, not plain Streamlit metrics.

Suggested card structure:

```text
Label
Large value
Small unit / delta / status
```

Examples:

```text
Mean yield
5.647
tấn/ha

Target completeness
92.3%
filtered rows
```

Use cards with:

```text
white background
border
shadow
rounded corners
consistent height
```

---

## 5.4 Plotly theme

Create a shared Plotly template/helper.

```python
def apply_plotly_theme(fig, height=None):
    fig.update_layout(
        template="plotly_white",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#111827", size=13),
        margin=dict(l=20, r=20, t=50, b=30),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
        ),
    )
    fig.update_xaxes(showgrid=True, gridcolor="#E5E7EB")
    fig.update_yaxes(showgrid=True, gridcolor="#E5E7EB")
    if height:
        fig.update_layout(height=height)
    return fig
```

All charts must use this helper.

---

## 6. V2 filter UX

## 6.1 Sidebar structure

Use grouped filters:

```text
Time
  Year
  Season

Metric
  Metric selector

Space
  Region
  Province

Flags
  Show missing
  Highlight outliers

Actions
  Reset filters
  Download filtered data
```

---

## 6.2 Active filter summary

Show compact active filters under header:

```text
Year: 1999 · Season: Đông Xuân · Metric: Năng suất · Regions: 3 · Provinces: 13
```

No long text.

---

## 6.3 Reset filters

Add button:

```text
Reset filters
```

Default state:

```text
year = max year
season = dong_xuan
metric = nang_suat
regions = all
provinces = all available after region filter
show_missing = True
show_outliers = True
```

---

## 7. V2 map requirements

## 7.1 Primary map

Use Plotly choropleth with local GeoJSON.

If `data/mekong_delta_adm1.geojson` exists and validates 13/13 provinces:

```text
render choropleth map
```

If not:

```text
show polished province ranking fallback
show short technical message: GeoJSON layer not loaded
```

---

## 7.2 Map metrics

Metric selector should support:

```text
nang_suat
dien_tich
san_luong
missing_target
yield_outlier
area_outlier
region
```

Metric-specific color behavior:

| Metric | Color logic |
|---|---|
| `nang_suat` | sequential green/teal scale |
| `dien_tich` | blue scale |
| `san_luong` | orange/gold scale |
| `missing_target` | gray/black scale |
| `yield_outlier` | red highlight |
| `area_outlier` | amber/red highlight |
| `region` | categorical region colors |

---

## 7.3 Tooltip

Tooltip must include:

```text
Province
Year
Season
Region
Yield
Area
Production
Sunshine
Rainfall
Humidity
Temperature
Missing target
Yield outlier
Area outlier
```

Use clean labels:

```text
Năng suất (tấn/ha)
Diện tích (nghìn ha)
Sản lượng (nghìn tấn)
```

---

## 7.4 Selected province behavior

V2 default:

```text
province selector remains source of truth
```

Map click can be implemented if stable, but it is not required.

However, selected province should be visually highlighted on the map if possible.

---

## 8. V2 component requirements

## 8.1 Header

Replace plain title with a professional header.

Example:

```text
Mekong Delta Rice Dataset
Interactive EDA Dashboard
```

Badges:

```text
Raw dataset
780 rows
13 provinces
1995–2024
2 seasons
```

Do not show local file path.

---

## 8.2 KPI cards

Required KPIs:

```text
Filtered rows
Selected year
Provinces shown
Target completeness
Mean yield
Missing target
Yield outliers
Area outliers
```

KPI labels must be clear.

Change:

```text
Years
```

to:

```text
Selected year
```

---

## 8.3 Map + province detail

Province detail panel should show:

```text
Province / selected group
Region
Selected year value
Selected season value
Mean yield over available period
Missing target count
Yield outlier count
Area outlier count
Latest available value
Rank by selected metric
```

If multiple provinces selected:

```text
Selected provinces: N
Mean selected metric
Missing target rows
Outlier flags
```

---

## 8.4 Trend chart

Trend chart must support:

```text
selected province(s)
selected region(s)
selected metric
season color
outlier markers
selected year highlight
```

Add vertical selected-year marker:

```text
selected_year
```

This makes the relationship between map snapshot and trend chart clearer.

---

## 8.5 Small multiples

Move small multiples into a polished expander:

```text
Province small multiples
```

Support:

```text
metric = nang_suat or dien_tich
color = season
outlier markers if enabled
```

Use consistent y-axis option:

```text
shared y-axis toggle
```

Optional but recommended.

---

## 8.6 Missing quality

Improve the missing heatmap:

```text
x = year
y = province
value = missing target
filter = season
```

Add mode:

```text
Missing target
Target completeness
```

Tables should show empty states instead of blank headers.

---

## 8.7 Distribution panel

Use sub-controls:

```text
Variable selector
Chart mode selector
```

Variables:

```text
nang_suat
dien_tich
san_luong
tổng số giờ nắng
tổng lượng mưa
độ ẩm trung bình
nhiệt độ trung bình
```

Modes:

```text
Histogram
Boxplot by season
Boxplot by province
Boxplot by province + season
```

Default:

```text
Variable = nang_suat
Mode = Boxplot by province + season
```

Add optional summary stats next to chart:

```text
mean
median
min
max
std
missing
```

No explanation text.

---

## 8.8 Correlation panel

Modes:

```text
Core numeric
Weather only
Yield vs drivers
```

Default:

```text
Core numeric
```

Variables:

```text
nang_suat
dien_tich
san_luong
tổng số giờ nắng
tổng lượng mưa
độ ẩm trung bình
nhiệt độ trung bình
```

Add scatter controls:

```text
Scatter x
Scatter color
```

Allowed caption:

```text
Correlation is descriptive only.
```

---

## 8.9 Filtered data table

Make table more polished:

```text
row count
column selector
download filtered CSV
download current special rows
```

Download filename should include filters:

```text
filtered_eda_<year>_<season>.csv
```

---

## 9. Navigation inside Tab 1

To avoid one very long scrolling page, use sub-tabs or segmented sections.

Recommended:

```text
Overview
Map & Trend
Data Quality
Distribution
Correlation
Data Table
```

All are still part of Tab 1.

Do not create separate top-level Streamlit pages yet.

---

## 10. Implementation phases for Codex

## Phase 1 — UI foundation

Tasks:

```text
create custom CSS
create card components
create shared Plotly theme helper
hide local data path
rename KPI labels
add active filter summary
add reset filters
```

Acceptance:

```text
dashboard looks polished before adding new charts
no local file path visible
KPI cards look like cards
```

---

## Phase 2 — Filter correctness

Tasks:

```text
make region filter affect all views
make province options depend on selected region
make reset filters work
ensure downloaded CSV follows filters
ensure empty filters do not crash
```

Acceptance:

```text
removing a region removes its provinces from charts/tables
filtered row count matches table rows
downloaded CSV equals current filtered data
```

---

## Phase 3 — Map-centered spatial view

Tasks:

```text
load cached GeoJSON
validate 13/13 province match
render choropleth map
implement metric-specific color logic
implement tooltip
highlight selected province if possible
keep province ranking fallback
```

Acceptance:

```text
map renders 13 provinces
year/season/metric changes update map
tooltip contains required fields
app does not crash if GeoJSON missing
```

---

## Phase 4 — Visualization polish

Tasks:

```text
improve trend chart
add selected-year marker
polish distribution panel
polish missing heatmap
polish correlation panel
add small multiples expander
add province ranking summary
```

Acceptance:

```text
charts use shared Plotly theme
charts have consistent heights
labels and units are correct
no narrative paragraphs added
```

---

## Phase 5 — UX and QA polish

Tasks:

```text
add empty states
add loading states if needed
add clear technical warnings
add data QA status panel
improve table/download naming
test all core flows
```

Acceptance:

```text
dashboard feels professional
all filters work
all panels handle empty data
all expected EDA counts are correct
```

---

## 11. Test flows for V2

### 11.1 Bến Tre 2020

```text
Year = 2020
Season = dong_xuan
Metric = nang_suat
Province = Bến Tre
```

Expected:

```text
low yield visible
outlier flag visible
trend highlights 2020
table shows filtered Bến Tre row
```

### 11.2 Cà Mau missing

```text
Province = Cà Mau
Season = dong_xuan
Metric = missing_target
```

Expected:

```text
missing heatmap shows missing years
missing detail table shows rows
map/fallback shows missing status
```

### 11.3 Region filtering

```text
Remove Ven biển / rủi ro mặn
```

Expected:

```text
coastal provinces disappear from charts/tables
province selector options update
filtered row count changes
downloaded CSV excludes coastal provinces
```

### 11.4 Correlation by season

```text
Correlation mode = Core numeric
Season = dong_xuan
then he_thu-thu_dong
```

Expected:

```text
heatmap changes
scatter changes
caption remains short
```

### 11.5 Download

```text
Select Year = 1999
Season = dong_xuan
Province = Hậu Giang
Download filtered CSV
```

Expected:

```text
CSV only includes selected filtered rows
filename reflects current filter context
```

---

## 12. Data correctness checks

V2 must preserve these expected EDA facts:

| Check | Expected |
|---|---:|
| rows | 780 |
| provinces | 13 |
| years | 30 |
| seasons | 2 |
| missing target rows | 31 |
| complete target rows | 749 |
| yield extreme outliers | 2 |
| yield low warnings | 3 |
| area outliers | 37 |
| mean yield | approx 5.318 |

Run these checks after refactor.

---

## 13. Definition of Done for V2

V2 is done when:

```text
1. UI looks professional and polished.
2. Local file path is hidden.
3. KPI labels are clear.
4. Region filter correctly affects all charts/tables.
5. Province filter UX is compact and usable.
6. Map renders real Mekong Delta province boundaries if GeoJSON exists.
7. Province ranking fallback remains available.
8. Trend chart highlights selected year.
9. Missing heatmap is clear and polished.
10. Distribution panel supports numeric variables and chart modes.
11. Correlation panel supports core/weather/yield modes.
12. Filtered table and download work correctly.
13. Empty states are handled cleanly.
14. No long narrative explanations are shown.
15. Dashboard remains stable if GeoJSON is missing.
```

---

## 14. Explicit non-goals for V2

Do not implement yet:

```text
Model performance tab
Residual/error explorer tab
FE dataset workflow
imputation workflow
causal explanation text
complex React frontend
mandatory map click state
autoplay animation as default
```

Autoplay animation can remain optional demo enhancement.

---

## 15. Final instruction to Codex

Upgrade V1 into a professional V2 dashboard.

Prioritize:

```text
beautiful UI
map-centered spatial view
clean interaction
filter correctness
polished charts
correct EDA metrics
```

Do not prioritize:

```text
long report text
causal interpretation
advanced frontend complexity
animation for its own sake
```
