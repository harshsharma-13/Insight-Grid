import streamlit as st

from components.ui.kpi_tile import kpi_tile
from components.ui.section import section_title


def render(kpis, market_df):

    section_title(
        "📈 Market Health",
        "Overall market coverage and sentiment snapshot."
    )

    c1, c2, c3, c4, c5 = st.columns(5)

    with c1:
        kpi_tile(
            "Phones Tracked",
            kpis["total_phones"],
            "📱"
        )

    with c2:
        kpi_tile(
            "Reviews Collected",
            f"{kpis['total_reviews']:,}",
            "💬"
        )
    
    with c3:
        kpi_tile(
            "Usable Reviews",
            f"{kpis['usable_reviews']:,}",
            "✅"
        )


    with c4:
        kpi_tile(
            "Brands Covered",
            market_df["brand"].dropna().nunique(),
            "🏷️"
        )

    with c5:
        kpi_tile(
            "Positive Sentiment",
            f"{kpis['avg_positive']}%",
            "😊"
        )

    st.divider()