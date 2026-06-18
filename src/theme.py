"""V2 Dashboard design system — CSS, card helpers, Plotly theme."""
from __future__ import annotations

import streamlit as st
import plotly.graph_objects as go

# ---------------------------------------------------------------------------
# Region color palette (used by map + charts)
# ---------------------------------------------------------------------------
REGION_COLORS: dict[str, str] = {
    "Thượng nguồn / vựa lúa": "#16A34A",
    "Ven biển / rủi ro mặn": "#0EA5E9",
    "Trung tâm / nội đồng": "#F97316",
}

# Metric → Plotly color scale
METRIC_COLORSCALES: dict[str, str | list] = {
    "nang_suat": "Teal",
    "dien_tich": "Blues",
    "san_luong": "YlOrBr",
    "missing_target": "Greys",
    "region": [[0, "#16A34A"], [0.5, "#0EA5E9"], [1.0, "#F97316"]],
}


# ---------------------------------------------------------------------------
# CSS injection
# ---------------------------------------------------------------------------
_V2_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

:root {
  --bg-main: #F4F1E8;
  --panel-bg: #FFFFFF;
  --panel-border: #E8E5DC;
  --text-main: #111827;
  --text-muted: #6B7280;
  --primary: #14B8A6;
  --primary-dark: #0F4C45;
  --accent: #22C7D6;
  --danger: #D97706;
  --upstream: #16A34A;
  --coastal: #0EA5E9;
  --center: #F97316;
  --shadow-card: 0 8px 24px rgba(15, 23, 42, 0.065);
  --radius-lg: 20px;
  --radius-md: 18px;
}

html, body, [class*="css"] {
  font-family: 'Inter', ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
}

/* ---------- page background ---------- */
.stApp {
  background: var(--bg-main) !important;
}

.block-container {
  padding-top: 0.85rem !important;
  padding-bottom: 1rem !important;
  padding-left: 1.05rem !important;
  padding-right: 1.05rem !important;
  max-width: 100% !important;
}

[data-testid="stVerticalBlock"] {
  gap: 0.5rem !important;
}

[data-testid="stHorizontalBlock"] {
  gap: 0.6rem !important;
}

[data-testid="column"] > div {
  gap: 0.46rem !important;
}

/* ---------- sidebar ---------- */
section[data-testid="stSidebar"] {
  background: #FFFFFF !important;
  border-right: 1px solid var(--panel-border);
}
section[data-testid="stSidebar"] .stMarkdown h3 {
  font-size: 0.78rem;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: var(--text-muted);
  margin: 1.1rem 0 0.35rem 0;
  padding: 0;
}

/* ---------- KPI card ---------- */
.kpi-row {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
  margin: 0.18rem 0 0.95rem;
}
.kpi-card {
  flex: 1 1 140px;
  background: var(--panel-bg);
  border: 1px solid var(--panel-border);
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-card);
  padding: 12px 16px 11px;
  min-width: 140px;
  min-height: 84px;
}
.kpi-label {
  font-size: 0.68rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  color: var(--text-muted);
  margin: 0 0 4px 0;
}
.kpi-value {
  font-size: 1.18rem;
  font-weight: 700;
  color: var(--text-main);
  line-height: 1.15;
  margin: 0;
}
.kpi-unit {
  font-size: 0.72rem;
  color: var(--text-muted);
  margin: 2px 0 0 0;
}

/* ---------- header ---------- */
.v2-header {
  background: linear-gradient(135deg, #0F4C45 0%, #0B6B61 100%);
  border-radius: var(--radius-lg);
  padding: 14px 20px 12px;
  margin-bottom: 0.7rem;
  color: #fff;
}
.v2-header h1 {
  font-size: 1.32rem;
  font-weight: 800;
  margin: 0 0 2px 0;
  letter-spacing: -0.01em;
}
.v2-header p {
  font-size: 0.88rem;
  font-weight: 500;
  opacity: 0.85;
  margin: 0;
}
.v2-badges {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  margin-top: 7px;
}
.v2-badge {
  background: rgba(255,255,255,0.15);
  backdrop-filter: blur(4px);
  border-radius: 20px;
  padding: 3px 12px;
  font-size: 0.72rem;
  font-weight: 500;
  color: #fff;
  letter-spacing: 0.01em;
}

/* ---------- filter summary ---------- */
.filter-bar {
  display: flex;
  gap: 8px;
  row-gap: 7px;
  flex-wrap: wrap;
  align-items: center;
  min-height: 2.12rem;
  padding: 0 0 0.38rem;
  margin: 0 0 0.65rem;
  position: relative;
  z-index: 1;
}
.filter-chip {
  background: #DDF7F3;
  color: #0F4C45;
  border-radius: 14px;
  padding: 4px 12px;
  font-size: 0.72rem;
  font-weight: 500;
  line-height: 1.15;
  white-space: nowrap;
}

/* ---------- province detail card ---------- */
.detail-card {
  background: var(--panel-bg);
  border: 1px solid var(--panel-border);
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-card);
  padding: 18px 20px;
}
.detail-card h4 {
  margin: 0 0 10px 0;
  font-size: 1.05rem;
  font-weight: 700;
  color: var(--text-main);
}
.detail-row {
  display: flex;
  justify-content: space-between;
  padding: 5px 0;
  border-bottom: 1px solid #F3F4F6;
  font-size: 0.82rem;
}
.detail-row:last-child { border-bottom: none; }
.detail-label { color: var(--text-muted); font-weight: 500; }
.detail-value { color: var(--text-main); font-weight: 600; }

/* ---------- sub-tab styling ---------- */
.stTabs [data-baseweb="tab-list"] {
  gap: 0px;
  background: var(--panel-bg);
  border-radius: var(--radius-md) var(--radius-md) 0 0;
  border: 1px solid var(--panel-border);
  border-bottom: none;
  padding: 0 8px;
}
.stTabs [data-baseweb="tab"] {
  padding: 10px 20px;
  font-size: 0.82rem;
  font-weight: 600;
  border-radius: 0;
}
.stTabs [aria-selected="true"] {
  border-bottom: 2.5px solid var(--primary) !important;
  color: var(--primary) !important;
}

/* ---------- empty state ---------- */
.empty-state {
  text-align: center;
  padding: 20px 12px;
  color: var(--text-muted);
  font-size: 0.85rem;
}
.empty-state .icon { font-size: 1.6rem; margin-bottom: 8px; }

/* ---------- hide default metric padding ---------- */
[data-testid="stMetric"] { display: none; }

/* ---------- section card wrapper ---------- */
[data-testid="stVerticalBlockBorderWrapper"] {
  background: var(--panel-bg);
  border: 1px solid var(--panel-border) !important;
  border-radius: var(--radius-md) !important;
  box-shadow: var(--shadow-card) !important;
  padding: 10px !important;
}
[data-testid="stVerticalBlockBorderWrapper"]:hover {
  box-shadow: var(--shadow-card) !important;
}

[data-testid="stMarkdownContainer"] h4 {
  margin: 0 0 0.18rem 0 !important;
}

div[data-baseweb="select"] > div {
  min-height: 2.12rem !important;
}

label[data-testid="stWidgetLabel"] {
  min-height: 1rem !important;
  margin-bottom: 0.08rem !important;
}

[data-testid="stPlotlyChart"] {
  margin-top: -0.1rem !important;
}

.mini-stat-row {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 8px;
  margin: 0.2rem 0 0.38rem;
}
.mini-stat {
  border: 1px solid var(--panel-border);
  border-radius: 14px;
  background: #FFFFFF;
  padding: 7px 10px;
}
.mini-stat-label {
  color: var(--text-muted);
  font-size: 0.66rem;
  font-weight: 700;
  letter-spacing: 0.04em;
  text-transform: uppercase;
}
.mini-stat-value {
  color: var(--text-main);
  font-size: 0.98rem;
  font-weight: 800;
  line-height: 1.2;
}
</style>
"""


def inject_custom_css() -> None:
    """Inject the V2 CSS design system into the page."""
    st.markdown(_V2_CSS, unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# KPI card HTML
# ---------------------------------------------------------------------------
def kpi_card_html(label: str, value: str, unit: str = "") -> str:
    unit_html = f'<p class="kpi-unit">{unit}</p>' if unit else ""
    return (
        f'<div class="kpi-card">'
        f'<p class="kpi-label">{label}</p>'
        f'<p class="kpi-value">{value}</p>'
        f'{unit_html}'
        f'</div>'
    )


def render_kpi_row(cards: list[str]) -> None:
    """Render a row of KPI card HTMLs."""
    html = '<div class="kpi-row">' + "".join(cards) + "</div>"
    st.markdown(html, unsafe_allow_html=True)


def render_mini_stats(items: list[tuple[str, str]]) -> None:
    html = '<div class="mini-stat-row">' + "".join(
        f'<div class="mini-stat">'
        f'<div class="mini-stat-label">{label}</div>'
        f'<div class="mini-stat-value">{value}</div>'
        f'</div>'
        for label, value in items
    ) + "</div>"
    st.markdown(html, unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------
def render_header(row_count: int, province_count: int, year_min: int, year_max: int, season_count: int) -> None:
    badges = [
        "Raw dataset",
        f"{row_count:,} rows",
        f"{province_count} provinces",
        f"{year_min}–{year_max}",
        f"{season_count} seasons",
    ]
    badges_html = "".join(f'<span class="v2-badge">{b}</span>' for b in badges)
    html = (
        '<div class="v2-header">'
        '<h1>🌾 Mekong Delta Rice Dataset</h1>'
        '<p>Interactive EDA Dashboard</p>'
        f'<div class="v2-badges">{badges_html}</div>'
        '</div>'
    )
    st.markdown(html, unsafe_allow_html=True)


def render_header(row_count: int, province_count: int, year_min: int, year_max: int, season_count: int) -> None:
    badges = [
        "Raw dataset",
        f"{row_count:,} rows",
        f"{province_count} provinces",
        f"{year_min}-{year_max}",
        f"{season_count} seasons",
    ]
    badges_html = "".join(f'<span class="v2-badge">{badge}</span>' for badge in badges)
    html = (
        '<div class="v2-header">'
        '<h1>Mekong Delta Rice Dashboard</h1>'
        '<p>Rice yield, weather, and production overview across 13 provinces, 1995-2024.</p>'
        f'<div class="v2-badges">{badges_html}</div>'
        '</div>'
    )
    st.markdown(html, unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Active filter summary
# ---------------------------------------------------------------------------
def render_filter_summary(
    year: int | tuple[int, int],
    season: str,
    metric_label: str,
    region_count: int,
    province_count: int,
    region_total: int | None = None,
    province_total: int | None = None,
    focused_provinces: tuple[str, ...] = (),
) -> None:
    year_chip = f"Year range: {year[0]}-{year[1]}" if isinstance(year, tuple) else f"Year: {year}"
    region_chip = "Regions: All" if region_total and region_count == region_total else f"Regions: {region_count}"
    province_chip = (
        f"Provinces: {province_total}"
        if province_total and province_count == province_total
        else f"Provinces: {province_count}"
    )
    chips = [
        year_chip,
        f"Season: {season}",
        f"Metric: {metric_label}",
        region_chip,
        province_chip,
    ]
    if focused_provinces:
        focused = ", ".join(focused_provinces[:3])
        if len(focused_provinces) > 3:
            focused = f"{focused} +{len(focused_provinces) - 3}"
        chips.append(f"Selected provinces: {focused}")
    html = '<div class="filter-bar">' + "".join(
        f'<span class="filter-chip">{c}</span>' for c in chips
    ) + "</div>"
    st.markdown(html, unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Province detail card
# ---------------------------------------------------------------------------
def render_detail_card(title: str, rows: list[tuple[str, str]]) -> None:
    rows_html = "".join(
        f'<div class="detail-row">'
        f'<span class="detail-label">{label}</span>'
        f'<span class="detail-value">{value}</span>'
        f'</div>'
        for label, value in rows
    )
    html = (
        f'<div class="detail-card">'
        f'<h4>{title}</h4>'
        f'{rows_html}'
        f'</div>'
    )
    st.markdown(html, unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Empty state
# ---------------------------------------------------------------------------
def render_empty_state(message: str, icon: str = "📭") -> None:
    st.markdown(
        f'<div class="empty-state">'
        f'<div class="icon">{icon}</div>'
        f'<div>{message}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# Shared Plotly theme
# ---------------------------------------------------------------------------
def apply_plotly_theme(fig: go.Figure, height: int | None = None) -> go.Figure:
    """Apply V2 Plotly visual standards to any figure."""
    fig.update_layout(
        template="plotly_white",
        paper_bgcolor="#FFFFFF",
        plot_bgcolor="#FFFFFF",
        font=dict(family="Inter, system-ui, sans-serif", color="#4B5563", size=12),
        title=dict(text=""),
        margin=dict(l=20, r=20, t=35, b=25),
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


def apply_dashboard_theme(fig: go.Figure, height: int = 360, show_legend: bool = True) -> go.Figure:
    apply_plotly_theme(fig, height=height)
    fig.update_layout(showlegend=show_legend)
    return fig
