import pandas as pd


THEME_KEYWORDS = {
    "Battery": {
        "Battery Backup": ["backup", "lasts", "long battery", "battery life"],
        "Battery Drain": ["drain", "drains", "battery issue"],
        "Charging Speed": ["fast charging", "slow charging", "charge speed", "charging"],
    },
    "Camera": {
        "Photo Quality": ["photo", "picture", "image quality", "camera quality"],
        "Low Light": ["low light", "night", "dark"],
        "Selfie": ["selfie", "front camera"],
        "Video": ["video", "recording"],
    },
    "Performance": {
        "Lag": ["lag", "slow", "hang", "stutter"],
        "Gaming": ["gaming", "game", "bgmi", "pubg"],
        "Smoothness": ["smooth", "fast", "performance"],
    },
    "Heating": {
        "General Heating": ["heating", "heat", "warm"],
        "Gaming Heat": ["heating while gaming", "game heat", "gaming heat"],
        "Charging Heat": ["heating while charging", "charging heat"],
    },
    "Software": {
        "Bugs": ["bug", "bugs", "glitch"],
        "Updates": ["update", "updates", "ota"],
        "UI Experience": ["ui", "interface", "software", "os"],
    },
    "Connectivity": {
        "Network": ["network", "signal", "call"],
        "5G": ["5g"],
        "WiFi": ["wifi", "wi-fi"],
    },
    "Display": {
        "Brightness": ["brightness", "bright"],
        "Touch": ["touch"],
        "Screen Quality": ["display", "screen"],
    },
    "Build Quality": {
        "Design": ["design", "look", "looks"],
        "Body Quality": ["build", "body", "quality"],
        "Durability": ["durable", "durability", "strong"],
    },
}


def clean(value):
    if value is None or pd.isna(value):
        return ""
    return str(value).lower().strip()


def theme_cluster_reviews(df, aspect="All"):
    if df.empty:
        return pd.DataFrame(
            columns=["theme", "reviews", "phones", "brands", "example_review"]
        )

    if aspect != "All" and aspect in THEME_KEYWORDS:
        theme_map = THEME_KEYWORDS[aspect]
    else:
        theme_map = {}
        for group in THEME_KEYWORDS.values():
            theme_map.update(group)

    rows = []

    for theme, keywords in theme_map.items():
        mask = df["search_text"].fillna("").apply(
            lambda text: any(keyword in clean(text) for keyword in keywords)
        )

        matched = df[mask]

        if matched.empty:
            continue

        example = matched.iloc[0]["review_text"]
        if not example:
            example = matched.iloc[0]["clean_review"]

        rows.append(
            {
                "theme": theme,
                "reviews": len(matched),
                "phones": matched["phone_id"].nunique(),
                "brands": matched["brand"].nunique(),
                "example_review": example,
            }
        )

    result = pd.DataFrame(rows)

    if result.empty:
        return result

    return result.sort_values("reviews", ascending=False).reset_index(drop=True)