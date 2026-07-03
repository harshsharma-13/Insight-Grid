import math
import streamlit as st

from components.ui.section import section_title


def sentiment_badge(row):
    positive = float(row.get("positive_percent", 0) or 0)
    negative = float(row.get("negative_percent", 0) or 0)

    if positive >= 70 and positive >= negative:
        return "🟢 Positive"
    if negative >= 25:
        return "🔴 Risky"
    return "🟡 Mixed"


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
    section_title(
        "🔎 Review Explorer",
        "Search and inspect real customer reviews behind every insight.",
    )

    df = get_review_dataset()

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
        "Search reviews",
        placeholder="battery drain, heating, lag, camera blur...",
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
        st.metric("Reviews Found", stats["reviews"])

    with s2:
        st.metric("Phones Covered", stats["phones"])

    with s3:
        st.metric("Brands Covered", stats["brands"])

    with s4:
        st.metric("Platforms", stats["platforms"])

    st.info(build_review_summary(filtered, aspect))

    st.markdown("### 🧩 Review Theme Clusters")

    if themes.empty:
        st.caption("No dominant themes detected.")
    else:
        cols = st.columns(3)

        for idx, (_, row) in enumerate(themes.head(6).iterrows()):
            with cols[idx % 3]:
                with st.container(border=True):
                    st.markdown(f"### {row['theme']}")
                    st.metric("Reviews", row["reviews"])
                    st.caption(f"{row['phones']} phones • {row['brands']} brands")

                    example = str(row["example_review"])
                    st.caption(example[:120] + "..." if len(example) > 120 else example)

    st.markdown("### Evidence Reviews")

    if filtered.empty:
        st.warning("No reviews found.")
        return

    p1, p2 = st.columns([2, 1])

    with p1:
        page_size = st.selectbox(
            "Reviews per page",
            [25, 50, 100],
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

        with st.container(border=True):
            top_left, top_right = st.columns([4, 1])

            with top_left:
                st.markdown(f"### {index}. {row['phone_name']}")
                st.caption(
                    f"{row['brand']} • {row['platform']} • {row.get('price_segment', 'Segment unavailable')}"
                )

            with top_right:
                st.markdown(f"**{sentiment_badge(row)}**")

            st.markdown("**Review Evidence**")
            st.write(review)

            st.markdown("**AI Takeaway**")
            st.caption(aspect_takeaway(aspect, review))

            meta1, meta2, meta3 = st.columns(3)

            with meta1:
                st.metric("Phone Positive %", f"{row['positive_percent']}%")

            with meta2:
                st.metric("Phone Negative %", f"{row['negative_percent']}%")

            with meta3:
                st.metric("Words", int(row["word_count"]) if row["word_count"] else 0)

    st.divider()