import streamlit as st

from components.style_loader import load_css
from components.ui.navbar import navbar

from competitive_intelligence import (
    get_competitive_dataset,
    brand_leaderboard,
    brand_scorecards,
    segment_leaders,
    whitespace_opportunities,
    build_competitive_summary,
    compare_brands,
    build_competitive_recommendation,
)

from sections.competitive_intelligence import (
    render as competitive_intelligence
)


st.set_page_config(
    page_title="Competitive Intelligence",
    page_icon="🏆",
    layout="wide",
)

load_css()

navbar()


competitive_intelligence(
    get_competitive_dataset,
    brand_leaderboard,
    brand_scorecards,
    segment_leaders,
    whitespace_opportunities,
    build_competitive_summary,
    compare_brands,
    build_competitive_recommendation,
)