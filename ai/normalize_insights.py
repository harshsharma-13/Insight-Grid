from pathlib import Path
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
FILE = PROJECT_ROOT / "data" / "processed" / "phone_ai_insights.csv"

def normalize_verdict(value):
    text = str(value).strip().lower()

    if "strong" in text or "highly" in text:
        return "Highly Recommended"

    if "positive" in text or "satisfactory" in text:
        return "Generally Positive"

    if "poor" in text or "negative" in text or "not recommended" in text:
        return "Not Recommended"

    if "insufficient" in text or "limited" in text:
        return "Limited Evidence"

    if "mixed" in text or "balanced" in text:
        return "Mixed Reception"

    return "Mixed Reception"

def main():
    df = pd.read_csv(FILE)
    df["consumer_verdict"] = df["consumer_verdict"].apply(normalize_verdict)
    df.to_csv(FILE, index=False, encoding="utf-8-sig")

    print("Verdicts normalized.")
    print(df["consumer_verdict"].value_counts())

if __name__ == "__main__":
    main()