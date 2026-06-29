from pathlib import Path
import sys
import csv
import pandas as pd
from tqdm import tqdm

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_ROOT))

from services.intelligence_service import search_phones, get_complete_phone_profile
from ai.providers.ollama_provider import OllamaProvider
from ai.insight_engine import generate_phone_insight


OUTPUT = PROJECT_ROOT / "data" / "processed" / "phone_ai_insights.csv"

COLUMNS = [
    "phone_id",
    "phone_name",
    "review_count",
    "insight_confidence",
    "executive_summary",
    "consumer_verdict",
    "top_strengths",
    "top_pain_points",
    "platform_insight",
    "ideal_for",
    "avoid_if",
    "recommendation",
]


def get_completed_ids():
    if not OUTPUT.exists():
        return set()

    df = pd.read_csv(OUTPUT)

    if "phone_id" not in df.columns:
        return set()

    return set(df["phone_id"].astype(str))


def has_summary(phone_id):
    profile = get_complete_phone_profile(phone_id)
    summary = profile["summary"]
    return summary is not None and not summary.empty


def append_row(row):
    file_exists = OUTPUT.exists()

    with open(OUTPUT, "a", newline="", encoding="utf-8-sig") as file:
        writer = csv.DictWriter(file, fieldnames=COLUMNS)

        if not file_exists:
            writer.writeheader()

        writer.writerow(row)


def main():
    print("=" * 55)
    print("Consumer Intelligence Platform")
    print("Module 13C - Generate All Local AI Insights")
    print("=" * 55)

    phones = search_phones("")
    completed_ids = get_completed_ids()

    print(f"Existing completed insights: {len(completed_ids)}")

    provider = OllamaProvider()

    remaining = []

    for _, phone in phones.iterrows():
        phone_id = str(phone["phone_id"])

        if phone_id in completed_ids:
            continue

        if not has_summary(phone_id):
            continue

        remaining.append(phone_id)

    print(f"Remaining phones to generate: {len(remaining)}")

    for phone_id in tqdm(remaining, desc="Generating insights"):
        try:
            row = generate_phone_insight(phone_id, provider=provider)

            if row is None:
                continue

            append_row(row)

        except KeyboardInterrupt:
            print("\nStopped by user. Progress has been saved.")
            break

        except Exception as error:
            print(f"\nFailed for {phone_id}: {error}")

    print("\nDone.")
    print(f"Output file: {OUTPUT}")


if __name__ == "__main__":
    main()