import pandas as pd

from dashboard_data import read_sql, normalize_brands


USE_CASE_RULES = {
    "Gaming": {
        "positive": ["gaming", "game", "performance", "processor", "smooth", "fast", "refresh", "display", "battery"],
        "negative": ["lag", "slow", "hang", "heating", "stutter", "battery drain"],
    },
    "Camera & Social Media": {
        "positive": ["camera", "photo", "photography", "selfie", "video", "portrait", "social"],
        "negative": ["blur", "low light", "poor camera", "camera issue", "average camera"],
    },
    "Battery & Daily Use": {
        "positive": ["battery", "backup", "endurance", "long lasting", "daily use", "charging"],
        "negative": ["battery drain", "poor backup", "slow charging", "heating", "charging issue"],
    },
    "Work & Productivity": {
        "positive": ["performance", "multitasking", "software", "smooth", "battery", "display", "daily use"],
        "negative": ["lag", "slow", "hang", "bug", "software issue", "battery drain"],
    },
    "Entertainment": {
        "positive": ["display", "screen", "speaker", "audio", "battery", "video", "brightness"],
        "negative": ["display issue", "screen issue", "low brightness", "heating", "poor speaker"],
    },
    "Value for Money": {
        "positive": ["value", "money", "price", "budget", "affordable", "worth", "deal"],
        "negative": ["overpriced", "not worth", "poor", "bad", "issue"],
    },
}


def clean(value):
    if value is None or pd.isna(value):
        return ""
    value = str(value).strip()
    return "" if value.lower() == "nan" else value


def _text(row, cols):
    return " ".join(clean(row.get(col)) for col in cols).lower()


def _keyword_score(text, keywords):
    return sum(1 for keyword in keywords if keyword in text)


def _price_to_number(value):
    if value is None or pd.isna(value):
        return None

    value = str(value)
    value = (
        value.replace("₹", "")
        .replace(",", "")
        .replace("Rs.", "")
        .replace("Rs", "")
        .strip()
    )

    digits = "".join(ch for ch in value if ch.isdigit())

    if not digits:
        return None

    return float(digits)


def get_phone_finder_dataset():
    df = read_sql("""
        SELECT
            s.phone_id,
            s.phone_name,
            s.review_count,
            s.positive_percent,
            s.negative_percent,

            sp.brand,

            pi.price_segment,
            pi.flipkart_price,
            pi.amazon_price,
            pc.image_local_path,

            ai.top_strengths,
            ai.top_pain_points,
            ai.consumer_verdict,
            ai.executive_summary,
            ai.ideal_for,
            ai.avoid_if,
            ai.recommendation

        FROM phone_summary s
        LEFT JOIN phones_specifications sp
            ON s.phone_id = sp.phone_id
        LEFT JOIN phones_product_intelligence pi
            ON s.phone_id = pi.phone_id
        LEFT JOIN phones_product_catalog pc
            ON s.phone_id = pc.phone_id
        LEFT JOIN phone_ai_insights ai
            ON s.phone_id = ai.phone_id
    """)

    df["flipkart_price_num"] = df["flipkart_price"].apply(_price_to_number)
    df["amazon_price_num"] = df["amazon_price"].apply(_price_to_number)

    df["launch_price"] = df[
        ["flipkart_price_num", "amazon_price_num"]
    ].min(axis=1)

    return normalize_brands(df)


def recommend_by_use_case(df, use_case, budget=None, limit=5):
    if df.empty:
        return pd.DataFrame()

    result = df.copy()

    # Fixed evidence benchmark from full dataset.
    # Budget should affect eligibility, not intrinsic recommendation score.
    global_max_reviews = df["review_count"].fillna(0).max()

    if budget is not None:
        result = result[
            result["launch_price"].fillna(float("inf")) <= budget
        ].copy()

    if result.empty:
        return pd.DataFrame()

    rules = USE_CASE_RULES.get(use_case, {"positive": [], "negative": []})

    def source_weighted_fit(row):
        ideal_for_text = clean(row.get("ideal_for")).lower()
        strengths_text = clean(row.get("top_strengths")).lower()
        verdict_text = clean(row.get("consumer_verdict")).lower()
        recommendation_text = clean(row.get("recommendation")).lower()

        score = 0

        score += _keyword_score(ideal_for_text, rules["positive"]) * 30
        score += _keyword_score(strengths_text, rules["positive"]) * 25
        score += _keyword_score(verdict_text, rules["positive"]) * 15
        score += _keyword_score(recommendation_text, rules["positive"]) * 15

        return min(score, 100)

    def source_weighted_penalty(row):
        pain_text = clean(row.get("top_pain_points")).lower()
        avoid_text = clean(row.get("avoid_if")).lower()

        penalty = 0

        penalty += _keyword_score(pain_text, rules["negative"]) * 25
        penalty += _keyword_score(avoid_text, rules["negative"]) * 35

        return min(penalty, 100)

    result["use_case_fit"] = result.apply(source_weighted_fit, axis=1)
    result["use_case_penalty"] = result.apply(source_weighted_penalty, axis=1)

    result["sentiment_score"] = (
        result["positive_percent"]
        .fillna(0)
        .clip(0, 100)
    )

    result["risk_score"] = (
        100
        - result["negative_percent"]
        .fillna(0)
        .clip(0, 100)
    )

    if global_max_reviews > 0:
        result["evidence_score"] = (
            result["review_count"].fillna(0)
            / global_max_reviews
            * 100
        )
    else:
        result["evidence_score"] = 0

    result["recommendation_score"] = (
        result["use_case_fit"] * 0.50
        + result["sentiment_score"] * 0.25
        + result["risk_score"] * 0.15
        + result["evidence_score"] * 0.10
        - result["use_case_penalty"] * 0.25
    ).clip(0, 100).round(1)

    return (
        result.sort_values(
            ["recommendation_score", "positive_percent", "review_count"],
            ascending=[False, False, False],
        )
        .head(limit)
        .reset_index(drop=True)
    )


def recommend_by_budget(df, max_budget, min_budget=0, limit=10):
    if df.empty:
        return pd.DataFrame()

    result = df[
        (df["launch_price"].fillna(-1) >= min_budget)
        & (df["launch_price"].fillna(float("inf")) <= max_budget)
    ].copy()

    if result.empty:
        return pd.DataFrame()

    positive_text_cols = [
        "top_strengths",
        "ideal_for",
        "consumer_verdict",
        "recommendation",
    ]

    negative_text_cols = [
        "top_pain_points",
        "avoid_if",
    ]

    result["positive_text"] = result.apply(
        lambda row: _text(row, positive_text_cols),
        axis=1,
    )

    result["negative_text"] = result.apply(
        lambda row: _text(row, negative_text_cols),
        axis=1,
    )

    value_positive_terms = [
        "value",
        "money",
        "price",
        "budget",
        "affordable",
        "worth",
        "deal",
        "recommended",
    ]

    value_negative_terms = [
        "not worth",
        "overpriced",
        "poor",
        "bad",
        "issue",
        "avoid",
    ]

    result["value_positive_match"] = result["positive_text"].apply(
        lambda text: _keyword_score(text, value_positive_terms)
    )

    result["value_negative_match"] = result["negative_text"].apply(
        lambda text: _keyword_score(text, value_negative_terms)
    )

    result["sentiment_score"] = (
        result["positive_percent"]
        .fillna(0)
        .clip(0, 100)
    )

    result["risk_score"] = (
        100
        - result["negative_percent"]
        .fillna(0)
        .clip(0, 100)
    )

    max_reviews = result["review_count"].fillna(0).max()

    if max_reviews > 0:
        result["evidence_score"] = (
            result["review_count"].fillna(0)
            / max_reviews
            * 100
        )
    else:
        result["evidence_score"] = 0

    result["value_signal"] = (
        result["value_positive_match"] * 12
        - result["value_negative_match"] * 10
    ).clip(-30, 30)

    result["value_score"] = (
        result["sentiment_score"] * 0.55
        + result["risk_score"] * 0.25
        + result["evidence_score"] * 0.15
        + result["value_signal"] * 0.05
    ).clip(0, 100).round(1)

    return (
        result.sort_values(
            ["value_score", "positive_percent", "review_count"],
            ascending=[False, False, False],
        )
        .head(limit)
        .reset_index(drop=True)
    )


def get_phone_reason(row, use_case=None):
    strengths = clean(row.get("top_strengths"))
    ideal_for = clean(row.get("ideal_for"))
    verdict = clean(row.get("consumer_verdict"))

    if use_case and ideal_for:
        return f"Best fit for {use_case.lower()} because it is positioned as ideal for: {ideal_for}"

    if strengths:
        return strengths

    if verdict:
        return verdict

    return "Ranks strongly based on sentiment, low complaint risk and review evidence."


def get_phone_warning(row):
    pain = clean(row.get("top_pain_points"))
    avoid_if = clean(row.get("avoid_if"))

    if pain and avoid_if:
        return f"{pain} Also avoid if: {avoid_if}"

    if pain:
        return pain

    if avoid_if:
        return avoid_if

    return "No major recurring concern identified from available insights."


def build_use_case_summary(results, use_case):
    if results.empty:
        return f"No suitable phones were found for **{use_case}** under the selected conditions."

    best = results.iloc[0]

    return (
        f"**{best['phone_name']}** by **{best['brand']}** is the strongest "
        f"match for **{use_case}**, with a recommendation score of "
        f"**{best['recommendation_score']}/100**. The score weighs use-case fit, "
        f"positive sentiment, complaint risk and review evidence."
    )


def build_budget_summary(results, max_budget):
    if results.empty:
        return f"No phones were found within the selected budget of **₹{max_budget:,.0f}**."

    best = results.iloc[0]

    return (
        f"Within **₹{max_budget:,.0f}**, **{best['phone_name']}** by "
        f"**{best['brand']}** ranks highest on the value model with a score of "
        f"**{best['value_score']}/100**."
    )