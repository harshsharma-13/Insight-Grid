import json
import re
import pandas as pd
import requests


OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "phi4-mini:latest"


def clean(value):
    if value is None or pd.isna(value):
        return ""

    value = str(value).strip()

    if value.lower() == "nan":
        return ""

    return value


def split_items(text):
    text = clean(text)

    if not text:
        return []

    return [x.strip() for x in text.split(";") if x.strip()]


def filter_relevant_items(items, keywords):
    if not items:
        return []

    filtered = []

    for item in items:
        text = item.lower()

        if any(keyword in text for keyword in keywords):
            filtered.append(item)

    return filtered[:4]


def detect_topic(question):
    q = question.lower()

    topic_map = {
        "battery": ["battery", "charging", "charge", "backup", "screen on time"],
        "camera": ["camera", "photo", "photography", "selfie", "video", "rear camera", "front camera"],
        "gaming": ["gaming", "game", "bgmi", "pubg", "performance", "processor", "lag", "heating"],
        "display": ["display", "screen", "refresh", "brightness", "multimedia"],
        "value": ["value", "money", "price", "budget", "worth", "cheap", "affordable"],
        "software": ["software", "android", "ui", "update", "os", "bugs"],
        "connectivity": ["network", "connectivity", "5g", "signal", "call", "wifi"],
    }

    for topic, keywords in topic_map.items():
        if any(keyword in q for keyword in keywords):
            return topic, keywords

    return "overall", []


def build_context(phone_name, catalog, insight, summary):
    strengths = split_items(insight.get("top_strengths")) if insight is not None else []
    pain_points = split_items(insight.get("top_pain_points")) if insight is not None else []

    return {
        "name": phone_name,
        "brand": clean(catalog.get("brand")) if catalog is not None else "",
        "price_segment": clean(catalog.get("price_segment")) if catalog is not None else "",
        "amazon_price": clean(catalog.get("amazon_price")) if catalog is not None else "",
        "flipkart_price": clean(catalog.get("flipkart_price")) if catalog is not None else "",
        "amazon_rating": clean(catalog.get("amazon_rating")) if catalog is not None else "",
        "flipkart_rating": clean(catalog.get("flipkart_rating")) if catalog is not None else "",
        "display": clean(catalog.get("display")) if catalog is not None else "",
        "refresh_rate": clean(catalog.get("refresh_rate")) if catalog is not None else "",
        "processor": clean(catalog.get("processor")) if catalog is not None else "",
        "ram": clean(catalog.get("ram")) if catalog is not None else "",
        "storage": clean(catalog.get("storage")) if catalog is not None else "",
        "battery": clean(catalog.get("battery")) if catalog is not None else "",
        "charging": clean(catalog.get("charging")) if catalog is not None else "",
        "rear_camera": clean(catalog.get("rear_camera")) if catalog is not None else "",
        "front_camera": clean(catalog.get("front_camera")) if catalog is not None else "",
        "android_version": clean(catalog.get("android_version")) if catalog is not None else "",
        "supports_5g": clean(catalog.get("supports_5g")) if catalog is not None else "",
        "executive_summary": clean(insight.get("executive_summary")) if insight is not None else "",
        "consumer_verdict": clean(insight.get("consumer_verdict")) if insight is not None else "",
        "strengths": strengths,
        "pain_points": pain_points,
        "recommendation": clean(insight.get("recommendation")) if insight is not None else "",
        "positive_percent": float(summary.get("positive_percent", 0)) if summary is not None else 0,
        "neutral_percent": float(summary.get("neutral_percent", 0)) if summary is not None else 0,
        "negative_percent": float(summary.get("negative_percent", 0)) if summary is not None else 0,
    }


def focused_phone_context(phone, topic, keywords):
    base = {
        "name": phone["name"],
        "brand": phone["brand"],
        "consumer_verdict": phone["consumer_verdict"],
        "positive_percent": phone["positive_percent"],
        "negative_percent": phone["negative_percent"],
        "relevant_strengths": filter_relevant_items(phone["strengths"], keywords),
        "relevant_pain_points": filter_relevant_items(phone["pain_points"], keywords),
    }

    if topic == "battery":
        base.update({
            "battery": phone["battery"],
            "charging": phone["charging"],
        })

    elif topic == "camera":
        base.update({
            "rear_camera": phone["rear_camera"],
            "front_camera": phone["front_camera"],
        })

    elif topic == "gaming":
        base.update({
            "processor": phone["processor"],
            "ram": phone["ram"],
            "storage": phone["storage"],
            "display": phone["display"],
            "refresh_rate": phone["refresh_rate"],
            "battery": phone["battery"],
        })

    elif topic == "display":
        base.update({
            "display": phone["display"],
            "refresh_rate": phone["refresh_rate"],
        })

    elif topic == "value":
        base.update({
            "price_segment": phone["price_segment"],
            "amazon_price": phone["amazon_price"],
            "flipkart_price": phone["flipkart_price"],
            "amazon_rating": phone["amazon_rating"],
            "flipkart_rating": phone["flipkart_rating"],
            "recommendation": phone["recommendation"],
        })

    elif topic == "software":
        base.update({
            "android_version": phone["android_version"],
        })

    elif topic == "connectivity":
        base.update({
            "supports_5g": phone["supports_5g"],
        })

    else:
        base.update({
            "price_segment": phone["price_segment"],
            "display": phone["display"],
            "processor": phone["processor"],
            "ram": phone["ram"],
            "storage": phone["storage"],
            "battery": phone["battery"],
            "charging": phone["charging"],
            "rear_camera": phone["rear_camera"],
            "front_camera": phone["front_camera"],
            "amazon_rating": phone["amazon_rating"],
            "flipkart_rating": phone["flipkart_rating"],
            "executive_summary": phone["executive_summary"],
            "recommendation": phone["recommendation"],
        })

    return base


def build_prompt(question, phone_a, phone_b):
    topic, keywords = detect_topic(question)

    context_a = focused_phone_context(phone_a, topic, keywords)
    context_b = focused_phone_context(phone_b, topic, keywords)

    return f"""
You are a smartphone comparison analyst.

Answer using ONLY the supplied data.
Do not invent specs, complaints, ratings or prices.
If evidence is weak, say so.
Be direct and concise.

Question:
{question}

Comparison focus:
{topic}

Phone A:
{json.dumps(context_a, ensure_ascii=False)}

Phone B:
{json.dumps(context_b, ensure_ascii=False)}

Return under 110 words.

Format:
### Answer
Give one clear recommendation.

### Evidence
- Point 1
- Point 2
- Point 3

### Confidence
High, Moderate, or Low with one short reason.
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
                "num_ctx": 1536,
                "num_predict": 90,
                "num_thread": 4,
            },
        },
        timeout=90,
    )

    response.raise_for_status()
    return response.json().get("response", "").strip()


def compare_question(question, phone_a, phone_b):
    if not question.strip():
        return ""

    prompt = build_prompt(question, phone_a, phone_b)

    try:
        return ask_ollama(prompt)
    except Exception as error:
        return f"""
### AI answer unavailable

The local AI model could not generate a response.

Error: `{error}`

Make sure Ollama is running and `{MODEL}` is available.
"""