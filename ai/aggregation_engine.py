"""
AI Consumer Intelligence Platform (CIP)

Module:
Aggregation Engine

Purpose:
Aggregate sentiment and aspect outputs into phone-level, platform-level,
aspect-level, and consumer intelligence summary files.

Author: Harsh Sharma
"""

from pathlib import Path
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parent.parent

PROCESSED_DATA = PROJECT_ROOT / "data" / "processed"

REVIEWS_SENTIMENT_FILE = PROCESSED_DATA / "reviews_sentiment.csv"
REVIEWS_ASPECTS_FILE = PROCESSED_DATA / "reviews_aspects.csv"

PHONE_SUMMARY_FILE = PROCESSED_DATA / "phone_summary.csv"
PLATFORM_SUMMARY_FILE = PROCESSED_DATA / "platform_summary.csv"
ASPECT_SUMMARY_FILE = PROCESSED_DATA / "aspect_summary.csv"
CONSUMER_INTELLIGENCE_FILE = PROCESSED_DATA / "consumer_intelligence.csv"


def load_data():
    """Load sentiment and aspect datasets."""

    reviews_df = pd.read_csv(REVIEWS_SENTIMENT_FILE)
    aspects_df = pd.read_csv(REVIEWS_ASPECTS_FILE)

    return reviews_df, aspects_df


def sentiment_percentages(group):
    """Calculate sentiment distribution for a grouped dataframe."""

    total = len(group)

    positive = (group["sentiment"] == "Positive").sum()
    neutral = (group["sentiment"] == "Neutral").sum()
    negative = (group["sentiment"] == "Negative").sum()

    return pd.Series({
        "review_count": total,
        "positive_count": positive,
        "neutral_count": neutral,
        "negative_count": negative,
        "positive_percent": round((positive / total) * 100, 2) if total else 0,
        "neutral_percent": round((neutral / total) * 100, 2) if total else 0,
        "negative_percent": round((negative / total) * 100, 2) if total else 0,
        "avg_confidence": round(group["sentiment_confidence"].mean(), 4)
    })


def build_phone_summary(reviews_df):
    """Create one-row-per-phone sentiment summary."""

    phone_summary = (
        reviews_df
        .groupby(["phone_id", "phone_name"])
        .apply(sentiment_percentages, include_groups=False)
        .reset_index()
    )

    return phone_summary


def build_platform_summary(reviews_df):
    """Create phone-platform-level sentiment summary."""

    platform_summary = (
        reviews_df
        .groupby(["phone_id", "phone_name", "platform"])
        .apply(sentiment_percentages, include_groups=False)
        .reset_index()
    )

    return platform_summary


def build_aspect_summary(aspects_df):
    """Create phone-aspect-platform-level sentiment summary."""

    aspect_summary = (
        aspects_df
        .groupby(["phone_id", "phone_name", "platform", "aspect"])
        .apply(sentiment_percentages, include_groups=False)
        .reset_index()
    )

    return aspect_summary


def get_top_aspect(aspect_df, sentiment_type):
    """Find strongest or weakest aspect for a phone."""

    if aspect_df.empty:
        return "Insufficient Data"

    if sentiment_type == "positive":
        sorted_df = aspect_df.sort_values(
            by=["positive_percent", "review_count"],
            ascending=[False, False]
        )
    else:
        sorted_df = aspect_df.sort_values(
            by=["negative_percent", "review_count"],
            ascending=[False, False]
        )

    return sorted_df.iloc[0]["aspect"]


def get_best_platform(platform_df):
    """Find the platform with higher positive sentiment."""

    if platform_df.empty:
        return "Insufficient Data"

    sorted_df = platform_df.sort_values(
        by=["positive_percent", "review_count"],
        ascending=[False, False]
    )

    return sorted_df.iloc[0]["platform"]


def assign_recommendation(row):
    """Create a simple recommendation label."""

    if row["review_count"] < 10:
        return "Insufficient review volume"

    if row["positive_percent"] >= 75 and row["negative_percent"] <= 15:
        return "Strong consumer response"

    if row["positive_percent"] >= 60:
        return "Generally positive response"

    if row["negative_percent"] >= 30:
        return "Consumer concerns need attention"

    return "Mixed consumer response"


def build_consumer_intelligence(phone_summary, platform_summary, aspect_summary):
    """Create business-oriented one-row-per-phone intelligence file."""

    rows = []

    for _, phone in phone_summary.iterrows():

        phone_id = phone["phone_id"]
        phone_name = phone["phone_name"]

        phone_platforms = platform_summary[
            platform_summary["phone_id"] == phone_id
        ]

        phone_aspects = aspect_summary[
            aspect_summary["phone_id"] == phone_id
        ]

        aspect_overall = (
            phone_aspects
            .groupby(["phone_id", "phone_name", "aspect"])
            .agg({
                "review_count": "sum",
                "positive_count": "sum",
                "neutral_count": "sum",
                "negative_count": "sum"
            })
            .reset_index()
        )

        if not aspect_overall.empty:
            aspect_overall["positive_percent"] = round(
                (aspect_overall["positive_count"] / aspect_overall["review_count"]) * 100,
                2
            )
            aspect_overall["negative_percent"] = round(
                (aspect_overall["negative_count"] / aspect_overall["review_count"]) * 100,
                2
            )

        rows.append({
            "phone_id": phone_id,
            "phone_name": phone_name,
            "review_count": phone["review_count"],
            "positive_percent": phone["positive_percent"],
            "neutral_percent": phone["neutral_percent"],
            "negative_percent": phone["negative_percent"],
            "strongest_aspect": get_top_aspect(aspect_overall, "positive"),
            "weakest_aspect": get_top_aspect(aspect_overall, "negative"),
            "best_platform": get_best_platform(phone_platforms),
            "recommendation_label": assign_recommendation(phone)
        })

    return pd.DataFrame(rows)


def save_outputs(phone_summary, platform_summary, aspect_summary, consumer_intelligence):
    """Save all aggregation outputs."""

    phone_summary.to_csv(PHONE_SUMMARY_FILE, index=False, encoding="utf-8-sig")
    platform_summary.to_csv(PLATFORM_SUMMARY_FILE, index=False, encoding="utf-8-sig")
    aspect_summary.to_csv(ASPECT_SUMMARY_FILE, index=False, encoding="utf-8-sig")
    consumer_intelligence.to_csv(
        CONSUMER_INTELLIGENCE_FILE,
        index=False,
        encoding="utf-8-sig"
    )


def print_summary(phone_summary, platform_summary, aspect_summary, consumer_intelligence):
    """Print execution summary."""

    print("\n==========================================")
    print("AGGREGATION SUMMARY")
    print("==========================================")
    print(f"Phone summary rows           : {len(phone_summary)}")
    print(f"Platform summary rows        : {len(platform_summary)}")
    print(f"Aspect summary rows          : {len(aspect_summary)}")
    print(f"Consumer intelligence rows   : {len(consumer_intelligence)}")
    print("\nCreated files:")
    print(PHONE_SUMMARY_FILE)
    print(PLATFORM_SUMMARY_FILE)
    print(ASPECT_SUMMARY_FILE)
    print(CONSUMER_INTELLIGENCE_FILE)
    print("==========================================\n")


def main():
    """Run aggregation module."""

    print("=" * 50)
    print("Consumer Intelligence Platform")
    print("Sprint 2 - Module 8: Aggregation Engine")
    print("=" * 50)

    reviews_df, aspects_df = load_data()

    phone_summary = build_phone_summary(reviews_df)
    platform_summary = build_platform_summary(reviews_df)
    aspect_summary = build_aspect_summary(aspects_df)
    consumer_intelligence = build_consumer_intelligence(
        phone_summary,
        platform_summary,
        aspect_summary
    )

    save_outputs(
        phone_summary,
        platform_summary,
        aspect_summary,
        consumer_intelligence
    )

    print_summary(
        phone_summary,
        platform_summary,
        aspect_summary,
        consumer_intelligence
    )


if __name__ == "__main__":
    main()