import pandas as pd

from dashboard_data import read_sql, normalize_brands


PAIN_POINT_KEYWORDS = {
    "Software": ["software", "bug", "update", "ui", "os", "lag after update"],
    "Performance": ["lag", "slow", "hang", "stutter", "performance"],
    "Heating": ["heating", "heat", "warm", "thermal"],
    "Charging": ["charging", "charger", "slow charge", "charge"],
    "Battery Drain": ["battery drain", "drain", "backup", "battery issue"],
    "Camera": ["camera", "photo", "selfie", "video", "blur"],
    "Connectivity": ["network", "signal", "connectivity", "5g", "wifi", "call"],
    "Display": ["display", "screen", "brightness", "touch"],
    "Build Quality": ["build", "body", "design", "quality"],
}


FEATURE_KEYWORDS = {
    "Battery": ["battery", "backup"],
    "Connectivity": ["network", "5g", "connectivity", "signal", "wifi"],
    "Display": ["display", "screen", "refresh", "brightness"],
    "Performance": ["performance", "smooth", "processor", "gaming"],
    "Value for Money": ["value", "money", "price", "budget", "affordable"],
    "Camera": ["camera", "photo", "selfie", "video"],
    "Design": ["design", "look", "build"],
    "Software": ["software", "ui", "android"],
}


def clean(value):
    if value is None or pd.isna(value):
        return ""
    value = str(value).strip()
    return "" if value.lower() == "nan" else value


def get_consumer_dataset():
    df = read_sql("""
        SELECT
            s.phone_id,
            s.phone_name,
            s.review_count,
            s.positive_percent,
            s.negative_percent,

            sp.brand,

            pi.price_segment,

            ai.consumer_verdict,
            ai.executive_summary,
            ai.top_strengths,
            ai.top_pain_points,
            ai.ideal_for,
            ai.avoid_if,
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


def _contains(text, keywords):
    text = clean(text).lower()
    return any(k in text for k in keywords)


def _combined_text(row):
    return " ".join([
        clean(row.get("executive_summary")),
        clean(row.get("top_strengths")),
        clean(row.get("top_pain_points")),
        clean(row.get("ideal_for")),
        clean(row.get("avoid_if")),
        clean(row.get("recommendation")),
    ])


def pain_point_intelligence(df):
    rows = []

    for issue, keywords in PAIN_POINT_KEYWORDS.items():
        matched = df[
            df.apply(
                lambda row: _contains(_combined_text(row), keywords),
                axis=1,
            )
        ]

        if matched.empty:
            continue

        estimated_mentions = (
            matched["review_count"].fillna(0)
            * matched["negative_percent"].fillna(0)
            / 100
        ).sum()

        avg_negative = matched["negative_percent"].fillna(0).mean()

        if estimated_mentions >= 500 or avg_negative >= 30:
            severity = "High"
        elif estimated_mentions >= 200 or avg_negative >= 18:
            severity = "Medium"
        else:
            severity = "Low"

        affected_brands_count = (
            matched.groupby("brand")
            .size()
            .sort_values(ascending=False)
        )

        affected_brands = ", ".join(
            f"{brand} ({count})"
            for brand, count in affected_brands_count.head(5).items()
        )

        example_phones = (
            matched["phone_name"]
            .dropna()
            .drop_duplicates()
            .head(5)
            .tolist()
        )

        rows.append({
            "issue": issue,
            "mentions": round(float(estimated_mentions)),
            "phones": int(matched["phone_id"].nunique()),
            "brands": int(matched["brand"].nunique()),
            "severity": severity,
            "affected_brands": affected_brands,
            "example_phones": ", ".join(example_phones),
            "recommendation": _issue_recommendation(issue),
        })

    return pd.DataFrame(rows).sort_values("mentions", ascending=False)


def feature_intelligence(df):
    rows = []

    for feature, keywords in FEATURE_KEYWORDS.items():
        matched = df[df.apply(lambda row: _contains(_combined_text(row), keywords), axis=1)]

        if matched.empty:
            continue

        estimated_mentions = (
            matched["review_count"].fillna(0)
            * matched["positive_percent"].fillna(0)
            / 100
        ).sum()

        best_brand = (
            matched.groupby("brand")["positive_percent"]
            .mean()
            .sort_values(ascending=False)
            .index[0]
        )

        rows.append({
            "feature": feature,
            "mentions": round(float(estimated_mentions)),
            "phones": int(matched["phone_id"].nunique()),
            "brands": int(matched["brand"].nunique()),
            "best_brand": best_brand,
            "example_phones": ", ".join(matched["phone_name"].head(3).tolist()),
            "opportunity": _feature_opportunity(feature),
        })

    return pd.DataFrame(rows).sort_values("mentions", ascending=False)


def _issue_recommendation(issue):
    mapping = {
        "Software": "Prioritize OTA stability, bug fixing and UI smoothness.",
        "Performance": "Review chipset optimization, memory management and app switching performance.",
        "Heating": "Investigate thermal tuning, gaming load and charging heat behaviour.",
        "Charging": "Review charger compatibility, charging speed claims and bundled accessories.",
        "Battery Drain": "Improve idle drain, background app control and battery optimization.",
        "Camera": "Improve image processing, low-light output and camera consistency.",
        "Connectivity": "Investigate signal stability, call quality and 5G reliability.",
        "Display": "Review brightness, touch response and screen quality expectations.",
        "Build Quality": "Review durability perception, material quality and finish consistency.",
    }
    return mapping.get(issue, "Investigate this issue using review evidence.")


def _feature_opportunity(feature):
    mapping = {
        "Battery": "Use battery endurance as a core marketing hook.",
        "Connectivity": "Position network reliability and 5G experience clearly.",
        "Display": "Highlight screen quality, refresh rate and viewing experience.",
        "Performance": "Use smooth everyday performance as a sales pitch.",
        "Value for Money": "Emphasize price-to-feature advantage.",
        "Camera": "Build campaign messaging around photography and social use.",
        "Design": "Use design and build quality in lifestyle positioning.",
        "Software": "Highlight clean UI and software experience where reviews support it.",
    }
    return mapping.get(feature, "Use this strength in marketing and sales messaging.")


def build_consumer_brief(pain_df, feature_df):
    top_issue = pain_df.iloc[0] if not pain_df.empty else None
    top_feature = feature_df.iloc[0] if not feature_df.empty else None

    if top_issue is None or top_feature is None:
        return "Consumer intelligence is not available yet."

    return (
        f"Customers are most positive about **{top_feature['feature']}**, "
        f"with around **{top_feature['mentions']} estimated positive mentions** across "
        f"{top_feature['phones']} phones. The biggest recurring concern is "
        f"**{top_issue['issue']}**, affecting {top_issue['phones']} phones with "
        f"around **{top_issue['mentions']} estimated negative mentions**. "
        f"Product teams should focus on **{top_issue['recommendation']}** while "
        f"marketing teams can use **{top_feature['opportunity']}**"
    )