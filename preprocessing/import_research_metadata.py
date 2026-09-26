from pathlib import Path
import pandas as pd
import sys


PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
from intelligence.catalog import normalize_date

RAW_FILE = PROJECT_ROOT / "data" / "raw" / "Smartphones research data.xlsx"
TEMPLATE_FILE = PROJECT_ROOT / "data" / "processed" / "phones_enrichment_template.csv"
ENRICHED_FILE = PROJECT_ROOT / "data" / "processed" / "phones_enriched.csv"


def clean_value(value):
    if pd.isna(value):
        return ""
    return str(value).strip()


def parse_research_file():
    df = pd.read_excel(RAW_FILE, sheet_name="Smartphone Data", header=None)
    master = pd.read_csv(PROJECT_ROOT / "data/processed/phones_master.csv")
    names = master["phone_name"].str.strip().str.casefold()
    if names.duplicated().any() or master["phone_id"].duplicated().any():
        raise ValueError("Ambiguous master identity")
    identity = dict(zip(names, master["phone_id"]))
    verified = __import__("intelligence.catalog", fromlist=["load_verified_catalog"]).load_verified_catalog()
    for phone_id, entry in verified["phones"].items():
        for alias in entry["accepted_names"]:
            existing = identity.get(alias.strip().casefold())
            if existing and existing != phone_id:
                raise ValueError("Ambiguous alias")
            identity[alias.strip().casefold()] = phone_id

    start_rows = []
    for i, row in df.iterrows():
        value = row[0]
        if isinstance(value, str) and value.strip().startswith("#"):
            start_rows.append(i)

    records = []

    for index, start in enumerate(start_rows, start=1):
        block = df.iloc[start:start + 19]

        phone_name = clean_value(df.iloc[start, 1])
        phone_id = identity.get(phone_name.casefold())
        if not phone_id:
            raise ValueError(f"Unmatched phone name: {phone_name}; refusing row-order ID assignment")

        launch_date = ""
        amazon_price = ""
        flipkart_price = ""
        amazon_rating = ""
        flipkart_rating = ""

        for _, row in block.iterrows():
            label = clean_value(row[1]).lower()

            if label == "launch date":
                launch_date = normalize_date(row[4]) or ""

            if label == "price (₹)":
                amazon_price = clean_value(row[4])
                flipkart_price = clean_value(row[10])

            if label == "overall rating":
                amazon_rating = clean_value(row[4])
                flipkart_rating = clean_value(row[10])

        records.append({
            "phone_id": phone_id,
            "research_phone_name": phone_name,
            "launch_date": launch_date,
            "amazon_price": amazon_price,
            "flipkart_price": flipkart_price,
            "amazon_rating": amazon_rating,
            "flipkart_rating": flipkart_rating,
            "price_last_updated": "",
            "spec_source_url": "Smartphones research data.xlsx",
        })

    return pd.DataFrame(records)


def update_template(metadata_df):
    raise RuntimeError("Unverified workbook metadata may be inspected but cannot overwrite active files. Stage and source-check fields in data/catalog first.")
    template = pd.read_csv(TEMPLATE_FILE)

    updated = template.merge(
        metadata_df,
        on="phone_id",
        how="left",
        suffixes=("", "_research")
    )

    fields = [
        "launch_date",
        "amazon_price",
        "flipkart_price",
        "amazon_rating",
        "flipkart_rating",
        "price_last_updated",
        "spec_source_url",
    ]

    for field in fields:
        research_col = f"{field}_research"
        if research_col in updated.columns:
            updated[field] = updated[research_col].combine_first(updated[field])
            updated = updated.drop(columns=[research_col])

    if "research_phone_name" in updated.columns:
        updated["notes"] = updated.apply(
            lambda row: f"Research file name: {row['research_phone_name']}"
            if pd.notna(row["research_phone_name"])
            else row.get("notes", ""),
            axis=1
        )
        updated = updated.drop(columns=["research_phone_name"])

    updated.to_csv(TEMPLATE_FILE, index=False, encoding="utf-8-sig")
    updated.to_csv(ENRICHED_FILE, index=False, encoding="utf-8-sig")

    return updated


def main():
    print("=" * 50)
    print("Consumer Intelligence Platform")
    print("Module 9.1 - Import Research Metadata")
    print("=" * 50)

    metadata_df = parse_research_file()
    updated_df = update_template(metadata_df)

    print("\nImported metadata rows:", len(metadata_df))
    print("Updated enrichment template rows:", len(updated_df))
    print("\nUpdated files:")
    print(TEMPLATE_FILE)
    print(ENRICHED_FILE)


if __name__ == "__main__":
    main()
