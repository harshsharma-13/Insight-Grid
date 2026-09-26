from __future__ import annotations


SEGMENTS = {
    "Entry": "Entry (≤ ₹10,000)",
    "Budget": "Budget (₹10,001–₹15,000)",
    "Lower Mid Range": "Lower Mid Range (₹15,001–₹20,000)",
    "Upper Mid Range": "Upper Mid Range (₹20,001–₹30,000)",
    "Premium": "Premium (> ₹30,000)",
}

BRAND_ALIASES = {
    "lava": "Lava",
    "moto": "Motorola",
    "motorola": "Motorola",
    "oneplus": "OnePlus",
    "iqoo": "iQOO",
}

USE_CASE_ASPECTS = {
    "overall": ["Performance", "Battery", "Camera", "Software"],
    "gaming": ["Performance", "Heating", "Display", "Battery"],
    "camera": ["Camera", "Display", "Software"],
    "battery": ["Battery", "Charging", "Heating"],
    "work": ["Performance", "Battery", "Connectivity", "Software"],
    "entertainment": ["Display", "Battery", "Performance"],
    "value": ["Performance", "Battery", "Camera", "Build Quality"],
}

ACTION_OWNERS = {
    "Software": "Software experience",
    "Performance": "Performance engineering",
    "Heating": "Thermal engineering",
    "Battery": "Power systems",
    "Battery Drain": "Power systems",
    "Charging": "Power systems",
    "Camera": "Imaging",
    "Connectivity": "Connectivity",
    "Display": "Display engineering",
    "Build Quality": "Industrial design",
}

ACTION_RECOMMENDATIONS = {
    "Software": "Prioritize stability, update quality and interaction smoothness in the next release train.",
    "Performance": "Profile sustained performance, memory pressure and app-switching regressions on affected devices.",
    "Heating": "Recalibrate thermal policies for gaming, charging and prolonged camera workloads.",
    "Battery": "Investigate idle drain and background activity before the next firmware release.",
    "Charging": "Audit charging consistency, bundled accessories and thermal throttling during fast charge.",
    "Camera": "Improve capture consistency and low-light tuning, then validate against customer evidence.",
    "Connectivity": "Reproduce network, call-quality and 5G stability complaints across high-volume regions.",
    "Display": "Validate brightness, touch response and panel consistency across suppliers.",
    "Build Quality": "Review material perception, durability failures and fit-and-finish consistency.",
}


def normalize_brand(value: str | None) -> str:
    value = (value or "Unknown").strip()
    return BRAND_ALIASES.get(value.casefold(), value)


def brand_query_keys(value: str | None) -> list[str]:
    """Return every case-insensitive raw brand key represented by a canonical label."""
    canonical = normalize_brand(value)
    aliases = [alias for alias, target in BRAND_ALIASES.items() if target == canonical]
    return sorted(set(aliases or [canonical.casefold()]))


def segment_label(value: str | None) -> str:
    value = (value or "Unknown").strip()
    return SEGMENTS.get(value, value)
