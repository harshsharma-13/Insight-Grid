import pandas as pd
import streamlit as st

from components.ui.section import section_title


USE_CASES = [
    "Gaming",
    "Camera & Social Media",
    "Battery & Daily Use",
    "Work & Productivity",
    "Entertainment",
    "Value for Money",
]


def _price(value):
    if value is None or pd.isna(value):
        return "Price unavailable"

    return f"₹{float(value):,.0f}"


def _result_card(
    row,
    rank,
    score_column,
    get_phone_reason,
    get_phone_warning,
    use_case=None,
):
    with st.container(border=True):
        top_left, top_right = st.columns([4, 1])

        with top_left:
            if rank == 1:
                badge = "🥇 Best Match"
            elif rank == 2:
                badge = "🥈 Runner-up"
            elif rank == 3:
                badge = "🥉 Third Choice"
            else:
                badge = f"#{rank}"

            st.caption(badge)

            st.markdown(
                f"### {row['phone_name']}"
            )

            st.caption(
                f"{row['brand']} • "
                f"{row.get('price_segment', 'Segment unavailable')} • "
                f"{_price(row.get('launch_price'))}"
            )

        with top_right:
            st.metric(
                "Match Score",
                f"{row[score_column]:.1f}/100",
            )

        m1, m2, m3 = st.columns(3)

        with m1:
            st.metric(
                "Positive",
                f"{row['positive_percent']}%",
            )

        with m2:
            st.metric(
                "Reviews",
                f"{int(row['review_count']):,}",
            )

        with m3:
            st.metric(
                "Negative",
                f"{row['negative_percent']}%",
            )

        st.markdown("**Why it ranks well**")

        st.write(
            get_phone_reason(
                row,
                use_case,
            )
        )

        warning = get_phone_warning(row)

        if warning:
            with st.expander("Things to consider"):
                st.write(warning)


def render(
    get_phone_finder_dataset,
    recommend_by_use_case,
    recommend_by_budget,
    get_phone_reason,
    get_phone_warning,
    build_use_case_summary,
    build_budget_summary,
):
    section_title(
        "🎯 Phone Finder",
        "Find the strongest phones for a specific use case or within your budget.",
    )

    df = get_phone_finder_dataset()

    if df.empty:
        st.info("Phone recommendation data is not available.")
        return

    tab1, tab2 = st.tabs(
        [
            "🎮 Best Phone by Use Case",
            "💰 Budget Recommendations",
        ]
    )

    # ==================================================
    # USE CASE FINDER
    # ==================================================

    with tab1:
        st.markdown("### Find the Best Phone for Your Needs")

        st.caption(
            "Recommendations combine use-case relevance, customer sentiment, "
            "negative sentiment risk and review evidence."
        )

        c1, c2 = st.columns(2)

        with c1:
            use_case = st.selectbox(
                "What matters most to you?",
                USE_CASES,
                key="finder_use_case",
            )

        valid_prices = (
            df["launch_price"]
            .dropna()
            .astype(float)
        )

        if valid_prices.empty:
            maximum_available = 50000
        else:
            maximum_available = int(valid_prices.max())

        budget_options = [
            "No Budget Limit",
            "₹10,000",
            "₹15,000",
            "₹20,000",
            "₹25,000",
            "₹30,000",
            "₹40,000",
            "₹50,000",
        ]

        with c2:
            budget_choice = st.selectbox(
                "Maximum Budget",
                budget_options,
                index=0,
                key="finder_use_case_budget",
            )

        budget_map = {
            "No Budget Limit": None,
            "₹10,000": 10000,
            "₹15,000": 15000,
            "₹20,000": 20000,
            "₹25,000": 25000,
            "₹30,000": 30000,
            "₹40,000": 40000,
            "₹50,000": 50000,
        }

        selected_budget = budget_map[budget_choice]

        results = recommend_by_use_case(
            df,
            use_case,
            budget=selected_budget,
            limit=5,
        )

        st.info(
            build_use_case_summary(
                results,
                use_case,
            )
        )

        if results.empty:
            st.warning(
                "No matching phones found. Try increasing the budget."
            )

        else:
            st.markdown("### Top Recommendations")

            for index, (_, row) in enumerate(
                results.iterrows(),
                start=1,
            ):
                _result_card(
                    row=row,
                    rank=index,
                    score_column="recommendation_score",
                    get_phone_reason=get_phone_reason,
                    get_phone_warning=get_phone_warning,
                    use_case=use_case,
                )

    # ==================================================
    # BUDGET FINDER
    # ==================================================

    with tab2:
        st.markdown("### Best Phones Within Your Budget")

        st.caption(
            "Phones are ranked using positive sentiment, complaint risk "
            "and the strength of available review evidence."
        )

        b1, b2 = st.columns(2)

        with b1:
            min_budget = st.number_input(
                "Minimum Price",
                min_value=0,
                max_value=max(maximum_available, 50000),
                value=0,
                step=1000,
                key="finder_min_budget",
            )

        with b2:
            default_max = min(
                25000,
                max(maximum_available, 25000),
            )

            max_budget = st.number_input(
                "Maximum Price",
                min_value=1000,
                max_value=max(maximum_available, 50000),
                value=default_max,
                step=1000,
                key="finder_max_budget",
            )

        if min_budget > max_budget:
            st.warning(
                "Minimum price cannot be greater than maximum price."
            )
            return

        budget_results = recommend_by_budget(
            df,
            max_budget=max_budget,
            min_budget=min_budget,
            limit=10,
        )

        st.info(
            build_budget_summary(
                budget_results,
                max_budget,
            )
        )

        if budget_results.empty:
            st.warning(
                "No phones were found in this price range."
            )

        else:
            st.markdown("### Recommended Phones")

            display_table = budget_results[
                [
                    "phone_name",
                    "brand",
                    "launch_price",
                    "price_segment",
                    "positive_percent",
                    "negative_percent",
                    "review_count",
                    "value_score",
                ]
            ].copy()

            display_table = display_table.rename(
                columns={
                    "phone_name": "Phone",
                    "brand": "Brand",
                    "launch_price": "Price",
                    "price_segment": "Segment",
                    "positive_percent": "Positive %",
                    "negative_percent": "Negative %",
                    "review_count": "Reviews",
                    "value_score": "Value Score",
                }
            )

            display_table.insert(
                0,
                "Rank",
                range(
                    1,
                    len(display_table) + 1,
                ),
            )

            st.dataframe(
                display_table,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Rank": st.column_config.NumberColumn(
                        "Rank",
                        width="small",
                    ),
                    "Price": st.column_config.NumberColumn(
                        "Price",
                        format="₹%d",
                    ),
                    "Positive %": st.column_config.ProgressColumn(
                        "Positive %",
                        format="%.1f%%",
                        min_value=0,
                        max_value=100,
                    ),
                    "Negative %": st.column_config.ProgressColumn(
                        "Negative %",
                        format="%.1f%%",
                        min_value=0,
                        max_value=100,
                    ),
                    "Value Score": st.column_config.ProgressColumn(
                        "Value Score",
                        format="%.1f",
                        min_value=0,
                        max_value=100,
                    ),
                },
            )

            st.markdown("### Top 3 Detailed Recommendations")

            for index, (_, row) in enumerate(
                budget_results.head(3).iterrows(),
                start=1,
            ):
                _result_card(
                    row=row,
                    rank=index,
                    score_column="value_score",
                    get_phone_reason=get_phone_reason,
                    get_phone_warning=get_phone_warning,
                )

    st.divider()