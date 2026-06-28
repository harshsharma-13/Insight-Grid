"""
AI Consumer Intelligence Platform (CIP)

Module:
Aspect Engine

Purpose:
Detect smartphone-related aspects from reviews and create reviews_aspects.csv.

Author: Harsh Sharma
"""

from pathlib import Path
import pandas as pd
from tqdm import tqdm


PROJECT_ROOT = Path(__file__).resolve().parent.parent

PROCESSED_DATA = PROJECT_ROOT / "data" / "processed"

INPUT_FILE = PROCESSED_DATA / "reviews_sentiment.csv"
OUTPUT_FILE = PROCESSED_DATA / "reviews_aspects.csv"


ASPECT_KEYWORDS = {
    "Battery": [
        "battery", "backup", "battery backup", "power", "lasting",
        "lasts", "mah", "drain", "draining"
    ],
    "Camera": [
        "camera", "photo", "photos", "picture", "pictures", "portrait",
        "selfie", "video", "night mode", "low light"
    ],
    "Display": [
        "display", "screen", "amoled", "lcd", "brightness", "refresh",
        "touch", "resolution"
    ],
    "Performance": [
        "performance", "speed", "fast", "slow", "lag", "lagging",
        "smooth", "processor", "ram", "multitasking"
    ],
    "Gaming": [
        "gaming", "game", "bgmi", "pubg", "fps", "graphics"
    ],
    "Charging": [
        "charging", "charger", "charge", "fast charging", "slow charging",
        "adapter"
    ],
    "Software": [
        "software", "ui", "os", "android", "update", "updates",
        "bug", "bugs", "bloatware", "app", "apps"
    ],
    "Build Quality": [
        "build", "quality", "durable", "durability", "body", "material",
        "plastic", "glass"
    ],
    "Design": [
        "design", "look", "looks", "style", "premium", "weight",
        "slim", "hand feel"
    ],
    "Speaker & Audio": [
        "speaker", "sound", "audio", "volume", "loud", "music",
        "earphone"
    ],
    "Connectivity": [
        "network", "5g", "wifi", "signal", "calling", "call",
        "sim", "connectivity"
    ],
    "Value for Money": [
        "value", "price", "money", "worth", "budget", "cost",
        "affordable", "overpriced"
    ],
    "Heating": [
        "heat", "heating", "heated", "hot", "warm", "overheat",
        "overheating"
    ],
}


def load_reviews() -> pd.DataFrame:
    """Load sentiment-enriched reviews."""

    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            f"Missing input file: {INPUT_FILE}. Run sentiment_engine.py first."
        )

    return pd.read_csv(INPUT_FILE)


def detect_aspects(review_text: str) -> list[str]:
    """Detect aspects using controlled keyword taxonomy."""

    if pd.isna(review_text):
        return []

    text = str(review_text).lower()

    detected = []

    for aspect, keywords in ASPECT_KEYWORDS.items():
        for keyword in keywords:
            if keyword in text:
                detected.append(aspect)
                break

    return detected


def build_aspect_dataset(df: pd.DataFrame) -> pd.DataFrame:
    """Create one row per detected review-aspect pair."""

    rows = []

    print("\nDetecting aspects...\n")

    for _, row in tqdm(df.iterrows(), total=len(df), desc="Processing reviews"):

        aspects = detect_aspects(row["clean_review"])

        for aspect in aspects:
            rows.append({
                "review_id": row["review_id"],
                "phone_id": row["phone_id"],
                "phone_name": row["phone_name"],
                "platform": row["platform"],
                "aspect": aspect,
                "sentiment": row["sentiment"],
                "sentiment_confidence": row["sentiment_confidence"],
                "review_text": row["review_text"],
                "clean_review": row["clean_review"],
                "quality_flag": row["quality_flag"],
                "is_duplicate": row["is_duplicate"],
            })

    return pd.DataFrame(rows)


def save_output(df: pd.DataFrame) -> None:
    """Save aspect dataset."""

    df.to_csv(
        OUTPUT_FILE,
        index=False,
        encoding="utf-8-sig"
    )


def print_summary(df: pd.DataFrame) -> None:
    """Print aspect detection summary."""

    print("\n==========================================")
    print("ASPECT DETECTION SUMMARY")
    print("==========================================")
    print(f"Total review-aspect rows : {len(df)}")

    if len(df) > 0:
        print("\nTop aspects:")
        print(df["aspect"].value_counts())

        print("\nPlatform distribution:")
        print(df["platform"].value_counts())

    print("==========================================")
    print(f"\nCreated file:\n{OUTPUT_FILE}\n")


def main() -> None:
    """Run aspect engine."""

    print("=" * 50)
    print("Consumer Intelligence Platform")
    print("Sprint 2 - Module 7: Aspect Engine")
    print("=" * 50)

    reviews_df = load_reviews()

    aspects_df = build_aspect_dataset(reviews_df)

    save_output(aspects_df)

    print_summary(aspects_df)


if __name__ == "__main__":
    main()