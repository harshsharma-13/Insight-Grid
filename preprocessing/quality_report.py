"""
AI Consumer Intelligence Platform (CIP)

Module:
Data Validation & Quality Report

Purpose:
Generate a quality report from phones_master.csv, reviews_clean.csv,
and acip.db.

Author: Harsh Sharma
"""

from pathlib import Path
import sqlite3
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parent.parent

DATA_DIR = PROJECT_ROOT / "data"
PROCESSED_DATA = DATA_DIR / "processed"
OUTPUTS_DIR = PROJECT_ROOT / "outputs"

PHONES_FILE = PROCESSED_DATA / "phones_master.csv"
REVIEWS_FILE = PROCESSED_DATA / "reviews_clean.csv"
DB_FILE = DATA_DIR / "acip.db"
REPORT_FILE = OUTPUTS_DIR / "quality_report.txt"

OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)


def load_data():
    """Load processed datasets."""

    phones_df = pd.read_csv(PHONES_FILE)
    reviews_df = pd.read_csv(REVIEWS_FILE)

    return phones_df, reviews_df


def validate_database():
    """Validate SQLite database counts."""

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM phones")
    db_phone_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM reviews")
    db_review_count = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COUNT(*)
        FROM reviews
        WHERE phone_id NOT IN (SELECT phone_id FROM phones)
    """)
    orphan_reviews = cursor.fetchone()[0]

    conn.close()

    return db_phone_count, db_review_count, orphan_reviews


def build_report(phones_df, reviews_df):
    """Build text report."""

    db_phone_count, db_review_count, orphan_reviews = validate_database()

    phones_without_reviews = phones_df[
        phones_df["total_review_count"] == 0
    ]

    report = []

    report.append("=" * 60)
    report.append("AI CONSUMER INTELLIGENCE PLATFORM")
    report.append("SPRINT 1 - DATA QUALITY REPORT")
    report.append("=" * 60)
    report.append("")

    report.append("1. DATASET OVERVIEW")
    report.append("-" * 60)
    report.append(f"Phones in master file      : {len(phones_df)}")
    report.append(f"Reviews in clean file      : {len(reviews_df)}")
    report.append(f"Phones in SQLite database  : {db_phone_count}")
    report.append(f"Reviews in SQLite database : {db_review_count}")
    report.append(f"Orphan reviews             : {orphan_reviews}")
    report.append("")

    report.append("2. PLATFORM DISTRIBUTION")
    report.append("-" * 60)
    platform_counts = reviews_df["platform"].value_counts()
    for platform, count in platform_counts.items():
        report.append(f"{platform:<10}: {count}")
    report.append("")

    report.append("3. QUALITY FLAGS")
    report.append("-" * 60)
    quality_counts = reviews_df["quality_flag"].value_counts()
    for flag, count in quality_counts.items():
        report.append(f"{flag:<15}: {count}")
    report.append("")

    report.append("4. DUPLICATE CHECKS")
    report.append("-" * 60)
    report.append(f"Duplicate review IDs       : {reviews_df['review_id'].duplicated().sum()}")
    report.append(f"Duplicate phone IDs        : {phones_df['phone_id'].duplicated().sum()}")
    report.append(f"Duplicate review texts     : {reviews_df['is_duplicate'].sum()}")
    report.append("")

    report.append("5. MISSING VALUE CHECKS")
    report.append("-" * 60)
    for column in reviews_df.columns:
        missing = reviews_df[column].isna().sum()
        report.append(f"{column:<20}: {missing}")
    report.append("")

    report.append("6. REVIEW LENGTH")
    report.append("-" * 60)
    report.append(f"Average word count         : {reviews_df['word_count'].mean():.2f}")
    report.append(f"Median word count          : {reviews_df['word_count'].median():.2f}")
    report.append(f"Max word count             : {reviews_df['word_count'].max()}")
    report.append("")

    report.append("7. PHONES WITHOUT REVIEWS")
    report.append("-" * 60)
    if len(phones_without_reviews) == 0:
        report.append("None")
    else:
        for phone in phones_without_reviews["phone_name"].tolist():
            report.append(f"- {phone}")
    report.append("")

    report.append("8. TOP 10 PHONES BY REVIEW COUNT")
    report.append("-" * 60)
    top_phones = phones_df.sort_values(
        by="total_review_count",
        ascending=False
    ).head(10)

    for _, row in top_phones.iterrows():
        report.append(
            f"{row['phone_name']:<35} : {row['total_review_count']}"
        )

    report.append("")
    report.append("=" * 60)
    report.append("REPORT COMPLETE")
    report.append("=" * 60)

    return "\n".join(report)


def save_report(report_text):
    """Save report to outputs folder."""

    with open(REPORT_FILE, "w", encoding="utf-8") as file:
        file.write(report_text)


def main():
    """Run quality report module."""

    print("=" * 50)
    print("Consumer Intelligence Platform")
    print("Module 5 - Data Validation & Quality Report")
    print("=" * 50)

    phones_df, reviews_df = load_data()

    report_text = build_report(phones_df, reviews_df)

    save_report(report_text)

    print(report_text)
    print(f"\nReport saved at:\n{REPORT_FILE}")


if __name__ == "__main__":
    main()