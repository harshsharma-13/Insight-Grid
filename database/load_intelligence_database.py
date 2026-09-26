"""
AI Consumer Intelligence Platform

Module 10
Intelligence Database Synchronizer
"""

from pathlib import Path
import sqlite3
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent

DB = PROJECT_ROOT / "data" / "acip.db"
PROCESSED = PROJECT_ROOT / "data" / "processed"

FILES = {
    "review_sentiment": PROCESSED / "reviews_sentiment.csv",
    "reviews_aspects": PROCESSED / "reviews_aspects.csv",
    "phone_summary": PROCESSED / "phone_summary.csv",
    "platform_summary": PROCESSED / "platform_summary.csv",
    "aspect_summary": PROCESSED / "aspect_summary.csv",
    "consumer_intelligence": PROCESSED / "consumer_intelligence.csv",
    "phones_product_intelligence": PROCESSED / "phones_product_intelligence.csv",
    "phone_ai_insights": PROCESSED / "phone_ai_insights.csv",
    "phones_product_catalog": PROCESSED / "phones_product_catalog.csv",
    "phones_specifications": PROCESSED / "phones_specifications.csv",
}


def sync_table(connection, table_name, csv_file):

    print(f"\nSynchronizing {table_name}")

    if not csv_file.exists():
        print("Missing:", csv_file)
        return

    df = pd.read_csv(csv_file)

    df.to_sql(
        table_name,
        connection,
        if_exists="replace",
        index=False
    )

    print(f"Rows synced: {len(df)}")


def main():
    raise RuntimeError("Full-table legacy sync is disabled during catalog repair. Use scripts/export_web_snapshot.py --catalog-only; existing reviews must remain unchanged.")

    print("=" * 55)
    print("Consumer Intelligence Platform")
    print("Module 10 - Intelligence Database Synchronizer")
    print("=" * 55)

    conn = sqlite3.connect(DB)

    for table, file in FILES.items():
        sync_table(conn, table, file)

    cursor = conn.cursor()

    cursor.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS idx_review_sentiment_review_id
        ON review_sentiment(review_id)
    """)
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_reviews_aspects_review_id
        ON reviews_aspects(review_id)
    """)
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_reviews_aspects_aspect
        ON reviews_aspects(aspect)
    """)
    cursor.execute("""
        UPDATE reviews
        SET is_duplicate = COALESCE(
            (SELECT review_sentiment.is_duplicate
             FROM review_sentiment
             WHERE review_sentiment.review_id = reviews.review_id),
            reviews.is_duplicate
        )
    """)
    cursor.execute("PRAGMA optimize")
    conn.commit()

    print("\n===================================")
    print("DATABASE TABLES")
    print("===================================")

    cursor.execute("""
        SELECT name
        FROM sqlite_master
        WHERE type='table'
        ORDER BY name
    """)

    tables = cursor.fetchall()

    for t in tables:
        print("-", t[0])

    conn.close()

    print("\nSynchronization Complete.")


if __name__ == "__main__":
    main()
