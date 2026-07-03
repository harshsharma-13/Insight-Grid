import streamlit as st
import plotly.express as px


def render_market_snapshot(verdict_df, brand_df, top_df):
    left, right = st.columns(2)

    with left:
        st.subheader("Consumer Verdict Distribution")
        fig = px.bar(
            verdict_df,
            x="consumer_verdict",
            y="count",
            text="count",
        )
        st.plotly_chart(fig, use_container_width=True)

    with right:
        st.subheader("Brand Portfolio")
        fig = px.pie(
            brand_df,
            names="brand",
            values="count",
        )
        st.plotly_chart(fig, use_container_width=True)

    st.subheader("Top Performing Smartphones")
    st.dataframe(top_df, use_container_width=True)