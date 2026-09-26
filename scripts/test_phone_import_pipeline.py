import argparse
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from intelligence.engine import IntelligenceEngine
from scripts.phone_import_pipeline import approve, candidate_checks, normalize_fields, persistent_phone_id, smartprix_image, specs_from_api


class PhoneImportPipelineTests(unittest.TestCase):
    def setUp(self):
        IntelligenceEngine.phones.cache_clear()

    def tearDown(self):
        IntelligenceEngine.phones.cache_clear()

    def test_phone_id_is_stable_and_source_specific(self):
        url = "https://www.smartprix.com/mobiles/example-phone-5g-ppd123456789"
        self.assertEqual(persistent_phone_id("Example Phone 5G", url), persistent_phone_id("Example Phone 5G", url))
        self.assertRegex(persistent_phone_id("Example Phone 5G", url), r"^PHONE-[a-f0-9]{16}$")

    def test_smartprix_image_is_derived_from_the_exact_product(self):
        url, filename = smartprix_image(
            {"imageId": "abc123"},
            "https://www.smartprix.com/mobiles/example-phone-5g-ppd123456789",
        )
        self.assertEqual(url, "https://cdn1.smartprix.com/rx-iabc123-w420-h420/example-phone-5g.webp")
        self.assertEqual(filename, "example-phone-5g.webp")

    def test_api_mapping_keeps_only_supported_populated_fields(self):
        product = {"fullSpecs": {"Technical": {"Chipset": "Example 9000", "OS": "Android 16"}, "Display": {"Size": "6.7 inch AMOLED", "Refresh Rate": "120 Hz"}, "Battery": {"Capacity": "6000 mAh", "Fast Charging": "45 W"}}}
        fields, keys = specs_from_api(product)
        self.assertEqual(fields["processor"], "Example 9000")
        self.assertEqual(fields["refresh_rate"], 120)
        self.assertEqual(fields["charging_w"], 45)
        self.assertIn("Technical Chipset", keys)

    def test_api_mapping_understands_parse_bot_title_description_groups(self):
        product = {"fullSpecs": [
            {"title": "Display", "items": [{"title": "Size", "description": "6.83 inches, 1280 x 2772 pixels, 120 Hz"}]},
            {"title": "Technical", "items": [{"title": "Chipset", "description": "Example 9000"}]},
            {"title": "Battery", "items": [{"title": "Size", "description": "7000 mAh"}]},
        ]}
        fields, keys = specs_from_api(product)
        self.assertEqual(fields["display"], "6.83 inches, 1280 x 2772 pixels, 120 Hz")
        self.assertEqual(fields["resolution"], "1280 x 2772 pixels")
        self.assertEqual(fields["refresh_rate"], 120)
        self.assertEqual(fields["processor"], "Example 9000")
        self.assertEqual(fields["battery"], "7000 mAh")
        self.assertIn("Technical Chipset", keys)

    def test_duplicate_identity_and_url_are_blocked(self):
        url = "https://www.smartprix.com/mobiles/example-phone-5g-ppd123456789"
        catalog = {"phones": {"PH999": {"phone_name": "Example Phone 5G", "accepted_names": ["Example Phone 5G"], "source_url": url}}}
        checks = candidate_checks("Example Phone 5G", url, {"processor": "A", "display": "B", "battery": "C"}, catalog)
        self.assertFalse(checks["source_url_is_new"])
        self.assertFalse(checks["name_is_new"])

    def test_approval_is_explicit_and_atomic(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            catalog_path = root / "verified-specs.json"
            staging = root / "candidate.json"
            audit_dir = root / "audits"
            catalog_path.write_text(json.dumps({"schema_version": 1, "phones": {}}), encoding="utf-8")
            candidate = {
                "schema_version": 1, "candidate_id": "abc", "phone_id": "PHONE-0123456789abcdef",
                "phone_name": "Example Phone 5G", "brand": "Example", "accepted_names": ["Example Phone 5G"],
                "market": "India Smartprix source check", "source_url": "https://www.smartprix.com/mobiles/example-phone-5g-ppd123456789",
                "launch_source_url": "https://www.smartprix.com/mobiles/example-phone-5g-ppd123456789",
                "launch_price": 29999, "amazon_price": 28999, "flipkart_price": None, "price_observed_at": "2026-09-21",
                "checked_at": "2026-09-21", "retrieved_at": "2026-09-21T00:00:00+00:00",
                "evidence_mode": "test", "evidence_note": "Exact product page reviewed for the staged model.",
                "variants": [{"ram": "8 GB", "storage": "128 GB"}],
                "fields": {"processor": "Example 9000", "display": "6.7 inch AMOLED", "battery": "6000 mAh"},
                "checks": {"exact_smartprix_url": True, "source_url_is_new": True, "name_is_new": True, "identity_match": True, "returned_url_match": True, "required_specs_present": True},
                "api_summary": None, "status": "ready_for_review",
            }
            staging.write_text(json.dumps(candidate), encoding="utf-8")
            args = argparse.Namespace(candidate=staging, confirm_name="Example Phone 5G", reviewed_by="test reviewer")
            with patch("scripts.phone_import_pipeline.CATALOG_PATH", catalog_path), patch("scripts.phone_import_pipeline.AUDIT_DIR", audit_dir):
                approve(args)
            saved = json.loads(catalog_path.read_text(encoding="utf-8"))
            self.assertEqual(saved["phones"][candidate["phone_id"]]["brand"], "Example")
            self.assertEqual(len(list(audit_dir.glob("approved-*.json"))), 1)

    def test_catalog_only_phone_appears_without_review_scores(self):
        catalog = {"schema_version": 1, "phones": {"PHONE-0123456789abcdef": {
            "phone_name": "Example Phone 5G", "brand": "Example", "accepted_names": ["Example Phone 5G"],
            "market": "India Smartprix source check", "source_url": "https://www.smartprix.com/mobiles/example-phone-5g-ppd123456789",
            "launch_source_url": "https://www.smartprix.com/mobiles/example-phone-5g-ppd123456789",
            "launch_price": 29999, "amazon_price": 28999, "flipkart_price": None, "price_observed_at": "2026-09-21",
            "checked_at": "2026-09-21", "evidence_note": "Exact product page reviewed for this model.", "variants": [],
            "fields": {"processor": "Example 9000", "display": "6.7 inch AMOLED", "battery": "6000 mAh", "launch_date": "2026-09-01"},
        }}}
        with patch("intelligence.engine.fetch_all", return_value=[]), patch("intelligence.engine.load_verified_catalog", return_value=catalog):
            phones = IntelligenceEngine.phones()
        self.assertEqual(len(phones), 1)
        self.assertEqual(phones[0]["processor"], "Example 9000")
        self.assertEqual(phones[0]["review_count"], 0)
        self.assertEqual(phones[0]["best_price"], 28999)


if __name__ == "__main__":
    unittest.main()
