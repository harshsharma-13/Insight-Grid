"""
AI Consumer Intelligence Platform (CIP)

Module:
Build Database

Purpose:
Extract all Flipkart and Amazon reviews from comments_data.xlsx
and generate the master CSV datasets.

Author: Harsh Sharma
"""

from pathlib import Path
import pandas as pd

# ==========================================================
# PROJECT PATHS
# ==========================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

RAW_DATA = PROJECT_ROOT / "data" / "raw"
PROCESSED_DATA = PROJECT_ROOT / "data" / "processed"

COMMENTS_FILE = RAW_DATA / "comments_data.xlsx"

PROCESSED_DATA.mkdir(parents=True, exist_ok=True)

# ==========================================================
# EXCEL LAYOUT
# ==========================================================

FLIPKART_COLUMN = 0
AMAZON_COLUMN = 2

FIRST_REVIEW_ROW = 1

EMPTY_TEXT = "No visible comments/reviews"

# ==========================================================
# HELPERS
# ==========================================================


def clean_review(text):
    """
    Returns a cleaned review or None if it should be ignored.
    """

    if pd.isna(text):
        return None

    text = str(text).strip()

    if text == "":
        return None

    if text.lower() == EMPTY_TEXT.lower():
        return None

    return text


def extract_platform_reviews(df, column_index):
    """
    Extract reviews from one platform column.
    """

    reviews = []

    if column_index >= len(df.columns):
        return reviews

    column = df.iloc[FIRST_REVIEW_ROW:, column_index]

    for value in column:

        review = clean_review(value)

        if review is not None:
            reviews.append(review)

    return reviews


# ==========================================================
# MAIN EXTRACTION
# ==========================================================


def build_database():

    workbook = pd.ExcelFile(COMMENTS_FILE)

    reviews_master = []
    phones_master = []

    review_counter = 1
    phone_counter = 1

    print("\nProcessing phones...\n")

    for sheet in workbook.sheet_names:

        phone_id = f"PH{phone_counter:03d}"
        phone_name = sheet

        df = pd.read_excel(workbook, sheet_name=sheet, header=None)

        flipkart_reviews = extract_platform_reviews(
            df,
            FLIPKART_COLUMN
        )

        amazon_reviews = extract_platform_reviews(
            df,
            AMAZON_COLUMN
        )

        phones_master.append({
            "phone_id": phone_id,
            "phone_name": phone_name,
            "flipkart_review_count": len(flipkart_reviews),
            "amazon_review_count": len(amazon_reviews),
            "total_review_count":
                len(flipkart_reviews) + len(amazon_reviews)
        })

        for review in flipkart_reviews:

            reviews_master.append({

                "review_id": f"REV{review_counter:06d}",

                "phone_id": phone_id,

                "phone_name": phone_name,

                "platform": "Flipkart",

                "review_text": review

            })

            review_counter += 1

        for review in amazon_reviews:

            reviews_master.append({

                "review_id": f"REV{review_counter:06d}",

                "phone_id": phone_id,

                "phone_name": phone_name,

                "platform": "Amazon",

                "review_text": review

            })

            review_counter += 1

        print(
            f"✓ {phone_name}"
            f" | Flipkart: {len(flipkart_reviews)}"
            f" | Amazon: {len(amazon_reviews)}"
        )

        phone_counter += 1

    phones_df = pd.DataFrame(phones_master)

    reviews_df = pd.DataFrame(reviews_master)

    return phones_df, reviews_df


# ==========================================================
# SAVE OUTPUTS
# ==========================================================


def save_outputs(phones_df, reviews_df):

    if any((PROCESSED_DATA / name).exists() for name in ("phones_master.csv", "reviews_master.csv")):
        raise RuntimeError("Legacy bootstrap cannot replace existing phone/review IDs. Use the verified catalog overlay; review imports are frozen.")

    phones_path = PROCESSED_DATA / "phones_master.csv"

    reviews_path = PROCESSED_DATA / "reviews_master.csv"

    phones_df.to_csv(
        phones_path,
        index=False,
        encoding="utf-8-sig"
    )

    reviews_df.to_csv(
        reviews_path,
        index=False,
        encoding="utf-8-sig"
    )

    print("\n------------------------------------------")

    print("CSV files created successfully.\n")

    print(phones_path)

    print(reviews_path)


# ==========================================================
# SUMMARY
# ==========================================================


def print_summary(phones_df, reviews_df):

    print("\n==========================================")

    print("BUILD SUMMARY")

    print("==========================================")

    print(f"Phones Processed : {len(phones_df)}")

    print(
        f"Total Reviews : {len(reviews_df)}"
    )

    print(
        f"Flipkart Reviews : "
        f"{(reviews_df['platform']=='Flipkart').sum()}"
    )

    print(
        f"Amazon Reviews : "
        f"{(reviews_df['platform']=='Amazon').sum()}"
    )

    print("==========================================\n")


# ==========================================================
# MAIN
# ==========================================================


def main():

    print("=" * 50)
    print("Consumer Intelligence Platform")
    print("Module 2 - Build Database")
    print("=" * 50)

    phones_df, reviews_df = build_database()

    save_outputs(phones_df, reviews_df)

    print_summary(phones_df, reviews_df)


if __name__ == "__main__":
    main()
