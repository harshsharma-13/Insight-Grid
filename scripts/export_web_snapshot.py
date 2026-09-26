from __future__ import annotations

import json
import argparse
import os
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from intelligence import IntelligenceEngine
from intelligence.taxonomy import USE_CASE_ASPECTS


OUTPUT = ROOT / "web" / "app" / "data" / "platform-data.json"
REVIEW_OUTPUT = ROOT / "web" / "public" / "data" / "reviews.json"


def build_snapshot(all_reviews: list[dict] | None = None) -> dict:
    phones = IntelligenceEngine.phones()
    all_reviews = all_reviews if all_reviews is not None else IntelligenceEngine.reviews(limit=None)
    phone_details = {}
    for phone in phones:
        detail = IntelligenceEngine.phone(phone["phone_id"]) or {}
        phone_details[phone["phone_id"]] = {
            "platforms": detail.get("platforms", []),
            "aspects": detail.get("aspects", []),
        }
    overall_results = IntelligenceEngine.finder("overall", limit=len(phones))
    phone_reviews: dict[str, list[dict]] = {}
    for review in all_reviews:
        bucket = phone_reviews.setdefault(review["phone_id"], [])
        if len(bucket) < 2:
            bucket.append({
                "review_id": review["review_id"],
                "phone_id": review["phone_id"],
                "phone_name": review["phone_name"],
                "brand": review["brand"],
                "platform": review["platform"],
                "review_text": str(review["review_text"])[:700],
                "word_count": review["word_count"],
                "signal": review["signal"],
                "aspects": review["aspects"],
            })
    return {
        "generated_at": datetime.now(UTC).isoformat(),
        "overview": IntelligenceEngine.overview(),
        "phones": phones,
        "phone_details": phone_details,
        "phone_reviews": phone_reviews,
        "overall_scores": {
            item["phone_id"]: {
                "score": item["score"],
                "reason": item["reason"],
                "evidence_label": item["evidence_label"],
            }
            for item in overall_results
        },
        # Keep the shared application bundle light. The complete searchable
        # corpus is emitted as a route-loaded public asset below.
        "reviews": all_reviews[:60],
        "finder": {
            use_case: IntelligenceEngine.finder(use_case, limit=len(phones))
            for use_case in USE_CASE_ASPECTS
        },
        "competitive": IntelligenceEngine.competitive(),
        "deep_intelligence": IntelligenceEngine.deep_intelligence(),
        "actions": IntelligenceEngine.actions(),
    }


def catalog_quality(phones):
    return {"source_checked_phones": sum(bool(p["verified_spec_fields"]) for p in phones), "awaiting_verification": sum(not p["verified_spec_fields"] for p in phones), "source_policy": "Exact manufacturer or Smartprix India product pages", "prices": "Dated research price observations; not live offers."}


def catalog_only_snapshot(snapshot):
    phones = IntelligenceEngine.phones()
    snapshot["phones"] = phones
    snapshot["catalog_updated_at"] = datetime.now(UTC).isoformat()
    snapshot["catalog_quality"] = catalog_quality(phones)
    snapshot["overview"]["metrics"]["phones"] = len(phones)
    snapshot["overview"]["metrics"]["catalog_brands"] = len({p["brand"] for p in phones})
    snapshot["finder"] = {use_case: IntelligenceEngine.finder(use_case, limit=len(phones)) for use_case in USE_CASE_ASPECTS}
    snapshot["overall_scores"] = {p["phone_id"]: {k: p[k] for k in ["score", "reason", "evidence_label"]} for p in snapshot["finder"]["overall"]}
    phone_map = {p["phone_id"]: p for p in phones}
    def scrub_catalog_fields(value):
        if isinstance(value, list):
            for child in value:
                scrub_catalog_fields(child)
        elif isinstance(value, dict):
            phone = phone_map.get(value.get("phone_id"))
            if phone:
                for key in ["phone_name", "brand", "best_price", "launch_price", "amazon_price", "flipkart_price", "amazon_rating", "flipkart_rating", "image_url"]:
                    if key in value:
                        value[key] = phone[key]
            for child in value.values():
                scrub_catalog_fields(child)
    scrub_catalog_fields(snapshot["deep_intelligence"])
    scrub_catalog_fields(snapshot["actions"])
    return snapshot


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--catalog-only", action="store_true", help="Preserve review data and existing analytical conclusions")
    args = parser.parse_args()
    if args.catalog_only:
        snapshot = catalog_only_snapshot(json.loads(OUTPUT.read_text(encoding="utf-8")))
    else:
        all_reviews = IntelligenceEngine.reviews(limit=None)
        snapshot = build_snapshot(all_reviews)
        snapshot["catalog_quality"] = catalog_quality(snapshot["phones"])
        REVIEW_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
        REVIEW_OUTPUT.write_text(json.dumps(all_reviews, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    temporary = OUTPUT.with_suffix(".json.tmp")
    temporary.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(temporary, OUTPUT)
    print(f"Wrote {OUTPUT}")
    print("Review asset unchanged" if args.catalog_only else f"Wrote {REVIEW_OUTPUT}")
