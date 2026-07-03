import streamlit as st

from components.ui.section import section_title
from components.ui.phone_tile import phone_tile


def _reason(phone):

    verdict = str(
        phone.get(
            "consumer_verdict",
            "",
        )
    )

    positive = phone.get(
        "positive_percent",
        0,
    )

    strengths = str(
        phone.get(
            "top_strengths",
            "",
        )
    )

    strengths = (
        strengths.replace("|", ", ")
        .replace(";", ", ")
        .strip()
    )

    if strengths:
        strengths = strengths.split(",")[0].strip()

    if positive >= 85:
        level = "Exceptional customer satisfaction"

    elif positive >= 75:
        level = "Very strong customer satisfaction"

    elif positive >= 65:
        level = "Positive customer reception"

    else:
        level = "Mixed customer reception"

    if strengths:

        return (
            f"{level}. "
            f"Customers particularly praised **{strengths.lower()}**."
        )

    return verdict


def render(get_featured_phones):

    section_title(
        "🔥 Featured Smartphones",
        "Most recommended devices based on consumer sentiment and AI insights.",
    )

    featured = get_featured_phones(6)

    if featured.empty:
        st.info("No featured phones available.")
        return

    cols = st.columns(3)

    for index, (_, phone) in enumerate(
        featured.iterrows()
    ):

        with cols[index % 3]:

            phone_tile(
                phone,
                key_prefix=f"featured_{index}",
            )

            with st.container(border=True):

                st.markdown("##### 🤖 Why it's Trending")

                st.caption(
                    _reason(phone)
                )

                positive = phone.get(
                    "positive_percent",
                    0,
                )

                reviews = phone.get(
                    "review_count",
                    0,
                )

                c1, c2 = st.columns(2)

                with c1:

                    st.metric(
                        "Positive",
                        f"{positive:.1f}%"
                    )

                with c2:

                    st.metric(
                        "Reviews",
                        int(reviews)
                    )

    st.divider()