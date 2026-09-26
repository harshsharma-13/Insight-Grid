"""Read-only catalog audit. Prints findings; never changes source data or runs importers."""
from __future__ import annotations

import ast
import csv
import hashlib
import json
import re
import sqlite3
from collections import Counter
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
EMPTY = {"", "nan", "none", "null", "n/a", "na", "unavailable", "unknown", "not listed", "not available", "not yet rated", "-"}


def missing(value):
    return value is None or str(value).strip().casefold() in EMPTY


def normalized(value):
    if missing(value):
        return None
    text = str(value).strip()
    if re.fullmatch(r"-?\d+(\.\d+)?", text):
        return float(text)
    return text


def canonical_name(value):
    text = str(value).casefold().strip()
    text = re.sub(r"\bmoto\b", "motorola", text)
    return re.sub(r"[^a-z0-9+]", "", text)


def group_duplicates(rows, key):
    groups = {}
    for row in rows:
        value = key(row)
        if value:
            groups.setdefault(value, []).append(row.get("phone_id"))
    return {str(k): v for k, v in groups.items() if len(v) > 1}


def describe(rows):
    columns = list(dict.fromkeys(k for row in rows for k in row))
    return {
        "rows": len(rows), "columns": columns,
        "populated": {k: sum(not missing(r.get(k)) for r in rows) for k in columns},
        "duplicate_phone_ids": group_duplicates(rows, lambda r: r.get("phone_id")) if "phone_id" in columns else {},
    }


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    paths = sorted((ROOT / "data").rglob("*")) + [ROOT / "web/app/data/platform-data.json", ROOT / "web/public/data/reviews.json"]
    paths = [p for p in paths if p.is_file()]
    initial_hashes = {str(p.relative_to(ROOT)): digest(p) for p in paths}
    csvs = {}
    for path in sorted((ROOT / "data/processed").glob("phones*.csv")):
        with path.open(encoding="utf-8-sig", newline="") as handle:
            csvs[path.stem] = list(csv.DictReader(handle))
    with (ROOT / "data/raw/phones_link.csv").open(encoding="utf-8-sig", newline="") as handle:
        csvs["phones_link"] = list(csv.DictReader(handle))
    master = csvs["phones_master"]
    master_by_id = {r["phone_id"]: r for r in master}
    out = {"scope": "Local source files, read-only SQLite, and local website snapshot. External factual spot checks are documented separately in the report; hosted state was not inspected.", "csv_files": {k: describe(v) for k, v in csvs.items()}}
    out["identity"] = {}
    for name, rows in csvs.items():
        out["identity"][name] = {
            "missing_master_ids": sorted(set(master_by_id) - {r["phone_id"] for r in rows}),
            "extra_ids": sorted({r["phone_id"] for r in rows} - set(master_by_id)),
            "name_mismatches": [{"phone_id": r["phone_id"], "name": r.get("phone_name"), "master": master_by_id[r["phone_id"]]["phone_name"]} for r in rows if r["phone_id"] in master_by_id and canonical_name(r.get("phone_name")) != canonical_name(master_by_id[r["phone_id"]]["phone_name"])],
            "duplicate_names": group_duplicates(rows, lambda r: canonical_name(r.get("phone_name"))),
        }
    specs = csvs["phones_specifications"]
    metadata = csvs["phones_product_intelligence"]
    out["raw_spec_brands"] = dict(Counter(r["brand"] for r in specs))
    out["spec_status"] = dict(Counter(r["spec_status"] for r in specs))
    out["enrichment_status"] = dict(Counter(r["enrichment_status"] for r in metadata))
    out["duplicate_spec_urls"] = group_duplicates(specs, lambda r: r.get("smartprix_link"))
    out["duplicate_images"] = group_duplicates(specs, lambda r: r.get("image_filename"))
    core_fields = ["display", "processor", "ram", "storage", "battery", "charging", "rear_camera", "front_camera"]
    out["core_coverage_distribution"] = dict(Counter(sum(not missing(r.get(k)) for k in core_fields) for r in specs))
    out["spec_gaps"] = [{"phone_id": r["phone_id"], "phone_name": r["phone_name"], "missing": [k for k in core_fields if missing(r.get(k))]} for r in specs if any(missing(r.get(k)) for k in core_fields)]
    out["spec_values"] = {k: dict(Counter(r.get(k, "") for r in specs)) for k in ["supports_5g", "nfc", "wifi", "refresh_rate", "charging"]}
    out["price_dates"] = dict(Counter(r.get("price_last_updated") for r in metadata))
    out["spec_sources"] = dict(Counter(r.get("spec_source_url") for r in metadata))
    out["launch_dates"] = [{"phone_id": r["phone_id"], "date": r.get("launch_date")} for r in metadata]
    out["missing_price_fields"] = {k: [r["phone_id"] for r in metadata if missing(r.get(k))] for k in ["amazon_price", "flipkart_price", "launch_price"]}
    out["price_segments"] = dict(Counter(r.get("price_segment") for r in metadata))
    out["high_refresh_rate_flags"] = [{"phone_id": r["phone_id"], "phone_name": r["phone_name"], "refresh_rate": r["refresh_rate"]} for r in specs if float(r["refresh_rate"] or 0) > 165]
    out["charging_without_forward_wattage"] = [{"phone_id": r["phone_id"], "phone_name": r["phone_name"], "charging": r["charging"]} for r in specs if not re.search(r"\d+(?:\.\d+)?\s*W\s+(?!Reverse)", r["charging"], flags=re.I)]
    out["spec_content_duplicates"] = group_duplicates(specs, lambda r: tuple(r.get(k) for k in core_fields + ["refresh_rate", "weight", "android_version", "nfc"]))
    out["raw_workbooks"] = {}
    for filename in ["smartphones_list.xlsx", "Smartphones research data.xlsx", "comments_data.xlsx"]:
        with pd.ExcelFile(ROOT / "data/raw" / filename) as book:
            record = {"sheets": book.sheet_names}
            if filename == "comments_data.xlsx":
                record["master_order_mismatches"] = [{"position": i + 1, "sheet": sheet, "master": master[i]["phone_name"] if i < len(master) else None} for i, sheet in enumerate(book.sheet_names) if i >= len(master) or canonical_name(sheet) != canonical_name(master[i]["phone_name"])]
            else:
                record["dimensions"] = {}
                for sheet in book.sheet_names:
                    frame = pd.read_excel(book, sheet_name=sheet, header=None, dtype=str).fillna("")
                    record["dimensions"][sheet] = list(frame.shape)
                    if filename == "Smartphones research data.xlsx" and sheet == "Smartphone Data":
                        research_names = [str(frame.iloc[i, 1]).strip() for i in range(len(frame)) if str(frame.iloc[i, 0]).strip().startswith("#")]
                        record["phone_blocks"] = len(research_names)
                        record["master_order_mismatches"] = [{"position": i + 1, "research": name, "master": master[i]["phone_name"] if i < len(master) else None} for i, name in enumerate(research_names) if i >= len(master) or canonical_name(name) != canonical_name(master[i]["phone_name"])]
                    if filename == "smartphones_list.xlsx" and sheet == "list":
                        record["header_claims"] = frame.iloc[:3, 0].tolist()
                        entries = frame[frame.iloc[:, 0].str.fullmatch(r"\d+")]
                        record["actual_model_rows"] = len(entries)
                        master_names = {canonical_name(r["phone_name"]) for r in master}
                        record["names_not_exactly_in_master"] = [str(row.iloc[1]) for _, row in entries.iterrows() if canonical_name(row.iloc[1]) not in master_names]
                        record["duplicate_serial_numbers"] = {k: v for k, v in Counter(entries.iloc[:, 0]).items() if v > 1}
                    if filename == "Smartphones research data.xlsx":
                        record["header_claim"] = " | ".join(str(value) for value in frame.iloc[0] if str(value))
                        record["capture_dates"] = dict(Counter(str(frame.iloc[i, 4]) for i in range(len(frame)) if str(frame.iloc[i, 1]).strip().casefold() == "date of capture"))
            out["raw_workbooks"][filename] = record
    with sqlite3.connect(f"file:{(ROOT / 'data/acip.db').as_posix()}?mode=ro", uri=True) as db:
        db.row_factory = sqlite3.Row
        out["database_integrity"] = [r[0] for r in db.execute("PRAGMA integrity_check")]
        out["database_tables"] = {}
        out["database_csv_differences"] = {}
        for name in ["phones", "phones_specifications", "phones_product_intelligence", "phones_product_catalog"]:
            rows = [dict(r) for r in db.execute(f'SELECT * FROM "{name}"')]
            out["database_tables"][name] = describe(rows)
            csv_name = "phones_master" if name == "phones" else name
            refs = {r["phone_id"]: r for r in csvs[csv_name]}
            deltas = []
            for row in rows:
                ref = refs.get(row["phone_id"], {})
                for key in set(row) & set(ref):
                    if normalized(row[key]) != normalized(ref[key]):
                        deltas.append({"phone_id": row["phone_id"], "field": key, "csv": ref[key], "db": row[key]})
            out["database_csv_differences"][name] = deltas
        out["review_linkage_only"] = {
            "rows": db.execute("SELECT COUNT(*) FROM reviews").fetchone()[0],
            "nonduplicate_rows": db.execute("SELECT COUNT(*) FROM reviews WHERE is_duplicate=0").fetchone()[0],
            "orphan_reviews": db.execute("SELECT COUNT(*) FROM reviews r LEFT JOIN phones p ON r.phone_id=p.phone_id WHERE p.phone_id IS NULL").fetchone()[0],
            "summary_phones": db.execute("SELECT COUNT(*) FROM phone_summary").fetchone()[0],
        }
    snapshot = json.loads((ROOT / "web/app/data/platform-data.json").read_text(encoding="utf-8"))
    phones = snapshot["phones"]
    out["snapshot"] = {"generated_at": snapshot.get("generated_at"), "overview_metrics": snapshot["overview"]["metrics"], "phone_data": describe(phones), "brands": dict(Counter(r["brand"] for r in phones)), "review_backed_brands": sorted({r["brand"] for r in phones if r["review_count"] > 0}), "zero_review_phones": [{"phone_id": r["phone_id"], "phone_name": r["phone_name"], "brand": r["brand"]} for r in phones if not r["review_count"]], "missing_master_ids": sorted(set(master_by_id) - {r["phone_id"] for r in phones})}
    specs_by_id = {r["phone_id"]: r for r in specs}
    spec_deltas = []
    for row in phones:
        ref = specs_by_id.get(row["phone_id"], {})
        for key in core_fields + ["refresh_rate"]:
            if normalized(row.get(key)) != normalized(ref.get(key)):
                spec_deltas.append({"phone_id": row["phone_id"], "field": key, "source": ref.get(key), "export": row.get(key)})
    out["snapshot_spec_differences"] = spec_deltas
    out["spec_fields_not_exported"] = [k for k in specs[0] if k not in phones[0]]
    out["metadata_fields_not_exported"] = [k for k in metadata[0] if k not in phones[0]]
    out["images_missing_on_disk"] = [r["phone_id"] for r in specs if not r.get("image_local_path") or not (ROOT / r["image_local_path"]).is_file()]
    out["images_missing_web"] = [r["phone_id"] for r in phones if not r.get("image_url") or not (ROOT / "web/public" / r["image_url"].lstrip("/")).is_file()]
    # Execute ONLY pure parser definitions, not imports, browser code, or entrypoints.
    tree = ast.parse((ROOT / "preprocessing/smartprix_spec_extractor.py").read_text(encoding="utf-8"))
    pure_names = {"clean", "section_lines", "display_type_from", "parse_specs"}
    module = ast.Module(body=[node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name in pure_names], type_ignores=[])
    namespace = {"re": re}
    exec(compile(module, "audited_pure_parser", "exec"), namespace)
    parse = namespace["parse_specs"]
    out["synthetic_parser_probes"] = {
        "empty_page_connectivity": {k: parse("")[k] for k in ["supports_5g", "nfc", "wifi"]},
        "explicit_no_nfc": parse("Connectivity\nNo NFC\nBattery")["nfc"],
        "pwm_before_refresh": parse("Display\n3840Hz PWM Dimming\n120Hz Refresh Rate\nCamera")["refresh_rate"],
        "touch_before_refresh": parse("Display\n1500Hz Touch Sampling Rate\n144Hz Refresh Rate\nCamera")["refresh_rate"],
    }
    out["hashes"] = initial_hashes
    out["source_hashes_unchanged_during_audit"] = all(digest(ROOT / name) == value for name, value in initial_hashes.items())
    print(json.dumps(out, ensure_ascii=True, indent=2))


if __name__ == "__main__":
    main()
