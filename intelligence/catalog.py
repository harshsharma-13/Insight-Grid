"""Verified catalog boundary. Legacy CSVs are evidence to review, never trusted fallback."""
from __future__ import annotations

import json
import math
import re
from datetime import date, datetime, timedelta
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
VERIFIED_FILE = ROOT / "data/catalog/verified-specs.json"
SPEC_FIELDS = (
    "processor", "ram", "storage", "display", "display_type", "resolution", "refresh_rate",
    "touch_sampling_hz", "pwm_hz", "battery", "charging", "charging_w", "reverse_charging_w",
    "rear_camera", "front_camera", "android_version", "supports_5g", "nfc", "wifi", "bluetooth",
    "weight", "dimensions", "launch_date", "model_code", "ip_rating", "os_updates", "security_updates",
)
CORE_FIELDS = ("processor", "ram", "storage", "display", "refresh_rate", "battery", "charging", "rear_camera", "front_camera")
COMMERCE_FIELDS = ("launch_price", "amazon_price", "flipkart_price", "amazon_rating", "flipkart_rating")
ALLOWED_SOURCE_HOSTS = {
    "www.smartprix.com",
    "www.hmd.com",
    "www.oppo.com",
    "www.realme.com",
    "www.mi.com",
    "www.samsung.com",
    "infinixmobiles.in",
    "www.oneplus.in",
    "www.vivo.com",
    "www.iqoo.com",
}


def normalize_date(value):
    """Preserve source observation dates; never replace them with an import date."""
    if value is None or str(value).strip().lower() in {"", "nan", "none"}:
        return None
    if isinstance(value, (date, datetime)):
        return value.date().isoformat() if isinstance(value, datetime) else value.isoformat()
    text = str(value).strip()
    if re.fullmatch(r"\d{5}(?:\.0)?", text):
        return (date(1899, 12, 30) + timedelta(days=int(float(text)))).isoformat()
    for fmt in ("%Y-%m-%d", "%d-%m-%Y", "%d-%b-%Y", "%d-%b-%y", "%B %d, %Y", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(text, fmt).date().isoformat()
        except ValueError:
            pass
    raise ValueError(f"Unrecognised source date: {text}")


def validate_catalog(payload):
    if payload.get("schema_version") != 1 or not isinstance(payload.get("phones"), dict):
        raise ValueError("Expected catalog schema_version 1 and a phones object")
    seen_urls = {}
    for phone_id, entry in payload["phones"].items():
        if not re.fullmatch(r"PH\d{3,}|PHONE-[a-f0-9]{16}", phone_id):
            raise ValueError(f"Invalid persistent phone ID: {phone_id}")
        if not entry.get("phone_name") or not entry.get("accepted_names") or not entry.get("market"):
            raise ValueError(f"Missing identity or market for {phone_id}")
        if phone_id.startswith("PHONE-") and (not isinstance(entry.get("brand"), str) or not entry["brand"].strip()):
            raise ValueError(f"New catalog phone requires a brand: {phone_id}")
        if not isinstance(entry["accepted_names"], list) or not all(isinstance(name, str) and name.strip() for name in entry["accepted_names"]):
            raise ValueError(f"Invalid aliases for {phone_id}")
        if not isinstance(entry.get("variants", []), list) or any(not isinstance(v, dict) or not all(isinstance(v.get(k), str) and v[k].strip() for k in ("ram", "storage")) for v in entry.get("variants", [])):
            raise ValueError(f"Invalid RAM/storage variants for {phone_id}")
        parsed = urlparse(entry.get("source_url", ""))
        if (parsed.scheme != "https" or parsed.hostname not in ALLOWED_SOURCE_HOSTS
                or parsed.path in {"", "/"} or parsed.query or parsed.fragment):
            raise ValueError(f"Expected an exact HTTPS approved product page for {phone_id}")
        if parsed.hostname == "www.smartprix.com" and not parsed.path.startswith("/mobiles/"):
            raise ValueError(f"Expected a Smartprix mobile product page for {phone_id}")
        if entry["source_url"] in seen_urls:
            raise ValueError(f"A source page maps to two phones: {phone_id}, {seen_urls[entry['source_url']]}")
        seen_urls[entry["source_url"]] = phone_id
        if phone_id.startswith("PHONE-"):
            launch_source = urlparse(entry.get("launch_source_url", ""))
            if launch_source.scheme != "https" or not launch_source.hostname or launch_source.path in {"", "/"}:
                raise ValueError(f"Expected an exact HTTPS launch source for {phone_id}")
            launch_price = entry.get("launch_price")
            if isinstance(launch_price, bool) or not isinstance(launch_price, (int, float)) or launch_price <= 0:
                raise ValueError(f"Expected a positive launch price for {phone_id}")
            for price_field in ("amazon_price", "flipkart_price"):
                price = entry.get(price_field)
                if price is not None and (isinstance(price, bool) or not isinstance(price, (int, float)) or price <= 0):
                    raise ValueError(f"Expected a positive {price_field} for {phone_id}")
            if (entry.get("amazon_price") is not None or entry.get("flipkart_price") is not None) and not normalize_date(entry.get("price_observed_at")):
                raise ValueError(f"Marketplace prices require an observation date for {phone_id}")
            if entry.get("image_source_url"):
                image_source = urlparse(entry["image_source_url"])
                if image_source.scheme != "https" or image_source.hostname not in {"cdn1.smartprix.com", "cdn2.smartprix.com"}:
                    raise ValueError(f"New phone images must come from Smartprix CDN: {phone_id}")
                if not re.fullmatch(r"[a-z0-9-]+\.webp", entry.get("image_filename", "")):
                    raise ValueError(f"Invalid Smartprix image filename for {phone_id}")
        checked = normalize_date(entry.get("checked_at"))
        if not checked or checked > date.today().isoformat():
            raise ValueError(f"Invalid verification date for {phone_id}")
        fields = entry.get("fields", {})
        if not fields or set(fields) - set(SPEC_FIELDS):
            raise ValueError(f"Missing or unsupported specification fields for {phone_id}")
        for key, value in fields.items():
            if key in {"supports_5g", "nfc", "wifi"}:
                if value not in ("Yes", "No"):
                    raise ValueError(f"Unknown booleans must be omitted: {phone_id}.{key}")
            elif key in {"refresh_rate", "touch_sampling_hz", "pwm_hz", "charging_w", "reverse_charging_w"}:
                if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value <= 0:
                    raise ValueError(f"Expected positive numeric units: {phone_id}.{key}")
                if key == "refresh_rate" and value > 300:
                    raise ValueError(f"Refresh-rate anomaly requires schema review: {phone_id}")
            elif not isinstance(value, str) or not value.strip():
                raise ValueError(f"Expected nonempty source-backed text: {phone_id}.{key}")
            if key == "launch_date":
                normalize_date(value)
        if not isinstance(entry.get("evidence_note"), str) or not entry["evidence_note"].strip():
            raise ValueError(f"Missing source-check notes for {phone_id}")
    return payload


def load_verified_catalog(path=VERIFIED_FILE):
    # Absence is safe (all specs withheld); corruption is a hard error, not silent fallback.
    if not path.exists():
        return {"schema_version": 1, "phones": {}}
    return validate_catalog(json.loads(path.read_text(encoding="utf-8")))


def apply_verified_specs(row, catalog):
    entry = catalog["phones"].get(row["phone_id"])
    legacy_name = row["phone_name"]
    if entry and legacy_name not in entry["accepted_names"]:
        raise ValueError(f"Catalog identity changed for {row['phone_id']}; refusing to attach specs")
    # Preserve the original research prices separately from specification verification.
    row["legacy_commerce"] = {key: row.get(key) for key in COMMERCE_FIELDS}
    row["price_status"] = "Recorded research price, not a live offer"
    row["price_last_updated"] = "2026-06-23"
    row["legacy_price_observed_at"] = "2026-06-23"
    if entry and row["phone_id"].startswith("PHONE-"):
        for key in COMMERCE_FIELDS:
            if key in entry:
                row[key] = entry[key]
        row["price_status"] = "Recorded marketplace price, not a live offer"
        row["price_last_updated"] = entry.get("price_observed_at")
    for key in SPEC_FIELDS:
        row[key] = entry.get("fields", {}).get(key) if entry else None
    row["phone_name"] = entry["phone_name"] if entry else legacy_name
    row["spec_status"] = "Source checked · partial" if entry else "Awaiting source verification"
    row["spec_source_url"] = entry["source_url"] if entry else None
    row["spec_checked_at"] = entry["checked_at"] if entry else None
    row["spec_market"] = entry["market"] if entry else None
    row["spec_notes"] = entry["evidence_note"] if entry else "Legacy specifications are preserved locally but withheld until checked against the correct product page."
    row["verified_spec_fields"] = sorted(entry["fields"]) if entry else []
    row["spec_core_coverage"] = sum(row[key] is not None for key in CORE_FIELDS)
    row["spec_core_total"] = len(CORE_FIELDS)
    row["spec_variants"] = entry.get("variants", []) if entry else []
    row["spec_field_sources"] = {key: {"url": entry["source_url"], "checked_at": entry["checked_at"]} for key in entry["fields"]} if entry else {}
    row["has_review_evidence"] = bool(row.get("review_count"))
    row["catalog_note"] = "Price segments reflect the historical research sample, not current offers."
    if row["phone_id"] in {"PH010", "PH048", "PH056"}:
        row["image_url"] = None
        row["image_filename"] = None
        row["image_local_path"] = None
    return row
