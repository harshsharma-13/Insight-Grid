from html import escape

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
            st.markdown(
                f"""
                <div class="segment-card-v2">
                    <div class="segment-card-kicker">{escape(profile['buyer'])}</div>
                    <h3>{escape(title)}</h3>
                    <div class="segment-sentiment"><strong>{row['avg_positive']}%</strong><span>positive sentiment</span></div>
                    <div class="segment-facts">
                        <div><span>Purchase priority</span><b>{escape(profile['priority'])}</b></div>
                        <div><span>Phones analysed</span><b>{row['phones']}</b></div>
                        <div><span>Leading brand</span><b>{escape(str(row['leading_brand']))}</b></div>
                        <div><span>Top strength</span><b>{escape(str(row['top_strength']))}</b></div>
                        <div><span>Primary concern</span><b>{escape(str(row['top_concern']))}</b></div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.divider()
