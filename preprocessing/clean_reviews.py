"""
AI Consumer Intelligence Platform (CIP)

Module:
Clean Reviews

Purpose:
Read reviews_master.csv, preserve original review text, create cleaned text,
quality metrics, duplicate flags, and save reviews_clean.csv.

Author: Harsh Sharma
"""

from pathlib import Path
import re
import unicodedata
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parent.parent

PROCESSED_DATA = PROJECT_ROOT / "data" / "processed"

INPUT_FILE = PROCESSED_DATA / "reviews_master.csv"
OUTPUT_FILE = PROCESSED_DATA / "reviews_clean.csv"


SHORT_REVIEW_WORD_LIMIT = 3
VERY_SHORT_REVIEW_WORD_LIMIT = 1


def normalize_text(text: str) -> str:
    """Normalize review text without changing customer meaning."""

    if pd.isna(text):
        return ""

    text = str(text)

    text = unicodedata.normalize("NFKC", text)

    text = text.replace("\n", " ")
    text = text.replace("\r", " ")
    text = text.replace("\t", " ")

    text = re.sub(r"\s+", " ", text)

    return text.strip()


def count_words(text: str) -> int:
    """Count words in cleaned review text."""

    if not text:
        return 0

    return len(text.split())


def assign_quality_flag(clean_review: str, word_count: int) -> str:
    """Assign a simple quality flag to each review."""

    if clean_review == "":
        return "Empty"

    if word_count <= VERY_SHORT_REVIEW_WORD_LIMIT:
        return "Very Short"

    if word_count <= SHORT_REVIEW_WORD_LIMIT:
        return "Short Review"

    return "Good"


def load_reviews() -> pd.DataFrame:
    """Load reviews_master.csv."""

    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            f"Input file not found: {INPUT_FILE}. "
            "Run build_database.py first."
        )

    return pd.read_csv(INPUT_FILE)


def clean_reviews(df: pd.DataFrame) -> pd.DataFrame:
    """Create cleaned review dataset."""

    required_columns = {
        "review_id",
        "phone_id",
        "phone_name",
        "platform",
        "review_text",
    }

    missing_columns = required_columns - set(df.columns)

    if missing_columns:
        raise ValueError(f"Missing required columns: {missing_columns}")

    df = df.copy()

    df["clean_review"] = df["review_text"].apply(normalize_text)

    df["review_length"] = df["clean_review"].str.len()

    df["word_count"] = df["clean_review"].apply(count_words)

    df["quality_flag"] = df.apply(
        lambda row: assign_quality_flag(
            row["clean_review"],
            row["word_count"]
        ),
        axis=1
    )

    df["duplicate_key"] = (
        df["phone_id"].astype(str)
        + "_"
        + df["platform"].astype(str)
        + "_"
        + df["clean_review"].str.lower()
    )

    df["is_duplicate"] = df.duplicated(
        subset=["duplicate_key"],
        keep="first"
    )

    df = df.drop(columns=["duplicate_key"])

    return df


def save_clean_reviews(df: pd.DataFrame) -> None:
    """Save cleaned reviews to CSV."""

    df.to_csv(
        OUTPUT_FILE,
        index=False,
        encoding="utf-8-sig"
    )


def print_summary(df: pd.DataFrame) -> None:
    """Print cleaning summary."""

    print("\n==========================================")
    print("CLEANING SUMMARY")
    print("==========================================")
    print(f"Total reviews processed : {len(df)}")
    print(f"Duplicate reviews flagged : {df['is_duplicate'].sum()}")
    print("\nQuality flags:")
    print(df["quality_flag"].value_counts())
    print("==========================================")
    print(f"\nCreated file:\n{OUTPUT_FILE}\n")


def main() -> None:
    """Run review cleaning module."""

    print("=" * 50)
    print("Consumer Intelligence Platform")
    print("Module 3 - Clean Reviews")
    print("=" * 50)

    reviews_df = load_reviews()

    clean_df = clean_reviews(reviews_df)

    save_clean_reviews(clean_df)

    print_summary(clean_df)


if __name__ == "__main__":
    main()