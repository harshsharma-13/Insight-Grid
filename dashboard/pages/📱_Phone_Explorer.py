from pathlib import Path
import pandas as pd
import streamlit as st
import plotly.express as px

from components.style_loader import load_css
from components.ui.insight_tile import insight_tile, list_insight_tile
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

load_css()


def clean(value):
    if value is None or pd.isna(value):
        return "Not available"

    value = str(value).strip()

    if value == "" or value.lower() == "nan":
        return "Not available"

    return value


def split_items(text):
    if text is None or pd.isna(text):
        return []

    return [item.strip() for item in str(text).split(";") if item.strip()]


def verdict_label(verdict):
    verdict = clean(verdict)

    if "Highly" in verdict or "Positive" in verdict:
        return f"🟢 {verdict}"

    if "Mixed" in verdict:
        return f"🟡 {verdict}"

    if "Not" in verdict:
        return f"🔴 {verdict}"

    return f"⚪ {verdict}"


def spec_card(title, specs, icon=""):
    with st.container(border=True):
        st.markdown(f"### {icon} {title}")

        for label, value in specs.items():
            st.markdown(f"**{label}:** {clean(value)}")


def metric_card(label, value, icon=""):
    with st.container(border=True):
        st.markdown(f"### {icon}")
        st.markdown(f"## {clean(value)}")
        st.caption(label)


def load_phone_image(image_path):
    if clean(image_path) == "Not available":
        return None

    full_path = PROJECT_ROOT / image_path

    if full_path.exists():
        return str(full_path)

    return None


st.markdown("## 📱 Phone Explorer")
st.caption("Explore specifications, review intelligence, AI analysis and platform performance.")

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

st.divider()

hero_left, hero_right = st.columns([1, 2])

with hero_left:
    if catalog_row is not None:
        image = load_phone_image(catalog_row.get("image_local_path"))
        if image:
            st.image(image, use_container_width=True)
        else:
            st.info("Image not available")
    else:
        st.info("Image not available")

with hero_right:
    st.markdown(f"# {selected_phone}")

    if catalog_row is not None:
        st.caption(
            f"{clean(catalog_row.get('brand'))} • "
            f"{clean(catalog_row.get('price_segment'))} • "
            f"{clean(catalog_row.get('android_version'))}"
        )

    if insight_row is not None:
        st.markdown(f"### {verdict_label(insight_row.get('consumer_verdict'))}")

    top_cols = st.columns(4)

    with top_cols[0]:
        metric_card(
            "Reviews Analysed",
            insight_row.get("review_count") if insight_row is not None else "NA",
            "💬",
        )

    with top_cols[1]:
        metric_card(
            "Insight Confidence",
            insight_row.get("insight_confidence") if insight_row is not None else "NA",
            "🤖",
        )

    with top_cols[2]:
        metric_card(
            "Amazon Rating",
            catalog_row.get("amazon_rating") if catalog_row is not None else "NA",
            "⭐",
        )

    with top_cols[3]:
        metric_card(
            "Flipkart Rating",
            catalog_row.get("flipkart_rating") if catalog_row is not None else "NA",
            "⭐",
        )

    price_cols = st.columns(2)

    with price_cols[0]:
        metric_card(
            "Amazon Price",
            catalog_row.get("amazon_price") if catalog_row is not None else "NA",
            "🛒",
        )

    with price_cols[1]:
        metric_card(
            "Flipkart Price",
            catalog_row.get("flipkart_price") if catalog_row is not None else "NA",
            "🛍️",
        )

    if catalog_row is not None and clean(catalog_row.get("smartprix_link")) != "Not available":
        st.link_button("Open Smartprix Page", catalog_row["smartprix_link"])

st.divider()

overview_tab, ai_tab, specs_tab, platform_tab = st.tabs(
    ["Overview", "AI Analysis", "Specifications", "Platforms"]
)

with overview_tab:
    st.markdown("### Product Snapshot")

    c1, c2, c3 = st.columns(3)

    with c1:
        spec_card(
            "Display",
            {
                "Panel": catalog_row.get("display") if catalog_row is not None else "",
                "Type": catalog_row.get("display_type") if catalog_row is not None else "",
                "Resolution": catalog_row.get("resolution") if catalog_row is not None else "",
                "Refresh Rate": catalog_row.get("refresh_rate") if catalog_row is not None else "",
            },
            "📺",
        )

    with c2:
        spec_card(
            "Performance",
            {
                "Processor": catalog_row.get("processor") if catalog_row is not None else "",
                "RAM": catalog_row.get("ram") if catalog_row is not None else "",
                "Storage": catalog_row.get("storage") if catalog_row is not None else "",
                "5G Support": catalog_row.get("supports_5g") if catalog_row is not None else "",
            },
            "⚡",
        )

    with c3:
        spec_card(
            "Battery & Camera",
            {
                "Battery": catalog_row.get("battery") if catalog_row is not None else "",
                "Charging": catalog_row.get("charging") if catalog_row is not None else "",
                "Rear Camera": catalog_row.get("rear_camera") if catalog_row is not None else "",
                "Front Camera": catalog_row.get("front_camera") if catalog_row is not None else "",
            },
            "🔋",
        )

    st.markdown("### AI Summary")

    if insight_row is not None:
        insight_tile(
            "Consumer Readout",
            clean(insight_row.get("executive_summary")),
            meta=clean(insight_row.get("consumer_verdict")),
            icon="🧠",
        )
    else:
        st.info("No AI summary available.")

    st.markdown("### Sentiment Breakdown")

    if summary_row is not None:
        sentiment_cols = st.columns(3)

        with sentiment_cols[0]:
            metric_card("Positive", f"{summary_row['positive_percent']:.1f}%", "🟢")

        with sentiment_cols[1]:
            metric_card("Neutral", f"{summary_row['neutral_percent']:.1f}%", "🟡")

        with sentiment_cols[2]:
            metric_card("Negative", f"{summary_row['negative_percent']:.1f}%", "🔴")
    else:
        st.info("No sentiment data available.")

with ai_tab:
    if insight_row is not None:
        st.markdown("### 🧠 AI Consumer Analysis")

        top_left, top_right = st.columns(2)

        with top_left:
            insight_tile(
                "Executive Summary",
                clean(insight_row.get("executive_summary")),
                icon="📝",
            )

        with top_right:
            insight_tile(
                "Recommendation",
                clean(insight_row.get("recommendation")),
                icon="🎯",
            )

        st.markdown("### Key Insights")

        left, right = st.columns(2)

        with left:
            list_insight_tile(
                "✅ Strengths",
                split_items(insight_row.get("top_strengths")),
                "•",
            )

        with right:
            list_insight_tile(
                "⚠️ Pain Points",
                split_items(insight_row.get("top_pain_points")),
                "•",
            )

        left2, right2 = st.columns(2)

        with left2:
            list_insight_tile(
                "👍 Ideal For",
                split_items(insight_row.get("ideal_for")),
                "•",
            )

        with right2:
            list_insight_tile(
                "🚫 Avoid If",
                split_items(insight_row.get("avoid_if")),
                "•",
            )

    else:
        st.warning("No AI insight available for this phone.")

with specs_tab:
    if catalog_row is not None:
        st.markdown("### Technical Specifications")

        r1c1, r1c2 = st.columns(2)

        with r1c1:
            spec_card(
                "Display",
                {
                    "Display": catalog_row.get("display"),
                    "Display Type": catalog_row.get("display_type"),
                    "Resolution": catalog_row.get("resolution"),
                    "Refresh Rate": catalog_row.get("refresh_rate"),
                },
                "📺",
            )

        with r1c2:
            spec_card(
                "Performance",
                {
                    "Processor": catalog_row.get("processor"),
                    "RAM": catalog_row.get("ram"),
                    "Storage": catalog_row.get("storage"),
                    "Android Version": catalog_row.get("android_version"),
                },
                "⚡",
            )

        r2c1, r2c2 = st.columns(2)

        with r2c1:
            spec_card(
                "Camera",
                {
                    "Rear Camera": catalog_row.get("rear_camera"),
                    "Front Camera": catalog_row.get("front_camera"),
                },
                "📷",
            )

        with r2c2:
            spec_card(
                "Battery & Connectivity",
                {
                    "Battery": catalog_row.get("battery"),
                    "Charging": catalog_row.get("charging"),
                    "5G Support": catalog_row.get("supports_5g"),
                    "NFC": catalog_row.get("nfc"),
                    "Wi-Fi": catalog_row.get("wifi"),
                    "Bluetooth": catalog_row.get("bluetooth"),
                    "Weight": catalog_row.get("weight"),
                },
                "🔋",
            )
    else:
        st.info("No specification data available.")

with platform_tab:
    if not platforms.empty:
        st.markdown("### Platform Performance")

        platform_cols = st.columns(len(platforms))

        for col, (_, row) in zip(platform_cols, platforms.iterrows()):
            with col:
                with st.container(border=True):
                    st.markdown(f"### {row['platform']}")
                    st.markdown(f"## {row['positive_percent']:.1f}%")
                    st.caption("Positive sentiment")
                    st.markdown(f"**Reviews:** {int(row['review_count'])}")
                    st.markdown(f"**Neutral:** {row['neutral_percent']:.1f}%")
                    st.markdown(f"**Negative:** {row['negative_percent']:.1f}%")

        st.markdown("### Sentiment Comparison")

        platform_chart = platforms.melt(
            id_vars=["platform"],
            value_vars=["positive_percent", "neutral_percent", "negative_percent"],
            var_name="Sentiment",
            value_name="Percent",
        )

        platform_chart["Sentiment"] = platform_chart["Sentiment"].replace({
            "positive_percent": "Positive",
            "neutral_percent": "Neutral",
            "negative_percent": "Negative",
        })

        fig = px.bar(
            platform_chart,
            x="platform",
            y="Percent",
            color="Sentiment",
            barmode="group",
            text="Percent",
        )

        fig.update_layout(
            height=420,
            paper_bgcolor="#111820",
            plot_bgcolor="#111820",
            font=dict(color="#e5e7eb"),
            margin=dict(l=20, r=20, t=30, b=20),
            legend=dict(orientation="h", y=1.05),
        )

        fig.update_xaxes(showgrid=False, color="#9ca3af")
        fig.update_yaxes(showgrid=True, gridcolor="#263244", color="#9ca3af")

        st.plotly_chart(
            fig,
            use_container_width=True,
            config={"displayModeBar": False},
        )

        if insight_row is not None:
            insight_tile(
                "Platform Insight",
                clean(insight_row.get("platform_insight")),
                icon="🛒",
            )
    else:
        st.info("No platform comparison available for this phone.")