"""Conservative Smartprix text parser. Stages candidates; never overwrites live data."""
from pathlib import Path
import argparse
import json
import re
from datetime import datetime, UTC
from uuid import uuid4

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def clean(value):
    return re.sub(r"\s+", " ", str(value or "")).strip()


def section_lines(lines, section_name, stop_sections):
    if section_name not in lines:
        return []
    start = lines.index(section_name) + 1
    end = min((i for i in range(start, len(lines)) if lines[i] in stop_sections), default=len(lines))
    return lines[start:end]


def display_type_from(display):
    return next((kind for word, kind in [("AMOLED", "AMOLED"), ("OLED", "OLED"), ("IPS", "IPS LCD"), ("LCD", "LCD")] if word in display.upper()), "")


def _capability(lines, pattern):
    joined = "\n".join(lines)
    if re.search(rf"\b{pattern}\s*(?:\||:)?\s*(?:unknown|n/a|not specified)\b", joined, re.I):
        return ""
    if re.search(rf"\b(?:no|without)\s+{pattern}\b|\b{pattern}\s*(?:\||:)?\s*(?:no|not supported)\b", joined, re.I):
        return "No"
    if re.search(rf"\b{pattern}\b", joined, re.I):
        return "Yes"
    return ""


def parse_specs(page_text):
    lines = [clean(line).lstrip("* ") for line in page_text.splitlines() if clean(line)]
    headings = ["General", "Design", "Display", "Camera", "Technical", "Memory", "Connectivity", "Battery", "Extra", "Multimedia", "Performance"]
    full = next((i for i, line in enumerate(lines) if re.search(r"\bFull Specs$", line)), None)
    if full is not None:
        lines = lines[full + 1:]
    sections = {key: section_lines(lines, key, [h for h in headings if h != key]) for key in headings}
    result = {key: "" for key in ["launch_date", "display", "display_type", "refresh_rate", "resolution", "processor", "ram", "storage", "battery", "charging", "charging_w", "reverse_charging_w", "rear_camera", "front_camera", "android_version", "supports_5g", "nfc", "bluetooth", "wifi", "weight"]}

    def table_value(section, key):
        values = sections[section]
        for i, line in enumerate(values):
            match = re.match(rf"^{re.escape(key)}\s*\|\s*(.+)$", line, re.I)
            if match:
                return match.group(1)
            if line.casefold() == key.casefold() and i + 1 < len(values):
                return values[i + 1]
        return ""

    def first(section, pattern):
        return next((line for line in sections[section] if re.search(pattern, line, re.I)), "")

    result["display"] = first("Display", r"\bScreen\b") or table_value("Display", "Type")
    result["display_type"] = display_type_from(result["display"])
    size = table_value("Display", "Size")
    if size:
        result["display"] = f"{size}; {result['display_type']}".strip("; ")
    refresh_text = "\n".join(sections["Display"])
    match = re.search(r"(?<![\d.])(\d+(?:\.\d+)?)\s*Hz\s+Refresh Rate\b", refresh_text, re.I)
    if not match:
        match = re.search(r"\bRefresh Rate\s*(?:\||:)?\s*(?:up to\s+)?(\d+(?:\.\d+)?)\s*Hz\b", refresh_text, re.I)
    if not match and size:
        match = re.search(r"(?<![\d.])(\d+(?:\.\d+)?)\s*Hz\b", size, re.I)
    result["refresh_rate"] = match.group(1) if match else ""
    resolution = re.search(r"\b\d{3,4}\s*[x×]\s*\d{3,4}\s*(?:pixels|px)\b", refresh_text, re.I)
    result["resolution"] = resolution.group(0) if resolution else ""
    result["processor"] = table_value("Technical", "Chipset") or first("Technical", "Chipset").replace(" Chipset", "")
    result["ram"] = table_value("Memory", "RAM")
    if not result["ram"]:
        match = re.search(r"(?<!\d)(\d+\s*GB)\s+RAM\b", "\n".join(sections["Technical"]), re.I)
        result["ram"] = match.group(1) if match else ""
    result["storage"] = table_value("Memory", "Storage") or first("Technical", "Inbuilt Memory").replace(" Inbuilt Memory", "")
    result["rear_camera"] = table_value("Camera", "Rear Camera") or first("Camera", "Rear Camera")
    result["front_camera"] = table_value("Camera", "Front Camera") or first("Camera", "Front Camera")
    result["android_version"] = table_value("Technical", "OS") or first("General", r"\bAndroid\b")
    result["launch_date"] = table_value("General", "Release Date")
    result["weight"] = table_value("Design", "Weight")
    if not result["weight"]:
        weight = re.search(r"\b\d+(?:\.\d+)?\s*g\b", "\n".join(sections["General"]), re.I)
        result["weight"] = weight.group(0) if weight else ""
    for field, pattern in [("supports_5g", "5G"), ("nfc", "NFC"), ("wifi", "Wi-?Fi")]:
        values = sections["Connectivity"] + (sections["Extra"] if field == "nfc" else [])
        result[field] = _capability(values, pattern)
    result["bluetooth"] = table_value("Connectivity", "Bluetooth") or first("Connectivity", "Bluetooth")
    result["battery"] = table_value("Battery", "Size") or first("Battery", "mAh")
    forward = table_value("Battery", "Fast Charging")
    reverse = table_value("Battery", "Reverse Charging")
    if not forward:
        forward = "; ".join(line for line in sections["Battery"] if re.search(r"\b(?:Fast|Turbo|SUPERVOOC|Wired)\b.*Charging", line, re.I) and not re.search("Reverse|Wireless|USB Features", line, re.I))
    if not reverse:
        reverse = first("Battery", "Reverse Charging")
    for field, value in [("charging_w", forward), ("reverse_charging_w", reverse)]:
        watts = re.search(r"(?<![\d.])(\d+(?:\.\d+)?)\s*W\b", value, re.I)
        result[field] = watts.group(1) if watts else ""
    result["charging"] = "; ".join(part for part in [f"Wired: {forward}" if forward else "", f"Reverse: {reverse}" if reverse else ""] if part)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-text", required=True, type=Path)
    parser.add_argument("--phone-id", required=True)
    parser.add_argument("--phone-name", required=True)
    parser.add_argument("--page-title", required=True)
    parser.add_argument("--source-url", required=True)
    args = parser.parse_args()
    if clean(args.phone_name).casefold() != clean(args.page_title).casefold():
        parser.error("Page title does not exactly match the intended phone. Resolve aliases explicitly before staging.")
    if not re.fullmatch(r"https://www\.smartprix\.com/mobiles/[a-z0-9-]+", args.source_url):
        parser.error("An exact Smartprix product URL is required")
    result = parse_specs(args.input_text.read_text(encoding="utf-8"))
    if not all(result[key] for key in ["processor", "display", "battery"]):
        parser.error("Incomplete or unrecognised page. Active data has not been changed.")
    target = PROJECT_ROOT / "data/catalog/staging"
    target.mkdir(parents=True, exist_ok=True)
    output = target / f"candidate-{uuid4().hex}.json"
    payload = {"phone_id": args.phone_id, "phone_name": args.phone_name, "source_url": args.source_url, "retrieved_at": datetime.now(UTC).isoformat(), "status": "Needs human verification", "fields": result}
    with output.open("x", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)
    print(f"Staged candidate: {output}. No active data or reviews changed.")


if __name__ == "__main__":
    main()
