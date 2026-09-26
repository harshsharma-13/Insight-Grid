from html import escape

import streamlit as st

from components.ui.page_header import executive_brief
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

    executive_brief(brief.replace("**", ""), label="Consumer signal brief")

    st.markdown('<div class="analysis-panel-title">Priority friction signals</div>', unsafe_allow_html=True)

    pain_cols = st.columns(2)
    for index, (_, row) in enumerate(pain_df.head(4).iterrows()):

        with pain_cols[index % 2]:
            st.markdown(
                f"""
                <div class="signal-detail-card signal-detail-risk">
                    <div class="signal-detail-top"><span>{escape(str(row['severity']))} priority</span><strong>{int(row['mentions']):,}</strong></div>
                    <h3>{escape(str(row['issue']))}</h3>
                    <p>{row['phones']} phones · {row['brands']} brands</p>
                    <div class="signal-detail-copy"><b>Recommended move</b>{escape(str(row['recommendation']))}</div>
                    <small>{escape(str(row['affected_brands']))}</small>
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.markdown('<div class="analysis-panel-title">Customer advocacy signals</div>', unsafe_allow_html=True)

    feature_cols = st.columns(2)
    for index, (_, row) in enumerate(feature_df.head(4).iterrows()):

        with feature_cols[index % 2]:
            st.markdown(
                f"""
                <div class="signal-detail-card signal-detail-positive">
                    <div class="signal-detail-top"><span>Advocacy</span><strong>{int(row['mentions']):,}</strong></div>
                    <h3>{escape(str(row['feature']))}</h3>
                    <p>{row['phones']} phones · {row['brands']} brands · led by {escape(str(row['best_brand']))}</p>
                    <div class="signal-detail-copy"><b>Commercial opportunity</b>{escape(str(row['opportunity']))}</div>
                    <small>{escape(str(row['example_phones']))}</small>
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.divider()
