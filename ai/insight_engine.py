"""
AI Consumer Intelligence Platform

Module 13B
Single Phone Insight Engine

Purpose:
Generate one AI-powered consumer intelligence insight for a given phone_id
using the Intelligence Service and local Ollama model.
"""

from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_ROOT))

from services.intelligence_service import get_complete_phone_profile
from ai.providers.ollama_provider import OllamaProvider


REQUIRED_KEYS = [
    "executive_summary",
    "consumer_verdict",
    "top_strengths",
    "top_pain_points",
    "platform_insight",
    "ideal_for",
    "avoid_if",
    "recommendation",
]


def first_row(df):
    if df is None or df.empty:
        return {}
    return df.iloc[0].to_dict()


def confidence_level(review_count: int) -> str:
    if review_count >= 100:
        return "Very High"
    if review_count >= 50:
        return "High"
    if review_count >= 20:
        return "Medium"
    if review_count >= 10:
        return "Low"
    return "Insufficient"


def clean_list(value, fallback):
    if isinstance(value, list):
        items = value
    elif value:
        items = [str(value)]
    else:
        items = []

    weak_terms = [
        "neutral",
        "no positive",
        "insufficient",
        "limited data",
        "not enough",
        "no clear",
    ]

    cleaned = []

    for item in items:
        item = str(item).strip()

        if not item:
            continue

        if any(term in item.lower() for term in weak_terms):
            continue

        cleaned.append(item)

    return cleaned if cleaned else [fallback]


def clean_text(value):
    if isinstance(value, dict):
        parts = []
        for key, val in value.items():
            if isinstance(val, list):
                val = "; ".join(str(x) for x in val)
            parts.append(f"{key}: {val}")
        return " ".join(parts)

    if isinstance(value, list):
        return "; ".join(str(x) for x in value)

    if value is None:
        return ""

    return str(value).strip()


def validate_result(result):
    validated = {}

    for key in REQUIRED_KEYS:
        validated[key] = result.get(key, "")

    validated["executive_summary"] = clean_text(
        validated["executive_summary"]
    )

    validated["consumer_verdict"] = clean_text(
        validated["consumer_verdict"]
    )

    validated["platform_insight"] = clean_text(
        validated["platform_insight"]
    )

    validated["recommendation"] = clean_text(
        validated["recommendation"]
    )

    validated["top_strengths"] = clean_list(
        validated["top_strengths"],
        "Insufficient positive evidence"
    )

    validated["top_pain_points"] = clean_list(
        validated["top_pain_points"],
        "No dominant pain point identified"
    )

    validated["ideal_for"] = clean_list(
        validated["ideal_for"],
        "General smartphone users"
    )

    validated["avoid_if"] = clean_list(
        validated["avoid_if"],
        "Users needing stronger evidence before purchase"
    )

    return validated


def format_platform_data(df):
    if df is None or df.empty:
        return "No platform comparison data available."

    lines = []

    for _, row in df.iterrows():
        lines.append(
            f"- {row['platform']}: {int(row['review_count'])} reviews, "
            f"{row['positive_percent']:.1f}% positive, "
            f"{row['negative_percent']:.1f}% negative"
        )

    return "\n".join(lines)


def format_aspect_data(df):
    if df is None or df.empty:
        return "No aspect data available."

    grouped = (
        df.groupby("aspect")
        .agg(
            mentions=("review_count", "sum"),
            positive=("positive_percent", "mean"),
            negative=("negative_percent", "mean"),
        )
        .reset_index()
        .sort_values("mentions", ascending=False)
        .head(10)
    )

    lines = []

    for _, row in grouped.iterrows():
        lines.append(
            f"- {row['aspect']}: {int(row['mentions'])} mentions, "
            f"{row['positive']:.1f}% positive, "
            f"{row['negative']:.1f}% negative"
        )

    return "\n".join(lines)


def format_reviews(df):
    if df is None or df.empty:
        return "No review examples available."

    lines = []

    for _, row in df.head(5).iterrows():
        review = str(row["review_text"]).replace("\n", " ").strip()
        platform = row["platform"]
        lines.append(f"- [{platform}] {review}")

    return "\n".join(lines)


def build_prompt(phone_id):
    profile = get_complete_phone_profile(phone_id)

    product = first_row(profile["profile"])
    summary = first_row(profile["summary"])
    consumer = first_row(profile["consumer_intelligence"])

    if not summary:
        return None, None

    phone_name = product.get(
        "phone_name",
        summary.get("phone_name", "Unknown Phone")
    )

    brand = product.get("brand", "")
    price_segment = product.get("price_segment", "")
    launch_date = product.get("launch_date", "")

    review_count = int(summary.get("review_count", 0))
    confidence = confidence_level(review_count)

    platform_text = format_platform_data(
        profile["platform_comparison"]
    )

    aspect_text = format_aspect_data(
        profile["aspect_summary"]
    )

    review_text = format_reviews(
        profile["reviews"]
    )

    prompt = f"""
You are a Senior Smartphone Consumer Intelligence Analyst.

Your audience includes product managers, consumer insight teams,
and business decision-makers.

Use ONLY the supplied data.
Do NOT invent specifications, prices, ratings, or product features.
Do NOT write marketing copy.
Do NOT overstate weak evidence.
If review volume is low, clearly mention that insight confidence is limited.
Platform insight must be a single plain-English paragraph, not a dictionary.
Strengths must represent clearly positive evidence only.
Do not use neutral, mixed, insufficient, or unclear points as strengths.
Pain points must be specific customer concerns.

PHONE INFORMATION
Phone: {phone_name}
Brand: {brand}
Launch date: {launch_date}
Price segment: {price_segment}

REVIEW VOLUME
Review count: {review_count}
Insight confidence: {confidence}

OVERALL SENTIMENT
Positive: {summary.get("positive_percent", 0):.1f}%
Neutral: {summary.get("neutral_percent", 0):.1f}%
Negative: {summary.get("negative_percent", 0):.1f}%

CONSUMER INTELLIGENCE
Strongest aspect: {consumer.get("strongest_aspect", "")}
Weakest aspect: {consumer.get("weakest_aspect", "")}
Best platform: {consumer.get("best_platform", "")}
Recommendation label: {consumer.get("recommendation_label", "")}

PLATFORM COMPARISON
{platform_text}

ASPECT ANALYSIS
{aspect_text}

REVIEW EXAMPLES
{review_text}

Return ONLY valid JSON with exactly these keys:
executive_summary
consumer_verdict
top_strengths
top_pain_points
platform_insight
ideal_for
avoid_if
recommendation

Rules:
- executive_summary: 2 short sentences.
- consumer_verdict: one short label.
- top_strengths: list of 3 short evidence-based strengths.
- top_pain_points: list of 3 short evidence-based pain points.
- platform_insight: one concise paragraph.
- ideal_for: list of 2-3 customer types.
- avoid_if: list of 2-3 caution points.
- recommendation: one concise business recommendation.
"""

    metadata = {
        "phone_id": phone_id,
        "phone_name": phone_name,
        "review_count": review_count,
        "insight_confidence": confidence,
    }

    return prompt, metadata


def generate_phone_insight(phone_id, provider=None):
    if provider is None:
        provider = OllamaProvider()

    prompt, metadata = build_prompt(phone_id)

    if prompt is None:
        return None

    try:
        result = provider.generate_json(prompt)
    except Exception as error:
        result = {
            "executive_summary": f"Insight generation failed: {error}",
            "consumer_verdict": "Generation Failed",
            "top_strengths": [],
            "top_pain_points": [],
            "platform_insight": "",
            "ideal_for": [],
            "avoid_if": [],
            "recommendation": "",
        }

    insight = validate_result(result)

    return {
        **metadata,
        "executive_summary": insight["executive_summary"],
        "consumer_verdict": insight["consumer_verdict"],
        "top_strengths": "; ".join(insight["top_strengths"]),
        "top_pain_points": "; ".join(insight["top_pain_points"]),
        "platform_insight": insight["platform_insight"],
        "ideal_for": "; ".join(insight["ideal_for"]),
        "avoid_if": "; ".join(insight["avoid_if"]),
        "recommendation": insight["recommendation"],
    }


if __name__ == "__main__":
    test_phone_id = "PH055"
    insight = generate_phone_insight(test_phone_id)
    print(insight)