import sqlite3
import pandas as pd
from config import DB_PATH


def get_connection():
    return sqlite3.connect(DB_PATH)


def read_sql(query, params=None):
    with get_connection() as conn:
        return pd.read_sql_query(query, conn, params=params or [])


def get_kpis():
    total_phones = read_sql("SELECT COUNT(*) AS count FROM phones").iloc[0]["count"]
    total_reviews = read_sql("SELECT COUNT(*) AS count FROM reviews").iloc[0]["count"]

    phones_with_insights = read_sql(
        "SELECT COUNT(*) AS count FROM phone_ai_insights"
    ).iloc[0]["count"]

    avg_positive = read_sql(
        "SELECT AVG(positive_percent) AS avg_positive FROM phone_summary"
    ).iloc[0]["avg_positive"]

    return {
        "total_phones": int(total_phones),
        "total_reviews": int(total_reviews),
        "phones_with_insights": int(phones_with_insights),
        "avg_positive": round(float(avg_positive), 1),
    }


def get_verdict_distribution():
    return read_sql("""
        SELECT consumer_verdict, COUNT(*) AS count
        FROM phone_ai_insights
        GROUP BY consumer_verdict
        ORDER BY count DESC
    """)


def get_top_phones(limit=10):
    return read_sql("""
        SELECT
            phone_name,
            review_count,
            positive_percent,
            negative_percent
        FROM phone_summary
        ORDER BY positive_percent DESC, review_count DESC
        LIMIT ?
    """, [limit])


def get_brand_distribution():
    return read_sql("""
        SELECT brand, COUNT(*) AS count
        FROM phones_product_intelligence
        GROUP BY brand
        ORDER BY count DESC
    """)

def get_phone_options():
    return read_sql("""
        SELECT phone_id, phone_name
        FROM phones
        ORDER BY phone_name
    """)


def get_phone_catalog(phone_id):
    return read_sql("""
        SELECT
            c.phone_id,
            c.phone_name,
            c.smartprix_link,
            c.image_filename,
            c.image_local_path,

            COALESCE(s.brand, p.brand) AS brand,
            s.launch_date,

            s.display,
            s.display_type,
            s.refresh_rate,
            s.resolution,
            s.processor,
            s.ram,
            s.storage,
            s.battery,
            s.charging,
            s.rear_camera,
            s.front_camera,
            s.android_version,
            s.supports_5g,
            s.nfc,
            s.bluetooth,
            s.wifi,
            s.weight,

            p.flipkart_price,
            p.amazon_price,
            p.flipkart_rating,
            p.amazon_rating,
            p.price_segment,
            p.chipset_brand,
            p.battery_segment

        FROM phones_product_catalog c
        LEFT JOIN phones_specifications s
            ON c.phone_id = s.phone_id
        LEFT JOIN phones_product_intelligence p
            ON c.phone_id = p.phone_id
        WHERE c.phone_id = ?
    """, [phone_id])


def get_phone_ai_insight(phone_id):
    return read_sql("""
        SELECT *
        FROM phone_ai_insights
        WHERE phone_id = ?
    """, [phone_id])


def get_phone_sentiment_summary(phone_id):
    return read_sql("""
        SELECT *
        FROM phone_summary
        WHERE phone_id = ?
    """, [phone_id])


def get_phone_platform_summary(phone_id):
    return read_sql("""
        SELECT *
        FROM platform_summary
        WHERE phone_id = ?
    """, [phone_id])