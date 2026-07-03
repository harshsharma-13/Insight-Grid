import streamlit as st

from components.ui.section import section_title


def render(
    market_df,
    get_consumer_dataset,
    pain_point_intelligence,
    feature_intelligence,
    build_consumer_brief,
):

    section_title(
        "🧠 Consumer Intelligence",
        "Understand what customers love, what frustrates them, and where product teams should focus.",
    )

    consumer_df = get_consumer_dataset()

    pain_df = pain_point_intelligence(consumer_df)

    feature_df = feature_intelligence(consumer_df)

    brief = build_consumer_brief(
        pain_df,
        feature_df,
    )

    st.info(brief)

    st.markdown("### 🚨 Top Customer Concerns")

    for _, row in pain_df.head(5).iterrows():

        with st.container(border=True):

            left, right = st.columns([4, 1])

            with left:

                st.markdown(f"### {row['issue']}")

                st.caption(
                    f"{row['phones']} phones • {row['brands']} brands"
                )

                st.write(
                    f"**Affected brands:** {row['affected_brands']}"
                )
        

                st.write(
                    f"**Recommendation:** {row['recommendation']}"
                )

                st.caption(
                    f"Example phones: {row['example_phones']}"
                )

            with right:

                st.metric(
                    "Mentions",
                    row["mentions"],
                )

                st.metric(
                    "Severity",
                    row["severity"],
                )

    st.markdown("### 💚 What Customers Appreciate")

    for _, row in feature_df.head(5).iterrows():

        with st.container(border=True):

            left, right = st.columns([4, 1])

            with left:

                st.markdown(f"### {row['feature']}")

                st.caption(
                    f"{row['phones']} phones • {row['brands']} brands"
                )

                st.write(
                    f"**Best performing brand:** {row['best_brand']}"
                )

                st.write(
                    f"**Opportunity:** {row['opportunity']}"
                )

                st.caption(
                    f"Example phones: {row['example_phones']}"
                )

            with right:

                st.metric(
                    "Mentions",
                    row["mentions"],
                )

    st.divider()