import sqlite3
from pathlib import Path

DB_PATH = Path("data/acip.db")

NEW_PATH = "assets/phone_images/xiaomi-redmi-note-15-v2.jpg"
PHONE_ID = "PH056"

conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

# Update catalog table
cur.execute("""
UPDATE phones_product_catalog
SET image_local_path = ?, image_filename = ?
WHERE phone_id = ?
""", (NEW_PATH, Path(NEW_PATH).name, PHONE_ID))

# Update specifications table
cur.execute("""
UPDATE phones_specifications
SET image_local_path = ?, image_filename = ?
WHERE phone_id = ?
""", (NEW_PATH, Path(NEW_PATH).name, PHONE_ID))

conn.commit()

print("Updated rows:")
print("phones_product_catalog:", cur.execute(
    "SELECT phone_name, image_local_path FROM phones_product_catalog WHERE phone_id=?",
    (PHONE_ID,)
).fetchone())

print("phones_specifications:", cur.execute(
    "SELECT phone_name, image_local_path FROM phones_specifications WHERE phone_id=?",
    (PHONE_ID,)
).fetchone())

conn.close()