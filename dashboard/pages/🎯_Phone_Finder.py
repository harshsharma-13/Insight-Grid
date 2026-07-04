import streamlit as st

from components.style_loader import load_css
from components.ui.navbar import navbar

from phone_finder import (
    get_phone_finder_dataset,
    recommend_by_use_case,
    recommend_by_budget,
    get_phone_reason,
    get_phone_warning,
    build_use_case_summary,
    build_budget_summary,
)

from sections.phone_finder import (
    render as phone_finder
)


st.set_page_config(
    page_title="Phone Finder",
    page_icon="🎯",
    layout="wide",
)

load_css()

navbar()


phone_finder(
    get_phone_finder_dataset,
    recommend_by_use_case,
    recommend_by_budget,
    get_phone_reason,
    get_phone_warning,
    build_use_case_summary,
    build_budget_summary,
)