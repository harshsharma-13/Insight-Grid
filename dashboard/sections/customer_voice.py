from html import escape

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
        rows = "".join(
            f'<div class="signal-row"><span class="signal-rank">{idx + 1:02d}</span>'
            f'<div><strong>{escape(str(row["issue"]))}</strong>'
            f'<small>{int(row["estimated_negative_reviews"]):,} mentions · {row["phones_affected"]} phones</small></div></div>'
            for idx, row in pain_top.iterrows()
        )
        st.markdown(
            f'<div class="signal-panel signal-panel-risk"><div class="signal-panel-label">Top friction</div>{rows}</div>',
            unsafe_allow_html=True,
        )

    with right:
        rows = "".join(
            f'<div class="signal-row"><span class="signal-rank">{idx + 1:02d}</span>'
            f'<div><strong>{escape(str(row["feature"]))}</strong>'
            f'<small>{int(row["estimated_positive_reviews"]):,} mentions · {row["phones_affected"]} phones</small></div></div>'
            for idx, row in love_top.iterrows()
        )
        st.markdown(
            f'<div class="signal-panel signal-panel-positive"><div class="signal-panel-label">Top advocacy</div>{rows}</div>',
            unsafe_allow_html=True,
        )

    st.divider()
