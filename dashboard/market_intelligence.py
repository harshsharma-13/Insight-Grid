import re
import pandas as pd

from dashboard_data import read_sql, normalize_brands


PAIN_POINT_KEYWORDS = {
    "Heating": ["heating", "heat", "warm"],
    "Battery Drain": ["battery drain", "drain", "backup", "battery issue"],
    "Charging": ["charging", "charge", "slow charging", "charger"],
    "Camera": ["camera", "photo", "selfie", "video", "blur"],
    "Performance": ["lag", "slow", "performance", "hang", "stutter"],
    "Software": ["software", "bug", "update", "ui", "os"],
    "Connectivity": ["network", "signal", "connectivity", "5g", "wifi", "call"],
    "Display": ["display", "screen", "brightness", "touch"],
    "Build Quality": ["build", "body", "design", "quality"],
}

LOVE_KEYWORDS = {
    "Battery": ["battery", "backup"],
    "Camera": ["camera", "photo", "selfie", "video"],
    "Display": ["display", "screen", "refresh", "brightness"],
    "Performance": ["performance", "smooth", "processor", "gaming"],
    "Design": ["design", "look", "build"],
    "Value for Money": ["value", "money", "price", "budget"],
    "Software": ["software", "ui", "android"],
    "Connectivity": ["network", "5g", "connectivity", "wifi"],
}


def clean(value):
    if value is None or pd.isna(value):
        return ""
    value = str(value).strip()
    return "" if value.lower() == "nan" else value


def parse_price(value):
    value = clean(value).replace("₹", "").replace(",", "").strip()
    try:
        return float(value)
    except Exception:
        return None


def get_market_dataset():
    df = read_sql("""
        SELECT
            s.phone_id,
            s.phone_name,
            s.review_count,
            s.positive_percent,
            s.negative_percent,

            sp.brand,
            sp.display,
            sp.processor,
            sp.battery,
            sp.charging,
            sp.rear_camera,
            sp.front_camera,
            sp.supports_5g,

            pi.amazon_price,
            pi.flipkart_price,
            pi.amazon_rating,
            pi.flipkart_rating,
            pi.price_segment,

            ai.consumer_verdict,
            ai.executive_summary,
            ai.top_strengths,
            ai.top_pain_points,
            ai.recommendation

        FROM phone_summary s
        LEFT JOIN phones_specifications sp
            ON s.phone_id = sp.phone_id
        LEFT JOIN phones_product_intelligence pi
            ON s.phone_id = pi.phone_id
        LEFT JOIN phone_ai_insights ai
            ON s.phone_id = ai.phone_id
    """)


    return normalize_brands(df)

def add_price_segment(df):
    df = df.copy()

    def best_price(row):
        prices = [
            parse_price(row.get("amazon_price")),
            parse_price(row.get("flipkart_price")),
        ]
        prices = [p for p in prices if p is not None]
        return min(prices) if prices else None

    def segment(price):
        if price is None or pd.isna(price):
            return "Unknown"
        if price <= 15000:
            return "Budget"
        if price <= 25000:
            return "Mid-range"
        return "Upper Mid-range"

    df["best_price"] = df.apply(best_price, axis=1)
    df["derived_segment"] = df["best_price"].apply(segment)

    return df


def keyword_match(text, keywords):
    text = clean(text).lower()
    return any(keyword in text for keyword in keywords)


def aggregate_pain_points(df, brand=None, segment=None):
    df = add_price_segment(df)

    if brand and brand != "All":
        df = df[df["brand"] == brand]

    if segment and segment != "All":
        df = df[df["derived_segment"] == segment]

    rows = []

    for issue, keywords in PAIN_POINT_KEYWORDS.items():
        matched = df[
            df.apply(
                lambda row: keyword_match(
                    " ".join([
                        clean(row.get("top_pain_points")),
                        clean(row.get("executive_summary")),
                        clean(row.get("recommendation")),
                    ]),
                    keywords,
                ),
                axis=1,
            )
        ]

        if matched.empty:
            rows.append({
                "issue": issue,
                "phones_affected": 0,
                "brands_affected": 0,
                "estimated_negative_reviews": 0,
                "avg_negative_percent": 0,
                "severity": "Low",
                "example_phones": "",
            })
            continue

        estimated_negative = (
            matched["review_count"].fillna(0) *
            matched["negative_percent"].fillna(0) / 100
        ).sum()

        avg_negative = matched["negative_percent"].fillna(0).mean()

        if estimated_negative >= 80 or avg_negative >= 30:
            severity = "High"
        elif estimated_negative >= 30 or avg_negative >= 18:
            severity = "Medium"
        else:
            severity = "Low"

        rows.append({
            "issue": issue,
            "phones_affected": int(matched["phone_id"].nunique()),
            "brands_affected": int(matched["brand"].nunique()),
            "estimated_negative_reviews": round(float(estimated_negative), 1),
            "avg_negative_percent": round(float(avg_negative), 1),
            "severity": severity,
            "example_phones": ", ".join(matched["phone_name"].head(3).tolist()),
        })

    result = pd.DataFrame(rows)
    return result.sort_values(
        ["estimated_negative_reviews", "phones_affected"],
        ascending=False,
    )


def aggregate_customer_loves(df, brand=None, segment=None):
    df = add_price_segment(df)

    if brand and brand != "All":
        df = df[df["brand"] == brand]

    if segment and segment != "All":
        df = df[df["derived_segment"] == segment]

    rows = []

    for feature, keywords in LOVE_KEYWORDS.items():
        matched = df[
            df.apply(
                lambda row: keyword_match(
                    " ".join([
                        clean(row.get("top_strengths")),
                        clean(row.get("executive_summary")),
                        clean(row.get("recommendation")),
                    ]),
                    keywords,
                ),
                axis=1,
            )
        ]

        estimated_positive = (
            matched["review_count"].fillna(0) *
            matched["positive_percent"].fillna(0) / 100
        ).sum()

        rows.append({
            "feature": feature,
            "phones_affected": int(matched["phone_id"].nunique()),
            "estimated_positive_reviews": round(float(estimated_positive), 1),
            "avg_positive_percent": round(float(matched["positive_percent"].fillna(0).mean()), 1) if not matched.empty else 0,
            "example_phones": ", ".join(matched["phone_name"].head(3).tolist()) if not matched.empty else "",
        })

    result = pd.DataFrame(rows)
    return result.sort_values(
        ["estimated_positive_reviews", "phones_affected"],
        ascending=False,
    )


def get_segment_overview(df):
    df = add_price_segment(df)

    rows = []

    for segment, group in df.groupby("derived_segment"):
        if segment == "Unknown":
            continue

        pain = aggregate_pain_points(group)
        loves = aggregate_customer_loves(group)

        top_pain = pain.iloc[0]["issue"] if not pain.empty else "Not available"
        top_love = loves.iloc[0]["feature"] if not loves.empty else "Not available"

        brand_health = (
            group.groupby("brand")["positive_percent"]
            .mean()
            .sort_values(ascending=False)
        )

        leading_brand = brand_health.index[0] if not brand_health.empty else "Not available"

        rows.append({
            "segment": segment,
            "phones": int(group["phone_id"].nunique()),
            "reviews": int(group["review_count"].fillna(0).sum()),
            "avg_positive": round(float(group["positive_percent"].fillna(0).mean()), 1),
            "top_strength": top_love,
            "top_concern": top_pain,
            "leading_brand": leading_brand,
        })

    return pd.DataFrame(rows)


def get_brand_landscape(df):
    df = add_price_segment(df)

    rows = []

    for brand, group in df.groupby("brand"):
        if not clean(brand):
            continue

        pain = aggregate_pain_points(group)
        loves = aggregate_customer_loves(group)

        rows.append({
            "brand": brand,
            "phones": int(group["phone_id"].nunique()),
            "reviews": int(group["review_count"].fillna(0).sum()),
            "avg_positive": round(float(group["positive_percent"].fillna(0).mean()), 1),
            "avg_negative": round(float(group["negative_percent"].fillna(0).mean()), 1),
            "top_strength": loves.iloc[0]["feature"] if not loves.empty else "Not available",
            "top_concern": pain.iloc[0]["issue"] if not pain.empty else "Not available",
        })

    return pd.DataFrame(rows).sort_values("avg_positive", ascending=False)


def build_market_summary(df):
    pain = aggregate_pain_points(df)
    loves = aggregate_customer_loves(df)
    segments = get_segment_overview(df)

    top_pain = pain.iloc[0]["issue"] if not pain.empty else "Not available"
    top_love = loves.iloc[0]["feature"] if not loves.empty else "Not available"

    best_segment = (
        segments.sort_values("avg_positive", ascending=False).iloc[0]["segment"]
        if not segments.empty else "Not available"
    )

    return (
        f"Customers are responding most positively to **{top_love}**, while "
        f"the most visible concern across the dataset is **{top_pain}**. "
        f"The strongest segment by average positive sentiment is **{best_segment}**. "
        f"Product teams should prioritize recurring pain points, while marketing teams "
        f"can use the most appreciated features as campaign hooks."
    )