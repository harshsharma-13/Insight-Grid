"""Regression checks for the platform's shared intelligence and UI contracts."""

from __future__ import annotations

import json
import re
import sqlite3
import sys
import unicodedata
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from intelligence import IntelligenceEngine


def _normalize(value: object) -> str:
    text = unicodedata.normalize("NFKC", str(value or "")).casefold()
    return re.sub(r"\s+", " ", text).strip().strip('"“”')


def main() -> None:
    database = ROOT / "data" / "acip.db"
    with sqlite3.connect(database) as connection:
        connection.row_factory = sqlite3.Row
        usable = connection.execute("SELECT COUNT(*) FROM reviews WHERE is_duplicate = 0").fetchone()[0]
        total = connection.execute("SELECT COUNT(*) FROM reviews").fetchone()[0]
        index_names = {
            row[1] for row in connection.execute("PRAGMA index_list('review_sentiment')").fetchall()
        }
        rows = connection.execute(
            """
            SELECT r.phone_id, r.clean_review, rs.sentiment
            FROM reviews r
            JOIN review_sentiment rs ON rs.review_id = r.review_id
            WHERE COALESCE(rs.is_duplicate, r.is_duplicate) = 0
            """
        ).fetchall()

    assert total == 3031, f"Expected 3031 source reviews, found {total}"
    assert usable == len(rows), "SQLite usable-review flags and sentiment join disagree"
    assert "idx_review_sentiment_review_id" in index_names, "Review sentiment lookup index is missing"

    seen: set[tuple[str, str]] = set()
    for row in rows:
        key = (row["phone_id"], _normalize(row["clean_review"]))
        assert not key[1] or key not in seen, f"Repeated usable review remains for {row['phone_id']}"
        seen.add(key)

    reviews = IntelligenceEngine.reviews(limit=5000)
    signal_by_sentiment = {"positive": "positive", "neutral": "mixed", "negative": "risk"}
    assert len(reviews) == usable, "Engine review corpus does not match the database"
    for review in reviews:
        expected = signal_by_sentiment[str(review["sentiment"]).casefold()]
        assert review["signal"] == expected, f"Incorrect signal for {review['review_id']}"

    overview = IntelligenceEngine.overview()
    competitive = IntelligenceEngine.competitive()
    assert overview["metrics"]["usable_reviews"] == usable
    assert overview["metrics"]["brands"] == 14
    assert overview["metrics"]["positive_percent"] == competitive["market_average"]

    snapshot = json.loads((ROOT / "web" / "app" / "data" / "platform-data.json").read_text(encoding="utf-8"))
    exported_reviews = json.loads((ROOT / "web" / "public" / "data" / "reviews.json").read_text(encoding="utf-8"))
    phones = IntelligenceEngine.phones()
    assert snapshot["overview"]["metrics"]["usable_reviews"] == usable
    assert len(snapshot["phones"]) == len(phones), "Published phone snapshot is out of date"
    assert len(exported_reviews) == usable
    assert all("aspects" in review for review in exported_reviews)
    assert snapshot["phone_reviews"], "Product-level evidence excerpts are missing"
    assert all("urgency_score" in action for action in snapshot["actions"])

    copilot = (ROOT / "web" / "app" / "components" / "IntelligenceCopilot.tsx").read_text(encoding="utf-8")
    actions = (ROOT / "web" / "app" / "components" / "ActionCenter.tsx").read_text(encoding="utf-8")
    layout = (ROOT / "web" / "app" / "layout.tsx").read_text(encoding="utf-8")
    shell = (ROOT / "web" / "app" / "components" / "PlatformShell.tsx").read_text(encoding="utf-8")
    assert "rawData.phones.filter" in copilot
    assert "/reviews?q=${encodeURIComponent(action.aspect)}" in actions
    assert "Insight Grid · Consumer Intelligence" in layout
    assert 'url: "/og-v3.png"' in layout
    assert "Insight Grid intelligence system" in shell
    assert "Insight Grid copilot" in copilot

    print(
        f"Reliability checks passed: {total} source reviews, {usable} usable reviews, "
        f"{overview['metrics']['brands']} brands, {len(snapshot['phones'])} phones."
    )


if __name__ == "__main__":
    main()
