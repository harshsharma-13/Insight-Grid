from pathlib import Path
import pandas as pd
from playwright.sync_api import sync_playwright

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CATALOG_FILE = PROJECT_ROOT / "data" / "processed" / "phones_product_catalog.csv"


def main():
    catalog = pd.read_csv(CATALOG_FILE)
    row = catalog.iloc[0]

    phone_name = row["phone_name"]
    url = row["smartprix_link"]

    print("Testing:", phone_name)
    print("URL:", url)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()

        page.goto(url, wait_until="networkidle", timeout=60000)
        page.wait_for_timeout(5000)

        print("\nPage title:")
        print(page.title())

        text = page.locator("body").inner_text()
        print("\nFirst 1500 characters:")
        print(text[:1500])

        browser.close()


if __name__ == "__main__":
    main()