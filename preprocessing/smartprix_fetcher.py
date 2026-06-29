from bs4 import BeautifulSoup
import requests
from urllib.parse import quote_plus


PHONE_NAME = "Realme P4R 5G"


def search_smartprix_direct(phone_name):
    query = quote_plus(phone_name)
    url = f"https://www.smartprix.com/products/?q={query}"

    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    response = requests.get(url, headers=headers, timeout=15)

    print("URL:", url)
    print("Status:", response.status_code)
    print("Final URL:", response.url)

    soup = BeautifulSoup(response.text, "lxml")

    links = []

    for a in soup.find_all("a"):
        href = a.get("href", "")

        if "/mobiles/" in href:
            if href.startswith("/"):
                href = "https://www.smartprix.com" + href

            links.append(href)

    links = list(dict.fromkeys(links))

    return links[:10]


def main():
    print("=" * 50)
    print("Smartprix Direct Fetcher Test")
    print("=" * 50)

    links = search_smartprix_direct(PHONE_NAME)

    print(f"\nResults for: {PHONE_NAME}\n")

    if not links:
        print("No Smartprix mobile links found.")
        return

    for link in links:
        print(link)


if __name__ == "__main__":
    main()