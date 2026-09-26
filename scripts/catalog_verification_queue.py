"""Build a conservative, private verification queue for the existing phone IDs.

The historical CSV remains immutable. API responses are evidence for review, never
written into the active verified catalog or the hosted application.
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import re
import sys
import time
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlparse
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from intelligence.catalog import load_verified_catalog  # noqa: E402

LEGACY_CSV = ROOT / "data/processed/phones_specifications.csv"
DEFAULT_OUTPUT = ROOT / "reports/catalog-verification/queue.json"
API_URL = "https://api.parse.bot/scraper/37d36dc7-0edf-44d4-8099-976c2da8a33e/get_smartphone_details"
SMARTPRIX_HOST = "www.smartprix.com"


def local_api_key():
    """Read only this credential from an ignored local .env; never display it."""
    if os.environ.get("PARSE_API_KEY"):
        return os.environ["PARSE_API_KEY"]
    env_file = ROOT / ".env"
    if not env_file.is_file():
        return None
    for line in env_file.read_text(encoding="utf-8-sig").splitlines():
        if "=" not in line or line.lstrip().startswith("#"):
            continue
        name, value = line.split("=", 1)
        if name.strip() == "PARSE_API_KEY":
            return value.strip().strip('"\'') or None
    return None


def normalized_name(value):
    name = re.sub(r"[^a-z0-9]", "", str(value).casefold())
    # Motorola commonly lists "Motorola Moto ..." where the catalog says
    # "Moto ...". Do not discard 4G/5G suffixes or other model tokens.
    return name.removeprefix("motorola") if name.startswith("motorolamoto") else name


def smartprix_path(url):
    parsed = urlparse(url or "")
    if parsed.scheme == "" and parsed.netloc == "" and parsed.path.startswith("/mobiles/"):
        return parsed.path.rstrip("/")
    if parsed.scheme != "https" or parsed.hostname != SMARTPRIX_HOST or not parsed.path.startswith("/mobiles/"):
        return None
    return parsed.path.rstrip("/")


def load_legacy(path=LEGACY_CSV):
    with path.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    ids = [row["phone_id"] for row in rows]
    if len(ids) != len(set(ids)):
        raise ValueError("Historical specifications contain duplicate phone IDs")
    return rows


def build_queue(rows, catalog):
    """Keep all IDs and report conflicts; do not infer specifications from CSV."""
    by_url = defaultdict(list)
    for row in rows:
        by_url[row.get("smartprix_link", "").rstrip("/")].append(row["phone_id"])
    queue = []
    for row in rows:
        phone_id = row["phone_id"]
        checked = catalog["phones"].get(phone_id)
        historical_url = row.get("smartprix_link", "").rstrip("/")
        checked_url = checked["source_url"] if checked else None
        flags = []
        if not smartprix_path(historical_url):
            flags.append("invalid_historical_smartprix_url")
        if historical_url and len(by_url[historical_url]) > 1:
            flags.append("shared_historical_source_url")
        if checked_url and smartprix_path(checked_url) and checked_url.rstrip("/") != historical_url:
            flags.append("historical_source_conflicts_with_checked_source")
        if checked and normalized_name(row["phone_name"]) not in {normalized_name(x) for x in checked["accepted_names"]}:
            flags.append("historical_name_not_in_checked_aliases")
        # A checked manufacturer source is better evidence than the historical
        # Smartprix URL, but only a Smartprix path can be sent to Parse Bot.
        api_url = checked_url if smartprix_path(checked_url) else historical_url
        if "shared_historical_source_url" in flags and not smartprix_path(checked_url or ""):
            api_url = None
        queue.append({
            "phone_id": phone_id,
            "historical_name": row["phone_name"],
            "accepted_names": checked["accepted_names"] if checked else [row["phone_name"]],
            "brand": row["brand"],
            "status": "source_checked_partial" if checked else "awaiting_source_verification",
            "historical_smartprix_url": historical_url or None,
            "checked_source_url": checked_url,
            "checked_at": checked.get("checked_at") if checked else None,
            "api_candidate_url": api_url if smartprix_path(api_url or "") else None,
            "historical_variant_hint": {"ram": row.get("ram") or None, "storage": row.get("storage") or None},
            "flags": flags,
            "review_required": True,
            "api_evidence": None,
        })
    return queue


def _product_payload(body):
    if not isinstance(body, dict) or body.get("status") == "error":
        raise ValueError("API returned an error or an unexpected body")
    data = body.get("data", body)
    for key in ("product", "smartphone", "phone", "details"):
        if isinstance(data, dict) and isinstance(data.get(key), dict):
            data = data[key]
    if not isinstance(data, dict):
        raise ValueError("API product data is not an object")
    return data


def review_api_response(item, body):
    """Summarize identity/variant evidence without accepting any spec field."""
    product = _product_payload(body)
    name = next((product[key] for key in ("name", "title", "productName", "phoneName", "model")
                 if isinstance(product.get(key), str) and product[key].strip()), None)
    expected = {normalized_name(x) for x in item["accepted_names"]}
    identity = "match" if name and normalized_name(name) in expected else "mismatch" if name else "unknown"
    url = next((product[key] for key in ("url", "productUrl", "smartprixUrl")
                if isinstance(product.get(key), str)), None)
    expected_path = smartprix_path(item["api_candidate_url"] or "")
    returned_path = smartprix_path(url) if url else None
    url_status = "match" if returned_path == expected_path else "mismatch" if returned_path else "not_returned"
    raw_variants = product.get("variants")
    variants = []
    if isinstance(raw_variants, list):
        for variant in raw_variants:
            if isinstance(variant, dict):
                ram = variant.get("ram") or variant.get("RAM")
                storage = variant.get("storage") or variant.get("Storage")
                variant_text = variant.get("variant_text") or variant.get("variantText")
                if ram or storage:
                    variants.append({"ram": str(ram) if ram else None, "storage": str(storage) if storage else None})
                elif variant_text:
                    variants.append({"variant_text": str(variant_text)})
    return {
        "returned_name": name,
        "identity": identity,
        "returned_url": url,
        "url_status": url_status,
        "reported_variants": variants,
        "reported_spec_keys": sorted(product.get("fullSpecs", {})) if isinstance(product.get("fullSpecs"), dict) else [],
        "needs_manual_review": True,
    }


def fetch_details(path, api_key, timeout=20):
    url = API_URL + "?" + urlencode({"slug": path})
    request = Request(url, headers={"X-API-Key": api_key, "Accept": "application/json"}, method="GET")
    # Parse Bot's detail endpoint accepts the exact Smartprix product path.
    with urlopen(request, timeout=timeout) as response:
        return json.load(response)


def enrich_with_api(queue, api_key, max_requests, delay, selected_ids=None, awaiting_only=False):
    if not api_key:
        raise ValueError("PARSE_API_KEY is not set; no API calls were made")
    calls = 0
    for item in queue:
        if awaiting_only and item["status"] != "awaiting_source_verification":
            continue
        if selected_ids is not None and item["phone_id"] not in selected_ids:
            continue
        if calls >= max_requests:
            break
        path = smartprix_path(item["api_candidate_url"] or "")
        if not path:
            continue
        if calls and delay:
            time.sleep(delay)
        calls += 1
        try:
            item["api_evidence"] = review_api_response(item, fetch_details(path, api_key))
            if item["api_evidence"]["identity"] != "match":
                item["flags"].append("api_identity_not_confirmed")
            if item["api_evidence"]["url_status"] == "mismatch":
                item["flags"].append("api_url_mismatch")
        except (HTTPError, URLError, TimeoutError, ValueError, json.JSONDecodeError) as exc:
            # Never persist the API key, headers, or raw body/error response.
            item["flags"].append("api_request_failed")
            item["api_evidence"] = {"error_type": type(exc).__name__, "needs_manual_review": True}
    return calls


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--fetch", action="store_true", help="Spend Parse Bot credits to cross-check candidate pages")
    parser.add_argument("--max-requests", type=int, default=10)
    parser.add_argument("--delay", type=float, default=0.5)
    parser.add_argument("--phone-id", action="append", dest="phone_ids", help="Limit API lookups to these existing IDs; repeat for a batch")
    parser.add_argument("--awaiting-only", action="store_true", help="Spend calls only on records still awaiting source verification")
    args = parser.parse_args(argv)
    if args.max_requests < 1 or args.delay < 0:
        parser.error("--max-requests must be positive and --delay nonnegative")
    api_key = local_api_key() if args.fetch else None
    if args.fetch and not api_key:
        parser.error("PARSE_API_KEY is not set in the environment or local .env; no API calls were made")
    rows = load_legacy()
    selected_ids = set(args.phone_ids) if args.phone_ids else None
    if selected_ids is not None:
        unknown = selected_ids - {row["phone_id"] for row in rows}
        if unknown:
            parser.error("Unknown phone IDs: " + ", ".join(sorted(unknown)))
    catalog = load_verified_catalog()
    queue = build_queue(rows, catalog)
    calls = enrich_with_api(queue, api_key, args.max_requests, args.delay, selected_ids, args.awaiting_only) if args.fetch else 0
    summary = Counter(item["status"] for item in queue)
    result = {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "mode": "api_cross_check" if args.fetch else "offline_audit",
        "summary": {"total": len(queue), "source_checked_partial": summary["source_checked_partial"],
                    "awaiting_source_verification": summary["awaiting_source_verification"],
                    "flagged": sum(bool(item["flags"]) for item in queue), "api_calls": calls},
        "phones": queue,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Queue: {len(queue)} phones, {summary['source_checked_partial']} partially checked, "
          f"{summary['awaiting_source_verification']} awaiting, {result['summary']['flagged']} flagged, {calls} API calls")
    print(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
