"""
AI Consumer Intelligence Platform

Module 11:
Intelligence Service

Purpose:
Provide reusable database query functions for the dashboard and insight engine.
"""

from pathlib import Path
import sqlite3
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DB_PATH = PROJECT_ROOT / "data" / "acip.db"


def get_connection():
    """Create SQLite database connection."""
    return sqlite3.connect(DB_PATH)


def read_sql(query, params=None):
    """Run SQL query and return dataframe."""
    with get_connection() as conn:
        return pd.read_sql_query(query, conn, params=params or [])


def search_phones(search_term=""):
    """Search phones by name."""
    query = """
        SELECT phone_id, phone_name
        FROM phones
        WHERE phone_name LIKE ?
        ORDER BY phone_name
    """
    return read_sql(query, [f"%{search_term}%"])


def get_phone_profile(phone_id):
    """Get product intelligence for one phone."""
    query = """
        SELECT *
        FROM phones_product_intelligence
        WHERE phone_id = ?
    """
    return read_sql(query, [phone_id])


def get_phone_summary(phone_id):
    """Get overall sentiment summary for one phone."""
    query = """
        SELECT *
        FROM phone_summary
        WHERE phone_id = ?
    """
    return read_sql(query, [phone_id])


def get_platform_comparison(phone_id):
    """Get Amazon vs Flipkart summary for one phone."""
    query = """
        SELECT *
        FROM platform_summary
        WHERE phone_id = ?
        ORDER BY platform
    """
    return read_sql(query, [phone_id])


def get_aspect_summary(phone_id):
    """Get aspect-level summary for one phone."""
    query = """
        SELECT *
        FROM aspect_summary
        WHERE phone_id = ?
        ORDER BY aspect, platform
    """
    return read_sql(query, [phone_id])


def get_consumer_intelligence(phone_id):
    """Get consumer intelligence row for one phone."""
    query = """
        SELECT *
        FROM consumer_intelligence
        WHERE phone_id = ?
    """
    return read_sql(query, [phone_id])


def get_reviews(phone_id, limit=5):
    """Get recent/available reviews for one phone."""
    query = """
        SELECT
            review_id,
            phone_id,
            phone_name,
            platform,
            review_text,
            clean_review,
            quality_flag,
            is_duplicate
        FROM reviews
        WHERE phone_id = ?
        LIMIT ?
    """
    return read_sql(query, [phone_id, limit])


def get_complete_phone_profile(phone_id):
    """Return all available intelligence for one phone as dataframes."""

    return {
        "profile": get_phone_profile(phone_id),
        "summary": get_phone_summary(phone_id),
        "platform_comparison": get_platform_comparison(phone_id),
        "aspect_summary": get_aspect_summary(phone_id),
        "consumer_intelligence": get_consumer_intelligence(phone_id),
        "reviews": get_reviews(phone_id),
        "ai_insights": get_ai_insights(phone_id),
    }


def test_service():
    """Simple service test."""

    print("=" * 50)
    print("Intelligence Service Test")
    print("=" * 50)

    phones = search_phones("Poco")

    print("\nSearch Results:")
    print(phones.head())

    if phones.empty:
        print("No phones found.")
        return

    phone_id = phones.iloc[0]["phone_id"]
    phone_name = phones.iloc[0]["phone_name"]

    print(f"\nTesting complete profile for: {phone_name} ({phone_id})")

    profile = get_complete_phone_profile(phone_id)

    for key, value in profile.items():
        print(f"{key}: {len(value)} rows")


def get_ai_insights(phone_id):
    """Get generated AI insights for one phone."""
    query = """
        SELECT *
        FROM phone_ai_insights
        WHERE phone_id = ?
    """
    return read_sql(query, [phone_id])


if __name__ == "__main__":
    test_service()