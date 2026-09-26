import streamlit as st

from components.style_loader import load_css
from components.ui.navbar import navbar
from product_actions import get_action_dataset, get_action_summary
from sections.product_action_center import render as product_action_center


st.set_page_config(
    page_title="Product Action Center",
    page_icon="🛠️",
    layout="wide",
)

load_css()

navbar("actions")

product_action_center(
    get_action_dataset,
    get_action_summary,
)
