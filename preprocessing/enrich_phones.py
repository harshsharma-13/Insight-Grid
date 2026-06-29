"""
AI Consumer Intelligence Platform (CIP)

Module:
Phone Enrichment Engine

Purpose:
Create and maintain a structured phone enrichment template and merge
enrichment fields with phones_master.csv.

Author: Harsh Sharma
"""

from pathlib import Path
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parent.parent
PROCESSED_DATA = PROJECT_ROOT / "data" / "processed"

PHONES_MASTER_FILE = PROCESSED_DATA / "phones_master.csv"
ENRICHMENT_TEMPLATE_FILE = PROCESSED_DATA / "phones_enrichment_template.csv"
PHONES_ENRICHED_FILE = PROCESSED_DATA / "phones_enriched.csv"


ENRICHMENT_COLUMNS = [
    "phone_id",
    "phone_name",
    "brand",

    # Static specifications
    "launch_date",
    "display",
    "processor",
    "battery",
    "camera",
    "ram",
    "storage",
    "os",

    # Platform-specific dynamic data
    "flipkart_price",
    "amazon_price",
    "flipkart_rating",
    "amazon_rating",
    "price_last_updated",

    # Media and sources
    "image_url",
    "image_local_path",
    "smartprix_url",
    "spec_source_url",

    # Tracking
    "enrichment_status",
    "last_updated",
    "notes",
]


def load_phones_master() -> pd.DataFrame:
    """Load phones master dataset."""

    if not PHONES_MASTER_FILE.exists():
        raise FileNotFoundError(
            f"Missing file: {PHONES_MASTER_FILE}. Run build_database.py first."
        )

    return pd.read_csv(PHONES_MASTER_FILE)


def infer_brand(phone_name: str) -> str:
    """Infer brand from phone name."""

    if pd.isna(phone_name) or str(phone_name).strip() == "":
        return ""

    aliases = {
        "Moto": "Motorola",
        "Motorola": "Motorola",
        "Samsung": "Samsung",
        "Realme": "Realme",
        "Redmi": "Redmi",
        "Poco": "Poco",
        "Vivo": "Vivo",
        "Oppo": "Oppo",
        "Oneplus": "OnePlus",
        "OnePlus": "OnePlus",
        "LAVA": "Lava",
        "Lava": "Lava",
        "Tecno": "Tecno",
        "Infinix": "Infinix",
        "Itel": "Itel",
        "iQOO": "iQOO",
        "HMD": "HMD",
        "Ai+": "Ai+",
    }

    first_word = str(phone_name).strip().split()[0]
    return aliases.get(first_word, first_word)


def create_base_template(phones_df: pd.DataFrame) -> pd.DataFrame:
    """Create a clean enrichment template."""

    template = pd.DataFrame()

    template["phone_id"] = phones_df["phone_id"]
    template["phone_name"] = phones_df["phone_name"]
    template["brand"] = phones_df["phone_name"].apply(infer_brand)

    for column in ENRICHMENT_COLUMNS:
        if column not in template.columns:
            template[column] = ""

    template["enrichment_status"] = "Pending"

    return template[ENRICHMENT_COLUMNS]


def load_or_update_template(phones_df: pd.DataFrame) -> pd.DataFrame:
    """Load existing template and safely update schema if needed."""

    if ENRICHMENT_TEMPLATE_FILE.exists():
        template_df = pd.read_csv(ENRICHMENT_TEMPLATE_FILE)

        # Add new schema columns if missing
        for column in ENRICHMENT_COLUMNS:
            if column not in template_df.columns:
                template_df[column] = ""

        # Remove old/deprecated columns by selecting only current schema
        template_df = template_df[ENRICHMENT_COLUMNS]

        existing_ids = set(template_df["phone_id"])
        master_ids = set(phones_df["phone_id"])

        missing_ids = master_ids - existing_ids

        if missing_ids:
            missing_phones = phones_df[phones_df["phone_id"].isin(missing_ids)]
            missing_template = create_base_template(missing_phones)

            template_df = pd.concat(
                [template_df, missing_template],
                ignore_index=True
            )

        return template_df

    return create_base_template(phones_df)


def build_enriched_phones(
    phones_df: pd.DataFrame,
    template_df: pd.DataFrame
) -> pd.DataFrame:
    """Merge master phone counts with enrichment fields."""

    enriched_df = phones_df.merge(
        template_df,
        on=["phone_id", "phone_name"],
        how="left"
    )

    return enriched_df


def save_outputs(
    template_df: pd.DataFrame,
    enriched_df: pd.DataFrame
) -> None:
    """Save enrichment template and enriched phone dataset."""

    template_df.to_csv(
        ENRICHMENT_TEMPLATE_FILE,
        index=False,
        encoding="utf-8-sig"
    )

    enriched_df.to_csv(
        PHONES_ENRICHED_FILE,
        index=False,
        encoding="utf-8-sig"
    )


def print_summary(
    template_df: pd.DataFrame,
    enriched_df: pd.DataFrame
) -> None:
    """Print enrichment summary."""

    print("\n==========================================")
    print("PHONE ENRICHMENT SUMMARY")
    print("==========================================")
    print(f"Phones in template     : {len(template_df)}")
    print(f"Phones enriched file   : {len(enriched_df)}")

    print("\nEnrichment status:")
    print(template_df["enrichment_status"].value_counts())

    print("\nFiles updated:")
    print(ENRICHMENT_TEMPLATE_FILE)
    print(PHONES_ENRICHED_FILE)
    print("==========================================\n")


def main() -> None:
    """Run phone enrichment module."""

    print("=" * 50)
    print("Consumer Intelligence Platform")
    print("Sprint 2 - Module 9: Phone Enrichment Engine")
    print("=" * 50)

    phones_df = load_phones_master()

    template_df = load_or_update_template(phones_df)

    enriched_df = build_enriched_phones(phones_df, template_df)

    save_outputs(template_df, enriched_df)

    print_summary(template_df, enriched_df)


if __name__ == "__main__":
    main()