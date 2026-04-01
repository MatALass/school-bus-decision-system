"""UI helpers for consistent analytical narration."""

from __future__ import annotations

import streamlit as st


LABEL_PRESETS = {
    "reading": ("Reading", "Decision angle"),
    "signal": ("Signal", "What it suggests"),
    "pattern": ("Pattern", "Why it matters"),
    "benchmark": ("Benchmark", "Interpretation"),
    "focus": ("Focus", "What to do with it"),
    "risk": ("Risk", "Strategic implication"),
}


def explain_chart(
    observation: str,
    implication: str,
    preset: str = "reading",
) -> None:
    """Render a compact analytical explanation below a chart."""
    label_left, label_right = LABEL_PRESETS.get(preset, LABEL_PRESETS["reading"])
    st.markdown(
        f"""
<div class="chart-note">
    <div><strong>{label_left}.</strong> {observation}</div>
    <div><strong>{label_right}.</strong> {implication}</div>
</div>
""",
        unsafe_allow_html=True,
    )


def section_intro(text: str) -> None:
    st.markdown(f"<div class='section-intro'>{text}</div>", unsafe_allow_html=True)


def page_story(kpi_title: str, kpi_value: str, observation: str, implication: str) -> None:
    """Narrative block used near the top of pages."""
    st.markdown(
        f"""
<div class="story-grid">
    <div class="story-card">
        <div class="story-label">KPI</div>
        <div class="story-value">{kpi_value}</div>
        <div class="story-text">{kpi_title}</div>
    </div>
    <div class="story-card">
        <div class="story-label">Key finding</div>
        <div class="story-text">{observation}</div>
    </div>
    <div class="story-card">
        <div class="story-label">Decision implication</div>
        <div class="story-text">{implication}</div>
    </div>
</div>
""",
        unsafe_allow_html=True,
    )


def hero(title: str, body: str) -> None:
    st.markdown(
        f"""
<div class="hero">
    <h1>{title}</h1>
    <p>{body}</p>
</div>
""",
        unsafe_allow_html=True,
    )


def insight_cards(items: list[tuple[str, str, str]]) -> None:
    cards = []
    for title, main, body in items:
        cards.append(
            f"""
<div class="insight-card">
    <div class="insight-title">{title}</div>
    <div class="insight-main">{main}</div>
    <div class="insight-body">{body}</div>
</div>
"""
        )
    html = "<div class='insight-grid'>" + "".join(cards) + "</div>"
    st.markdown(html, unsafe_allow_html=True)


def recommendation_card(step: str, title: str, text: str) -> None:
    st.markdown(
        f"""
<div class="rec-card">
    <div class="rec-step">{step}</div>
    <div class="rec-title">{title}</div>
    <div class="rec-text">{text}</div>
</div>
""",
        unsafe_allow_html=True,
    )
