import streamlit as st

from components.style_loader import load_css
from review_themes import theme_cluster_reviews

from review_explorer import (
    get_review_dataset,
    filter_reviews,
    get_review_stats,
    build_review_summary,
)

from sections.review_explorer import render as review_explorer


st.set_page_config(
    page_title="Review Explorer",
    page_icon="🔎",
    layout="wide",
)

load_css()

review_explorer(
    get_review_dataset,
    filter_reviews,
    get_review_stats,
    build_review_summary,
    theme_cluster_reviews,
)