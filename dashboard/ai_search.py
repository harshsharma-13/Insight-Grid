import json
import re
import pandas as pd
import requests

from dashboard_data import read_sql


OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "phi4-mini:latest"


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
    return read_sql("""
        SELECT
            s.phone_id,
            s.phone_name,

            sp.brand,
            sp.image_local_path,
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
        LEFT JOIN phone_ai_insights ai
            ON s.phone_id = ai.phone_id
    """)


def best_available_price(row):
    prices = [
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

    high = ["dimensity 7400", "dimensity 7300", "snapdragon 7", "snapdragon 6", "helio g99"]
    mid = ["dimensity 6300", "dimensity 6100", "snapdragon 4", "helio", "mediatek", "unisoc"]

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
    return max(0, positive - (negative * 0.5))


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
        processor_score(row.get("processor")) * 0.25 +
        ram_score(row.get("ram")) * 0.15 +
        storage_score(row.get("storage")) * 0.10 +
        battery_score(row.get("battery")) * 0.20 +
        charging_score(row.get("charging")) * 0.10 +
        camera_score(row.get("rear_camera")) * 0.10 +
        refresh_score(row.get("refresh_rate")) * 0.10
    )

    return (
        price_component * 0.30 +
        specs_component * 0.40 +
        sentiment_score(row) * 0.20 +
        confidence_score(row) * 0.10
    )


def calculate_recommendation_score(row, topic):
    base_sentiment = sentiment_score(row)
    confidence = confidence_score(row)

    if topic == "battery":
        score = (
            battery_score(row.get("battery")) * 0.35 +
            charging_score(row.get("charging")) * 0.15 +
            base_sentiment * 0.25 +
            confidence * 0.10
        )
        if text_contains(row, ["battery", "backup"]):
            score += 12
        if text_contains(row, ["battery drain", "charging issue", "slow charging"]):
            score -= 12
        return score

    if topic == "camera":
        score = (
            camera_score(row.get("rear_camera")) * 0.30 +
            camera_score(row.get("front_camera")) * 0.12 +
            base_sentiment * 0.25 +
            confidence * 0.10
        )
        if text_contains(row, ["camera", "photo", "selfie"]):
            score += 14
        if text_contains(row, ["camera issue", "blur", "poor camera"]):
            score -= 12
        return score

    if topic == "gaming":
        score = (
            processor_score(row.get("processor")) * 0.35 +
            ram_score(row.get("ram")) * 0.15 +
            refresh_score(row.get("refresh_rate")) * 0.15 +
            battery_score(row.get("battery")) * 0.10 +
            base_sentiment * 0.15 +
            confidence * 0.10
        )
        if text_contains(row, ["gaming", "performance", "smooth"]):
            score += 12
        if text_contains(row, ["lag", "heating", "performance issue"]):
            score -= 12
        return score

    if topic == "heating":
        score = (
            base_sentiment * 0.45 +
            confidence * 0.20
        )
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
            battery_score(row.get("battery")) * 0.20 +
            base_sentiment * 0.35 +
            confidence * 0.20 +
            value_score(row) * 0.15
        )
        if text_contains(row, ["simple", "reliable", "basic", "everyday"]):
            score += 12
        if text_contains(row, ["bugs", "heating", "lag"]):
            score -= 10
        return score

    return (
        value_score(row) * 0.35 +
        base_sentiment * 0.35 +
        confidence * 0.20 +
        processor_score(row.get("processor")) * 0.10
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


def build_candidate_record(row):
    return {
        "phone_name": clean(row.get("phone_name")),
        "brand": clean(row.get("brand")),
        "best_price": row.get("best_price"),
        "processor": clean(row.get("processor")),
        "ram": clean(row.get("ram")),
        "storage": clean(row.get("storage")),
        "battery": clean(row.get("battery")),
        "charging": clean(row.get("charging")),
        "rear_camera": clean(row.get("rear_camera")),
        "front_camera": clean(row.get("front_camera")),
        "display": clean(row.get("display")),
        "refresh_rate": clean(row.get("refresh_rate")),
        "positive_percent": row.get("positive_percent"),
        "negative_percent": row.get("negative_percent"),
        "review_count": row.get("review_count"),
        "consumer_verdict": clean(row.get("consumer_verdict")),
        "strengths": clean(row.get("top_strengths")),
        "pain_points": clean(row.get("top_pain_points")),
        "recommendation": clean(row.get("recommendation")),
        "ranking_score": round(float(row.get("recommendation_score", 0)), 1),
    }


def build_prompt(query, candidates, topic, budget):
    records = [build_candidate_record(row) for _, row in candidates.iterrows()]
    budget_text = f"Budget constraint: under ₹{int(budget)}" if budget else "No budget constraint detected"

    return f"""
You are explaining a recommendation engine output.

The system has already ranked the phones using topic-specific scoring.
Do NOT change the ranking order.
Do NOT recommend a phone outside the ranked list.
Use ONLY the data below.
Explain the ranking using both specifications and consumer intelligence.

User query:
{query}

Detected topic:
{topic}

{budget_text}

Ranked candidates:
{json.dumps(records, ensure_ascii=False)}

Return in this exact format:

### Best Matches
1. Phone name — explain why it ranked here using specs plus review/sentiment evidence.
2. Phone name — explain why it ranked here using specs plus review/sentiment evidence.
3. Phone name — explain why it ranked here using specs plus review/sentiment evidence.
4. Phone name — explain why it ranked here using specs plus review/sentiment evidence.
5. Phone name — explain why it ranked here using specs plus review/sentiment evidence.

### Recommendation Logic
Explain the ranking logic in 2 to 3 sentences.

### Final Pick
Choose the best overall phone from the ranked list for this query.

### Confidence
High, Moderate, or Low with one reason.

Keep the answer concise but complete.
Do not stop mid-sentence.
Target approximately 350–450 words if needed.
"""


def ask_ollama(prompt):
    response = requests.post(
        OLLAMA_URL,
        json={
            "model": MODEL,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.1,
                "top_p": 0.9,
                "top_k": 30,
                "repeat_penalty": 1.05,
                "num_ctx": 3072,
                "num_predict": 550,
            },
        },
        timeout=180,
    )

    response.raise_for_status()
    return response.json().get("response", "").strip()


def answer_search_query(query):
    if not query.strip():
        return "", pd.DataFrame()

    candidates, topic, budget = retrieve_candidates(query, limit=10)

    if candidates.empty:
        return """
### No strong matches found

No phones matched the query constraints clearly. Try relaxing the budget or using a broader query.
""", candidates

    prompt = build_prompt(query, candidates.head(5), topic, budget)

    try:
        answer = ask_ollama(prompt)
    except Exception:
    return """
## AI Search unavailable at the moment

The AI search assistant is currently unavailable in the deployed version.

Please use the platform modules below to explore phones, reviews, recommendations, and competitive insights.
""", pd.DataFrame()