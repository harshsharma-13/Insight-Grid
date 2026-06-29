from pathlib import Path
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
PROCESSED = PROJECT_ROOT / "data" / "processed"

PHONE_SUMMARY = PROCESSED / "phone_summary.csv"
ASPECT_SUMMARY = PROCESSED / "aspect_summary.csv"
PLATFORM_SUMMARY = PROCESSED / "platform_summary.csv"
OUTPUT = PROCESSED / "phone_ai_insights.csv"

MIN_REVIEWS_FOR_INSIGHT = 10
MIN_ASPECT_MENTIONS = 3
RISK_ASPECTS = {"Heating"}


def insight_confidence(review_count):
    if review_count >= 50:
        return "High"
    if review_count >= 20:
        return "Medium"
    if review_count >= 10:
        return "Low"
    return "Insufficient"


def top_aspects(df, sentiment_column, top_n=3, exclude_risks=False):
    if df.empty:
        return []

    grouped = (
        df.groupby("aspect")
        .agg(
            review_count=("review_count", "sum"),
            positive_percent=("positive_percent", "mean"),
            negative_percent=("negative_percent", "mean"),
        )
        .reset_index()
    )

    grouped = grouped[grouped["review_count"] >= MIN_ASPECT_MENTIONS]

    if exclude_risks:
        grouped = grouped[~grouped["aspect"].isin(RISK_ASPECTS)]

    if grouped.empty:
        return []

    return (
        grouped.sort_values(
            by=[sentiment_column, "review_count"],
            ascending=[False, False],
        )
        .head(top_n)["aspect"]
        .tolist()
    )


def  executive_summary(row):
    review_count = int(row["review_count"])
    positive = row["positive_percent"]
    negative = row["negative_percent"]

    if review_count < MIN_REVIEWS_FOR_INSIGHT:
        review_word = "review" if review_count == 1 else "reviews"

        return (
            f"Only {review_count} {review_word} "
            "are available, so consumer insights should be treated "
            "as indicative rather than conclusive."
        )

    if positive >= 80 and negative <= 15:
        tone = "Customers show a strong positive response to this smartphone."
    elif positive >= 65:
        tone = "Customer response is generally positive."
    elif negative >= 30:
        tone = "Customer feedback shows noticeable concerns."
    else:
        tone = "Customer feedback is mixed or balanced."

    return (
        f"{tone} Based on {review_count} reviews, "
        f"positive sentiment is {positive:.1f}% "
        f"and negative sentiment is {negative:.1f}%."
    )
    if positive >= 80 and negative <= 15:
        tone = "Customers show a strong positive response to this smartphone."
    elif positive >= 65:
        tone = "Customer response is generally positive."
    elif negative >= 30:
        tone = "Customer feedback shows noticeable concerns."
    else:
        tone = "Customer feedback is mixed or balanced."

    return (
        f"{tone} Based on {int(review_count)} reviews, positive sentiment is "
        f"{positive:.1f}% and negative sentiment is {negative:.1f}%."
    )


def recommendation(row):
    review_count = row["review_count"]
    positive = row["positive_percent"]
    negative = row["negative_percent"]

    if review_count < MIN_REVIEWS_FOR_INSIGHT:
        return "Insufficient review volume for a reliable recommendation."

    if positive >= 80 and negative <= 15:
        return "Strong consumer response."

    if positive >= 65 and negative <= 25:
        return "Generally positive response with some trade-offs."

    if negative >= 30:
        return "Consumer concerns need attention before stronger recommendation."

    return "Mixed consumer response."


def platform_insight(df):
    if df.empty:
        return "No platform-level review data available."

    if len(df) < 2:
        platform = df.iloc[0]["platform"]
        return f"Reviews are available only from {platform}, so platform comparison is not possible."

    best = df.sort_values(by="positive_percent", ascending=False).iloc[0]
    worst = df.sort_values(by="positive_percent", ascending=True).iloc[0]
    diff = abs(best["positive_percent"] - worst["positive_percent"])

    if diff < 5:
        return "Customer sentiment is broadly consistent across Amazon and Flipkart."

    return (
        f"{best['platform']} shows stronger satisfaction than "
        f"{worst['platform']} by about {diff:.1f} percentage points."
    )


def main():
    print("=" * 55)
    print("Consumer Intelligence Platform")
    print("Module 12 - Insight Engine v1.1")
    print("=" * 55)

    phone_summary = pd.read_csv(PHONE_SUMMARY)
    aspect_summary = pd.read_csv(ASPECT_SUMMARY)
    platform_summary = pd.read_csv(PLATFORM_SUMMARY)

    rows = []

    for _, phone in phone_summary.iterrows():
        pid = phone["phone_id"]

        phone_aspects = aspect_summary[aspect_summary["phone_id"] == pid]
        phone_platforms = platform_summary[platform_summary["phone_id"] == pid]

        strengths = top_aspects(
            phone_aspects,
            "positive_percent",
            exclude_risks=True
        )

        pain_points = top_aspects(
            phone_aspects,
            "negative_percent",
            exclude_risks=False
        )

        rows.append({
            "phone_id": pid,
            "phone_name": phone["phone_name"],
            "review_count": phone["review_count"],
            "insight_confidence": insight_confidence(phone["review_count"]),
            "executive_summary": executive_summary(phone),
            "top_strengths": ", ".join(strengths) if strengths else "Insufficient aspect data",
            "top_pain_points": ", ".join(pain_points) if pain_points else "Insufficient aspect data",
            "platform_insight": platform_insight(phone_platforms),
            "recommendation": recommendation(phone),
        })

    output = pd.DataFrame(rows)

    output.to_csv(OUTPUT, index=False, encoding="utf-8-sig")

    print("\nCreated:")
    print(OUTPUT)
    print(f"\nInsights generated: {len(output)}")


if __name__ == "__main__":
    main()