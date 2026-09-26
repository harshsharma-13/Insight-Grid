import streamlit as st

from components.ui.section import section_title
from components.ui.summary_tiles import summary_tile


def render(market_df, get_brand_landscape):

    section_title(
        "🏆 Competitive Landscape",
        "Compare brand performance, strengths and weaknesses across the market.",
    )

    brand_df = get_brand_landscape(market_df)

    if brand_df.empty:
        st.info("No brand intelligence available.")
        return

    best_brand = brand_df.iloc[0]

    most_reviews = (
        brand_df
        .sort_values("reviews", ascending=False)
        .iloc[0]
    )

    weakest_brand = (
        brand_df
        .sort_values("avg_negative", ascending=False)
        .iloc[0]
    )

    c1, c2, c3 = st.columns(3)

    with c1:

        summary_tile(
            "Market Leader",
            best_brand["brand"],
            f"{best_brand['avg_positive']}% positive sentiment",
            "🥇",
            "#22C55E",
        )

    with c2:

        summary_tile(
            "Most Discussed Brand",
            most_reviews["brand"],
            f"{int(most_reviews['reviews'])} reviews analysed",
            "💬",
            "#3B82F6",
        )

    with c3:

        summary_tile(
            "Needs Most Attention",
            weakest_brand["brand"],
            weakest_brand["top_concern"],
            "⚠️",
            "#F97316",
        )

    st.markdown("### Brand Performance")

    st.caption(
        "Brands ranked by overall consumer sentiment."
    )

    for rank, (_, row) in enumerate(
        brand_df.sort_values(
            "avg_positive",
            ascending=False,
        ).iterrows(),
        start=1,
    ):

        medal = "🥇"

        if rank == 2:
            medal = "🥈"

        elif rank == 3:
            medal = "🥉"

        with st.container(key=f"landscape_brand_card_{rank}", border=True):

            left, middle, right = st.columns(
                [3, 1.3, 2]
            )

            with left:

                st.markdown(
                    f"### {medal} {row['brand']}"
                )

                st.caption(
                    f"{row['phones']} phones analysed"
                )

            with middle:

                st.metric(
                    "Positive",
                    f"{row['avg_positive']}%",
                )

            with right:

                st.markdown(
                    f"**👍 Strength**  \n{row['top_strength']}"
                )

                st.markdown(
                    f"**⚠ Concern**  \n{row['top_concern']}"
                )

    st.divider()

    st.markdown("### Executive Observations")

    top3 = (
        brand_df
        .sort_values(
            "avg_positive",
            ascending=False,
        )
        .head(3)
    )

    with st.container(key="landscape_observations", border=True):

        st.markdown(
            f"""
**• Market Leader:** {top3.iloc[0]['brand']}

**• Strong Challengers:** {top3.iloc[1]['brand']} and {top3.iloc[2]['brand']}

**• Most common weakness across brands:** {weakest_brand['top_concern']}

**• Highest customer engagement:** {most_reviews['brand']}
"""
        )

    st.divider()
