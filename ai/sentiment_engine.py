"""
AI Consumer Intelligence Platform (CIP)

Module:
Sentiment Engine

Purpose:
Run transformer-based sentiment analysis on cleaned reviews and create
reviews_sentiment.csv.

Author: Harsh Sharma
"""

from pathlib import Path
import pandas as pd
from tqdm import tqdm
from transformers import pipeline


PROJECT_ROOT = Path(__file__).resolve().parent.parent

PROCESSED_DATA = PROJECT_ROOT / "data" / "processed"

INPUT_FILE = PROCESSED_DATA / "reviews_clean.csv"
OUTPUT_FILE = PROCESSED_DATA / "reviews_sentiment.csv"

MODEL_NAME = "cardiffnlp/twitter-roberta-base-sentiment-latest"


def load_reviews() -> pd.DataFrame:
    """Load cleaned reviews."""

    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            f"Missing input file: {INPUT_FILE}. Run clean_reviews.py first."
        )

    return pd.read_csv(INPUT_FILE)


def normalize_label(label: str) -> str:
    """Normalize model label names."""

    label = str(label).lower()

    if "positive" in label:
        return "Positive"

    if "negative" in label:
        return "Negative"

    return "Neutral"


def run_sentiment_analysis(df: pd.DataFrame) -> pd.DataFrame:
    """Run transformer sentiment analysis."""

    df = df.copy()

    sentiment_pipeline = pipeline(
        task="sentiment-analysis",
        model=MODEL_NAME,
        tokenizer=MODEL_NAME,
        truncation=True,
        max_length=512
    )

    sentiments = []
    confidences = []

    reviews = df["clean_review"].fillna("").astype(str).tolist()

    print("\nRunning sentiment analysis...")
    print("This may take several minutes on first run.\n")

    for review in tqdm(reviews, desc="Analyzing reviews"):
        if review.strip() == "":
            sentiments.append("Neutral")
            confidences.append(0.0)
            continue

        result = sentiment_pipeline(review)[0]

        sentiments.append(normalize_label(result["label"]))
        confidences.append(round(float(result["score"]), 4))

    df["sentiment"] = sentiments
    df["sentiment_confidence"] = confidences

    return df


def save_output(df: pd.DataFrame) -> None:
    """Save sentiment output."""

    df.to_csv(
        OUTPUT_FILE,
        index=False,
        encoding="utf-8-sig"
    )


def print_summary(df: pd.DataFrame) -> None:
    """Print sentiment summary."""

    print("\n==========================================")
    print("SENTIMENT SUMMARY")
    print("==========================================")
    print(f"Total reviews processed : {len(df)}")
    print("\nSentiment distribution:")
    print(df["sentiment"].value_counts())
    print(f"\nAverage confidence      : {df['sentiment_confidence'].mean():.4f}")
    print("==========================================")
    print(f"\nCreated file:\n{OUTPUT_FILE}\n")


def main() -> None:
    """Run sentiment module."""

    print("=" * 50)
    print("Consumer Intelligence Platform")
    print("Sprint 2 - Module 6: Sentiment Engine")
    print("=" * 50)

    reviews_df = load_reviews()

    sentiment_df = run_sentiment_analysis(reviews_df)

    save_output(sentiment_df)

    print_summary(sentiment_df)


if __name__ == "__main__":
    main()