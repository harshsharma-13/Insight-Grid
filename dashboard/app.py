import streamlit as st
import plotly.express as px

from config import APP_TITLE, APP_SUBTITLE, DEFAULT_PAGE_ICON
from dashboard_data import (
    get_kpis,
    get_verdict_distribution,
    get_top_phones,
    get_brand_distribution,
)
from components.cards import kpi_card


st.set_page_config(
    page_title=APP_TITLE,
    page_icon=DEFAULT_PAGE_ICON,
    layout="wide",
)

st.title(APP_TITLE)
st.caption(APP_SUBTITLE)

st.divider()

kpis = get_kpis()

col1, col2, col3, col4 = st.columns(4)

with col1:
    kpi_card("Total Phones", kpis["total_phones"])

with col2:
    kpi_card("Total Reviews", kpis["total_reviews"])

with col3:
    kpi_card("AI Insights Generated", kpis["phones_with_insights"])

with col4:
    kpi_card("Average Positive Sentiment", f'{kpis["avg_positive"]}%')

st.divider()

left, right = st.columns(2)

with left:
    st.subheader("Consumer Verdict Distribution")
    verdict_df = get_verdict_distribution()
    fig = px.bar(
        verdict_df,
        x="consumer_verdict",
        y="count",
        text="count",
    )
    st.plotly_chart(fig, use_container_width=True)

with right:
    st.subheader("Brand Distribution")
    brand_df = get_brand_distribution()
    fig = px.pie(
        brand_df,
        names="brand",
        values="count",
    )
    st.plotly_chart(fig, use_container_width=True)

st.divider()

st.subheader("Top Phones by Positive Sentiment")
top_df = get_top_phones(10)
st.dataframe(top_df, use_container_width=True)