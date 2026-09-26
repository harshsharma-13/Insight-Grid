"""Rebuild review intelligence with one canonical duplicate policy.

The source CSVs remain the durable data layer for the legacy dashboard, SQLite
database, API, and hosted web snapshot. This script keeps those consumers in
sync and guarantees that exact repeated reviews only contribute once.
"""

from __future__ import annotations

import re
import unicodedata
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "data" / "processed"

REVIEW_CLEAN = PROCESSED / "reviews_clean.csv"
REVIEW_SENTIMENT = PROCESSED / "reviews_sentiment.csv"
REVIEW_ASPECTS = PROCESSED / "reviews_aspects.csv"


def _truthy(series: pd.Series) -> pd.Series:
    return series.fillna(False).astype(str).str.strip().str.casefold().isin({"1", "true", "yes"})


def _normalize_review(value: object) -> str:
    text = unicodedata.normalize("NFKC", str(value or "")).casefold()
    return re.sub(r"\s+", " ", text).strip().strip('"“”')


def _write(frame: pd.DataFrame, path: Path) -> None:
    frame.to_csv(path, index=False, encoding="utf-8")


def _summary(frame: pd.DataFrame, group_columns: list[str]) -> pd.DataFrame:
    grouped = frame.groupby(group_columns, dropna=False)
    result = grouped.agg(
        review_count=("review_id", "count"),
        positive_count=("sentiment", lambda values: values.astype(str).str.casefold().eq("positive").sum()),
        neutral_count=("sentiment", lambda values: values.astype(str).str.casefold().eq("neutral").sum()),
        negative_count=("sentiment", lambda values: values.astype(str).str.casefold().eq("negative").sum()),
        avg_confidence=("sentiment_confidence", "mean"),
    ).reset_index()
    for column in ["review_count", "positive_count", "neutral_count", "negative_count"]:
        result[column] = result[column].astype(int)
    denominator = result["review_count"].replace(0, pd.NA)
    result["positive_percent"] = (result["positive_count"] * 100 / denominator).fillna(0).round(2)
    result["neutral_percent"] = (result["neutral_count"] * 100 / denominator).fillna(0).round(2)
    result["negative_percent"] = (result["negative_count"] * 100 / denominator).fillna(0).round(2)
    result["avg_confidence"] = result["avg_confidence"].fillna(0).round(4)
    ordered = group_columns + [
        "review_count", "positive_count", "neutral_count", "negative_count",
        "positive_percent", "neutral_percent", "negative_percent", "avg_confidence",
    ]
    return result[ordered]


def main() -> None:
    clean = pd.read_csv(REVIEW_CLEAN)
    sentiment = pd.read_csv(REVIEW_SENTIMENT)
    aspects = pd.read_csv(REVIEW_ASPECTS)

    if sentiment["review_id"].duplicated().any():
        raise ValueError("reviews_sentiment.csv must contain one row per review_id")

    sentiment = sentiment.sort_values("review_id", kind="stable").reset_index(drop=True)
    existing_duplicates = _truthy(sentiment["is_duplicate"])
    normalized = sentiment["clean_review"].map(_normalize_review)
    repeated = sentiment.assign(_normalized_review=normalized).duplicated(
        subset=["phone_id", "_normalized_review"], keep="first"
    ) & normalized.ne("")
    sentiment["is_duplicate"] = existing_duplicates | repeated
    duplicate_ids = set(sentiment.loc[sentiment["is_duplicate"], "review_id"].astype(str))

    clean["is_duplicate"] = clean["review_id"].astype(str).isin(duplicate_ids)
    aspects["is_duplicate"] = aspects["review_id"].astype(str).isin(duplicate_ids)

    usable_sentiment = sentiment.loc[~sentiment["is_duplicate"]].copy()
    usable_aspects = aspects.loc[~aspects["is_duplicate"]].copy()

    phone_summary = _summary(usable_sentiment, ["phone_id", "phone_name"])
    platform_summary = _summary(usable_sentiment, ["phone_id", "phone_name", "platform"])
    aspect_summary = _summary(usable_aspects, ["phone_id", "phone_name", "platform", "aspect"])

    _write(clean, REVIEW_CLEAN)
    _write(sentiment, REVIEW_SENTIMENT)
    _write(aspects, REVIEW_ASPECTS)
    _write(phone_summary, PROCESSED / "phone_summary.csv")
    _write(platform_summary, PROCESSED / "platform_summary.csv")
    _write(aspect_summary, PROCESSED / "aspect_summary.csv")

    print(f"Reviews: {len(sentiment)} total, {len(usable_sentiment)} usable, {len(duplicate_ids)} duplicates")
    print(f"Summaries: {len(phone_summary)} phones, {len(platform_summary)} platform rows, {len(aspect_summary)} aspect rows")


if __name__ == "__main__":
    main()
