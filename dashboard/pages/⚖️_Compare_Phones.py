from pathlib import Path
import pandas as pd
import streamlit as st

from components.style_loader import load_css
from components.ui.navbar import navbar
from components.ui.page_header import page_header
from ai_compare import build_context, compare_question
from dashboard_data import (
    get_phone_options,
    get_phone_catalog,
    get_phone_ai_insight,
    get_phone_sentiment_summary,
)

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

st.set_page_config(page_title="Compare Phones", page_icon="⚖️", layout="wide")
load_css()

navbar("compare")


def clean(value):
    if value is None or pd.isna(value):
        return "Not available"
    value = str(value).strip()
    return "Not available" if value == "" or value.lower() == "nan" else value

def format_price(value):
    if value is None or pd.isna(value):
        return "Not available"

    try:
        cleaned = (
            str(value)
            .replace("₹", "")
            .replace("Rs.", "")
            .replace("Rs", "")
            .replace(",", "")
            .strip()
        )

        return f"₹ {float(cleaned):,.0f}"

    except (ValueError, TypeError):
        return "Not available"


def split_items(text):
    if text is None or pd.isna(text):
        return []
    return [x.strip() for x in str(text).split(";") if x.strip()]


def parse_number(value):
    value = clean(value).replace("/5", "").strip()
    try:
        return float(value)
    except Exception:
        return None


def load_image(path):
    if clean(path) == "Not available":
        return None
    full_path = PROJECT_ROOT / path
    return str(full_path) if full_path.exists() else None


def get_rows(phone_id):
    catalog = get_phone_catalog(phone_id)
    insight = get_phone_ai_insight(phone_id)
    summary = get_phone_sentiment_summary(phone_id)

    return {
        "catalog": catalog.iloc[0] if not catalog.empty else None,
        "insight": insight.iloc[0] if not insight.empty else None,
        "summary": summary.iloc[0] if not summary.empty else None,
    }


def score_phone(data):
    catalog = data["catalog"]
    insight = data["insight"]
    summary = data["summary"]

    score = 0
    reasons = []

    if summary is not None:
        positive = parse_number(summary.get("positive_percent"))
        negative = parse_number(summary.get("negative_percent"))

        if positive is not None:
            score += positive * 0.45
            reasons.append(f"{positive:.1f}% positive sentiment")

        if negative is not None:
            score -= negative * 0.20

    if insight is not None:
        reviews = parse_number(insight.get("review_count"))
        confidence = clean(insight.get("insight_confidence"))

        if reviews is not None:
            score += min(reviews / 10, 15)
            reasons.append(f"{int(reviews)} reviews analysed")

        if "Very High" in confidence:
            score += 8
        elif "High" in confidence:
            score += 5

    if catalog is not None:
        amazon_rating = parse_number(catalog.get("amazon_rating"))
        flipkart_rating = parse_number(catalog.get("flipkart_rating"))

        ratings = [x for x in [amazon_rating, flipkart_rating] if x is not None]

        if ratings:
            avg_rating = sum(ratings) / len(ratings)
            score += avg_rating * 6
            reasons.append(f"{avg_rating:.1f}/5 average platform rating")

    return score, reasons


def ai_verdict(phone_1, phone_2, data_1, data_2):
    score_1, reasons_1 = score_phone(data_1)
    score_2, reasons_2 = score_phone(data_2)

    if score_1 > score_2:
        winner = phone_1
        loser = phone_2
        margin = score_1 - score_2
        reasons = reasons_1
    elif score_2 > score_1:
        winner = phone_2
        loser = phone_1
        margin = score_2 - score_1
        reasons = reasons_2
    else:
        winner = "Tie"
        loser = ""
        margin = 0
        reasons = []

    with st.container(key="comparison_verdict", border=True):
        st.caption("DECISION READOUT")
        st.markdown("## Comparative verdict")

        if winner == "Tie":
            st.info("Both smartphones perform similarly based on the available data.")
            return

        if margin >= 15:
            confidence = "High"
        elif margin >= 7:
            confidence = "Moderate"
        else:
            confidence = "Low"

        st.success(f"Recommended: **{winner}**")

        st.markdown(
            f"""
**Confidence:** {confidence}

Based on overall consumer sentiment, review quality and marketplace data,
**{winner}** appears to be the stronger overall recommendation compared with **{loser}**.
"""
        )

        if reasons:
            st.markdown("### Why it leads")
            for reason in reasons[:3]:
                st.markdown(f"• {reason}")


def phone_header(phone_name, data, key):
    catalog = data["catalog"]
    insight = data["insight"]
    summary = data["summary"]

    with st.container(key=f"comparison_phone_card_{key}", border=True):
        # ----------------------------------
        # IMAGE AREA
        # ----------------------------------

        with st.container(
            border=False,
            height=320,
        ):
            if catalog is not None:
                image = load_image(
                    catalog.get("image_local_path")
                )

                if image:
                    st.image(
                        image,
                        width=220,
                    )
                else:
                    st.info("Image not available")

            else:
                st.info("Image not available")


        # ----------------------------------
        # PHONE IDENTITY
        # ----------------------------------

        st.markdown(f"### {phone_name}")

        if catalog is not None:
            st.caption(
                f"{clean(catalog.get('brand'))} • "
                f"{clean(catalog.get('price_segment'))}"
            )

        if insight is not None:
            st.markdown(
                f"**{clean(insight.get('consumer_verdict'))}**"
            )
        else:
            st.markdown(
                "**Consumer verdict unavailable**"
            )


        # ----------------------------------
        # SENTIMENT + REVIEWS
        # ----------------------------------

        c1, c2 = st.columns(2)

        with c1:
            positive_value = (
                f"{summary.get('positive_percent'):.1f}%"
                if summary is not None
                and pd.notna(
                    summary.get("positive_percent")
                )
                else "NA"
            )

            st.metric(
                "Positive",
                positive_value,
            )

        with c2:
            st.metric(
                "Reviews",
                clean(
                    insight.get("review_count")
                )
                if insight is not None
                else "NA",
            )


        # ----------------------------------
        # PRICES
        # ----------------------------------

        p1, p2 = st.columns(2)

        with p1:
            st.metric(
                "Amazon",
                format_price(
                    catalog.get("amazon_price")
                    if catalog is not None
                    else None
                ),
            )

        with p2:
            st.metric(
                "Flipkart",
                format_price(
                    catalog.get("flipkart_price")
                    if catalog is not None
                    else None
                ),
            )


def comparison_row(label, left_value, right_value):
    c1, c2, c3 = st.columns([1.1, 2, 2])

    with c1:
        st.caption(label)

    with c2:
        st.write(clean(left_value))

    with c3:
        st.write(clean(right_value))


def list_block(title, items, key):
    with st.container(key=f"comparison_list_card_{key}", border=True):
        st.markdown(f"#### {title}")

        if not items:
            st.caption("No data available")

        for item in items[:3]:
            st.caption(f"• {item}")


phones = get_phone_options()
phone_names = phones["phone_name"].tolist()
phone_map = dict(zip(phones["phone_name"], phones["phone_id"]))

page_header(
    "Decision workspace",
    "Compare Phones",
    "Place two devices side by side and surface the differences that materially affect a buying decision.",
    context=[f"{len(phone_names)} phones", "Evidence-aware verdict", "Specification parity"],
)

with st.container(key="compare_controls"):
    st.markdown('<div class="filter-label">Comparison set</div>', unsafe_allow_html=True)
    select_left, select_right = st.columns(2)

    with select_left:
        phone_1 = st.selectbox(
            "Reference phone",
            phone_names,
            key="compare_phone_1",
        )

    phone_2_options = [name for name in phone_names if name != phone_1]

    if "compare_phone_2" not in st.session_state or st.session_state["compare_phone_2"] == phone_1:
        st.session_state["compare_phone_2"] = phone_2_options[0]

    with select_right:
        phone_2 = st.selectbox(
            "Comparison phone",
            phone_2_options,
            key="compare_phone_2",
        )

data_1 = get_rows(phone_map[phone_1])
data_2 = get_rows(phone_map[phone_2])

catalog_1 = data_1["catalog"]
catalog_2 = data_2["catalog"]
insight_1 = data_1["insight"]
insight_2 = data_2["insight"]

left, right = st.columns(2)

with left:
    phone_header(phone_1, data_1, "left")

with right:
    phone_header(phone_2, data_2, "right")

st.divider()

ai_verdict(phone_1, phone_2, data_1, data_2)

st.markdown('<div class="analysis-panel-title">Ask the comparison</div>', unsafe_allow_html=True)
st.markdown('<div class="analysis-panel-caption">Interrogate this pair for a specific use case or trade-off.</div>', unsafe_allow_html=True)

question = st.text_input(
    "Ask a comparison question",
    placeholder="Example: Which is better for gaming, camera, battery, or value?",
    label_visibility="collapsed",
)

if question:
    context_1 = build_context(phone_1, catalog_1, insight_1, data_1["summary"])
    context_2 = build_context(phone_2, catalog_2, insight_2, data_2["summary"])

    answer = compare_question(question, context_1, context_2)

    with st.container(key="comparison_answer", border=True):
        st.markdown(answer)

st.divider()

st.markdown('<div class="analysis-panel-title">Specification matrix</div>', unsafe_allow_html=True)
st.markdown('<div class="analysis-panel-caption">A direct field-by-field view of the hardware differences.</div>', unsafe_allow_html=True)

with st.container(key="comparison_matrix", border=True):
    comparison_row("Display", catalog_1.get("display") if catalog_1 is not None else "", catalog_2.get("display") if catalog_2 is not None else "")
    comparison_row("Refresh Rate", catalog_1.get("refresh_rate") if catalog_1 is not None else "", catalog_2.get("refresh_rate") if catalog_2 is not None else "")
    comparison_row("Processor", catalog_1.get("processor") if catalog_1 is not None else "", catalog_2.get("processor") if catalog_2 is not None else "")
    comparison_row("RAM", catalog_1.get("ram") if catalog_1 is not None else "", catalog_2.get("ram") if catalog_2 is not None else "")
    comparison_row("Storage", catalog_1.get("storage") if catalog_1 is not None else "", catalog_2.get("storage") if catalog_2 is not None else "")
    comparison_row("Battery", catalog_1.get("battery") if catalog_1 is not None else "", catalog_2.get("battery") if catalog_2 is not None else "")
    comparison_row("Charging", catalog_1.get("charging") if catalog_1 is not None else "", catalog_2.get("charging") if catalog_2 is not None else "")
    comparison_row("Rear Camera", catalog_1.get("rear_camera") if catalog_1 is not None else "", catalog_2.get("rear_camera") if catalog_2 is not None else "")
    comparison_row("Front Camera", catalog_1.get("front_camera") if catalog_1 is not None else "", catalog_2.get("front_camera") if catalog_2 is not None else "")

st.divider()

st.markdown('<div class="analysis-panel-title">Consumer intelligence comparison</div>', unsafe_allow_html=True)

ai_left, ai_right = st.columns(2)

with ai_left:
    with st.container(key="comparison_summary_left", border=True):
        st.markdown(f"#### {phone_1}")
        st.caption(clean(insight_1.get("executive_summary")) if insight_1 is not None else "No summary available")

with ai_right:
    with st.container(key="comparison_summary_right", border=True):
        st.markdown(f"#### {phone_2}")
        st.caption(clean(insight_2.get("executive_summary")) if insight_2 is not None else "No summary available")

strength_left, strength_right = st.columns(2)

with strength_left:
    list_block(
        f"✅ {phone_1} Strengths",
        split_items(insight_1.get("top_strengths")) if insight_1 is not None else [],
        "strengths_left",
    )

with strength_right:
    list_block(
        f"✅ {phone_2} Strengths",
        split_items(insight_2.get("top_strengths")) if insight_2 is not None else [],
        "strengths_right",
    )

pain_left, pain_right = st.columns(2)

with pain_left:
    list_block(
        f"⚠️ {phone_1} Pain Points",
        split_items(insight_1.get("top_pain_points")) if insight_1 is not None else [],
        "pain_left",
    )

with pain_right:
    list_block(
        f"⚠️ {phone_2} Pain Points",
        split_items(insight_2.get("top_pain_points")) if insight_2 is not None else [],
        "pain_right",
    )
