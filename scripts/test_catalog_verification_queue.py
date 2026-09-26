"""Offline checks for the source-verification queue and API safety boundary."""
import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from intelligence.catalog import load_verified_catalog  # noqa: E402
from scripts.catalog_verification_queue import build_queue, load_legacy, main, normalized_name, review_api_response, smartprix_path  # noqa: E402


class VerificationQueueTests(unittest.TestCase):
    def test_all_existing_phones_queued_without_promotion(self):
        rows = load_legacy()
        catalog = load_verified_catalog()
        queue = build_queue(rows, catalog)
        self.assertEqual(len(queue), 57)
        self.assertEqual({item["phone_id"] for item in queue}, {row["phone_id"] for row in rows})
        self.assertEqual(sum(item["status"] == "source_checked_partial" for item in queue), 57)
        self.assertEqual(sum(item["status"] == "awaiting_source_verification" for item in queue), 0)
        self.assertEqual(len(catalog["phones"]), 62)
        self.assertEqual(catalog["phones"]["PH027"]["fields"]["charging_w"], 15)
        self.assertEqual(catalog["phones"]["PH032"]["fields"]["ram"], "4 GB")
        self.assertNotIn("charging_w", catalog["phones"]["PH032"]["fields"])
        self.assertEqual(catalog["phones"]["PH050"]["phone_name"], "Redmi Note 15 Pro 5G")
        self.assertTrue(all(item["review_required"] for item in queue))
        oppo = next(item for item in queue if item["phone_id"] == "PH047")
        self.assertIn("historical_source_conflicts_with_checked_source", oppo["flags"])
        self.assertIn("shared_historical_source_url", oppo["flags"])
        self.assertIn("oppo-k14x", oppo["api_candidate_url"])
        lava = next(item for item in queue if item["phone_id"] == "PH046")
        self.assertIn("lava-yuva-star-3", lava["api_candidate_url"])

    def test_api_identity_and_relative_url(self):
        self.assertEqual(normalized_name("Moto G37"), normalized_name("Motorola Moto G37"))
        self.assertNotEqual(normalized_name("Moto G37 Power"), normalized_name("Motorola Moto G37 Power 5G"))
        item = {"historical_name": "Oppo K14x 5G", "accepted_names": ["Oppo K14x 5G"],
                "api_candidate_url": "https://www.smartprix.com/mobiles/oppo-k14x-5g-ppd1259g0jtq"}
        body = {"status": "success", "data": {"name": "Oppo K14x 5G",
                "url": "/mobiles/oppo-k14x-5g-ppd1259g0jtq",
                "variants": [{"variant_text": "4 GB + 128 GB", "price": 10000}], "fullSpecs": {"Display": []}}}
        evidence = review_api_response(item, body)
        self.assertEqual(evidence["identity"], "match")
        self.assertEqual(evidence["url_status"], "match")
        self.assertEqual(evidence["reported_variants"], [{"variant_text": "4 GB + 128 GB"}])
        self.assertTrue(evidence["needs_manual_review"])
        wrong = copy.deepcopy(body)
        wrong["data"]["name"] = "Lava Yuva Star 3"
        wrong["data"]["url"] = "/mobiles/lava-yuva-star-3-ppd1srzb84ba"
        evidence = review_api_response(item, wrong)
        self.assertEqual((evidence["identity"], evidence["url_status"]), ("mismatch", "mismatch"))
        self.assertIsNone(smartprix_path("https://example.com/mobiles/oppo-k14x"))

    def test_offline_cli_and_missing_key_do_not_change_catalog(self):
        catalog_path = ROOT / "data/catalog/verified-specs.json"
        before = catalog_path.read_bytes()
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "queue.json"
            run = subprocess.run([sys.executable, str(ROOT / "scripts/catalog_verification_queue.py"),
                                  "--output", str(output)], capture_output=True, text=True, check=True)
            self.assertIn("0 API calls", run.stdout)
            self.assertEqual(json.loads(output.read_text(encoding="utf-8"))["summary"]["total"], 57)
            missing_key_output = Path(temporary) / "should-not-exist.json"
            with patch("scripts.catalog_verification_queue.local_api_key", return_value=None):
                with self.assertRaises(SystemExit) as blocked:
                    main(["--fetch", "--output", str(missing_key_output)])
            self.assertNotEqual(blocked.exception.code, 0)
            self.assertFalse(missing_key_output.exists())
        self.assertEqual(catalog_path.read_bytes(), before)


if __name__ == "__main__":
    unittest.main(verbosity=2)
