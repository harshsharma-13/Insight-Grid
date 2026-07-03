import streamlit as st

from components.ui.section import section_title


def render(pain_df, love_df):

    section_title(
        "🎙 Consumer Voice Snapshot",
        "A quick view of what customers are praising and complaining about most.",
    )

    pain_top = pain_df.head(3).reset_index(drop=True)
    love_top = love_df.head(3).reset_index(drop=True)

    left, right = st.columns(2)

    with left:
        with st.container(border=True):
            st.markdown("### ⚠️ Top Complaints")

            for idx, row in pain_top.iterrows():
                st.markdown(f"**{idx + 1}. {row['issue']}**")
                st.caption(
                    f"{int(row['estimated_negative_reviews'])} estimated mentions | "
                    f"{row['phones_affected']} phones"
                )

                if idx < len(pain_top) - 1:
                    st.divider()

    with right:
        with st.container(border=True):
            st.markdown("### 💚 Top Praises")

            for idx, row in love_top.iterrows():
                st.markdown(f"**{idx + 1}. {row['feature']}**")
                st.caption(
                    f"{int(row['estimated_positive_reviews'])} estimated mentions | "
                    f"{row['phones_affected']} phones"
                )

                if idx < len(love_top) - 1:
                    st.divider()

    st.divider()