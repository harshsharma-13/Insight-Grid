from pathlib import Path
import re
import pandas as pd
from tqdm import tqdm
from playwright.sync_api import sync_playwright


PROJECT_ROOT = Path(__file__).resolve().parent.parent

CATALOG_FILE = PROJECT_ROOT / "data" / "processed" / "phones_product_catalog.csv"
OUTPUT_FILE = PROJECT_ROOT / "data" / "processed" / "phones_specifications.csv"


def clean(value):
    if not value:
        return ""
    return re.sub(r"\s+", " ", str(value)).strip()


def section_lines(lines, section_name, stop_sections):
    if section_name not in lines:
        return []

    start = lines.index(section_name) + 1
    end = len(lines)

    for stop in stop_sections:
        if stop in lines[start:]:
            end = min(end, lines.index(stop, start))

    return lines[start:end]


def display_type_from(display):
    text = display.upper()

    if "AMOLED" in text:
        return "AMOLED"
    if "OLED" in text:
        return "OLED"
    if "IPS" in text:
        return "IPS LCD"
    if "LCD" in text:
        return "LCD"

    return ""


def parse_specs(page_text):
    lines = [clean(line) for line in page_text.splitlines() if clean(line)]

    result = {
        "launch_date": "",
        "display": "",
        "display_type": "",
        "refresh_rate": "",
        "resolution": "",
        "processor": "",
        "ram": "",
        "storage": "",
        "battery": "",
        "charging": "",
        "rear_camera": "",
        "front_camera": "",
        "android_version": "",
        "supports_5g": "",
        "nfc": "",
        "bluetooth": "",
        "wifi": "",
        "weight": "",
    }

    general = section_lines(lines, "General", ["Display"])
    display = section_lines(lines, "Display", ["Camera"])
    camera = section_lines(lines, "Camera", ["Technical"])
    technical = section_lines(lines, "Technical", ["Connectivity"])
    connectivity = section_lines(lines, "Connectivity", ["Battery"])
    battery = section_lines(lines, "Battery", ["Extra"])

    # General
    result["android_version"] = next((x for x in general if "Android" in x), "")
    weight_line = next(
        (
            x for x in general
            if re.search(r"\d+(\.\d+)?\s*g", x, re.IGNORECASE)
         ),
         ""
        )

    if weight_line:
            match = re.search(r"(\d+(\.\d+)?\s*g)", weight_line, re.IGNORECASE)
            result["weight"] = match.group(1) if match else ""


    # Display
    result["display"] = next((x for x in display if "Screen" in x), "")
    result["display_type"] = display_type_from(result["display"])
    result["resolution"] = next((x for x in display if "pixels" in x), "")

    refresh_text = next((x for x in display if "Hz" in x), "")
    match = re.search(r"(\d{2,3})\s*Hz", refresh_text)
    result["refresh_rate"] = match.group(1) if match else ""

    # Camera
    result["rear_camera"] = next((x for x in camera if "Rear Camera" in x), "")
    result["front_camera"] = next((x for x in camera if "Front Camera" in x), "")

    # Technical
    result["processor"] = next(
        (x.replace(" Chipset", "") for x in technical if "Chipset" in x),
        ""
    )

    ram_line = next(
        (
            x for x in technical
            if re.search(r"\d+\s*GB.*RAM", x, re.IGNORECASE)
        ),
        ""
    )

    if ram_line:
        match = re.search(r"(\d+\s*GB)", ram_line, re.IGNORECASE)
        result["ram"] = match.group(1) if match else ""

    result["storage"] = next(
        (x.replace(" Inbuilt Memory", "") for x in technical if "Inbuilt Memory" in x),
        ""
    )

    # Connectivity
    result["supports_5g"] = "Yes" if any("5G" in x for x in connectivity) else "No"
    result["nfc"] = "Yes" if any("NFC" in x for x in connectivity) else "No"
    result["wifi"] = "Yes" if any("WiFi" in x or "Wifi" in x for x in connectivity) else "No"
    result["bluetooth"] = next((x for x in connectivity if "Bluetooth" in x), "")

    # Battery
    result["battery"] = next((x for x in battery if "mAh" in x), "")
    result["charging"] = "; ".join(x for x in battery if "Charging" in x)

    return result


def fetch_page_text(page, url):
    page.goto(url, wait_until="networkidle", timeout=60000)
    page.wait_for_timeout(2500)

    try:
        page.get_by_text("VIEW FULL SPECS").click(timeout=4000)
        page.wait_for_timeout(1500)
    except Exception:
        pass

    return page.locator("body").inner_text()


def main():
    print("=" * 55)
    print("Smartprix Specification Extractor - Module 13.6B")
    print("=" * 55)

    catalog = pd.read_csv(CATALOG_FILE)

    rows = []

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=False,
            slow_mo=200
)
        page = browser.new_page(
            viewport={"width": 1440, "height": 900}
)

        for _, row in tqdm(catalog.iterrows(), total=len(catalog), desc="Extracting specs"):
            phone_id = row["phone_id"]
            phone_name = row["phone_name"]
            url = row["smartprix_link"]

            try:
                page_text = fetch_page_text(page, url)
                specs = parse_specs(page_text)

                rows.append({
                    "phone_id": phone_id,
                    "phone_name": phone_name,
                    "brand": phone_name.split()[0],
                    "smartprix_link": url,
                    "image_filename": row.get("image_filename", ""),
                    "image_local_path": row.get("image_local_path", ""),
                    **specs,
                    "spec_status": "Extracted",
                })

            except Exception as error:
                rows.append({
                    "phone_id": phone_id,
                    "phone_name": phone_name,
                    "brand": phone_name.split()[0],
                    "smartprix_link": url,
                    "image_filename": row.get("image_filename", ""),
                    "image_local_path": row.get("image_local_path", ""),
                    "spec_status": f"Failed: {error}",
                })

            pd.DataFrame(rows).to_csv(
                OUTPUT_FILE,
                index=False,
                encoding="utf-8-sig",
            )

        browser.close()

    print("\nCreated:")
    print(OUTPUT_FILE)
    print(f"Rows saved: {len(rows)}")


if __name__ == "__main__":
    main()