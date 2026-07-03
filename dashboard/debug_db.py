from dashboard_data import read_sql

print("phones_product_catalog")
print(read_sql("PRAGMA table_info(phones_product_catalog)"))

print("\nphones_specifications")
print(read_sql("PRAGMA table_info(phones_specifications)"))

print("\nphone_ai_insights")
print(read_sql("PRAGMA table_info(phone_ai_insights)"))

print("\nphone_summary")
print(read_sql("PRAGMA table_info(phone_summary)"))
