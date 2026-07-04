import streamlit as st

from components.ui.navbar import navbar
from config import APP_TITLE, DEFAULT_PAGE_ICON
from dashboard_data import get_kpis, get_featured_phones
from ai_search import answer_search_query
from market_intelligence import (
    get_market_dataset,
    aggregate_pain_points,
    aggregate_customer_loves,
    get_segment_overview,
    get_brand_landscape,
    build_market_summary,
)
from components.style_loader import load_css
from components.ui.search import ai_search_box
from components.ui.section import section_title
from components.ui.phone_tile import phone_tile
from components.ui.summary_tiles import summary_tile
from sections.hero import render as hero
from sections.market_health import render as market_health
from sections.executive_summary import render as executive_summary
from sections.customer_voice import render as customer_voice
from sections.segment_overview import render as segment_overview
from sections.competitive_landscape import render as competitive_landscape
from sections.featured_phones import render as featured_phones
from consumer_intelligence import (
    get_consumer_dataset,
    pain_point_intelligence,
    feature_intelligence,
    build_consumer_brief,
)

from sections.consumer_intelligence import render as consumer_intelligence


st.set_page_config(
    page_title=APP_TITLE,
    page_icon=DEFAULT_PAGE_ICON,
    layout="wide",
)

load_css()

navbar()

# ============================
# Load datasets
# ============================

kpis = get_kpis()
market_df = get_market_dataset()

hero()

query = ai_search_box()

if query:

    st.markdown("## 🤖 AI Search Results")
    st.caption(f"Query: {query}")

    with st.spinner("Searching specifications, review sentiment and AI insights..."):
        answer, candidates = answer_search_query(query)

    with st.container(border=True):
        st.markdown(answer)

    if not candidates.empty:
        st.markdown("### Recommended Phones")

        for i in range(0, len(candidates), 4):
            cols = st.columns(4)
            batch = candidates.iloc[i:i + 4]

            for col, (_, phone) in zip(cols, batch.iterrows()):
                with col:
                    phone_tile(phone, key_prefix=f"search_{i}")


market_health(
    kpis,
    market_df,
)

summary = build_market_summary(market_df)

executive_summary(summary)

filter_col1, filter_col2 = st.columns(2)

brands = ["All"] + sorted([b for b in market_df["brand"].dropna().unique().tolist() if b])
segment_labels = {
    "All": "All",
    "Budget": "Budget (≤ ₹15,000)",
    "Mid-range": "Mid-range (₹15,001–₹25,000)",
    "Upper Mid-range": "Upper Mid-range (> ₹25,000)",
}


segments = list(segment_labels.keys())

with filter_col1:
    selected_brand = st.selectbox("Filter by Brand", brands)

with filter_col2:
    selected_segment_label = st.selectbox(
    "Filter by Segment",
    [segment_labels[s] for s in segments],
)

selected_segment = {
    label: key for key, label in segment_labels.items()
}[selected_segment_label]


pain_df = aggregate_pain_points(
    market_df,
    brand=selected_brand,
    segment=selected_segment,
)

love_df = aggregate_customer_loves(
    market_df,
    brand=selected_brand,
    segment=selected_segment,
)

top_pain = pain_df.iloc[0]
top_love = love_df.iloc[0]

s1, s2, s3, s4 = st.columns(4)

with s1:
    summary_tile(
        "Top Customer Concern",
        top_pain["issue"],
        f"{top_pain['phones_affected']} phones affected",
        "⚠️",
        "#EF4444",
    )

with s2:
    summary_tile(
        "Estimated Negative Mentions",
        int(top_pain["estimated_negative_reviews"]),
        f"Severity: {top_pain['severity']}",
        "📉",
        "#F97316",
    )

with s3:
    summary_tile(
        "Most Loved Feature",
        top_love["feature"],
        f"{top_love['phones_affected']} phones affected",
        "💚",
        "#22C55E",
    )

with s4:
    summary_tile(
        "Estimated Positive Mentions",
        int(top_love["estimated_positive_reviews"]),
        f"Avg positive: {top_love['avg_positive_percent']}%",
        "📈",
        "#3B82F6",
    )




consumer_intelligence(
    market_df,
    get_consumer_dataset,
    pain_point_intelligence,
    feature_intelligence,
    build_consumer_brief,
)


customer_voice(
    pain_df,
    love_df,
)


segment_overview(
    market_df,
    get_segment_overview,
)

competitive_landscape(
    market_df,
    get_brand_landscape,
)

featured_phones(
    get_featured_phones
)