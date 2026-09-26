import math
from html import escape

import streamlit as st

from components.ui.kpi_tile import kpi_tile
from components.ui.page_header import executive_brief, page_header


def sentiment_style(row):
    positive = float(row.get("positive_percent", 0) or 0)
    negative = float(row.get("negative_percent", 0) or 0)

    if positive >= 70 and positive >= negative:
        return "Positive", "positive"
    if negative >= 25:
        return "Risk signal", "risky"
    return "Mixed", "mixed"


def aspect_takeaway(aspect, review):
    review = str(review).lower()

    if aspect != "All":
        return f"This review is relevant to **{aspect.lower()}** feedback."

    if "battery" in review:
        return "This review highlights battery-related experience."
    if "camera" in review:
        return "This review highlights camera-related experience."
    if "heating" in review or "heat" in review:
        return "This review points to heating or thermal experience."
    if "lag" in review or "slow" in review:
        return "This review points to performance or smoothness concerns."
    if "network" in review or "signal" in review:
        return "This review highlights connectivity experience."

    return "This review provides general customer experience evidence."


def render(
    get_review_dataset,
    filter_reviews,
    get_review_stats,
    build_review_summary,
    theme_cluster_reviews,
):
    df = get_review_dataset()

    page_header(
        "Evidence workspace",
        "Review Explorer",
        "Search, segment and inspect the customer evidence behind every market signal.",
        context=[
            f"{len(df):,} review records",
            f"{df['brand'].nunique()} brands",
            "Source-level evidence",
        ],
    )

    brands = ["All"] + sorted(df["brand"].dropna().unique().tolist())
    platforms = ["All"] + sorted(df["platform"].dropna().unique().tolist())
    phones = ["All"] + sorted(df["phone_name"].dropna().unique().tolist())

    aspects = [
        "All",
        "Battery",
        "Charging",
        "Camera",
        "Performance",
        "Heating",
        "Software",
        "Connectivity",
        "Display",
        "Build Quality",
    ]

    with st.container(key="filter_toolbar"):
        st.markdown('<div class="filter-label">Evidence filters</div>', unsafe_allow_html=True)
        c1, c2, c3, c4 = st.columns(4)

        with c1:
            brand = st.selectbox("Brand", brands, key="review_brand")

        with c2:
            phone = st.selectbox("Phone", phones, key="review_phone")

        with c3:
            platform = st.selectbox("Platform", platforms, key="review_platform")

        with c4:
            aspect = st.selectbox("Aspect", aspects, key="review_aspect")

        query = st.text_input(
            "Search review evidence",
            placeholder="Try: battery drain, heating, lag or camera blur",
        )

    filtered = filter_reviews(
        df,
        search_query=query,
        brand=brand,
        platform=platform,
        phone=phone,
        aspect=aspect,
        limit=None,
    )

    themes = theme_cluster_reviews(filtered, aspect)
    stats = get_review_stats(filtered)

    s1, s2, s3, s4 = st.columns(4)

    with s1:
        kpi_tile("Evidence found", f"{stats['reviews']:,}", "◫")

    with s2:
        kpi_tile("Phones covered", stats["phones"], "▣")

    with s3:
        kpi_tile("Brands covered", stats["brands"], "◎")

    with s4:
        kpi_tile("Sources", stats["platforms"], "↗")

    executive_brief(
        build_review_summary(filtered, aspect).replace("**", ""),
        label="Evidence readout",
    )

    st.markdown('<div class="analysis-panel-title">Theme clusters</div>', unsafe_allow_html=True)
    st.markdown('<div class="analysis-panel-caption">Recurring topics detected in the current evidence set.</div>', unsafe_allow_html=True)

    if themes.empty:
        st.caption("No dominant themes detected.")
    else:
        cols = st.columns(3)

        for idx, (_, row) in enumerate(themes.head(6).iterrows()):
            with cols[idx % 3]:
                example = str(row["example_review"])
                example = example[:140] + "…" if len(example) > 140 else example
                st.markdown(
                    f"""
                    <article class="theme-card">
                        <div class="theme-count">{int(row['reviews']):,}</div>
                        <div class="theme-name">{escape(str(row['theme']))}</div>
                        <div class="theme-meta">{int(row['phones'])} phones · {int(row['brands'])} brands</div>
                        <div class="theme-example">“{escape(example)}”</div>
                    </article>
                    """,
                    unsafe_allow_html=True,
                )

    st.markdown('<div class="analysis-panel-title">Evidence stream</div>', unsafe_allow_html=True)
    st.markdown('<div class="analysis-panel-caption">Individual customer reviews with source context and an analytical takeaway.</div>', unsafe_allow_html=True)

    if filtered.empty:
        st.warning("No reviews found.")
        return

    with st.container(key="review_pagination"):
        p1, p2 = st.columns([2, 1])

        with p1:
            page_size = st.selectbox(
                "Reviews per page",
                [10, 25, 50],
                index=0,
                key="review_page_size",
            )

        total_pages = max(1, math.ceil(len(filtered) / page_size))

        with p2:
            page = st.number_input(
                "Page",
                min_value=1,
                max_value=total_pages,
                value=1,
                step=1,
                key="review_page",
            )

    start = (page - 1) * page_size
    end = start + page_size
    display_df = filtered.iloc[start:end]

    st.caption(
        f"Showing {start + 1}–{min(end, len(filtered))} of {len(filtered)} reviews"
    )

    for index, (_, row) in enumerate(display_df.iterrows(), start=start + 1):
        review = row["review_text"] if row["review_text"] else row["clean_review"]

        sentiment_label, sentiment_class = sentiment_style(row)
        takeaway = aspect_takeaway(aspect, review).replace("**", "")
        word_count = int(row["word_count"]) if row["word_count"] else 0
        st.markdown(
            f"""
            <article class="evidence-card">
                <div class="evidence-top">
                    <div>
                        <div class="evidence-rank">EVIDENCE {index:03d}</div>
                        <div class="evidence-phone">{escape(str(row['phone_name']))}</div>
                        <div class="evidence-source">{escape(str(row['brand']))} · {escape(str(row['platform']))} · {escape(str(row.get('price_segment', 'Segment unavailable')))}</div>
                    </div>
                    <span class="sentiment-pill sentiment-{sentiment_class}">{sentiment_label}</span>
                </div>
                <div class="evidence-quote">“{escape(str(review))}”</div>
                <div class="evidence-takeaway"><strong>Analyst takeaway</strong> · {escape(takeaway)}</div>
                <div class="evidence-footer">
                    <span class="evidence-meta">{row['positive_percent']}% phone positive</span>
                    <span class="evidence-meta">{row['negative_percent']}% phone negative</span>
                    <span class="evidence-meta">{word_count} words</span>
                </div>
            </article>
            """,
            unsafe_allow_html=True,
        )

    st.divider()
