"""Stage and approve new phone profiles without touching reviews or existing IDs.

Staging is read-only with respect to the active catalog. Approval requires an exact
name confirmation and promotes only a validated candidate into verified-specs.json.
"""
from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
import sys
from datetime import UTC, date, datetime
from pathlib import Path
from urllib.parse import urlparse
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from intelligence.catalog import SPEC_FIELDS, load_verified_catalog, validate_catalog  # noqa: E402
from preprocessing.smartprix_spec_extractor import clean, parse_specs  # noqa: E402
from scripts.catalog_verification_queue import (  # noqa: E402
    _product_payload,
    fetch_details,
    local_api_key,
    normalized_name,
    smartprix_path,
)

CATALOG_PATH = ROOT / "data/catalog/verified-specs.json"
STAGING_DIR = ROOT / "data/catalog/staging"
AUDIT_DIR = ROOT / "reports/catalog-imports"
NUMERIC_FIELDS = {"refresh_rate", "touch_sampling_hz", "pwm_hz", "charging_w", "reverse_charging_w"}
BOOLEAN_FIELDS = {"supports_5g", "nfc", "wifi"}
PRICE_FIELDS = ("launch_price", "amazon_price", "flipkart_price")


def persistent_phone_id(phone_name: str, source_url: str) -> str:
    identity = f"{normalized_name(phone_name)}|{smartprix_path(source_url) or source_url}".encode()
    return "PHONE-" + hashlib.sha256(identity).hexdigest()[:16]


def _scalar(value):
    if isinstance(value, (str, int, float, bool)):
        return str(value).strip()
    if isinstance(value, list):
        return "; ".join(filter(None, (_scalar(item) for item in value)))
    return ""


def _flatten(value, prefix=""):
    result = {}
    if isinstance(value, dict):
        title = _scalar(value.get("title"))
        description = _scalar(value.get("description"))
        if title and description:
            result[f"{prefix} {title}".strip()] = description
        child_prefix = f"{prefix} {title}".strip() if title and isinstance(value.get("items"), list) else prefix
        for key, child in value.items():
            if key in {"title", "description"}:
                continue
            path = f"{prefix} {key}".strip()
            result.update(_flatten(child, child_prefix if key == "items" else path))
    elif isinstance(value, list):
        scalar = _scalar(value)
        if scalar:
            result[prefix] = scalar
        for index, child in enumerate(value):
            if isinstance(child, dict):
                result.update(_flatten(child, prefix if child.get("title") else f"{prefix} {index}"))
    else:
        scalar = _scalar(value)
        if scalar:
            result[prefix] = scalar
    return result


def _first(flat, *patterns):
    for pattern in patterns:
        for key, value in flat.items():
            if re.search(pattern, key, re.I) and value:
                return value
    return ""


def _value_first(flat, pattern):
    return next((value for value in flat.values() if re.search(pattern, value, re.I)), "")


def _api_text(value):
    text = html.unescape(re.sub(r"<[^>]+>", "; ", str(value or "")))
    text = re.sub(r"(?:\s*;\s*)+", "; ", text).strip(" ;")
    return clean(text)


def _number(value):
    match = re.search(r"(?<!\d)(\d+(?:\.\d+)?)", str(value or ""))
    if not match:
        return None
    number = float(match.group(1))
    return int(number) if number.is_integer() else number


def _hz_number(value):
    match = re.search(r"(?<![\d.])(\d+(?:\.\d+)?)\s*Hz\b", str(value or ""), re.I)
    if not match:
        return None
    number = float(match.group(1))
    return int(number) if number.is_integer() else number


def specs_from_api(product):
    """Map common Parse Bot/Smartprix labels; unknown fields stay staged, never guessed."""
    raw = product.get("fullSpecs") if isinstance(product.get("fullSpecs"), (dict, list)) else product
    flat = _flatten(raw)
    fields = {
        "processor": _first(flat, r"\bchipset\b", r"\bprocessor\b"),
        "ram": _first(flat, r"\bram\b"),
        "storage": _first(flat, r"\b(?:inbuilt memory|storage)\b"),
        "display": _first(flat, r"display.*size", r"screen.*size", r"display.*type", r"screen.*type"),
        "display_type": _first(flat, r"display.*type", r"screen.*type"),
        "resolution": _first(flat, r"\bresolution\b"),
        "rear_camera": _first(flat, r"rear.*camera", r"camera.*rear"),
        "front_camera": _first(flat, r"front.*camera", r"selfie.*camera"),
        "battery": _first(flat, r"battery.*(?:size|capacity)", r"\bbattery\b"),
        "charging": _first(flat, r"fast.*charging", r"wired.*charging", r"\bcharging\b"),
        "android_version": _first(flat, r"technical os$", r"general os$", r"operating system$", r"android.*version"),
        "os_updates": _first(flat, r"os updates$"),
        "security_updates": _first(flat, r"security updates$"),
        "bluetooth": _first(flat, r"\bbluetooth\b"),
        "weight": _first(flat, r"\bweight\b"),
        "dimensions": _first(flat, r"\bdimensions?\b"),
        "ip_rating": _first(flat, r"\bip rating\b", r"water.*resistan"),
        "launch_date": _first(flat, r"release date", r"launch date"),
    }
    numeric_sources = {
        "refresh_rate": _first(flat, r"refresh rate") or _first(flat, r"display size$") or _value_first(flat, r"\b\d+(?:\.\d+)?\s*Hz\s+Refresh Rate"),
        "touch_sampling_hz": _first(flat, r"touch sampling") or _value_first(flat, r"\b\d+(?:\.\d+)?\s*Hz\s+Touch Sampling"),
        "pwm_hz": _first(flat, r"pwm"),
        "charging_w": _first(flat, r"fast.*charging", r"wired.*charging"),
        "reverse_charging_w": _first(flat, r"reverse.*charging"),
    }
    display_text = fields.get("display", "")
    resolution = re.search(r"\b\d{3,4}\s*[x×]\s*\d{3,4}\s*(?:pixels|px)?\b", display_text, re.I)
    if resolution:
        fields["resolution"] = resolution.group(0)
    for key, value in numeric_sources.items():
        number = _hz_number(value) if key in {"refresh_rate", "touch_sampling_hz", "pwm_hz"} else _number(value)
        if number:
            fields[key] = number
    for key, pattern in [("supports_5g", r"(?:^|\s)5g(?:\s|$)"), ("nfc", r"\bnfc\b"), ("wifi", r"wi-?fi")]:
        value = _first(flat, pattern)
        if value:
            fields[key] = "No" if re.search(r"\b(?:no|not supported|false)\b", value, re.I) else "Yes"
    return {key: value for key, value in fields.items() if value not in (None, "") and key in SPEC_FIELDS}, flat


def variants_from_api(product):
    variants = []
    for item in product.get("variants", []) if isinstance(product.get("variants"), list) else []:
        if not isinstance(item, dict):
            continue
        ram = item.get("ram") or item.get("RAM")
        storage = item.get("storage") or item.get("Storage")
        if ram and storage:
            pair = {"ram": str(ram).strip(), "storage": str(storage).strip()}
            if pair not in variants:
                variants.append(pair)
    return variants


def smartprix_image(product, source_url):
    image_id = clean(product.get("imageId"))
    path = smartprix_path(source_url)
    if not image_id or not path:
        return None, None
    slug = path.rsplit("/", 1)[-1].rsplit("-ppd", 1)[0]
    filename = f"{slug}.webp"
    return f"https://cdn1.smartprix.com/rx-i{image_id}-w420-h420/{filename}", filename


def normalize_fields(fields):
    normalized = {}
    for key, value in fields.items():
        if key not in SPEC_FIELDS or value in (None, ""):
            continue
        if key in NUMERIC_FIELDS:
            value = _number(value)
            if value is None:
                continue
        elif key in BOOLEAN_FIELDS:
            text = str(value).strip().casefold()
            value = "Yes" if text in {"yes", "true", "1", "supported"} else "No" if text in {"no", "false", "0", "not supported"} else ""
            if not value:
                continue
        else:
            value = _api_text(value)
            if key == "processor":
                value = re.sub(r"^(\w+)\s+\1\b", r"\1", value, flags=re.I)
        normalized[key] = value
    return normalized


def candidate_checks(phone_name, source_url, fields, catalog, returned_name=None, returned_url=None):
    aliases = {normalized_name(phone_name)}
    existing_aliases = {normalized_name(alias) for item in catalog["phones"].values() for alias in item["accepted_names"]}
    existing_urls = {item["source_url"].rstrip("/") for item in catalog["phones"].values()}
    return {
        "exact_smartprix_url": bool(smartprix_path(source_url)),
        "source_url_is_new": source_url.rstrip("/") not in existing_urls,
        "name_is_new": aliases.isdisjoint(existing_aliases),
        "identity_match": returned_name is None or normalized_name(returned_name) == normalized_name(phone_name),
        "returned_url_match": returned_url is None or smartprix_path(returned_url) == smartprix_path(source_url),
        "required_specs_present": all(fields.get(key) for key in ("processor", "display", "battery")),
    }


def stage(args):
    catalog = load_verified_catalog()
    source_url = args.source_url.rstrip("/")
    if not smartprix_path(source_url):
        raise ValueError("An exact HTTPS Smartprix /mobiles/ product URL is required; no API call was made")
    returned_name = returned_url = None
    image_source_url = args.image_url
    image_filename = None
    variants = []
    raw_keys = []
    if args.fetch:
        key = local_api_key()
        if not key:
            raise ValueError("PARSE_API_KEY is not configured; no API call was made")
        product = _product_payload(fetch_details(smartprix_path(source_url), key))
        returned_name = next((product.get(k) for k in ("name", "title", "productName", "phoneName", "model") if isinstance(product.get(k), str) and product[k].strip()), None)
        returned_url = next((product.get(k) for k in ("url", "productUrl", "smartprixUrl") if isinstance(product.get(k), str)), None)
        fields, flat = specs_from_api(product)
        api_image_url, api_image_filename = smartprix_image(product, source_url)
        image_source_url = image_source_url or api_image_url
        image_filename = api_image_filename
        variants = variants_from_api(product)
        if args.variant:
            variants = []
            for value in args.variant:
                ram, separator, storage = value.partition("|")
                if not separator or not ram.strip() or not storage.strip():
                    raise ValueError("Each --variant must use the format 'RAM|storage'")
                pair = {"ram": clean(ram), "storage": clean(storage)}
                if pair not in variants:
                    variants.append(pair)
        if not variants and fields.get("ram") and fields.get("storage"):
            variants = [{"ram": fields["ram"], "storage": fields["storage"]}]
        raw_keys = sorted(flat)
        evidence_mode = "parse_bot_smartprix_api"
    else:
        if not args.input_text:
            raise ValueError("Use --fetch or provide --input-text; active data was not changed")
        fields = normalize_fields(parse_specs(args.input_text.read_text(encoding="utf-8")))
        evidence_mode = "reviewed_smartprix_page_text"
    if image_source_url:
        image_source_url = image_source_url.rstrip("/")
        image_filename = image_filename or image_source_url.rsplit("/", 1)[-1]
    fields["launch_date"] = args.launch_date
    checks = candidate_checks(args.phone_name, source_url, fields, catalog, returned_name, returned_url)
    checks["launch_is_in_2026"] = args.launch_date.startswith("2026-")
    checks["launch_price_at_or_below_30000"] = 0 < args.launch_price <= 30000
    checks["smartprix_image_source"] = bool(
        image_source_url and urlparse(image_source_url).scheme == "https"
        and urlparse(image_source_url).hostname in {"cdn1.smartprix.com", "cdn2.smartprix.com"}
    )
    phone_id = persistent_phone_id(args.phone_name, source_url)
    candidate = {
        "schema_version": 1,
        "candidate_id": uuid4().hex,
        "phone_id": phone_id,
        "phone_name": clean(args.phone_name),
        "brand": clean(args.brand),
        "accepted_names": list(dict.fromkeys([clean(args.phone_name), *[clean(x) for x in args.alias]])),
        "market": "India Smartprix source check",
        "source_url": source_url,
        "launch_source_url": args.launch_source_url.rstrip("/"),
        "launch_price": args.launch_price,
        "amazon_price": args.amazon_price,
        "flipkart_price": args.flipkart_price,
        "price_observed_at": args.price_observed_at,
        "image_source_url": image_source_url,
        "image_filename": image_filename,
        "image_local_path": f"assets/phone_images/{image_filename}" if image_filename else None,
        "checked_at": date.today().isoformat(),
        "retrieved_at": datetime.now(UTC).isoformat(),
        "evidence_mode": evidence_mode,
        "evidence_note": clean(args.note) or f"Exact Smartprix India product page reviewed for {clean(args.phone_name)}. Only populated fields are proposed.",
        "variants": variants,
        "fields": normalize_fields(fields),
        "checks": checks,
        "api_summary": {"returned_name": returned_name, "returned_url": returned_url, "reported_keys": raw_keys} if args.fetch else None,
        "status": "ready_for_review" if all(checks.values()) else "blocked",
    }
    STAGING_DIR.mkdir(parents=True, exist_ok=True)
    output = STAGING_DIR / f"{phone_id.lower()}-{candidate['candidate_id'][:8]}.json"
    output.write_text(json.dumps(candidate, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"status": candidate["status"], "phone_id": phone_id, "fields": len(candidate["fields"]), "variants": len(variants), "checks": checks, "candidate": str(output)}, indent=2))
    return 0 if candidate["status"] == "ready_for_review" else 2


def approve(args):
    candidate = json.loads(args.candidate.read_text(encoding="utf-8"))
    if candidate.get("status") != "ready_for_review" or not all(candidate.get("checks", {}).values()):
        raise ValueError("Candidate is blocked or incomplete; active data was not changed")
    if args.confirm_name != candidate["phone_name"]:
        raise ValueError("--confirm-name must exactly match the staged phone name")
    catalog = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
    if candidate["phone_id"] in catalog["phones"]:
        raise ValueError("Phone ID already exists; active data was not changed")
    if any(item["source_url"].rstrip("/") == candidate["source_url"].rstrip("/") for item in catalog["phones"].values()):
        raise ValueError("Source URL already belongs to another phone; active data was not changed")
    required_record_keys = (
        "phone_name", "brand", "accepted_names", "market", "source_url", "launch_source_url",
        "checked_at", "evidence_note", "variants", "fields", "launch_price", "amazon_price",
        "flipkart_price", "price_observed_at",
    )
    record = {key: candidate[key] for key in required_record_keys}
    record.update({key: candidate.get(key) for key in ("image_source_url", "image_filename", "image_local_path") if candidate.get(key)})
    catalog["phones"][candidate["phone_id"]] = record
    validate_catalog(catalog)
    temp = CATALOG_PATH.with_suffix(".json.tmp")
    temp.write_text(json.dumps(catalog, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    temp.replace(CATALOG_PATH)
    AUDIT_DIR.mkdir(parents=True, exist_ok=True)
    audit = {**candidate, "status": "approved", "approved_at": datetime.now(UTC).isoformat(), "reviewed_by": clean(args.reviewed_by)}
    audit_path = AUDIT_DIR / f"approved-{candidate['phone_id'].lower()}-{date.today().isoformat()}.json"
    audit_path.write_text(json.dumps(audit, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"status": "approved", "phone_id": candidate["phone_id"], "catalog_total": len(catalog["phones"]), "audit": str(audit_path), "next": "python scripts/export_web_snapshot.py --catalog-only"}, indent=2))
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    stage_parser = commands.add_parser("stage", help="Create a review candidate; never changes active data")
    stage_parser.add_argument("--phone-name", required=True)
    stage_parser.add_argument("--brand", required=True)
    stage_parser.add_argument("--source-url", required=True)
    stage_parser.add_argument("--launch-source-url", required=True)
    stage_parser.add_argument("--launch-date", required=True, type=date.fromisoformat)
    stage_parser.add_argument("--launch-price", required=True, type=int)
    stage_parser.add_argument("--amazon-price", type=int)
    stage_parser.add_argument("--flipkart-price", type=int)
    stage_parser.add_argument("--price-observed-at", type=date.fromisoformat)
    stage_parser.add_argument("--alias", action="append", default=[])
    stage_parser.add_argument("--variant", action="append", default=[], help="Reviewed RAM|storage pair; repeat for each variant")
    stage_parser.add_argument("--image-url", help="Exact Smartprix CDN image URL; normally discovered from Parse Bot")
    stage_parser.add_argument("--note", default="")
    evidence = stage_parser.add_mutually_exclusive_group(required=True)
    evidence.add_argument("--fetch", action="store_true", help="Use one Parse Bot API call")
    evidence.add_argument("--input-text", type=Path, help="Saved text from the exact Smartprix product page")
    approve_parser = commands.add_parser("approve", help="Promote a reviewed candidate into the active catalog")
    approve_parser.add_argument("--candidate", required=True, type=Path)
    approve_parser.add_argument("--confirm-name", required=True)
    approve_parser.add_argument("--reviewed-by", required=True)
    args = parser.parse_args(argv)
    if args.command == "stage":
        args.launch_date = args.launch_date.isoformat()
        args.price_observed_at = args.price_observed_at.isoformat() if args.price_observed_at else None
    try:
        return stage(args) if args.command == "stage" else approve(args)
    except (ValueError, OSError, json.JSONDecodeError) as exc:
        parser.error(str(exc))


if __name__ == "__main__":
    raise SystemExit(main())
