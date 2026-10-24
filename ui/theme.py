"""Shared dark trading-terminal visual system for the read-only research UI."""

from __future__ import annotations

import streamlit as st

TRADING_DESK_CSS = """
<style>
:root { color-scheme: dark; }
.block-container { max-width: 1680px; padding-top: 1.15rem; padding-bottom: 2.5rem; }
[data-testid="stSidebar"] { background: #131a24; border-right: 1px solid #293342; }
[data-testid="stSidebar"] * { color: #dce5ef; }
[data-testid="stHeader"] { background: rgba(16, 21, 29, .88); }
[data-testid="stMetric"] { background: #181f2a; border: 1px solid #2b3544; border-radius: 9px; padding: .7rem .85rem; }
[data-testid="stMetricLabel"] { color: #9baabd; font-size: .76rem; }
[data-testid="stMetricValue"] { color: #e7edf5; font-variant-numeric: tabular-nums; }
[data-testid="stDataFrame"] { border: 1px solid #2b3544; border-radius: 8px; overflow: hidden; }
[data-testid="stAlert"] { border-radius: 8px; }
[data-testid="stTabs"] button { color: #9baabd; }
[data-testid="stTabs"] button[aria-selected="true"] { color: #78c8b8; border-bottom-color: #61b8a8; }
[data-testid="stSelectbox"] label, [data-testid="stMultiSelect"] label,
[data-testid="stDateInput"] label, [data-testid="stSlider"] label { color: #aeb9c8; }
[data-testid="stButton"] button { border-radius: 7px; border-color: #384657; }
.hero { padding: 1rem 1.2rem; border: 1px solid #303c4d; border-radius: 10px; background: linear-gradient(120deg, #1a2431, #161e29); margin-bottom: 1rem; }
.eyebrow { font-size: .7rem; letter-spacing: .12em; text-transform: uppercase; color: #78c8b8; font-weight: 700; }
.hero h1 { margin: .2rem 0; color: #edf2f8; font-size: 1.8rem; }
.hero p { margin: 0; color: #aab6c6; }
.status-pill { display: inline-block; padding: .18rem .55rem; border-radius: 999px; font-size: .75rem; font-weight: 700; background: #263342; color: #c6d2df; }
.status-pill.good { background: #17372f; color: #8ad5bd; }
.status-pill.warn { background: #3b3020; color: #edc47b; }
.status-pill.bad { background: #40272a; color: #ef9b9b; }
.freshness-badge { color: #9eacbe; font-size: .78rem; }
hr { border-color: #2b3544; }
</style>
"""


def apply_theme() -> None:
    """Apply shared styles and use Plotly's readable dark chart template."""
    import plotly.io as pio

    pio.templates.default = "plotly_dark"
    st.markdown(TRADING_DESK_CSS, unsafe_allow_html=True)
