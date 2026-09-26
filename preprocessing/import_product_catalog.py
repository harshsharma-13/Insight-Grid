from pathlib import Path
import pandas as pd
import re
from difflib import SequenceMatcher


PROJECT_ROOT = Path(__file__).resolve().parent.parent

RAW_LINKS_FILE = PROJECT_ROOT / "data" / "raw" / "phones_link.csv"
IMAGE_DIR = PROJECT_ROOT / "assets" / "phone_images"

OUTPUT_FILE = PROJECT_ROOT / "data" / "processed" / "phones_product_catalog.csv"


def slugify(text):
    text = str(text).lower().strip()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return text.strip("-")


def similarity(a, b):
    return SequenceMatcher(None, a, b).ratio()


def find_image(phone_name):
    phone_slug = slugify(phone_name)

    images = [
        image for image in IMAGE_DIR.iterdir()
        if image.is_file()
    ]

    # Stage 1: exact match
    for image in images:
        image_slug = slugify(image.stem)
        if image_slug == phone_slug:
            return image.name, "Exact"

    # Similar names are not evidence that two model images are interchangeable.
    return "", "Needs image verification"


def main():
    print("=" * 55)
    print("Product Catalog Importer")
    print("=" * 55)

    links_df = pd.read_csv(RAW_LINKS_FILE)

    rows = []

    for _, row in links_df.iterrows():
        phone_id = row["phone_id"]
        phone_name = row["phone_name"]
        smartprix_link = row["smartprix_link"]

        image_filename, match_type = find_image(phone_name)

        rows.append({
            "phone_id": phone_id,
            "phone_name": phone_name,
            "smartprix_link": smartprix_link,
            "image_filename": image_filename,
            "image_local_path": f"assets/phone_images/{image_filename}" if image_filename else "",
            "image_status": "Found" if image_filename else "Missing",
            "image_match_type": match_type,
        })

    output = pd.DataFrame(rows)
    if OUTPUT_FILE.exists():
        existing = pd.read_csv(OUTPUT_FILE)
        extras = [key for key in existing.columns if key not in output.columns and key != "phone_id"]
        output = output.merge(existing[["phone_id", *extras]], on="phone_id", how="left", validate="one_to_one")
    # Legacy link files are not source-verified. Save candidates only.
    staged_file = OUTPUT_FILE.with_name("phones_product_catalog.candidate.csv")
    output.to_csv(staged_file, index=False, encoding="utf-8-sig")

    print(f"Phones processed : {len(output)}")

    print("\nImage status:")
    print(output["image_status"].value_counts())

    print("\nMatch type:")
    print(output["image_match_type"].value_counts())

    missing = output[output["image_status"] == "Missing"]

    if len(missing) > 0:
        print("\nMissing images:")
        for _, row in missing.iterrows():
            print(f"- {row['phone_id']} | {row['phone_name']}")

    print("\nCreated:")
    print(staged_file)


if __name__ == "__main__":
    main()
