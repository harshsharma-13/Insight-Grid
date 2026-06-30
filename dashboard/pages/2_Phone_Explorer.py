from pathlib import Path
import pandas as pd
import streamlit as st
import plotly.express as px

from dashboard_data import (
    get_phone_options,
    get_phone_catalog,
    get_phone_ai_insight,
    get_phone_sentiment_summary,
    get_phone_platform_summary,
)

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

st.set_page_config(
    page_title="Phone Explorer",
    page_icon="📱",
    layout="wide",
)


def clean(value):
    if value is None:
        return "Not available"

    if pd.isna(value):
        return "Not available"

    value = str(value).strip()

    if value == "" or value.lower() == "nan":
        return "Not available"

    return value


def render_list(text, icon):
    items = str(text).split(";")

    for item in items:
        item = item.strip()
        if item:
            st.markdown(f"{icon} {item}")


def metric_or_text(label, value):
    value = clean(value)
    st.metric(label, value)


st.title("📱 Phone Explorer")
st.caption("Product specifications, prices, AI insights, sentiment, and platform comparison")

phones = get_phone_options()
phone_map = dict(zip(phones["phone_name"], phones["phone_id"]))

selected_phone = st.selectbox(
    "Search / Select Phone",
    list(phone_map.keys())
)

phone_id = phone_map[selected_phone]

catalog = get_phone_catalog(phone_id)
insight = get_phone_ai_insight(phone_id)
summary = get_phone_sentiment_summary(phone_id)
platforms = get_phone_platform_summary(phone_id)

catalog_row = catalog.iloc[0] if not catalog.empty else None
insight_row = insight.iloc[0] if not insight.empty else None
summary_row = summary.iloc[0] if not summary.empty else None

left, right = st.columns([1, 2])

with left:
    if catalog_row is not None and clean(catalog_row.get("image_local_path")) != "Not available":
        image_path = PROJECT_ROOT / catalog_row["image_local_path"]

        if image_path.exists():
            st.image(str(image_path), use_container_width=True)
        else:
            st.info("Image file not found")
    else:
        st.info("Image not available")

    if catalog_row is not None and clean(catalog_row.get("smartprix_link")) != "Not available":
        st.link_button("Open Smartprix Page", catalog_row["smartprix_link"])

with right:
    st.subheader(selected_phone)

    if catalog_row is not None:
        st.markdown(f"**Brand:** {clean(catalog_row.get('brand'))}")
        st.markdown(f"**Launch Date:** {clean(catalog_row.get('launch_date'))}")
        st.markdown(f"**Price Segment:** {clean(catalog_row.get('price_segment'))}")

        price_col1, price_col2 = st.columns(2)

        with price_col1:
            metric_or_text("Flipkart Price", catalog_row.get("flipkart_price"))
            metric_or_text("Flipkart Rating", catalog_row.get("flipkart_rating"))

        with price_col2:
            metric_or_text("Amazon Price", catalog_row.get("amazon_price"))
            metric_or_text("Amazon Rating", catalog_row.get("amazon_rating"))

    if insight_row is not None:
        st.success(f"Consumer Verdict: {clean(insight_row.get('consumer_verdict'))}")

        info_col1, info_col2 = st.columns(2)
        with info_col1:
            metric_or_text("Insight Confidence", insight_row.get("insight_confidence"))
        with info_col2:
            metric_or_text("Review Count", insight_row.get("review_count"))

st.divider()

st.subheader("Specifications")

if catalog_row is not None:
    spec_col1, spec_col2 = st.columns(2)

    with spec_col1:
        st.markdown(f"**Display:** {clean(catalog_row.get('display'))}")
        st.markdown(f"**Refresh Rate:** {clean(catalog_row.get('refresh_rate'))}")
        st.markdown(f"**Processor:** {clean(catalog_row.get('processor'))}")
        st.markdown(f"**Chipset Brand:** {clean(catalog_row.get('chipset_brand'))}")
        st.markdown(f"**RAM:** {clean(catalog_row.get('ram'))}")
        st.markdown(f"**Storage:** {clean(catalog_row.get('storage'))}")

    with spec_col2:
        st.markdown(f"**Battery:** {clean(catalog_row.get('battery'))}")
        st.markdown(f"**Charging:** {clean(catalog_row.get('charging'))}")
        st.markdown(f"**Rear Camera:** {clean(catalog_row.get('rear_camera'))}")
        st.markdown(f"**Front Camera:** {clean(catalog_row.get('front_camera'))}")
        st.markdown(f"**Android Version:** {clean(catalog_row.get('android_version'))}")
else:
    st.info("No product catalog available for this phone.")

st.divider()

if insight_row is not None:
    st.subheader("AI Executive Summary")
    st.write(clean(insight_row.get("executive_summary")))

    insight_col1, insight_col2 = st.columns(2)

    with insight_col1:
        st.subheader("Top Strengths")
        render_list(insight_row.get("top_strengths"), "✅")

    with insight_col2:
        st.subheader("Top Pain Points")
        render_list(insight_row.get("top_pain_points"), "⚠️")

    audience_col1, audience_col2 = st.columns(2)

    with audience_col1:
        st.subheader("Ideal For")
        render_list(insight_row.get("ideal_for"), "🎯")

    with audience_col2:
        st.subheader("Avoid If")
        render_list(insight_row.get("avoid_if"), "🚫")

    st.subheader("Recommendation")
    st.write(clean(insight_row.get("recommendation")))

else:
    st.warning("No AI insight available for this phone.")

st.divider()

if summary_row is not None:
    st.subheader("Overall Sentiment")

    sentiment_df = pd.DataFrame({
        "Sentiment": ["Positive", "Neutral", "Negative"],
        "Percent": [
            summary_row["positive_percent"],
            summary_row["neutral_percent"],
            summary_row["negative_percent"],
        ],
    })

    fig = px.bar(
        sentiment_df,
        x="Sentiment",
        y="Percent",
        text="Percent",
    )

    st.plotly_chart(fig, use_container_width=True)

else:
    st.info("No sentiment summary available for this phone.")

if not platforms.empty:
    st.subheader("Amazon vs Flipkart")

    fig = px.bar(
        platforms,
        x="platform",
        y="positive_percent",
        text="positive_percent",
    )

    st.plotly_chart(fig, use_container_width=True)

    if insight_row is not None:
        st.subheader("Platform Insight")
        st.write(clean(insight_row.get("platform_insight")))
else:
    st.info("No platform comparison available for this phone.")