import pandas as pd

from dashboard_data import read_sql


STRENGTH_CATEGORIES = {
    "Battery": [
        "battery",
        "backup",
        "endurance",
        "battery life",
    ],
    "Camera": [
        "camera",
        "photo",
        "selfie",
        "video",
        "photography",
    ],
    "Performance": [
        "performance",
        "smooth",
        "processor",
        "gaming",
        "fast",
        "multitasking",
    ],
    "Display": [
        "display",
        "screen",
        "brightness",
        "refresh",
        "amoled",
    ],
    "Design": [
        "design",
        "build",
        "look",
        "premium",
        "finish",
    ],
    "Connectivity": [
        "network",
        "signal",
        "5g",
        "connectivity",
        "wifi",
    ],
    "Software": [
        "software",
        "ui",
        "android",
        "clean ui",
        "interface",
    ],
    "Value for Money": [
        "value",
        "price",
        "budget",
        "affordable",
        "worth",
    ],
}


CONCERN_CATEGORIES = {
    "Software": [
        "software",
        "bug",
        "bugs",
        "update",
        "ui",
        "os",
        "glitch",
    ],
    "Performance": [
        "lag",
        "slow",
        "hang",
        "stutter",
        "performance issue",
    ],
    "Heating": [
        "heating",
        "heat",
        "warm",
        "thermal",
    ],
    "Charging": [
        "charging",
        "charger",
        "slow charge",
        "charging issue",
    ],
    "Battery Drain": [
        "battery drain",
        "drain",
        "poor backup",
        "battery issue",
    ],
    "Camera": [
        "camera",
        "blur",
        "low light",
        "photo quality",
        "camera issue",
    ],
    "Connectivity": [
        "network",
        "signal",
        "5g",
        "wifi",
        "call",
        "connectivity",
    ],
    "Display": [
        "display",
        "screen",
        "brightness",
        "touch",
    ],
    "Build Quality": [
        "build",
        "body",
        "quality",
        "durability",
    ],
}


def clean(value):
    if value is None or pd.isna(value):
        return ""

    value = str(value).strip()

    if value.lower() == "nan":
        return ""

    return value


def _combined_column_text(series):
    return " ".join(
        clean(value)
        for value in series
        if clean(value)
    ).lower()


def _top_category(text, category_map):
    if not text:
        return "Not identified"

    scores = {
        category: sum(
            text.count(keyword.lower())
            for keyword in keywords
        )
        for category, keywords in category_map.items()
    }

    if not scores:
        return "Not identified"

    highest_score = max(scores.values())

    if highest_score == 0:
        return "Not identified"

    return max(scores, key=scores.get)


def get_competitive_dataset():
    df = read_sql("""
        SELECT
            s.phone_id,
            s.phone_name,
            s.review_count,
            s.positive_percent,
            s.negative_percent,

            sp.brand,

            pi.price_segment,

            ai.top_strengths,
            ai.top_pain_points,
            ai.consumer_verdict,
            ai.executive_summary

        FROM phone_summary s

        LEFT JOIN phones_specifications sp
            ON s.phone_id = sp.phone_id

        LEFT JOIN phones_product_intelligence pi
            ON s.phone_id = pi.phone_id

        LEFT JOIN phone_ai_insights ai
            ON s.phone_id = ai.phone_id
    """)


    df["brand"] = df["brand"].replace({
        "LAVA": "Lava",
        "Moto": "Motorola",
    })

    return df

def brand_leaderboard(df):
    if df.empty:
        return pd.DataFrame(
            columns=[
                "brand",
                "phones",
                "reviews",
                "avg_positive",
                "avg_negative",
            ]
        )

    valid_df = df[df["brand"].notna()].copy()

    leaderboard = (
        valid_df.groupby("brand")
        .agg(
            phones=("phone_id", "nunique"),
            reviews=("review_count", "sum"),
            avg_positive=("positive_percent", "mean"),
            avg_negative=("negative_percent", "mean"),
        )
        .reset_index()
    )

    leaderboard["reviews"] = (
        leaderboard["reviews"]
        .fillna(0)
        .astype(int)
    )

    leaderboard["avg_positive"] = (
        leaderboard["avg_positive"]
        .fillna(0)
        .round(1)
    )

    leaderboard["avg_negative"] = (
        leaderboard["avg_negative"]
        .fillna(0)
        .round(1)
    )

    return leaderboard.sort_values(
        ["avg_positive", "reviews"],
        ascending=[False, False],
    ).reset_index(drop=True)


def brand_scorecards(df):
    rows = []

    if df.empty:
        return pd.DataFrame(
            columns=[
                "brand",
                "phones",
                "reviews",
                "avg_positive",
                "avg_negative",
                "top_strength",
                "top_concern",
            ]
        )

    brands = sorted(
        df["brand"]
        .dropna()
        .unique()
        .tolist()
    )

    for brand in brands:
        subset = df[df["brand"] == brand].copy()

        strength_text = _combined_column_text(
            subset["top_strengths"]
        )

        concern_text = _combined_column_text(
            subset["top_pain_points"]
        )

        top_strength = _top_category(
            strength_text,
            STRENGTH_CATEGORIES,
        )

        top_concern = _top_category(
            concern_text,
            CONCERN_CATEGORIES,
        )

        avg_positive = subset["positive_percent"].mean()
        avg_negative = subset["negative_percent"].mean()

        rows.append(
            {
                "brand": brand,
                "phones": int(
                    subset["phone_id"].nunique()
                ),
                "reviews": int(
                    subset["review_count"]
                    .fillna(0)
                    .sum()
                ),
                "avg_positive": round(
                    float(avg_positive)
                    if pd.notna(avg_positive)
                    else 0,
                    1,
                ),
                "avg_negative": round(
                    float(avg_negative)
                    if pd.notna(avg_negative)
                    else 0,
                    1,
                ),
                "top_strength": top_strength,
                "top_concern": top_concern,
            }
        )

    result = pd.DataFrame(rows)

    if result.empty:
        return result

    return result.sort_values(
        ["avg_positive", "reviews"],
        ascending=[False, False],
    ).reset_index(drop=True)


def segment_leaders(df):
    rows = []

    if df.empty:
        return pd.DataFrame(
            columns=[
                "segment",
                "leader",
                "positive",
            ]
        )

    segments = (
        df["price_segment"]
        .dropna()
        .unique()
        .tolist()
    )

    preferred_order = [
        "Budget",
        "Mid-range",
        "Upper Mid-range",
    ]

    ordered_segments = [
        segment
        for segment in preferred_order
        if segment in segments
    ]

    remaining_segments = sorted(
        [
            segment
            for segment in segments
            if segment not in preferred_order
        ]
    )

    ordered_segments.extend(remaining_segments)

    for segment in ordered_segments:
        segment_df = df[
            df["price_segment"] == segment
        ].copy()

        brand_performance = (
            segment_df[
                segment_df["brand"].notna()
            ]
            .groupby("brand")
            .agg(
                positive=("positive_percent", "mean"),
                phones=("phone_id", "nunique"),
                reviews=("review_count", "sum"),
            )
            .reset_index()
        )

        if brand_performance.empty:
            continue

        brand_performance = (
            brand_performance.sort_values(
                ["positive", "reviews"],
                ascending=[False, False],
            )
        )

        leader = brand_performance.iloc[0]

        rows.append(
            {
                "segment": segment,
                "leader": leader["brand"],
                "positive": round(
                    float(leader["positive"]),
                    1,
                ),
            }
        )

    return pd.DataFrame(rows)


def whitespace_opportunities(df):
    if df.empty:
        return pd.DataFrame(
            columns=[
                "brand",
                "opportunity",
            ]
        )

    scorecards = brand_scorecards(df)

    if scorecards.empty:
        return pd.DataFrame(
            columns=[
                "brand",
                "opportunity",
            ]
        )

    market_positive = scorecards[
        "avg_positive"
    ].mean()

    market_negative = scorecards[
        "avg_negative"
    ].mean()

    opportunities = []

    for _, row in scorecards.iterrows():
        if row["avg_positive"] >= market_positive:
            continue

        if row["top_concern"] == "Software":
            opportunity = (
                "Improve software stability, update quality and UI smoothness "
                "to close the sentiment gap with stronger competitors."
            )

        elif row["top_concern"] == "Performance":
            opportunity = (
                "Strengthen everyday smoothness, memory management and sustained "
                "performance to improve competitive perception."
            )

        elif row["top_concern"] == "Heating":
            opportunity = (
                "Reduce thermal complaints through optimization of gaming, "
                "charging and heavy-use behaviour."
            )

        elif row["top_concern"] == "Camera":
            opportunity = (
                "Improve camera consistency and low-light output to strengthen "
                "product differentiation."
            )

        elif row["top_concern"] == "Battery Drain":
            opportunity = (
                "Improve battery optimization and idle drain performance to "
                "strengthen endurance perception."
            )

        elif row["top_concern"] == "Connectivity":
            opportunity = (
                "Improve network reliability, call quality and 5G stability "
                "to build stronger everyday-use confidence."
            )

        else:
            opportunity = (
                f"Address {row['top_concern'].lower()} concerns while reinforcing "
                f"{row['top_strength'].lower()} as the primary competitive advantage."
            )

        if row["avg_negative"] > market_negative:
            opportunity += (
                " Negative sentiment is also above the market benchmark, "
                "making this a higher-priority improvement area."
            )

        opportunities.append(
            {
                "brand": row["brand"],
                "opportunity": opportunity,
            }
        )

    return pd.DataFrame(opportunities)


def build_competitive_summary(df):
    leaderboard = brand_leaderboard(df)

    if leaderboard.empty:
        return "Competitive intelligence is not available yet."

    sentiment_leader = leaderboard.iloc[0]

    review_leader = (
        leaderboard
        .sort_values(
            "reviews",
            ascending=False,
        )
        .iloc[0]
    )

    risk_brand = (
        leaderboard
        .sort_values(
            "avg_negative",
            ascending=False,
        )
        .iloc[0]
    )

    total_brands = int(
        leaderboard["brand"].nunique()
    )

    total_phones = int(
        df["phone_id"].nunique()
    )

    return (
        f"**{sentiment_leader['brand']}** currently leads sentiment with "
        f"**{sentiment_leader['avg_positive']}% average positive sentiment**. "
        f"**{review_leader['brand']}** has the strongest review coverage with "
        f"**{int(review_leader['reviews']):,} reviews**, while "
        f"**{risk_brand['brand']}** records the highest average negative sentiment "
        f"at **{risk_brand['avg_negative']}%**. "
        f"The competitive benchmark covers **{total_brands} brands** across "
        f"**{total_phones} smartphones**."
    )


def compare_brands(df, brand_a, brand_b):
    scorecards = brand_scorecards(df)

    brand_a_data = scorecards[
        scorecards["brand"] == brand_a
    ]

    brand_b_data = scorecards[
        scorecards["brand"] == brand_b
    ]

    if brand_a_data.empty or brand_b_data.empty:
        return None

    a = brand_a_data.iloc[0]
    b = brand_b_data.iloc[0]

    comparison = {
        "brand_a": {
            "brand": a["brand"],
            "phones": int(a["phones"]),
            "reviews": int(a["reviews"]),
            "avg_positive": float(a["avg_positive"]),
            "avg_negative": float(a["avg_negative"]),
            "top_strength": a["top_strength"],
            "top_concern": a["top_concern"],
        },
        "brand_b": {
            "brand": b["brand"],
            "phones": int(b["phones"]),
            "reviews": int(b["reviews"]),
            "avg_positive": float(b["avg_positive"]),
            "avg_negative": float(b["avg_negative"]),
            "top_strength": b["top_strength"],
            "top_concern": b["top_concern"],
        },
    }

    comparison["positive_gap"] = round(
        a["avg_positive"] - b["avg_positive"],
        1,
    )

    comparison["negative_gap"] = round(
        a["avg_negative"] - b["avg_negative"],
        1,
    )

    comparison["review_gap"] = int(
        a["reviews"] - b["reviews"]
    )

    return comparison


def build_competitive_recommendation(comparison):
    if comparison is None:
        return "Competitive recommendation is not available."

    a = comparison["brand_a"]
    b = comparison["brand_b"]

    positive_gap = comparison["positive_gap"]
    negative_gap = comparison["negative_gap"]

    messages = []

    if positive_gap > 5:
        messages.append(
            f"**{a['brand']}** holds a clear sentiment advantage over "
            f"**{b['brand']}**, leading by **{positive_gap:.1f} percentage points** "
            f"in average positive sentiment."
        )

    elif positive_gap < -5:
        messages.append(
            f"**{a['brand']}** trails **{b['brand']}** by "
            f"**{abs(positive_gap):.1f} percentage points** in positive sentiment, "
            f"indicating a meaningful customer experience gap."
        )

    else:
        messages.append(
            f"**{a['brand']}** and **{b['brand']}** are relatively close in "
            f"positive sentiment, so differentiation is likely to depend more on "
            f"specific product strengths and recurring pain points."
        )

    if a["top_strength"] != "Not identified":
        messages.append(
            f"{a['brand']} should continue defending its strength in "
            f"**{a['top_strength']}**."
        )

    if a["top_concern"] != "Not identified":
        messages.append(
            f"Its clearest improvement priority is **{a['top_concern']}**, "
            f"which should be addressed to improve competitive perception."
        )

    if (
        b["top_strength"] != "Not identified"
        and b["top_strength"] != a["top_strength"]
    ):
        messages.append(
            f"Meanwhile, {b['brand']}'s strength in **{b['top_strength']}** "
            f"represents an area that should be monitored when shaping product "
            f"positioning and communication."
        )

    if negative_gap > 5:
        messages.append(
            f"{a['brand']} also has materially higher negative sentiment than "
            f"{b['brand']}, making complaint reduction an immediate priority."
        )

    return " ".join(messages)


def compare_brands(df, brand_a, brand_b):
    scorecards = brand_scorecards(df)

    brand_a_data = scorecards[
        scorecards["brand"] == brand_a
    ]

    brand_b_data = scorecards[
        scorecards["brand"] == brand_b
    ]

    if brand_a_data.empty or brand_b_data.empty:
        return None

    a = brand_a_data.iloc[0]
    b = brand_b_data.iloc[0]

    comparison = {
        "brand_a": {
            "brand": a["brand"],
            "phones": int(a["phones"]),
            "reviews": int(a["reviews"]),
            "avg_positive": float(a["avg_positive"]),
            "avg_negative": float(a["avg_negative"]),
            "top_strength": a["top_strength"],
            "top_concern": a["top_concern"],
        },
        "brand_b": {
            "brand": b["brand"],
            "phones": int(b["phones"]),
            "reviews": int(b["reviews"]),
            "avg_positive": float(b["avg_positive"]),
            "avg_negative": float(b["avg_negative"]),
            "top_strength": b["top_strength"],
            "top_concern": b["top_concern"],
        },
    }

    comparison["positive_gap"] = round(
        a["avg_positive"] - b["avg_positive"],
        1,
    )

    comparison["negative_gap"] = round(
        a["avg_negative"] - b["avg_negative"],
        1,
    )

    comparison["review_gap"] = int(
        a["reviews"] - b["reviews"]
    )

    return comparison


def build_competitive_recommendation(comparison):
    if comparison is None:
        return "Competitive recommendation is not available."

    a = comparison["brand_a"]
    b = comparison["brand_b"]

    positive_gap = comparison["positive_gap"]
    negative_gap = comparison["negative_gap"]

    messages = []

    if positive_gap > 5:
        messages.append(
            f"**{a['brand']}** holds a clear sentiment advantage over "
            f"**{b['brand']}**, leading by **{positive_gap:.1f} percentage points** "
            f"in average positive sentiment."
        )

    elif positive_gap < -5:
        messages.append(
            f"**{a['brand']}** trails **{b['brand']}** by "
            f"**{abs(positive_gap):.1f} percentage points** in positive sentiment, "
            f"indicating a meaningful customer experience gap."
        )

    else:
        messages.append(
            f"**{a['brand']}** and **{b['brand']}** are relatively close in "
            f"positive sentiment, so differentiation is likely to depend more on "
            f"specific product strengths and recurring pain points."
        )

    if a["top_strength"] != "Not identified":
        messages.append(
            f"{a['brand']} should continue defending its strength in "
            f"**{a['top_strength']}**."
        )

    if a["top_concern"] != "Not identified":
        messages.append(
            f"Its clearest improvement priority is **{a['top_concern']}**, "
            f"which should be addressed to improve competitive perception."
        )

    if (
        b["top_strength"] != "Not identified"
        and b["top_strength"] != a["top_strength"]
    ):
        messages.append(
            f"Meanwhile, {b['brand']}'s strength in **{b['top_strength']}** "
            f"represents an area that should be monitored when shaping product "
            f"positioning and communication."
        )

    if negative_gap > 5:
        messages.append(
            f"{a['brand']} also has materially higher negative sentiment than "
            f"{b['brand']}, making complaint reduction an immediate priority."
        )

    return " ".join(messages)