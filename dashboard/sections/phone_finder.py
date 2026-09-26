from pathlib import Path

import pandas as pd
import streamlit as st

from components.ui.page_header import executive_brief, page_header
from dashboard_data import segment_label


PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


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


def _image_path(value):
    if value is None or pd.isna(value):
        return None

    value = str(value).strip()

    if not value or value.lower() == "nan":
        return None

    full_path = PROJECT_ROOT / value

    if full_path.exists():
        return str(full_path)

    return None


def _go_to_details(row):
    st.session_state["selected_phone_id"] = row["phone_id"]
    st.session_state["selected_phone_name"] = row["phone_name"]
    st.switch_page("pages/📱_Phone_Explorer.py")


def _result_card(
    row,
    rank,
    score_column,
    get_phone_reason,
    get_phone_warning,
    use_case=None,
):
    with st.container(
        key=f"ranked_result_{score_column}_{rank}",
        border=True,
    ):
        img_col, info_col, score_col = st.columns([1.2, 4, 1.4])

        with img_col:
            image = _image_path(row.get("image_local_path"))

            if image:
                st.image(image, width="stretch")
            else:
                st.info("No image")

        with info_col:
            if rank == 1:
                badge = "🥇 Best Match"
            elif rank == 2:
                badge = "🥈 Runner-up"
            elif rank == 3:
                badge = "🥉 Third Choice"
            else:
                badge = f"#{rank}"

            st.caption(badge)
            st.markdown(f"### {row['phone_name']}")

            st.caption(
                f"{row['brand']} • "
                f"{segment_label(row.get('price_segment'))} • "
                f"{_price(row.get('launch_price'))}"
            )

            st.markdown("**Why it ranks well**")
            st.write(get_phone_reason(row, use_case))

            warning = get_phone_warning(row)

            if warning:
                with st.expander("Things to consider"):
                    st.write(warning)

        with score_col:
            st.metric(
                "Match Score",
                f"{row[score_column]:.1f}/100",
            )

            st.metric(
                "Positive",
                f"{row['positive_percent']}%",
            )

            if st.button(
                "View Details",
                key=f"finder_view_{row['phone_id']}_{rank}_{score_column}",
                width="stretch",
            ):
                _go_to_details(row)


def render(
    get_phone_finder_dataset,
    recommend_by_use_case,
    recommend_by_budget,
    get_phone_reason,
    get_phone_warning,
    build_use_case_summary,
    build_budget_summary,
):
    df = get_phone_finder_dataset()

    page_header(
        "Decision workspace",
        "Phone Finder",
        "Move from a broad need to a defensible shortlist using sentiment, specifications and evidence strength.",
        context=[
            f"{len(df)} candidates",
            f"{df['brand'].nunique()} brands" if not df.empty else "",
            "Evidence-weighted ranking",
        ],
    )

    if df.empty:
        st.info("Phone recommendation data is not available.")
        return

    tab1, tab2 = st.tabs(
        [
            "Use-case match",
            "Budget shortlist",
        ]
    )

    with tab1:
        st.markdown('<div class="analysis-panel-title">Define the decision</div>', unsafe_allow_html=True)
        st.markdown('<div class="analysis-panel-caption">Choose the job the phone needs to perform and optionally constrain the budget.</div>', unsafe_allow_html=True)

        with st.container(key="finder_controls"):
            c1, c2 = st.columns(2)

            with c1:
                use_case = st.selectbox(
                    "Primary use case",
                    USE_CASES,
                    key="finder_use_case",
                )

        valid_prices = df["launch_price"].dropna().astype(float)

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
                "Maximum budget",
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

        executive_brief(
            build_use_case_summary(results, use_case).replace("**", ""),
            label="Recommendation logic",
        )

        if results.empty:
            st.warning("No matching phones found. Try increasing the budget.")
        else:
            st.markdown('<div class="analysis-panel-title">Ranked recommendations</div>', unsafe_allow_html=True)
            st.markdown('<div class="analysis-panel-caption">Ordered by match quality, customer reception and supporting evidence.</div>', unsafe_allow_html=True)

            for index, (_, row) in enumerate(results.iterrows(), start=1):
                _result_card(
                    row=row,
                    rank=index,
                    score_column="recommendation_score",
                    get_phone_reason=get_phone_reason,
                    get_phone_warning=get_phone_warning,
                    use_case=use_case,
                )

    with tab2:
        st.markdown('<div class="analysis-panel-title">Set the price window</div>', unsafe_allow_html=True)
        st.markdown('<div class="analysis-panel-caption">Build a shortlist optimized for value, sentiment and complaint risk.</div>', unsafe_allow_html=True)

        with st.container(key="finder_budget_controls"):
            b1, b2 = st.columns(2)

            with b1:
                min_budget = st.number_input(
                    "Minimum price",
                    min_value=0,
                    max_value=max(maximum_available, 50000),
                    value=0,
                    step=1000,
                    key="finder_min_budget",
                )

            with b2:
                default_max = min(25000, max(maximum_available, 25000))

                max_budget = st.number_input(
                    "Maximum price",
                    min_value=1000,
                    max_value=max(maximum_available, 50000),
                    value=default_max,
                    step=1000,
                    key="finder_max_budget",
                )

        if min_budget > max_budget:
            st.warning("Minimum price cannot be greater than maximum price.")
            return

        budget_results = recommend_by_budget(
            df,
            max_budget=max_budget,
            min_budget=min_budget,
            limit=10,
        )

        executive_brief(
            build_budget_summary(budget_results, max_budget).replace("**", ""),
            label="Value readout",
        )

        if budget_results.empty:
            st.warning("No phones were found in this price range.")
        else:
            st.markdown('<div class="analysis-panel-title">Value-ranked shortlist</div>', unsafe_allow_html=True)

            for index, (_, row) in enumerate(
                budget_results.head(10).iterrows(),
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
