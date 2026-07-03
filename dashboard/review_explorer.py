import re
import pandas as pd

from dashboard_data import read_sql


ASPECT_KEYWORDS = {
    "All": [],
    "Battery": ["battery", "backup", "drain"],
    "Charging": ["charging", "charger", "charge"],
    "Camera": ["camera", "photo", "selfie", "video", "blur"],
    "Performance": ["performance", "lag", "slow", "hang", "smooth"],
    "Heating": ["heating", "heat", "warm"],
    "Software": ["software", "bug", "update", "ui", "os"],
    "Connectivity": ["network", "signal", "5g", "wifi", "call"],
    "Display": ["display", "screen", "brightness", "touch"],
    "Build Quality": ["build", "design", "body", "quality"],
}


def clean(value):
    if value is None or pd.isna(value):
        return ""
    value = str(value).strip()
    return "" if value.lower() == "nan" else value


def get_review_dataset():
    df = read_sql("""
        SELECT
            r.review_id,
            r.phone_id,
            r.phone_name,
            r.platform,
            r.review_text,
            r.clean_review,
            r.word_count,
            r.quality_flag,
            r.is_duplicate,
            s.positive_percent,
            s.negative_percent,
            sp.brand,
            pi.price_segment
        FROM reviews r
        LEFT JOIN phone_summary s
            ON r.phone_id = s.phone_id
        LEFT JOIN phones_specifications sp
            ON r.phone_id = sp.phone_id
        LEFT JOIN phones_product_intelligence pi
            ON r.phone_id = pi.phone_id
    """)

    df["brand"] = df["brand"].replace({"LAVA": "Lava"})
    df["review_text"] = df["review_text"].fillna("")
    df["clean_review"] = df["clean_review"].fillna("")
    df["search_text"] = (
        df["review_text"].fillna("") + " " + df["clean_review"].fillna("")
    ).str.lower()

    if "is_duplicate" in df.columns:
        df = df[df["is_duplicate"].isin([0, False, "0", "False", "false"])]

    return df.reset_index(drop=True)


def _contains_any(text, keywords):
    text = clean(text).lower()
    return any(keyword in text for keyword in keywords)


def _search_match(text, query):
    text = clean(text).lower()
    query = clean(query).lower()

    if not query:
        return True

    terms = [t for t in re.split(r"\s+", query) if t]

    return all(term in text for term in terms)


def filter_reviews(
    df,
    search_query="",
    brand="All",
    platform="All",
    aspect="All",
    phone="All",
    limit=None,
):
    result = df.copy()

    if brand != "All":
        result = result[result["brand"] == brand]

    if phone != "All":
        result = result[result["phone_name"] == phone]

    if platform != "All":
        result = result[result["platform"] == platform]

    if aspect != "All":
        keywords = ASPECT_KEYWORDS.get(aspect, [])
        if keywords:
            result = result[
                result["search_text"].apply(lambda x: _contains_any(x, keywords))
            ]

    if search_query.strip():
        result = result[
            result["search_text"].apply(lambda x: _search_match(x, search_query))
        ]

    if limit is not None:
        result = result.head(limit)

    return result.reset_index(drop=True)

def get_review_stats(df):
    return {
        "reviews": len(df),
        "phones": df["phone_id"].nunique() if not df.empty else 0,
        "brands": df["brand"].nunique() if not df.empty else 0,
        "platforms": df["platform"].nunique() if not df.empty else 0,
    }


def build_review_summary(df, aspect="All"):
    if df.empty:
        return "No matching reviews found for the selected filters."

    phones = df["phone_name"].nunique()
    brands = df["brand"].nunique()
    platforms = ", ".join(df["platform"].dropna().unique().tolist())

    focus = "overall customer feedback" if aspect == "All" else f"{aspect.lower()} feedback"

    return (
        f"This view contains **{len(df)} reviews** across **{phones} phones** "
        f"and **{brands} brands**. Current focus: **{focus}**. "
        f"Platforms included: **{platforms}**."
    )