"""
AI Consumer Intelligence Platform

Module 9.2
Product Intelligence Features
"""

from pathlib import Path
import pandas as pd
import re

PROJECT_ROOT = Path(__file__).resolve().parent.parent
PROCESSED = PROJECT_ROOT / "data" / "processed"

INPUT = PROCESSED / "phones_enriched.csv"
OUTPUT = PROCESSED / "phones_product_intelligence.csv"


def classify_price(price):

    try:
        price = float(str(price).replace("₹", "").replace(",", "").strip())
    except:
        return ""

    if price < 10000:
        return "Entry"

    elif price < 15000:
        return "Budget"

    elif price < 20000:
        return "Lower Mid Range"

    elif price < 30000:
        return "Upper Mid Range"

    return "Premium"


def chipset_brand(processor):

    p = str(processor).lower()

    if "snapdragon" in p:
        return "Qualcomm"

    if "dimensity" in p or "mediatek" in p:
        return "MediaTek"

    if "exynos" in p:
        return "Samsung"

    if "tensor" in p:
        return "Google"

    if "apple" in p or "a18" in p:
        return "Apple"

    if "unisoc" in p:
        return "Unisoc"

    return ""


def battery_segment(battery):

    text = str(battery)

    numbers = re.findall(r"\d+", text)

    if not numbers:
        return ""

    mah = int(numbers[0])

    if mah < 5000:
        return "Small"

    elif mah < 6000:
        return "Standard"

    elif mah < 7000:
        return "Large"

    return "Extra Large"


def display_type(display):

    d = str(display).lower()

    if "amoled" in d:
        return "AMOLED"

    if "oled" in d:
        return "OLED"

    if "ips" in d:
        return "IPS LCD"

    if "lcd" in d:
        return "LCD"

    return ""


def refresh_rate(display):

    text = str(display)

    nums = re.findall(r"\d+", text)

    for n in nums:

        hz = int(n)

        if hz in [60, 90, 120, 144, 165]:
            return hz

    return ""


def supports_5g(name):
    # Product names are not a verified connectivity source.
    return ""


def main():

    print("=" * 50)
    print("Product Intelligence Features")
    print("=" * 50)

    df = pd.read_csv(INPUT)

    reference_price = (
        df["flipkart_price"]
        .replace("", pd.NA)
        .fillna(df["amazon_price"])
    )

    df["price_segment"] = reference_price.apply(classify_price)

    df["chipset_brand"] = df["processor"].apply(chipset_brand)

    df["battery_segment"] = df["battery"].apply(battery_segment)

    df["display_type"] = df["display"].apply(display_type)

    df["refresh_rate"] = df["display"].apply(refresh_rate)

    df["supports_5g"] = df["phone_name"].apply(supports_5g)

    df.to_csv(OUTPUT, index=False, encoding="utf-8-sig")

    print("\nCreated:")
    print(OUTPUT)

    print("\nPhones processed:", len(df))


if __name__ == "__main__":
    main()
