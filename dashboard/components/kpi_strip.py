import streamlit as st
from components.ui_cards import info_card


def render_kpi_strip(kpis):
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        info_card("Total Phones", kpis["total_phones"], "📱")

    with col2:
        info_card("Total Reviews", kpis["total_reviews"], "💬")

    with col3:
        info_card("AI Insights", kpis["phones_with_insights"], "🤖")

    with col4:
        info_card("Avg Positive Sentiment", f'{kpis["avg_positive"]}%', "😊")