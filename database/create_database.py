"""
AI Consumer Intelligence Platform (CIP)

Module:
Create SQLite Database

Purpose:
Create data/acip.db from processed CSV files.

Author: Harsh Sharma
"""

from pathlib import Path
import sqlite3
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parent.parent

DATA_DIR = PROJECT_ROOT / "data"
PROCESSED_DATA = DATA_DIR / "processed"

DB_PATH = DATA_DIR / "acip.db"

PHONES_FILE = PROCESSED_DATA / "phones_master.csv"
REVIEWS_FILE = PROCESSED_DATA / "reviews_clean.csv"


def load_csv_files():
    """Load processed CSV files."""

    if not PHONES_FILE.exists():
        raise FileNotFoundError(f"Missing file: {PHONES_FILE}")

    if not REVIEWS_FILE.exists():
        raise FileNotFoundError(f"Missing file: {REVIEWS_FILE}")

    phones_df = pd.read_csv(PHONES_FILE)
    reviews_df = pd.read_csv(REVIEWS_FILE)

    return phones_df, reviews_df


def create_connection():
    """Create SQLite connection."""

    return sqlite3.connect(DB_PATH)


def create_tables(conn):
    """Create database tables."""

    cursor = conn.cursor()

    cursor.execute("DROP TABLE IF EXISTS phones")
    cursor.execute("DROP TABLE IF EXISTS reviews")

    cursor.execute("""
        CREATE TABLE phones (
            phone_id TEXT PRIMARY KEY,
            phone_name TEXT NOT NULL,
            flipkart_review_count INTEGER,
            amazon_review_count INTEGER,
            total_review_count INTEGER
        )
    """)

    cursor.execute("""
        CREATE TABLE reviews (
            review_id TEXT PRIMARY KEY,
            phone_id TEXT NOT NULL,
            phone_name TEXT NOT NULL,
            platform TEXT NOT NULL,
            review_text TEXT NOT NULL,
            clean_review TEXT,
            review_length INTEGER,
            word_count INTEGER,
            quality_flag TEXT,
            is_duplicate BOOLEAN,
            FOREIGN KEY (phone_id) REFERENCES phones(phone_id)
        )
    """)

    conn.commit()


def insert_data(conn, phones_df, reviews_df):
    """Insert dataframes into SQLite tables."""

    phones_df.to_sql(
        "phones",
        conn,
        if_exists="append",
        index=False
    )

    reviews_df.to_sql(
        "reviews",
        conn,
        if_exists="append",
        index=False
    )

    conn.commit()


def validate_database(conn):
    """Validate inserted records."""

    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM phones")
    phone_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM reviews")
    review_count = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COUNT(*)
        FROM reviews
        WHERE phone_id NOT IN (SELECT phone_id FROM phones)
    """)
    orphan_reviews = cursor.fetchone()[0]

    return phone_count, review_count, orphan_reviews


def print_summary(phone_count, review_count, orphan_reviews):
    """Print database creation summary."""

    print("\n==========================================")
    print("DATABASE SUMMARY")
    print("==========================================")
    print(f"Database path       : {DB_PATH}")
    print(f"Phones inserted     : {phone_count}")
    print(f"Reviews inserted    : {review_count}")
    print(f"Orphan reviews      : {orphan_reviews}")
    print("==========================================\n")


def main():
    """Run database creation module."""

    print("=" * 50)
    print("Consumer Intelligence Platform")
    print("Module 4 - Create SQLite Database")
    print("=" * 50)

    phones_df, reviews_df = load_csv_files()

    conn = create_connection()

    create_tables(conn)

    insert_data(conn, phones_df, reviews_df)

    phone_count, review_count, orphan_reviews = validate_database(conn)

    conn.close()

    print_summary(phone_count, review_count, orphan_reviews)


if __name__ == "__main__":
    main()