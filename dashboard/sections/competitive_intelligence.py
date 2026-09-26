import streamlit as st
import plotly.express as px

from components.ui.kpi_tile import kpi_tile
from components.ui.page_header import executive_brief, page_header
from dashboard_data import segment_label


def render(
    get_competitive_dataset,
    brand_leaderboard,
    brand_scorecards,
    segment_leaders,
    whitespace_opportunities,
    build_competitive_summary,
    compare_brands,
    build_competitive_recommendation,

):
    df = get_competitive_dataset()

    page_header(
        "Market strategy workspace",
        "Competitive Intelligence",
        "Benchmark brands, understand market position and identify the clearest competitive openings.",
        context=[
            f"{df['brand'].nunique()} brands" if not df.empty else "",
            f"{df['phone_id'].nunique()} phones" if not df.empty else "",
            "Sentiment benchmark",
        ],
    )

    if df.empty:
        st.info("Competitive intelligence data is not available yet.")
        return

    leaderboard = brand_leaderboard(df)
    scorecards = brand_scorecards(df)
    segments = segment_leaders(df)
    opportunities = whitespace_opportunities(df)

    # --------------------------------------------------
    # EXECUTIVE BRIEF
    # --------------------------------------------------

    executive_brief(
        build_competitive_summary(df).replace("**", ""),
        label="Market intelligence brief",
    )

    # --------------------------------------------------
    # MARKET SNAPSHOT
    # --------------------------------------------------

    st.markdown('<div class="analysis-panel-title">Market snapshot</div>', unsafe_allow_html=True)
    st.markdown('<div class="analysis-panel-caption">The strongest, most discussed and highest-risk brands in the current dataset.</div>', unsafe_allow_html=True)

    strongest = leaderboard.iloc[0]

    review_leader = (
        leaderboard
        .sort_values("reviews", ascending=False)
        .iloc[0]
    )

    risk_brand = (
        leaderboard
        .sort_values("avg_negative", ascending=False)
        .iloc[0]
    )

    k1, k2, k3, k4 = st.columns(4)

    with k1:
        kpi_tile("Sentiment leader", strongest["brand"], "↑")

    with k2:
        kpi_tile("Coverage leader", review_leader["brand"], "◎")

    with k3:
        kpi_tile("Highest risk", risk_brand["brand"], "!")

    with k4:
        kpi_tile("Brands benchmarked", leaderboard["brand"].nunique(), "▣")

    # --------------------------------------------------
    # POSITIONING MAP
    # --------------------------------------------------

    st.markdown("### Competitive Positioning Map")

    st.caption(
        "Brands further right have stronger positive sentiment. "
        "Larger bubbles represent greater review coverage."
    )

    position_fig = px.scatter(
        leaderboard,
        x="avg_positive",
        y="avg_negative",
        size="reviews",
        text="brand",
        hover_name="brand",
        hover_data={
            "phones": True,
            "reviews": ":,",
            "avg_positive": True,
            "avg_negative": True,
        },
        labels={
            "avg_positive": "Average Positive Sentiment (%)",
            "avg_negative": "Average Negative Sentiment (%)",
            "reviews": "Reviews",
        },
        size_max=55,
        color="avg_positive",
        color_continuous_scale=["#334155", "#60a5fa", "#67e8f9"],
    )

    position_fig.update_traces(
        textposition="top center"
    )

    position_fig.update_layout(
        height=520,
        margin=dict(l=20, r=20, t=30, b=20),
        legend_title_text="Brand",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(7,10,18,0.35)",
        font=dict(color="#cbd5e1"),
        coloraxis_showscale=False,
    )

    position_fig.update_xaxes(gridcolor="rgba(148,163,184,0.10)", zeroline=False)
    position_fig.update_yaxes(gridcolor="rgba(148,163,184,0.10)", zeroline=False)

    st.plotly_chart(
        position_fig,
        width="stretch",
    )

    # --------------------------------------------------
    # BRAND LEADERBOARD
    # --------------------------------------------------

        # --------------------------------------------------
    # BRAND LEADERBOARD
    # --------------------------------------------------

    st.markdown("### Brand Performance Leaderboard")

    st.caption(
        "All brands ranked by positive sentiment, with review volume and negative sentiment for context."
    )

    leaderboard_table = leaderboard.copy().reset_index(drop=True)
    leaderboard_table.insert(0, "Rank", leaderboard_table.index + 1)

    leaderboard_table = leaderboard_table.rename(
        columns={
            "brand": "Brand",
            "phones": "Phones",
            "reviews": "Reviews",
            "avg_positive": "Positive %",
            "avg_negative": "Negative %",
        }
    )

    leaderboard_table["Reviews"] = leaderboard_table["Reviews"].astype(int)

    st.dataframe(
        leaderboard_table,
        width="stretch",
        hide_index=True,
        column_config={
            "Rank": st.column_config.NumberColumn(
                "Rank",
                width="small",
            ),
            "Brand": st.column_config.TextColumn(
                "Brand",
                width="medium",
            ),
            "Phones": st.column_config.NumberColumn(
                "Phones",
                width="small",
            ),
            "Reviews": st.column_config.NumberColumn(
                "Reviews",
                format="%d",
                width="medium",
            ),
            "Positive %": st.column_config.ProgressColumn(
                "Positive %",
                format="%.1f%%",
                min_value=0,
                max_value=100,
                width="medium",
            ),
            "Negative %": st.column_config.ProgressColumn(
                "Negative %",
                format="%.1f%%",
                min_value=0,
                max_value=100,
                width="medium",
            ),
        },
    )

    # --------------------------------------------------
    # BRAND SCORECARDS
    # --------------------------------------------------

    st.markdown("### Brand Competitive Scorecards")

    top_scorecards = scorecards.head(6)

    for start in range(0, len(top_scorecards), 3):
        cols = st.columns(3)

        batch = top_scorecards.iloc[start:start + 3]

        for col, (_, row) in zip(cols, batch.iterrows()):
            with col:
                with st.container(key=f"brand_scorecard_{start}_{row['brand']}", border=True):

                    st.markdown(f"### {row['brand']}")

                    st.metric(
                        "Positive Sentiment",
                        f"{row['avg_positive']}%",
                    )

                    st.markdown(
                        f"<span style='color:#EF4444;font-size:14px;'>↓ {row['avg_negative']}% negative</span>",
                        unsafe_allow_html=True,
                    )

                    st.caption(
                        f"{row['phones']} phones • "
                        f"{int(row['reviews']):,} reviews"
                    )

                    st.markdown("**Primary Strength**")
                    st.write(row["top_strength"])

                    st.markdown("**Primary Concern**")
                    st.write(row["top_concern"])

    # --------------------------------------------------
    # SEGMENT LEADERS
    # --------------------------------------------------

    st.markdown("### Segment Leaders")

    if segments.empty:
        st.caption("No segment-level competitive data available.")

    else:
        segment_order = {
            "Entry": 1,
            "Budget": 2,
            "Lower Mid Range": 3,
            "Upper Mid Range": 4,
            "Premium": 5,
        }

        segments = segments.copy()

        segments["_sort_order"] = (
            segments["segment"]
            .map(segment_order)
            .fillna(999)
        )

        segments = (
            segments
            .sort_values("_sort_order")
            .drop(columns="_sort_order")
            .reset_index(drop=True)
        )

        segment_cols = st.columns(len(segments))

        for segment_index, (col, (_, row)) in enumerate(zip(
            segment_cols,
            segments.iterrows(),
        )):
            with col:

                with st.container(
                    key=f"segment_leader_{segment_index}",
                    border=True,
                ):
                    segment_name = segment_label(
                        row["segment"]
                    )

                    # Segment title
                    st.markdown(
                        f"""
                        <div style="
                            height: 75px;
                            display: flex;
                            align-items: flex-start;
                        ">
                            <div style="
                                margin: 0;
                                font-size: 20px;
                                font-weight: 650;
                                line-height: 1.3;
                            ">
                                {segment_name}
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

                    # Brand card
                    with st.container(
                        key=f"segment_leader_brand_{segment_index}",
                        border=True,
                    ):

                        st.caption("Leading Brand")

                        st.markdown(
                            f"#### {row['leader']}"
                        )

                        st.markdown(
                            f"""
                            <span style="
                                display: inline-block;
                                background: #174C35;
                                color: #4ADE80;
                                border-radius: 999px;
                                padding: 4px 9px;
                                font-size: 12px;
                                font-weight: 600;
                                line-height: 1.2;
                                white-space: nowrap;
                            ">
                                ↑ {row['positive']}% positive sentiment
                            </span>
                            """,
                            unsafe_allow_html=True,
                        )

    # --------------------------------------------------
    # COMPETITIVE OPPORTUNITIES
    # --------------------------------------------------

    st.markdown("### Competitive Opportunity Watchlist")

    st.caption(
        "Brands currently performing below the market sentiment benchmark."
    )

    if opportunities.empty:
        st.success(
            "No major below-benchmark competitive opportunities detected."
        )

    else:
        for opportunity_index, (_, row) in enumerate(opportunities.iterrows()):
            with st.container(
                key=f"opportunity_card_{opportunity_index}",
                border=True,
            ):

                c1, c2 = st.columns([1, 4])

                with c1:
                    st.markdown(f"### {row['brand']}")

                with c2:
                    st.markdown("**Opportunity**")
                    st.write(row["opportunity"])
        # --------------------------------------------------
    # BRAND VS BRAND GAP ANALYSIS
    # --------------------------------------------------

    st.markdown("### Brand vs Brand Competitive Gap Analysis")

    st.caption(
        "Compare two brands directly to identify sentiment gaps, scale advantages, strengths and improvement priorities."
    )

    brand_options = sorted(leaderboard["brand"].dropna().unique().tolist())

    if len(brand_options) >= 2:
        with st.container(key="brand_compare_controls"):
            col_a, col_b = st.columns(2)

            with col_a:
                brand_a = st.selectbox(
                    "Reference brand",
                    brand_options,
                    index=0,
                    key="compare_brand_a",
                )

            remaining_brands = [
                brand for brand in brand_options if brand != brand_a
            ]

            with col_b:
                brand_b = st.selectbox(
                    "Comparison brand",
                    remaining_brands,
                    index=0,
                    key="compare_brand_b",
                )

        comparison = compare_brands(
            df,
            brand_a,
            brand_b,
        )

        if comparison is None:
            st.warning("Brand comparison is not available for the selected brands.")

        else:
            a = comparison["brand_a"]
            b = comparison["brand_b"]

            st.markdown("#### Competitive Snapshot")

            left, right = st.columns(2)

            with left:
                with st.container(key="brand_compare_card_left", border=True):
                    st.markdown(f"### {a['brand']}")

                    st.metric(
                        "Positive Sentiment",
                        f"{a['avg_positive']}%",
                    )

                    st.markdown(
                        f"<span style='color:#EF4444;font-size:14px;'>↓ {a['avg_negative']}% negative</span>",
                        unsafe_allow_html=True,
                    )

                    st.caption(
                        f"{a['phones']} phones • {a['reviews']:,} reviews"
                    )

                    st.markdown("**Top Strength**")
                    st.write(a["top_strength"])

                    st.markdown("**Top Concern**")
                    st.write(a["top_concern"])

            with right:
                with st.container(key="brand_compare_card_right", border=True):
                    st.markdown(f"### {b['brand']}")

                    st.metric(
                        "Positive Sentiment",
                        f"{b['avg_positive']}%",
                    )

                    st.markdown(
                        f"<span style='color:#EF4444;font-size:14px;'>↓ {b['avg_negative']}% negative</span>",
                        unsafe_allow_html=True,
                    )

                    st.caption(
                        f"{b['phones']} phones • {b['reviews']:,} reviews"
                    )

                    st.markdown("**Top Strength**")
                    st.write(b["top_strength"])

                    st.markdown("**Top Concern**")
                    st.write(b["top_concern"])

            st.markdown("#### Gap Summary")

            g1, g2, g3 = st.columns(3)

            with g1:
                positive_gap = comparison["positive_gap"]

                st.metric(
                    "Positive Sentiment Gap",
                    f"{positive_gap:+.1f} pts",
                )

            with g2:
                negative_gap = comparison["negative_gap"]

                if negative_gap > 0:
                    st.markdown(
                        f"<span style='color:#EF4444;font-size:24px;font-weight:700;'>+{negative_gap:.1f} pts</span>",
                        unsafe_allow_html=True,
                    )
                    st.caption("Higher negative sentiment than competitor")
                else:
                    st.markdown(
                        f"<span style='color:#22C55E;font-size:24px;font-weight:700;'>{negative_gap:.1f} pts</span>",
                        unsafe_allow_html=True,
                    )
                    st.caption("Lower negative sentiment than competitor")

            with g3:
                review_gap = comparison["review_gap"]

                st.metric(
                    "Review Coverage Gap",
                    f"{review_gap:+,}",
                )

            st.markdown("#### Strategic Recommendation")

            with st.container(key="brand_compare_recommendation", border=True):
                st.write(
                    build_competitive_recommendation(comparison)
                )

    else:
        st.info("At least two brands are required for brand comparison.")

    st.divider()
