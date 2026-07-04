import sqlite3
import pandas as pd
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
DB_PATH = PROJECT_ROOT / "data" / "acip.db"


CSV_PATH = "data/processed/phones_product_intelligence.csv"


# --------------------------------------------------
# LOAD CSV
# --------------------------------------------------

csv_df = pd.read_csv(CSV_PATH)

print("\nCSV columns:")
print(csv_df.columns.tolist())


required_columns = [
    "phone_id",
    "launch_price",
]

missing_columns = [
    col for col in required_columns
    if col not in csv_df.columns
]

if missing_columns:
    raise ValueError(
        f"Missing CSV columns: {missing_columns}"
    )


# --------------------------------------------------
# CLEAN LAUNCH PRICE
# --------------------------------------------------

def clean_price(value):
    if pd.isna(value):
        return None

    value = str(value).strip()

    value = (
        value
        .replace("₹", "")
        .replace(",", "")
        .replace("Rs.", "")
        .replace("Rs", "")
        .strip()
    )

    try:
        return float(value)
    except ValueError:
        return None


csv_df["launch_price"] = (
    csv_df["launch_price"]
    .apply(clean_price)
)


# --------------------------------------------------
# CONNECT TO DATABASE
# --------------------------------------------------

print("\nDatabase:")
print(DB_PATH)

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()


# --------------------------------------------------
# CHECK TABLE
# --------------------------------------------------

cursor.execute(
    "PRAGMA table_info(phones_product_intelligence)"
)

existing_columns = [
    row[1]
    for row in cursor.fetchall()
]

print("\nCurrent database columns:")
print(existing_columns)


# --------------------------------------------------
# ADD COLUMN IF MISSING
# --------------------------------------------------

if "launch_price" not in existing_columns:

    print("\nAdding launch_price column...")

    cursor.execute("""
        ALTER TABLE phones_product_intelligence
        ADD COLUMN launch_price REAL
    """)

else:

    print("\nlaunch_price column already exists.")


# --------------------------------------------------
# UPDATE DATABASE
# --------------------------------------------------

updated = 0
missing_prices = 0


for _, row in csv_df.iterrows():

    phone_id = row["phone_id"]
    launch_price = row["launch_price"]

    if pd.isna(launch_price):
        missing_prices += 1
        continue

    cursor.execute(
        """
        UPDATE phones_product_intelligence
        SET launch_price = ?
        WHERE phone_id = ?
        """,
        (
            float(launch_price),
            phone_id,
        ),
    )

    if cursor.rowcount > 0:
        updated += 1


conn.commit()


# --------------------------------------------------
# VALIDATE
# --------------------------------------------------

validation = pd.read_sql_query(
    """
    SELECT
        phone_id,
        phone_name,
        launch_price
    FROM phones_product_intelligence
    ORDER BY phone_id
    """,
    conn,
)


print("\n----------------------------------")
print("IMPORT COMPLETE")
print("----------------------------------")

print(f"Rows updated: {updated}")
print(f"CSV rows without price: {missing_prices}")

print("\nDatabase preview:")
print(validation.head(10))

print("\nLaunch prices present:")
print(validation["launch_price"].notna().sum())

print("\nLaunch prices missing:")
print(validation["launch_price"].isna().sum())


conn.close()