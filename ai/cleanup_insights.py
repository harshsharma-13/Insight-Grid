from pathlib import Path
import ast
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parent.parent
FILE = PROJECT_ROOT / "data" / "processed" / "phone_ai_insights.csv"


WEAK_TERMS = [
    "neutral",
    "no positive",
    "insufficient",
    "limited data",
    "lack of",
    "not enough",
    "no clear",
]


def flatten_text(value):
    if pd.isna(value):
        return ""

    text = str(value).strip()

    try:
        parsed = ast.literal_eval(text)

        if isinstance(parsed, dict):
            parts = []
            for key, val in parsed.items():
                if isinstance(val, list):
                    val = "; ".join(str(x) for x in val)
                parts.append(f"{key}: {val}")
            return " ".join(parts)

        if isinstance(parsed, list):
            return "; ".join(str(x) for x in parsed)

    except Exception:
        pass

    return text


def clean_list_field(value, fallback):
    if pd.isna(value) or str(value).strip() == "":
        return fallback

    items = [item.strip() for item in str(value).split(";")]

    cleaned = []

    for item in items:
        lower = item.lower()

        if not item:
            continue

        if any(term in lower for term in WEAK_TERMS):
            continue

        cleaned.append(item)

    if not cleaned:
        return fallback

    return "; ".join(cleaned)


def main():
    print("=" * 50)
    print("Insight Cleanup")
    print("=" * 50)

    df = pd.read_csv(FILE)

    df["platform_insight"] = df["platform_insight"].apply(flatten_text)

    df["top_strengths"] = df["top_strengths"].apply(
        lambda x: clean_list_field(x, "Insufficient positive evidence")
    )

    df["top_pain_points"] = df["top_pain_points"].apply(
        lambda x: clean_list_field(x, "No dominant pain point identified")
    )

    df["ideal_for"] = df["ideal_for"].apply(
        lambda x: clean_list_field(x, "General smartphone users")
    )

    df["avoid_if"] = df["avoid_if"].apply(
        lambda x: clean_list_field(x, "Users needing stronger evidence before purchase")
    )

    df.to_csv(FILE, index=False, encoding="utf-8-sig")

    print("Cleaned file updated:")
    print(FILE)
    print(f"Rows cleaned: {len(df)}")


if __name__ == "__main__":
    main()