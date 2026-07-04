import sqlite3
import pandas as pd
from pathlib import Path

DB_PATH = Path("data/acip.db")

conn = sqlite3.connect(DB_PATH)

query = """
SELECT
    p.phone_id,
    p.phone_name,
    pc.image_local_path AS catalog_image,
    ps.image_local_path AS specs_image
FROM phones p
LEFT JOIN phones_product_catalog pc
    ON p.phone_id = pc.phone_id
LEFT JOIN phones_specifications ps
    ON p.phone_id = ps.phone_id
WHERE p.phone_name LIKE '%Redmi Note 15%'
"""

df = pd.read_sql_query(query, conn)
print(df.to_string(index=False))

conn.close()