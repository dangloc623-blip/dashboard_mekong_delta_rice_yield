# Codex Agent Plan — Dashboard V3 Upgrade with Execution/Debug Loop

## 0. Mission

Upgrade the current **Streamlit Tab 1 — Dataset Overview / EDA** from V2 into a more polished **V3 analytics web app**.

V3 should keep the existing V2 strengths:

```text
professional header
KPI cards
GeoJSON map
Map & Trend tab
Data Quality tab
Distribution tab
Correlation tab
Data Table tab
filtered CSV download
```

but improve the weak parts:

```text
Data Quality default view is still hard to read
Distribution default chart is not context-aware
map is mostly hover-only, not selection-driven
region/province filter UX is still too Streamlit-like
layout can look closer to a React analytics website
```

The final V3 target:

```text
Beautiful, polished, React-like Streamlit dashboard
Map-centered interactive EDA workspace
No long narrative explanation
Correct data and stable filters
```

---

## 1. Hard constraints

### 1.1 Keep Tab 1 as EDA only

Do not implement:

```text
model performance
residual explorer
feature-engineered dataset analysis
imputation workflow
causal explanation text
```

### 1.2 Raw dataset remains source of truth

Use:

```text
merged_dataset.csv
```

Do not use:

```text
merged_dataset_fe.csv
```

for Tab 1.

### 1.3 Do not break V2

V2 is already functional. V3 must be an incremental upgrade.

Do not rewrite everything from scratch unless necessary.

### 1.4 No long narrative UI

Allowed UI text:

```text
section title
filter label
axis label
legend
tooltip
short empty-state message
short technical caption
```

Not allowed:

```text
paragraph-style explanation
causal claims
report-like interpretation
```

---

## 2. Priority map

## P0 — Required before V3 is acceptable

```text
1. Revise Data Quality default
2. Revise Distribution default and add Distribution Scope
3. Fix region/province filtering correctness
4. Compact province filter UX
5. Hide or repurpose Validation dropdown
6. Clarify downloads in Data Table
7. Add validation/debug loop
```

## P1 — Strongly recommended

```text
1. Map province click/select support if technically stable
2. Selected province highlight on map
3. Year range and animation mode
4. Distribution horizontal layouts
5. Missing-by-province bar chart
6. Compact statistic cards
7. Correlation advanced modes refinement
```

## P2 — Polish / React-like finish

```text
1. React-like app shell
2. Better pill navigation
3. Card hover effects and micro-interactions
4. Sidebar compact mode or top-filter mode
5. Smooth chart transitions
6. Loading skeletons / polished empty states
```

---

# 3. P0 Implementation Details

---

## 3.1 P0-A — Data Quality default redesign

### Current problem

The default Data Quality view opens directly with a raw missing heatmap.

This is technically correct, but hard to read because missing values are sparse.

### New V3 default

Default view:

```text
Coverage Summary
```

### Required layout

```text
Data Quality
├── Quality KPI cards
│   ├── Missing target rows
│   ├── Affected provinces
│   ├── Target completeness
│   └── Affected years
│
├── Missing by province
│   └── horizontal bar chart, sorted descending
│
├── Province × Year heatmap
│   ├── sorted by missing count
│   ├── soft warm color scale
│   └── mode: Missing target / Target completeness
│
└── Detail tabs
    ├── Missing target rows
    ├── Yield warnings/outliers
    └── Area outliers
```

### Files likely to modify

```text
src/components/missing_quality_panel.py
src/theme.py
src/eda_metrics.py
```

### Required functions

Add helper functions:

```python
def compute_quality_summary(df_filtered: pd.DataFrame) -> dict:
    ...

def compute_missing_by_province(df_filtered: pd.DataFrame) -> pd.DataFrame:
    ...

def compute_missing_heatmap_matrix(df_filtered: pd.DataFrame, mode: str) -> pd.DataFrame:
    ...
```

### KPI cards

Add compact quality cards:

```text
Missing target rows
Affected provinces
Target completeness
Affected years
```

Expected global values on full data:

```text
missing target rows = 31
affected provinces = 3
target completeness = 96.03%
affected years depends on filter
```

### Missing-by-province bar chart

Chart:

```text
y = province
x = missing_count
orientation = horizontal
sort = descending missing_count
```

Default should immediately show:

```text
Hậu Giang
Cà Mau
Bạc Liêu
```

as the affected provinces on full data.

### Heatmap revision

Current heatmap should remain, but improve:

```text
sort provinces by missing count desc
use warm color scale, not harsh black/white
show only meaningful year ticks
height adjusts to province count
```

Recommended Plotly scale:

```python
color_continuous_scale = ["#FFF7ED", "#FDBA74", "#EA580C", "#7C2D12"]
```

For binary missing:

```text
0 = no missing
1 = missing target
```

For target completeness:

```text
0–100%
```

### Empty states

If no missing rows under current filters:

```text
No missing target rows under current filters.
```

If no yield warnings:

```text
No yield warnings under current filters.
```

If no area outliers:

```text
No area outliers under current filters.
```

Use styled empty-state card, not just plain text.

---

## 3.2 P0-B — Distribution default redesign

### Current problem

Distribution default uses:

```text
Boxplot by province + season
```

but current filters often produce one row per province:

```text
selected_year = 2024
selected_season = dong_xuan
```

In that case, boxplot degenerates into tiny lines and is hard to read.

### New concept

Add:

```text
Distribution Scope
```

Options:

```text
Current snapshot
Full period
Selected year range
```

### Required behavior

| Scope | Data used | Default chart |
|---|---|---|
| Current snapshot | current selected year + season + filters | Province ranking / dot plot |
| Full period | all years under province/region/season filters | Boxplot by province + season |
| Selected year range | selected range + filters | Boxplot or histogram |

### Files likely to modify

```text
src/components/distribution_panel.py
src/filters.py
src/theme.py
```

### Required controls

```text
Variable selector
Distribution scope selector
Chart mode selector
Bin count slider if chart mode = Histogram
Optional density toggle
```

### Numeric variables only

Distribution variables must be numeric only:

```text
nang_suat
dien_tich
san_luong
tổng số giờ nắng
tổng lượng mưa
độ ẩm trung bình
nhiệt độ trung bình
```

Do not include:

```text
region
missing_target
yield_outlier
area_outlier
```

as distribution variables.

### Current snapshot default

If:

```text
scope = Current snapshot
```

default chart:

```text
Province ranking / dot plot
```

Chart:

```text
y = province
x = selected variable
orientation = horizontal
sort = descending x
color = region or season
```

### Full period default

If:

```text
scope = Full period
```

default chart:

```text
Boxplot by province + season
```

But use horizontal layout:

```text
y = province
x = selected variable
color = season
```

### Histogram

If chart mode = Histogram:

```text
x = selected variable
bins = user-controlled
optional marginal box
optional density curve
```

Add bin slider:

```text
Bins: 5–40
default = 15
```

### Summary statistics

Replace the current summary statistics table with compact statistic cards:

```text
Mean
Median
Min
Max
Std
Missing
```

These cards should appear above the chart.

---

## 3.3 P0-C — Region/province filter correctness

### Current issue

Region filter may not fully remove provinces from all views.

### Required logic

Apply filters in this order:

```python
selected_regions -> available_provinces -> selected_provinces -> df_filtered
```

Pseudo-code:

```python
available_provinces = sorted(
    df_base.loc[df_base["region"].isin(selected_regions), "tinh_thanh"].unique()
)

selected_provinces = [
    p for p in selected_provinces
    if p in available_provinces
]

df_filtered = df_base[
    df_base["region"].isin(selected_regions)
    & df_base["tinh_thanh"].isin(selected_provinces)
    & ...
]
```

### Required behavior

If user removes:

```text
Ven biển / rủi ro mặn
```

then these provinces must disappear from:

```text
province selector options
map
trend
small multiples
data quality
distribution
correlation
data table
downloaded CSV
```

Affected provinces:

```text
Kiên Giang
Sóc Trăng
Bạc Liêu
Trà Vinh
Bến Tre
Cà Mau
```

### Files likely to modify

```text
src/components/filters.py
src/filters.py
app.py
```

---

## 3.4 P0-D — Compact province selector UX

### Current issue

Province filter displays many red tags and consumes sidebar height.

### New UX

Use:

```text
compact searchable multiselect
selected count badge
Select all / Clear all buttons
optional expander showing selected names
```

Display:

```text
13 provinces selected
```

instead of forcing all tags to dominate the sidebar.

### Required behavior

```text
Select all -> selects all available provinces after region filter
Clear all -> clears province list or resets to all with warning
If empty selection -> show "No province selected" and no-data state
```

### Files likely to modify

```text
src/components/filters.py
src/theme.py
```

---

## 3.5 P0-E — Hide or repurpose Validation dropdown

### Current issue

The header contains a dropdown labeled:

```text
Validation
```

It is unclear and consumes top visual space.

### Required action

Either:

```text
remove it
```

or rename/move to:

```text
Data QA Status
```

inside Data Quality tab.

Recommended V3:

```text
Move Validation into Data Quality tab as a collapsible "Data QA Status" panel.
```

Data QA Status should show:

```text
raw dataset loaded
rows = 780
provinces = 13
years = 30
seasons = 2
GeoJSON matched = 13/13
missing target = 31
outlier flags created
```

---

## 3.6 P0-F — Data Table downloads

### Current issue

There is:

```text
Download filtered CSV
Special rows (3)
```

but the second label is unclear.

### Required V3 behavior

Use two clear actions:

```text
Download filtered CSV
Download special rows CSV
```

Optional:

```text
View special rows
```

### Special rows definition

Special rows include:

```text
is_missing_target == True
or is_yield_extreme_outlier == True
or is_yield_low_warning == True
or is_area_outlier == True
```

### Filename convention

```text
filtered_eda_<year_or_range>_<season>.csv
special_rows_<year_or_range>_<season>.csv
```

---

# 4. P1 Implementation Details

---

## 4.1 P1-A — Map click select/deselect province

### Goal

Allow user to click provinces on the map to update selected provinces.

### Important technical note

Native Streamlit + Plotly click selection may depend on Streamlit version.

Implementation should be robust:

```text
Attempt native st.plotly_chart selection support first.
If not available, keep province selector as source of truth.
Do not break map rendering.
```

### Best-effort implementation

Try:

```python
event = st.plotly_chart(
    fig,
    use_container_width=True,
    on_select="rerun",
    selection_mode="points",
    key="map_selection",
)
```

Then parse selected province from:

```python
event["selection"]["points"]
```

If unsupported:

```text
fallback to hover-only map + province selector
```

### Required behavior if click works

```text
click unselected province -> add to selected_provinces
click selected province -> remove from selected_provinces
```

### Session state

Use:

```python
st.session_state["selected_provinces"]
```

Do not rely on local variables only.

---

## 4.2 P1-B — Selected province highlight on map

Even if click is not stable, V3 must highlight selected provinces.

Map visual behavior:

```text
selected provinces = strong border / full opacity
non-selected provinces = lower opacity
```

For Plotly choropleth, if border styling per feature is difficult, add an overlay trace for selected province boundaries.

Fallback:

```text
use selected province markers or annotation
```

---

## 4.3 P1-C — Hover cross-filter

### Goal

When hovering a province on map:

```text
trend/distribution highlight matching province
```

### Realistic Streamlit constraint

True hover cross-component interaction is difficult in pure Streamlit.

Implement in stages:

```text
Stage 1 required: click/select cross-filter
Stage 2 optional: hover cross-filter within same Plotly chart
Stage 3 optional: custom component for real hover cross-filter
```

Do not block V3 completion on hover cross-filter if it requires heavy custom JavaScript.

---

## 4.4 P1-D — Year range and animation mode

### Add Year Mode

Sidebar should include:

```text
Year mode:
  Snapshot
  Range
  Animated
```

### Snapshot mode

Current behavior:

```text
selected_year = one year
map = selected year
KPI = selected year
trend = full period with selected-year marker
```

### Range mode

Add range slider:

```text
year_range = [start_year, end_year]
```

Use for:

```text
distribution
data table
correlation
optional trend filtering
```

Map behavior in range mode:

```text
option 1: aggregate over range
option 2: still use snapshot year
```

Recommended:

```text
Map uses snapshot year unless user chooses "Map aggregate over range".
```

### Animated mode

Add play/pause or Plotly animation.

Recommended implementation:

```text
animated choropleth map with animation_frame = nam
```

Do not animate every panel.

Animation controls:

```text
Play
Pause
Speed
```

Animation is optional and user-triggered.

Never autoplay by default.

---

## 4.5 P1-E — Correlation refinement

Ensure modes:

```text
Core numeric
Weather only
Yield vs drivers
```

### Core numeric

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

### Weather only

Variables:

```text
tổng số giờ nắng
tổng lượng mưa
độ ẩm trung bình
nhiệt độ trung bình
```

### Yield vs drivers

Show:

```text
horizontal bar chart of corr(nang_suat, variable)
```

Variables:

```text
dien_tich
san_luong
4 weather variables
```

Optional controls:

```text
hide/show diagonal
sort by absolute correlation
```

No p-value required unless already implemented cleanly.

---

# 5. P2 Implementation Details

---

## 5.1 P2-A — React-like app shell

### Goal

Make the Streamlit app feel closer to a modern React analytics dashboard.

### Design direction

```text
shorter header
sticky top filter summary
pill navigation
card-based panels
consistent section headers
more whitespace control
less default Streamlit feel
```

### CSS targets

Style:

```text
main container
sidebar
tabs
buttons
cards
metric cards
plot containers
download buttons
expanders
```

---

## 5.2 P2-B — Shorter header

Current header is good but tall.

V3 should use:

```text
compact hero header
```

Example:

```text
Mekong Delta Rice Dataset
Interactive EDA Dashboard
Raw dataset · 780 rows · 13 provinces · 1995–2024 · 2 seasons
```

Keep visual impact but reduce vertical height.

---

## 5.3 P2-C — Pill navigation

Replace or style Streamlit tabs to look like pill navigation.

Desired look:

```text
Overview | Map & Trend | Data Quality | Distribution | Correlation | Table
```

with:

```text
rounded pill background
active state
hover state
consistent icons
```

---

## 5.4 P2-D — Card containers for every chart

Every major panel should look like a card:

```text
title
subtitle/filter context
control row
chart body
footer/action row
```

Examples:

```text
Distribution
Variable: Năng suất · Scope: Current snapshot · Season: Đông Xuân

Data Quality
Missing target · 3 affected provinces · 31 missing rows
```

Keep subtitles short.

---

## 5.5 P2-E — Micro-interactions

Add subtle effects:

```text
card hover shadow
button hover transform
tab hover background
smooth chart transition
KPI card fade-in
loading spinner/skeleton
```

Do not add distracting animations.

---

# 6. Agent execution loop

The agent must not implement blindly. It must execute, validate, debug, and repeat.

## 6.1 Loop overview

For each phase:

```text
PLAN -> IMPLEMENT -> RUN CHECKS -> INSPECT ERRORS -> PATCH -> RE-RUN -> REPORT
```

Do not move to the next phase until the current phase passes its checks.

---

## 6.2 Global loop pseudo-code

```text
for phase in [P0, P1, P2]:
    create task checklist for phase
    for task in phase.tasks:
        implement smallest safe change
        run syntax checks
        run data validation checks
        run streamlit smoke check
        if failed:
            inspect traceback/log
            patch root cause
            rerun checks
        update V3 validation report
    run manual UI checklist for phase
    only proceed if phase acceptance criteria pass
```

---

## 6.3 Maximum retry rule

For each task:

```text
max_attempts = 3
```

If still failing after 3 attempts:

```text
revert or isolate the change
document blocker in reports/v3_validation_report.md
continue only if dashboard still runs
```

Do not leave app broken.

---

## 6.4 Required commands

From dashboard root:

```bash
cd d:\DS107_TuDuyTinhToan\dashboard
```

### Syntax checks

```bash
python -m py_compile app.py
python -m py_compile src/*.py
python -m py_compile src/components/*.py
```

If Windows shell does not expand wildcards, run explicit file list or use Python script:

```bash
python scripts/compile_check.py
```

### Data validation

Create:

```text
scripts/validate_dashboard_v3.py
```

It must check:

```text
rows = 780
provinces = 13
years = 30
seasons = 2
missing target rows = 31
complete target rows = 749
yield extreme outliers = 2
yield low warnings = 3
area outliers = 37
mean yield ≈ 5.318
GeoJSON match = 13/13
```

Run:

```bash
python scripts/validate_dashboard_v3.py
```

### Streamlit smoke check

Run:

```bash
streamlit run app.py --server.headless true --server.port 8501
```

Then check:

```bash
curl http://localhost:8501/_stcore/health
```

Expected:

```text
ok
```

Stop the Streamlit process after smoke check.

---

## 6.5 Optional visual smoke test

If browser automation is available:

```text
open localhost:8501
capture screenshots for:
  Overview
  Map & Trend
  Data Quality
  Distribution
  Correlation
  Data Table
```

Save screenshots:

```text
reports/screenshots/v3_overview.png
reports/screenshots/v3_map_trend.png
reports/screenshots/v3_data_quality.png
reports/screenshots/v3_distribution.png
reports/screenshots/v3_correlation.png
reports/screenshots/v3_data_table.png
```

---

# 7. Phase acceptance criteria

---

## 7.1 P0 acceptance criteria

P0 passes when:

```text
Data Quality opens with Coverage Summary, not raw heatmap
Missing by province bar chart exists and is sorted descending
Heatmap still exists and is sorted by missing count
Distribution has Scope control
Distribution default is context-aware
Current snapshot uses ranking/dot plot, not boxplot
Full period uses horizontal boxplot
Region filter affects all views and downloads
Province selector is compact
Validation dropdown is removed or moved
Download buttons are clear
All syntax/data/smoke checks pass
```

---

## 7.2 P1 acceptance criteria

P1 passes when:

```text
Selected provinces are highlighted on map
Map click selection works or is documented as unsupported with safe fallback
Year mode exists: Snapshot / Range / Animated
Animated map is user-triggered only
Trend shows selected-year marker
Correlation modes work: Core numeric, Weather only, Yield vs drivers
No panel crashes under empty filters
```

---

## 7.3 P2 acceptance criteria

P2 passes when:

```text
Dashboard looks like a polished analytics web app
Header is compact and professional
Tabs/pills look custom and clean
Charts sit inside consistent card containers
KPI cards and chart cards have consistent spacing/shadows
Sidebar/filter area is visually cleaner
Micro-interactions are subtle and not distracting
No long narrative text appears
```

---

# 8. Manual test flows

The agent must test these flows.

## Flow 1 — Bến Tre 2020 outlier

```text
Year = 2020
Season = dong_xuan
Province = Bến Tre
Metric = nang_suat
```

Expected:

```text
Bến Tre selected/highlighted
low yield visible
outlier flag visible
trend marker around 2020
special rows include Bến Tre 2020
```

---

## Flow 2 — Cà Mau missing

```text
Province = Cà Mau
Season = dong_xuan
Data Quality tab
```

Expected:

```text
missing summary shows Cà Mau affected
heatmap shows missing years
missing detail table has rows
```

---

## Flow 3 — Region filter correctness

```text
Remove Ven biển / rủi ro mặn
```

Expected:

```text
coastal provinces disappear from:
  province options
  map
  trend
  distribution
  correlation
  data table
  downloads
```

---

## Flow 4 — Distribution scope

```text
Distribution tab
Scope = Current snapshot
```

Expected:

```text
default chart = province ranking / dot plot
```

Then:

```text
Scope = Full period
```

Expected:

```text
default chart = horizontal boxplot by province + season
```

---

## Flow 5 — Data table downloads

```text
Data Table tab
Download filtered CSV
Download special rows CSV
```

Expected:

```text
filtered CSV matches current filters
special rows CSV contains only missing/outlier/warning rows
```

---

## Flow 6 — Animation mode

```text
Year mode = Animated
Click Play
```

Expected:

```text
map animates by year
user can pause/stop
dashboard does not freeze
```

If animation cannot be implemented cleanly:

```text
document as deferred
dashboard remains stable
```

---

# 9. Required report file

Agent must produce:

```text
reports/v3_validation_report.md
```

Include:

```text
implemented changes
files modified
checks run
pass/fail status
known limitations
screenshots if available
manual test flow results
```

Template:

```markdown
# V3 Validation Report

## Summary
...

## Files Modified
...

## Automated Checks
| Check | Status | Notes |
|---|---|---|

## Data Validation
| Metric | Expected | Actual | Status |
|---|---:|---:|---|

## Manual UI Flows
| Flow | Status | Notes |
|---|---|---|

## Known Limitations
...

## Next Suggested Improvements
...
```

---

# 10. Final definition of done

V3 is complete only if:

```text
1. App runs without error.
2. P0 acceptance criteria pass.
3. P1 acceptance criteria pass or unsupported features are documented with safe fallback.
4. P2 visual polish is applied.
5. Data validation expected values match.
6. Streamlit smoke check passes.
7. reports/v3_validation_report.md exists.
8. No long report-like narratives are added.
9. No local file paths are exposed in UI.
10. Dashboard remains usable if map click or animation is unsupported.
```

---

# 11. Final instruction to agent

Work in small safe patches.

Never leave the dashboard broken.

Prefer:

```text
correctness
stability
professional UI
clear defaults
clean interactions
```

over:

```text
complex hacks
heavy custom JavaScript
animation for its own sake
full rewrite
```

If a feature is technically unstable in Streamlit, implement a safe fallback and document it.
