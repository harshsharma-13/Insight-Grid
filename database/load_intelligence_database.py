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
    "phone_summary": PROCESSED / "phone_summary.csv",
    "platform_summary": PROCESSED / "platform_summary.csv",
    "aspect_summary": PROCESSED / "aspect_summary.csv",
    "consumer_intelligence": PROCESSED / "consumer_intelligence.csv",
    "phones_product_intelligence": PROCESSED / "phones_product_intelligence.csv",
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

    print("=" * 55)
    print("Consumer Intelligence Platform")
    print("Module 10 - Intelligence Database Synchronizer")
    print("=" * 55)

    conn = sqlite3.connect(DB)

    for table, file in FILES.items():
        sync_table(conn, table, file)

    conn.commit()

    cursor = conn.cursor()

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