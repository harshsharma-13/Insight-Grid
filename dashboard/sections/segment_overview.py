import streamlit as st

from components.ui.section import section_title


SEGMENT_DISPLAY = {
    "Budget": "Budget (≤ ₹15,000)",
    "Mid-range": "Mid-range (₹15,001–₹25,000)",
    "Upper Mid-range": "Upper Mid-range (> ₹25,000)",
}

SEGMENT_PROFILE = {
    "Budget": {
        "buyer": "Students & First-time Buyers",
        "priority": "Value for Money",
        "icon": "🎓",
    },
    "Mid-range": {
        "buyer": "Young Professionals",
        "priority": "Balanced Experience",
        "icon": "💼",
    },
    "Upper Mid-range": {
        "buyer": "Power Users",
        "priority": "Premium Features",
        "icon": "🚀",
    },
}


def _metric(label, value):
    st.markdown(
        f"""
**{label}**

{value}
"""
    )


def render(market_df, get_segment_overview):

    section_title(
        "🧭 Segment Overview",
        "Understand how each price segment performs and who it is best suited for.",
    )

    segment_df = get_segment_overview(market_df)

    if segment_df.empty:
        st.info("No segment information available.")
        return

    cols = st.columns(len(segment_df))

    for col, (_, row) in zip(cols, segment_df.iterrows()):

        segment = row["segment"]

        profile = SEGMENT_PROFILE.get(
            segment,
            {
                "buyer": "-",
                "priority": "-",
                "icon": "📱",
            },
        )

        title = SEGMENT_DISPLAY.get(segment, segment)

        with col:

            with st.container(border=True):

                st.markdown(
                    f"## {profile['icon']} {title}"
                )

                st.metric(
                    "Average Positive Sentiment",
                    f"{row['avg_positive']}%",
                )

                st.divider()

                _metric(
                    "👤 Typical Buyer",
                    profile["buyer"],
                )

                _metric(
                    "⭐ Purchase Priority",
                    profile["priority"],
                )

                _metric(
                    "📱 Phones Analysed",
                    row["phones"],
                )

                _metric(
                    "👍 Top Strength",
                    row["top_strength"],
                )

                _metric(
                    "⚠️ Biggest Concern",
                    row["top_concern"],
                )

                _metric(
                    "🏆 Leading Brand",
                    row["leading_brand"],
                )

    st.divider()