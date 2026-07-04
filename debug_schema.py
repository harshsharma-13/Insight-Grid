import sqlite3
import pandas as pd
from pathlib import Path

DB_PATH = Path("data/acip.db")

conn = sqlite3.connect(DB_PATH)

tables = [
    "phones",
    "reviews",
    "phone_ai_insights",
    "phone_summary",
    "phones_product_catalog",
    "phones_specifications",
    "phones_product_intelligence",
]

for table in tables:
    print("\n" + "=" * 60)
    print(table)
    print("=" * 60)

    df = pd.read_sql_query(f"PRAGMA table_info({table})", conn)
    print(df[["name", "type"]].to_string(index=False))

conn.close()