"""Read-only regression checks for the audited catalog repair."""
import copy
import hashlib
import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from intelligence.catalog import load_verified_catalog, validate_catalog, normalize_date, apply_verified_specs
from intelligence.engine import IntelligenceEngine
from preprocessing.smartprix_spec_extractor import parse_specs


class CatalogRepairs(unittest.TestCase):
    def test_historical_data_and_reviews_unchanged(self):
        audit = json.loads((ROOT / 'reports/audits/2026-09-03/catalog-audit-results.json').read_text())
        for name, digest in audit['hashes'].items():
            if name.replace('\\', '/') == 'web/app/data/platform-data.json':
                continue
            with self.subTest(file=name):
                self.assertEqual(hashlib.sha256((ROOT / name).read_bytes()).hexdigest(), digest)

    def test_review_snapshot_sections_unchanged(self):
        web_root = ROOT / 'web'
        old = json.loads(subprocess.check_output([
            'git', '-c', f'safe.directory={web_root.as_posix()}', 'show',
            '7ed1bbf54a429c3e2ffc635fdf5990b190520ca8:app/data/platform-data.json',
        ], cwd=web_root))
        new = json.loads((ROOT / 'web/app/data/platform-data.json').read_text(encoding='utf-8'))
        for key in ['phone_details', 'phone_reviews', 'reviews', 'competitive', 'actions', 'generated_at']:
            self.assertEqual(old[key], new[key], key)
        self.assertTrue({p['phone_id'] for p in old['phones']}.issubset({p['phone_id'] for p in new['phones']}))
        self.assertEqual(len([p for p in new['phones'] if p['phone_id'].startswith('PHONE-')]), 5)

    def test_source_boundary(self):
        catalog = load_verified_catalog()
        self.assertGreaterEqual(len(catalog['phones']), 10)
        phones = IntelligenceEngine.phones()
        self.assertEqual(sum(p['launch_price'] is not None for p in phones), 62)
        self.assertEqual(sum(p['amazon_price'] is not None for p in phones), 52)
        self.assertEqual(sum(p['flipkart_price'] is not None for p in phones), 58)
        self.assertTrue(all(p['best_price'] is not None for p in phones if p['amazon_price'] or p['flipkart_price']))
        self.assertTrue(all(p['processor'] is None for p in phones if not p['verified_spec_fields']))
        oppo = next(p for p in phones if p['phone_id'] == 'PH047')
        self.assertIn('oppo-k14x', oppo['spec_source_url'])
        self.assertEqual(oppo['processor'], 'MediaTek Dimensity 6300')
        self.assertEqual(oppo['battery'], '6500 mAh')
        hmd = next(p for p in phones if p['phone_id'] == 'PH008')
        self.assertEqual(hmd['storage'], '128 GB')
        self.assertEqual(hmd['spec_core_coverage'], 9)
        self.assertEqual(hmd['spec_source_url'], 'https://www.hmd.com/en_in/hmd-vibe2-5g/specs')
        infinix = next(p for p in phones if p['phone_id'] == 'PH003')
        self.assertEqual(infinix['model_code'], 'X6840')
        self.assertEqual(infinix['storage'], '64 GB')
        self.assertEqual(infinix['charging_w'], 15)
        self.assertEqual(infinix['spec_source_url'], 'https://infinixmobiles.in/products/smart-20')
        pova = next(p for p in phones if p['phone_id'] == 'PH001')
        self.assertEqual(pova['spec_market'], 'India Smartprix source check')
        self.assertEqual(pova['ram'], '6 GB')
        self.assertIsNone(pova['charging_w'])
        g37 = next(p for p in phones if p['phone_id'] == 'PH010')
        g37_power = next(p for p in phones if p['phone_id'] == 'PH009')
        self.assertEqual(g37['battery'], '5200 mAh')
        self.assertEqual(g37_power['battery'], '7000 mAh')
        self.assertNotEqual(g37['spec_source_url'], g37_power['spec_source_url'])
        self.assertIsNone(next(p for p in phones if p['phone_id'] == 'PH011')['front_camera'])
        self.assertIsNone(next(p for p in phones if p['phone_id'] == 'PH012')['storage'])
        redmi = next(p for p in phones if p['phone_id'] == 'PH016')
        self.assertEqual(redmi['phone_name'], 'Redmi A7 Pro 5G')
        self.assertEqual(redmi['processor'], 'T8300 5G')
        invalid = copy.deepcopy(catalog)
        invalid['phones']['PH047']['source_url'] = invalid['phones']['PH004']['source_url']
        with self.assertRaises(ValueError):
            validate_catalog(invalid)
        invalid = copy.deepcopy(catalog)
        invalid['phones']['PH008']['source_url'] = 'https://example.com/hmd-vibe2-5g/specs'
        with self.assertRaises(ValueError):
            validate_catalog(invalid)
        with self.assertRaises(ValueError):
            apply_verified_specs({'phone_id': 'PH047', 'phone_name': 'Lava Yuva Star 3'}, catalog)
        invalid = copy.deepcopy(catalog)
        invalid['phones']['PH047']['fields']['nfc'] = 'Unknown'
        with self.assertRaises(ValueError):
            validate_catalog(invalid)

    def test_rate_and_charging_parser(self):
        sample = 'Display\n3840 Hz PWM Dimming\n1500 Hz Touch Sampling\n144 Hz Refresh Rate\nBattery\n7000 mAh Battery\n68W Fast Charging\n10W Reverse Charging\nExtra\nNo NFC'
        parsed = parse_specs(sample)
        self.assertEqual(parsed['refresh_rate'], '144')
        self.assertEqual(parsed['charging_w'], '68')
        self.assertEqual(parsed['reverse_charging_w'], '10')
        self.assertEqual(parsed['nfc'], 'No')
        self.assertEqual(parse_specs('Connectivity\nNFC | Unknown')['nfc'], '')
        self.assertEqual(parse_specs('Battery\n10W Reverse Charging')['charging_w'], '')
        self.assertEqual(parse_specs('Display\n3840 Hz PWM Dimming')['refresh_rate'], '')

    def test_no_false_winner_and_complete_rankings(self):
        result = IntelligenceEngine.compare('PH001', 'PH047')
        self.assertIsNone(result['winner_id'])
        self.assertIsNone(IntelligenceEngine.compare('PH047', 'PH047')['winner_id'])
        phones = IntelligenceEngine.phones()
        ranked = IntelligenceEngine.finder('overall', limit=len(phones))
        self.assertEqual({p['phone_id'] for p in ranked}, {p['phone_id'] for p in phones if p['review_count']})

    def test_source_dates(self):
        self.assertEqual(normalize_date(46114), '2026-04-02')
        self.assertIsNone(normalize_date(''))
        with self.assertRaises(ValueError):
            normalize_date('not a date')


if __name__ == '__main__':
    unittest.main(verbosity=2)
