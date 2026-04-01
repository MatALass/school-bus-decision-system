"""Electric School Bus Decision System"""

from pathlib import Path
import sys

import streamlit as st

ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT))

st.set_page_config(
    page_title="Electric School Bus Decision System",
    page_icon="ESB",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
<style>
    .block-container {
        padding-top: 1.1rem;
        padding-bottom: 2rem;
        max-width: 1420px;
    }
    [data-testid="metric-container"] {
        background: linear-gradient(180deg, #ffffff 0%, #f8fafc 100%);
        border: 1px solid #e2e8f0;
        border-radius: 18px;
        padding: 0.9rem;
        box-shadow: 0 8px 30px rgba(15, 23, 42, 0.05);
    }
    [data-testid="metric-container"] label {
        color: #64748b !important;
        font-size: 0.8rem !important;
    }
    .section-intro {
        background: linear-gradient(135deg, #f8fafc 0%, #ffffff 100%);
        border: 1px solid #e2e8f0;
        border-radius: 18px;
        padding: 1rem 1.1rem;
        margin-bottom: 1rem;
        color: #334155;
        line-height: 1.55;
    }
    .chart-note {
        background: linear-gradient(180deg, #ffffff 0%, #fbfdff 100%);
        border: 1px solid #dbeafe;
        border-left: 4px solid #0f766e;
        border-radius: 14px;
        padding: 0.9rem 1rem;
        margin-top: 0.45rem;
        margin-bottom: 1rem;
        font-size: 0.95rem;
        color: #334155;
        box-shadow: 0 6px 18px rgba(15, 23, 42, 0.04);
    }
    .chart-note div + div { margin-top: 0.35rem; }
    .story-grid {
        display: grid;
        grid-template-columns: 1.05fr 1.25fr 1.25fr;
        gap: 0.95rem;
        margin: 0.2rem 0 1rem 0;
    }
    .story-card,
    .insight-card,
    .rec-card,
    .mini-panel {
        background: linear-gradient(180deg, #ffffff 0%, #f8fafc 100%);
        border: 1px solid #e2e8f0;
        border-radius: 18px;
        padding: 1rem 1.05rem;
        box-shadow: 0 8px 26px rgba(15, 23, 42, 0.05);
    }
    .story-card { min-height: 132px; }
    .story-label,
    .insight-title,
    .rec-step,
    .mini-label {
        font-size: 0.75rem;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        color: #0f766e;
        font-weight: 800;
        margin-bottom: 0.45rem;
    }
    .story-value {
        font-size: 1.85rem;
        line-height: 1.08;
        font-weight: 800;
        color: #0f172a;
        margin-bottom: 0.28rem;
    }
    .story-text,
    .insight-body,
    .rec-text,
    .mini-text {
        font-size: 0.95rem;
        color: #334155;
        line-height: 1.5;
    }
    .hero {
        background: radial-gradient(circle at top left, rgba(20,184,166,0.16), transparent 36%),
                    radial-gradient(circle at bottom right, rgba(59,130,246,0.12), transparent 28%),
                    linear-gradient(135deg, #0f172a 0%, #172554 45%, #0f766e 100%);
        color: white;
        border-radius: 24px;
        padding: 1.45rem 1.45rem 1.25rem 1.45rem;
        margin-bottom: 1rem;
        box-shadow: 0 18px 44px rgba(15, 23, 42, 0.2);
    }
    .hero h1 {
        margin: 0 0 0.35rem 0;
        font-size: 2.05rem;
        line-height: 1.08;
    }
    .hero p {
        margin: 0;
        color: rgba(255,255,255,0.9);
        max-width: 980px;
        font-size: 1rem;
        line-height: 1.58;
    }
    .insight-grid {
        display: grid;
        grid-template-columns: repeat(3, minmax(0, 1fr));
        gap: 0.95rem;
        margin: 0.3rem 0 1rem 0;
    }
    .insight-main {
        font-size: 1.35rem;
        font-weight: 800;
        color: #0f172a;
        margin-bottom: 0.35rem;
    }
    .rec-title {
        font-size: 1.06rem;
        font-weight: 800;
        color: #0f172a;
        margin-bottom: 0.35rem;
    }
    .sidebar-panel {
        background: linear-gradient(180deg, #ffffff 0%, #f8fafc 100%);
        border: 1px solid #e2e8f0;
        border-radius: 18px;
        padding: 0.95rem 1rem;
        box-shadow: 0 6px 20px rgba(15, 23, 42, 0.04);
    }
    .sidebar-kicker {
        display: inline-block;
        padding: 0.26rem 0.55rem;
        border-radius: 999px;
        background: #dcfce7;
        color: #166534;
        font-size: 0.72rem;
        font-weight: 800;
        letter-spacing: 0.04em;
        text-transform: uppercase;
        margin-bottom: 0.55rem;
    }
    .sidebar-meta {
        color: #475569;
        font-size: 0.92rem;
        line-height: 1.48;
    }
    .mini-grid {
        display: grid;
        grid-template-columns: repeat(2, minmax(0, 1fr));
        gap: 0.85rem;
        margin-bottom: 0.9rem;
    }
    @media (max-width: 1000px) {
        .story-grid,
        .insight-grid,
        .mini-grid { grid-template-columns: 1fr; }
    }
</style>
""",
    unsafe_allow_html=True,
)

with st.sidebar:
    st.markdown(
        """
<div class="sidebar-panel">
    <div style="font-size:1.2rem; font-weight:800; color:#0f172a; margin-bottom:0.35rem;">Electric School Bus Decision System</div>
    <div class="sidebar-meta"><strong>Author</strong><br>Mathieu Alassoeur</div>
    <div class="sidebar-meta" style="margin-top:0.55rem;">Decision-oriented analytics project built from the World Resources Institute electric school bus workbook. The objective is not to show every chart available in the data, but to surface a small set of defensible insights and a transparent prioritization logic.</div>
</div>
""",
        unsafe_allow_html=True,
    )
    st.divider()

    page = st.radio(
        "Navigation",
        options=[
            "Executive briefing",
            "Strategy and inequity",
            "Decision engine",
            "District deep dive",
            "Market and ecosystem",
            "Methodology and caveats",
        ],
        label_visibility="visible",
    )

    st.divider()
    st.caption("Source workbook: World Resources Institute — Electric School Bus Initiative")

if page == "Executive briefing":
    from pages.executive import render
elif page == "Strategy and inequity":
    from pages.equity import render
elif page == "Decision engine":
    from pages.decision_engine import render
elif page == "District deep dive":
    from pages.district_explorer import render
elif page == "Market and ecosystem":
    from pages.fleet_tech import render
else:
    from pages.methodology import render

render()
