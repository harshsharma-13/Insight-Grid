import re
import pandas as pd

from dashboard_data import read_sql, normalize_brands


def clean(value):
    if value is None or pd.isna(value):
        return ""
    value = str(value).strip()
    return "" if value.lower() == "nan" else value


def parse_price(value):
    value = clean(value)
    value = (
        value.replace("₹", "")
        .replace("Rs.", "")
        .replace("Rs", "")
        .replace(",", "")
        .strip()
    )

    try:
        return float(value)
    except Exception:
        return None


def extract_budget(query):
    q = query.lower().replace(",", "")

    patterns = [
        r"under\s*₹?\s*(\d+)",
        r"below\s*₹?\s*(\d+)",
        r"less than\s*₹?\s*(\d+)",
        r"within\s*₹?\s*(\d+)",
    ]

    for pattern in patterns:
        match = re.search(pattern, q)
        if match:
            return float(match.group(1))

    return None


def detect_topic(query):
    q = query.lower()

    if any(x in q for x in ["battery", "charging", "backup", "mah"]):
        return "battery"
    if any(x in q for x in ["camera", "photo", "selfie", "video", "photography"]):
        return "camera"
    if any(x in q for x in ["gaming", "game", "bgmi", "pubg", "processor", "performance", "lag"]):
        return "gaming"
    if any(x in q for x in ["heating", "heat", "thermal"]):
        return "heating"
    if any(x in q for x in ["value", "money", "budget", "price", "cheap", "under", "below", "worth"]):
        return "value"
    if any(x in q for x in ["parents", "parent", "elderly", "simple", "basic"]):
        return "parents"

    return "overall"


def get_search_dataset():
    df = read_sql("""
        SELECT
            s.phone_id,
            s.phone_name,

            sp.brand,
            pc.image_local_path,
            sp.display,
            sp.display_type,
            sp.refresh_rate,
            sp.processor,
            sp.ram,
            sp.storage,
            sp.battery,
            sp.charging,
            sp.rear_camera,
            sp.front_camera,
            sp.android_version,
            sp.supports_5g,

            pi.amazon_price,
            pi.flipkart_price,
            pi.launch_price,
            pi.amazon_rating,
            pi.flipkart_rating,
            pi.price_segment,

            s.review_count,
            s.positive_percent,
            s.neutral_percent,
            s.negative_percent,

            ai.consumer_verdict,
            ai.executive_summary,
            ai.top_strengths,
            ai.top_pain_points,
            ai.platform_insight,
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

    return normalize_brands(df)


def best_available_price(row):
    prices = [
        parse_price(row.get("launch_price")),
        parse_price(row.get("amazon_price")),
        parse_price(row.get("flipkart_price")),
    ]

    prices = [p for p in prices if p is not None]
    return min(prices) if prices else None


def extract_first_number(text):
    text = clean(text).replace(",", "")
    match = re.search(r"(\d+(\.\d+)?)", text)
    if match:
        return float(match.group(1))
    return 0


def ram_score(value):
    ram = extract_first_number(value)
    return min(ram / 8, 1) * 100 if ram else 40


def storage_score(value):
    storage = extract_first_number(value)
    return min(storage / 256, 1) * 100 if storage else 40


def battery_score(value):
    battery = extract_first_number(value)
    if not battery:
        return 40
    return min(battery / 7000, 1) * 100


def charging_score(value):
    charging = extract_first_number(value)
    if not charging:
        return 35
    return min(charging / 80, 1) * 100


def camera_score(value):
    camera = extract_first_number(value)
    if not camera:
        return 40
    return min(camera / 108, 1) * 100


def refresh_score(value):
    refresh = extract_first_number(value)
    if not refresh:
        return 40
    return min(refresh / 144, 1) * 100


def processor_score(value):
    text = clean(value).lower()

    high = [
        "dimensity 7400",
        "dimensity 7300",
        "snapdragon 7",
        "snapdragon 6",
        "helio g99",
    ]

    mid = [
        "dimensity 6300",
        "dimensity 6100",
        "snapdragon 4",
        "helio",
        "mediatek",
        "unisoc",
    ]

    if any(x in text for x in high):
        return 90
    if any(x in text for x in mid):
        return 65
    if text:
        return 55

    return 40


def text_contains(row, keywords):
    text = " ".join([
        clean(row.get("executive_summary")),
        clean(row.get("top_strengths")),
        clean(row.get("top_pain_points")),
        clean(row.get("ideal_for")),
        clean(row.get("avoid_if")),
        clean(row.get("recommendation")),
        clean(row.get("platform_insight")),
    ]).lower()

    return any(k in text for k in keywords)


def sentiment_score(row):
    positive = float(row.get("positive_percent", 0) or 0)
    negative = float(row.get("negative_percent", 0) or 0)
    return max(0, positive - negative * 0.5)


def confidence_score(row):
    reviews = float(row.get("review_count", 0) or 0)
    return min(reviews / 150, 1) * 100


def value_score(row):
    price = row.get("best_price")

    if price is None or pd.isna(price):
        price_component = 45
    else:
        price_component = max(0, 100 - (price / 25000 * 100))

    specs_component = (
        processor_score(row.get("processor")) * 0.25
        + ram_score(row.get("ram")) * 0.15
        + storage_score(row.get("storage")) * 0.10
        + battery_score(row.get("battery")) * 0.20
        + charging_score(row.get("charging")) * 0.10
        + camera_score(row.get("rear_camera")) * 0.10
        + refresh_score(row.get("refresh_rate")) * 0.10
    )

    return (
        price_component * 0.30
        + specs_component * 0.40
        + sentiment_score(row) * 0.20
        + confidence_score(row) * 0.10
    )


def calculate_recommendation_score(row, topic):
    base_sentiment = sentiment_score(row)
    confidence = confidence_score(row)

    if topic == "battery":
        score = (
            battery_score(row.get("battery")) * 0.35
            + charging_score(row.get("charging")) * 0.15
            + base_sentiment * 0.25
            + confidence * 0.10
        )
        if text_contains(row, ["battery", "backup"]):
            score += 12
        if text_contains(row, ["battery drain", "charging issue", "slow charging"]):
            score -= 12
        return score

    if topic == "camera":
        score = (
            camera_score(row.get("rear_camera")) * 0.30
            + camera_score(row.get("front_camera")) * 0.12
            + base_sentiment * 0.25
            + confidence * 0.10
        )
        if text_contains(row, ["camera", "photo", "selfie"]):
            score += 14
        if text_contains(row, ["camera issue", "blur", "poor camera"]):
            score -= 12
        return score

    if topic == "gaming":
        score = (
            processor_score(row.get("processor")) * 0.35
            + ram_score(row.get("ram")) * 0.15
            + refresh_score(row.get("refresh_rate")) * 0.15
            + battery_score(row.get("battery")) * 0.10
            + base_sentiment * 0.15
            + confidence * 0.10
        )
        if text_contains(row, ["gaming", "performance", "smooth"]):
            score += 12
        if text_contains(row, ["lag", "heating", "performance issue"]):
            score -= 12
        return score

    if topic == "heating":
        score = base_sentiment * 0.45 + confidence * 0.20
        if text_contains(row, ["heating", "heat", "warm"]):
            score -= 30
        else:
            score += 15
        return score

    if topic == "value":
        score = value_score(row)
        if text_contains(row, ["value", "money", "budget", "affordable"]):
            score += 12
        if text_contains(row, ["overpriced", "poor value"]):
            score -= 12
        return score

    if topic == "parents":
        score = (
            battery_score(row.get("battery")) * 0.20
            + base_sentiment * 0.35
            + confidence * 0.20
            + value_score(row) * 0.15
        )
        if text_contains(row, ["simple", "reliable", "basic", "everyday"]):
            score += 12
        if text_contains(row, ["bugs", "heating", "lag"]):
            score -= 10
        return score

    return (
        value_score(row) * 0.35
        + base_sentiment * 0.35
        + confidence * 0.20
        + processor_score(row.get("processor")) * 0.10
    )


def retrieve_candidates(query, limit=10):
    df = get_search_dataset()
    topic = detect_topic(query)
    budget = extract_budget(query)

    df = df.copy()
    df["best_price"] = df.apply(best_available_price, axis=1)

    if budget is not None:
        df = df[df["best_price"].notna()]
        df = df[df["best_price"] <= budget]

    if df.empty:
        return df, topic, budget

    df["recommendation_score"] = df.apply(
        lambda row: calculate_recommendation_score(row, topic),
        axis=1,
    )

    df = df.sort_values(
        ["recommendation_score", "positive_percent", "review_count"],
        ascending=[False, False, False],
    )

    return df.head(limit), topic, budget


def _topic_label(topic):
    labels = {
        "battery": "battery life and charging",
        "camera": "camera and social media use",
        "gaming": "gaming and performance",
        "heating": "lower heating risk",
        "value": "value for money",
        "parents": "simple daily use",
        "overall": "overall recommendation",
    }

    return labels.get(topic, "overall recommendation")


def build_fallback_answer(candidates, topic, budget):
    top = candidates.head(5)

    budget_line = (
        f"The results were filtered for phones priced under Rs. {int(budget):,}."
        if budget is not None
        else "No budget filter was detected."
    )

    lines = [
        "## Live LLM response unavailable",
        "",
        "A live LLM-generated explanation is unavailable in the deployed version.",
        "Here are pre-generated AI recommendations based on real smartphone review data, sentiment scores, product specifications, and stored AI insights.",
        "",
        f"**Detected focus:** {_topic_label(topic).title()}",
        f"**Budget:** {budget_line}",
        "",
        "### Best Matches",
    ]

    for rank, (_, row) in enumerate(top.iterrows(), start=1):
        lines.append(
            f"{rank}. **{clean(row.get('phone_name'))}** — "
            f"{clean(row.get('brand'))}; "
            f"{float(row.get('positive_percent') or 0):.1f}% positive sentiment; "
            f"{int(row.get('review_count') or 0):,} reviews; "
            f"score {float(row.get('recommendation_score') or 0):.1f}/100."
        )

    best = top.iloc[0]

    lines.extend([
        "",
        "### Recommendation Logic",
        "Phones are ranked using topic-specific scoring, customer sentiment, review volume, complaint risk, product specifications, and stored AI insight fields.",
        "",
        "### Final Pick",
        f"**{clean(best.get('phone_name'))}** is the strongest match for this query based on the available structured data.",
    ])

    return "\n".join(lines)


def answer_search_query(query):
    if not query.strip():
        return "", pd.DataFrame()

    candidates, topic, budget = retrieve_candidates(query, limit=10)

    if candidates.empty:
        return """
### No strong matches found

No phones matched the query constraints clearly. Try relaxing the budget or using a broader query.
""", candidates

    answer = build_fallback_answer(
        candidates.head(5),
        topic,
        budget,
    )

    return answer, candidates