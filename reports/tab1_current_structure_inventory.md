# Tab 1 Current Structure Inventory

## Current Entry Point
- `dashboard/app.py` renders a single-page dashboard with header, filter chips, KPI strip, map/ranking, trend, distribution, data completeness, driver relationship, and a collapsed data table section.
- No old top-level EDA section radio is present.

## Current Sidebar
- Sidebar uses a form in `dashboard/src/components/filters.py`.
- Current defaults before this patch are Snapshot, latest year, `dong_xuan`, all regions, all provinces, and a visible missing-target row toggle.
- Primary metric was removed from the sidebar in the previous pass and needs to return as a global DATA filter.

## Current Main Canvas
- Top row: map card plus province ranking card.
- Second row: trend, distribution, and data completeness cards.
- Data completeness is still a visible main-grid card, which conflicts with the final card-mosaic plan.
- Data table is collapsed and lazy-loaded.

## Current Interactions
- Ranking uses native Streamlit Plotly selection and stores focused provinces in `interactive_selected_provinces`.
- Map selection is disabled for fullscreen stability.
- Selected provinces are highlighted in ranking and map boundaries.

## Required Changes From New Plan
- Change initial defaults to Range 1995-2024, Season All, Metric yield, all regions, all provinces.
- Remove visible global missing-target toggle.
- Add a right-column Season Comparison card under Province Ranking.
- Keep exactly five KPI cards and include Year / Year range.
- Move missing-target details to the bottom collapsed section.
- Make map the largest card with 500-540 px height and ranking/season comparison stacked on the right.
