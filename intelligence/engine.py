from __future__ import annotations

import math
import re
from collections import defaultdict
from functools import lru_cache
from typing import Any

from .db import fetch_all, fetch_one, scalar
from .catalog import apply_verified_specs, load_verified_catalog
from .taxonomy import (
    ACTION_OWNERS,
    ACTION_RECOMMENDATIONS,
    USE_CASE_ASPECTS,
    brand_query_keys,
    normalize_brand,
    segment_label,
)


def _number(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _price(value: Any) -> float | None:
    match = re.search(r"\d[\d,]*", str(value or ""))
    return float(match.group(0).replace(",", "")) if match else None


def _items(value: Any) -> list[str]:
    return [item.strip() for item in re.split(r"[;|]", str(value or "")) if item.strip()]


def _round(value: Any, digits: int = 1) -> float:
    return round(_number(value), digits)


def _evidence_score(review_count: Any, confidence: Any = 0) -> float:
    volume = min(1.0, math.log1p(max(_number(review_count), 0)) / math.log(181))
    model_confidence = max(0.0, min(_number(confidence, 0.75), 1.0))
    return round((volume * 0.78 + model_confidence * 0.22) * 100, 1)


class IntelligenceEngine:
    """Single source of truth for API, exports and future model pipelines."""

    @staticmethod
    @lru_cache(maxsize=1)
    def overview() -> dict[str, Any]:
        phone_count = int(scalar("SELECT COUNT(*) FROM phones"))
        review_count = int(scalar("SELECT COUNT(*) FROM reviews"))
        usable_reviews = int(scalar("SELECT COUNT(*) FROM reviews WHERE is_duplicate = 0"))
        aspect_count = int(scalar("SELECT COUNT(*) FROM aspect_summary"))
        competitive = IntelligenceEngine.competitive()
        average_positive = competitive["market_average"]

        aspects = fetch_all(
            """
            SELECT aspect,
                   SUM(positive_count) positive,
                   SUM(negative_count) negative,
                   SUM(review_count) evidence
            FROM aspect_summary
            GROUP BY aspect
            ORDER BY evidence DESC
            """
        )
        strongest = max(aspects, key=lambda row: _number(row["positive"])) if aspects else {}
        friction = max(aspects, key=lambda row: _number(row["negative"])) if aspects else {}
        brands = competitive["brands"]
        brand_count = len(brands)
        leader = brands[0] if brands else {}

        return {
            "metrics": {
                "phones": phone_count,
                "reviews": review_count,
                "usable_reviews": usable_reviews,
                "brands": brand_count,
                "catalog_brands": len({phone["brand"] for phone in IntelligenceEngine.phones()}),
                "aspects": aspect_count,
                "positive_percent": average_positive,
            },
            "signals": {
                "strongest_aspect": strongest.get("aspect", "Unavailable"),
                "strongest_mentions": int(_number(strongest.get("positive"))),
                "primary_friction": friction.get("aspect", "Unavailable"),
                "friction_mentions": int(_number(friction.get("negative"))),
                "sentiment_leader": leader.get("brand", "Unavailable"),
                "leader_positive": leader.get("positive_percent", 0),
            },
            "brief": (
                f"{strongest.get('aspect', 'Customer experience')} is the clearest advocacy signal, "
                f"while {friction.get('aspect', 'product consistency')} generates the largest volume of negative evidence. "
                "The immediate opportunity is to connect market-level movement to the products and reviews driving it."
            ),
        }

    @staticmethod
    @lru_cache(maxsize=1)
    def phones() -> list[dict[str, Any]]:
        rows = fetch_all(
            """
            SELECT p.phone_id, p.phone_name,
                   s.brand, s.processor, s.ram, s.storage, s.battery, s.charging,
                   s.display, s.refresh_rate, s.rear_camera, s.front_camera,
                   s.image_filename, s.image_local_path,
                   pi.price_segment, pi.launch_price, pi.amazon_price, pi.flipkart_price,
                   pi.amazon_rating, pi.flipkart_rating,
                   ps.review_count, ps.positive_percent, ps.negative_percent, ps.avg_confidence,
                   ai.consumer_verdict, ai.insight_confidence, ai.top_strengths,
                   ai.top_pain_points, ai.executive_summary, ai.recommendation
            FROM phones p
            LEFT JOIN phones_specifications s ON s.phone_id = p.phone_id
            LEFT JOIN phones_product_intelligence pi ON pi.phone_id = p.phone_id
            LEFT JOIN phone_summary ps ON ps.phone_id = p.phone_id
            LEFT JOIN phone_ai_insights ai ON ai.phone_id = p.phone_id
            ORDER BY COALESCE(ps.positive_percent, 0) DESC, COALESCE(ps.review_count, 0) DESC
            """
        )
        catalog = load_verified_catalog()
        existing_ids = {row["phone_id"] for row in rows}
        for phone_id, entry in catalog["phones"].items():
            if phone_id in existing_ids:
                continue
            rows.append({
                "phone_id": phone_id,
                "phone_name": entry["phone_name"],
                "brand": entry["brand"],
                "processor": None, "ram": None, "storage": None, "battery": None,
                "charging": None, "display": None, "refresh_rate": None,
                "rear_camera": None, "front_camera": None, "image_filename": entry.get("image_filename"),
                "image_local_path": entry.get("image_local_path"), "price_segment": None, "launch_price": entry.get("launch_price"),
                "amazon_price": entry.get("amazon_price"), "flipkart_price": entry.get("flipkart_price"), "amazon_rating": None,
                "flipkart_rating": None, "review_count": 0, "positive_percent": None,
                "negative_percent": None, "avg_confidence": None, "consumer_verdict": None,
                "insight_confidence": None, "top_strengths": None, "top_pain_points": None,
                "executive_summary": None, "recommendation": None,
            })
        for row in rows:
            row["brand"] = normalize_brand(row.get("brand"))
            row["segment_label"] = segment_label(row.get("price_segment"))
            # Launch price is a separate historical fact, never a marketplace offer.
            row["best_price"] = min(
                [price for price in [_price(row.get("amazon_price")), _price(row.get("flipkart_price"))] if price is not None],
                default=None,
            )
            row["positive_percent"] = _round(row.get("positive_percent"))
            row["negative_percent"] = _round(row.get("negative_percent"))
            row["review_count"] = int(_number(row.get("review_count")))
            row["evidence_score"] = _evidence_score(row["review_count"], row.get("avg_confidence"))
            row["strengths"] = _items(row.get("top_strengths"))
            row["pain_points"] = _items(row.get("top_pain_points"))
            filename = row.get("image_filename") or str(row.get("image_local_path") or "").replace("\\", "/").split("/")[-1]
            row["image_url"] = f"/phone-images/{filename}" if filename else None
            apply_verified_specs(row, catalog)
        return rows

    @staticmethod
    def phone(phone_id: str) -> dict[str, Any] | None:
        phone = next((item.copy() for item in IntelligenceEngine.phones() if item["phone_id"] == phone_id), None)
        if not phone:
            return None
        phone["platforms"] = fetch_all(
            "SELECT platform, review_count, positive_percent, neutral_percent, negative_percent, avg_confidence FROM platform_summary WHERE phone_id = ? ORDER BY platform",
            [phone_id],
        )
        phone["aspects"] = fetch_all(
            """
            SELECT aspect, SUM(review_count) review_count,
                   ROUND(SUM(positive_count) * 100.0 / NULLIF(SUM(review_count), 0), 1) positive_percent,
                   ROUND(SUM(negative_count) * 100.0 / NULLIF(SUM(review_count), 0), 1) negative_percent,
                   AVG(avg_confidence) avg_confidence
            FROM aspect_summary WHERE phone_id = ? GROUP BY aspect ORDER BY review_count DESC
            """,
            [phone_id],
        )
        return phone

    @staticmethod
    def reviews(limit: int | None = 40, brand: str | None = None, platform: str | None = None, query: str | None = None) -> list[dict[str, Any]]:
        where = ["COALESCE(rs.is_duplicate, r.is_duplicate) = 0"]
        params: list[Any] = []
        if brand:
            brand_keys = brand_query_keys(brand)
            where.append(f"LOWER(TRIM(s.brand)) IN ({','.join('?' for _ in brand_keys)})")
            params.extend(brand_keys)
        if platform:
            where.append("r.platform = ?")
            params.append(platform)
        if query:
            where.append("LOWER(r.clean_review) LIKE ?")
            params.append(f"%{query.lower()}%")
        params.append(-1 if limit is None else max(1, min(limit, 5000)))
        rows = fetch_all(
            f"""
            SELECT r.review_id, r.phone_id, r.phone_name, s.brand, r.platform,
                   r.review_text, r.word_count, r.quality_flag,
                   rs.sentiment, rs.sentiment_confidence,
                   ra.aspects,
                   ps.positive_percent phone_positive, ps.negative_percent phone_negative
            FROM reviews r
            LEFT JOIN phones_specifications s ON s.phone_id = r.phone_id
            LEFT JOIN review_sentiment rs ON rs.review_id = r.review_id
            LEFT JOIN (
                SELECT review_id, GROUP_CONCAT(DISTINCT aspect) aspects
                FROM reviews_aspects
                WHERE is_duplicate = 0
                GROUP BY review_id
            ) ra ON ra.review_id = r.review_id
            LEFT JOIN phone_summary ps ON ps.phone_id = r.phone_id
            WHERE {' AND '.join(where)}
            ORDER BY r.word_count DESC, r.review_id
            LIMIT ?
            """,
            params,
        )
        for row in rows:
            row["brand"] = normalize_brand(row.get("brand"))
            sentiment = str(row.get("sentiment") or "Neutral").casefold()
            row["signal"] = "positive" if sentiment == "positive" else "risk" if sentiment == "negative" else "mixed"
            row["aspects"] = [item for item in str(row.get("aspects") or "").split(",") if item]
        return rows

    @staticmethod
    def finder(use_case: str = "overall", budget: float | None = None, limit: int = 8) -> list[dict[str, Any]]:
        use_case = use_case if use_case in USE_CASE_ASPECTS else "overall"
        aspects_by_phone: dict[str, dict[str, dict[str, Any]]] = defaultdict(dict)
        for row in fetch_all(
            """
            SELECT phone_id, aspect, SUM(review_count) review_count,
                   SUM(positive_count) positive_count, SUM(negative_count) negative_count
            FROM aspect_summary GROUP BY phone_id, aspect
            """
        ):
            aspects_by_phone[row["phone_id"]][row["aspect"]] = row

        results = []
        for phone in IntelligenceEngine.phones():
            if not phone["review_count"]:
                continue
            if budget is not None and (phone["best_price"] is None or phone["best_price"] > budget):
                continue
            relevant = [aspects_by_phone[phone["phone_id"]].get(name) for name in USE_CASE_ASPECTS[use_case]]
            relevant = [row for row in relevant if row and _number(row["review_count"]) > 0]
            if relevant:
                positive = sum(_number(row["positive_count"]) for row in relevant)
                negative = sum(_number(row["negative_count"]) for row in relevant)
                total = sum(_number(row["review_count"]) for row in relevant)
                aspect_fit = max(0.0, min(100.0, positive * 100 / total))
                aspect_risk = max(0.0, min(100.0, negative * 100 / total))
            else:
                aspect_fit = phone["positive_percent"]
                aspect_risk = phone["negative_percent"]
            sentiment = phone["positive_percent"]
            safety = 100 - max(phone["negative_percent"], aspect_risk)
            evidence = phone["evidence_score"]
            overall = sentiment * 0.38 + aspect_fit * 0.32 + safety * 0.16 + evidence * 0.14
            results.append({
                **phone,
                "score": {
                    "overall": round(overall, 1),
                    "sentiment": round(sentiment, 1),
                    "aspect_fit": round(aspect_fit, 1),
                    "complaint_safety": round(safety, 1),
                    "evidence": round(evidence, 1),
                },
                "reason": f"Strongest fit comes from {', '.join(USE_CASE_ASPECTS[use_case][:2]).lower()} evidence with {phone['review_count']} reviews behind the signal.",
                "evidence_label": "High evidence" if evidence >= 75 else "Moderate evidence" if evidence >= 50 else "Limited evidence",
            })
        return sorted(results, key=lambda item: (item["score"]["overall"], item["review_count"]), reverse=True)[:limit]

    @staticmethod
    def compare(left_id: str, right_id: str) -> dict[str, Any] | None:
        left = IntelligenceEngine.phone(left_id)
        right = IntelligenceEngine.phone(right_id)
        if not left or not right:
            return None
        left_score = IntelligenceEngine.finder("overall", limit=len(IntelligenceEngine.phones()))
        score_map = {row["phone_id"]: row["score"] for row in left_score}
        comparable = left_id in score_map and right_id in score_map and left_id != right_id
        tied = comparable and score_map[left_id]["overall"] == score_map[right_id]["overall"]
        winner = (left if score_map[left_id]["overall"] > score_map[right_id]["overall"] else right) if comparable and not tied else None
        return {
            "left": left,
            "right": right,
            "scores": {left_id: score_map.get(left_id), right_id: score_map.get(right_id)},
            "winner_id": winner["phone_id"] if winner else None,
            "verdict": f"{winner['phone_name']} has the higher review-derived score." if winner else "Review scores are tied." if tied else "Specification-only comparison: insufficient review evidence for a winner.",
        }

    @staticmethod
    @lru_cache(maxsize=1)
    def competitive() -> dict[str, Any]:
        rows = fetch_all(
            """
            SELECT s.brand, COUNT(DISTINCT ps.phone_id) phones,
                   SUM(ps.review_count) reviews,
                   SUM(ps.positive_count) positive_count,
                   SUM(ps.negative_count) negative_count
            FROM phone_summary ps
            JOIN phones_specifications s ON s.phone_id = ps.phone_id
            GROUP BY s.brand
            """
        )
        brand_totals: dict[str, dict[str, float]] = defaultdict(lambda: {
            "phones": 0, "reviews": 0, "positive_count": 0, "negative_count": 0,
        })
        for row in rows:
            brand = normalize_brand(row.get("brand"))
            brand_totals[brand]["phones"] += _number(row["phones"])
            brand_totals[brand]["reviews"] += _number(row["reviews"])
            brand_totals[brand]["positive_count"] += _number(row["positive_count"])
            brand_totals[brand]["negative_count"] += _number(row["negative_count"])
        brands = []
        for brand, totals in brand_totals.items():
            reviews = max(totals["reviews"], 1)
            brands.append({
                "brand": brand,
                "phones": int(totals["phones"]),
                "reviews": int(reviews),
                "positive_percent": round(totals["positive_count"] * 100 / reviews, 1),
                "negative_percent": round(totals["negative_count"] * 100 / reviews, 1),
                "evidence_score": _evidence_score(reviews),
            })
        brands.sort(key=lambda row: (row["positive_percent"], row["reviews"]), reverse=True)

        aspects = fetch_all(
            """
            SELECT s.brand, a.aspect, SUM(a.review_count) evidence,
                   SUM(a.positive_count) positive, SUM(a.negative_count) negative
            FROM aspect_summary a JOIN phones_specifications s ON s.phone_id = a.phone_id
            GROUP BY s.brand, a.aspect
            """
        )
        aspect_totals: dict[tuple[str, str], dict[str, float]] = defaultdict(lambda: {
            "evidence": 0, "positive": 0, "negative": 0,
        })
        for row in aspects:
            key = (normalize_brand(row.get("brand")), row["aspect"])
            aspect_totals[key]["evidence"] += _number(row["evidence"])
            aspect_totals[key]["positive"] += _number(row["positive"])
            aspect_totals[key]["negative"] += _number(row["negative"])
        grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for (brand, aspect), totals in aspect_totals.items():
            grouped[brand].append({"aspect": aspect, **totals})
        for brand in brands:
            rows_for_brand = grouped.get(brand["brand"], [])
            brand["top_strength"] = max(rows_for_brand, key=lambda row: _number(row["positive"]), default={}).get("aspect", "Unavailable")
            brand["top_concern"] = max(rows_for_brand, key=lambda row: _number(row["negative"]), default={}).get("aspect", "Unavailable")
        total_reviews = sum(row["reviews"] for row in brands)
        market_average = sum(row["positive_percent"] * row["reviews"] for row in brands) / max(total_reviews, 1)
        return {"brands": brands, "market_average": round(market_average, 1)}

    @staticmethod
    @lru_cache(maxsize=1)
    def deep_intelligence() -> dict[str, Any]:
        """Build defensible market, brand, segment and product-level intelligence."""
        competitive = IntelligenceEngine.competitive()
        market_aspect_rows = fetch_all(
            """
            SELECT aspect, SUM(review_count) evidence,
                   SUM(positive_count) positive, SUM(negative_count) negative
            FROM aspect_summary
            GROUP BY aspect
            ORDER BY evidence DESC
            """
        )
        aspect_landscape = []
        market_aspect_map: dict[str, dict[str, Any]] = {}
        for row in market_aspect_rows:
            evidence = max(_number(row.get("evidence")), 1)
            item = {
                "aspect": row["aspect"],
                "evidence": int(evidence),
                "positive_mentions": int(_number(row.get("positive"))),
                "negative_mentions": int(_number(row.get("negative"))),
                "positive_percent": round(_number(row.get("positive")) * 100 / evidence, 1),
                "negative_percent": round(_number(row.get("negative")) * 100 / evidence, 1),
            }
            item["net_signal"] = round(item["positive_percent"] - item["negative_percent"], 1)
            aspect_landscape.append(item)
            market_aspect_map[item["aspect"]] = item

        brand_aspect_rows = fetch_all(
            """
            SELECT s.brand, a.aspect, SUM(a.review_count) evidence,
                   SUM(a.positive_count) positive, SUM(a.negative_count) negative
            FROM aspect_summary a
            JOIN phones_specifications s ON s.phone_id = a.phone_id
            GROUP BY s.brand, a.aspect
            """
        )
        brand_aspect_totals: dict[tuple[str, str], dict[str, float]] = defaultdict(lambda: {
            "evidence": 0, "positive": 0, "negative": 0,
        })
        for row in brand_aspect_rows:
            brand = normalize_brand(row.get("brand"))
            key = (brand, row["aspect"])
            brand_aspect_totals[key]["evidence"] += _number(row.get("evidence"))
            brand_aspect_totals[key]["positive"] += _number(row.get("positive"))
            brand_aspect_totals[key]["negative"] += _number(row.get("negative"))
        brand_aspects: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for (brand, aspect), totals in brand_aspect_totals.items():
            evidence = max(totals["evidence"], 1)
            positive_percent = round(totals["positive"] * 100 / evidence, 1)
            negative_percent = round(totals["negative"] * 100 / evidence, 1)
            market_positive = market_aspect_map.get(aspect, {}).get("positive_percent", 0)
            brand_aspects[brand].append({
                "aspect": aspect,
                "evidence": int(evidence),
                "positive_percent": positive_percent,
                "negative_percent": negative_percent,
                "market_gap": round(positive_percent - _number(market_positive), 1),
            })

        brand_profiles = []
        for brand in competitive["brands"]:
            profile = dict(brand)
            profile["market_gap"] = round(profile["positive_percent"] - competitive["market_average"], 1)
            aspects = sorted(brand_aspects.get(profile["brand"], []), key=lambda item: item["evidence"], reverse=True)
            profile["aspects"] = aspects
            eligible = [item for item in aspects if item["evidence"] >= 8]
            profile["distinctive_advantage"] = max(eligible, key=lambda item: item["market_gap"], default={}).get("aspect", "Evidence developing")
            profile["largest_gap"] = min(eligible, key=lambda item: item["market_gap"], default={}).get("aspect", "Evidence developing")
            brand_profiles.append(profile)

        segment_rows = fetch_all(
            """
            SELECT pi.price_segment, s.brand, COUNT(DISTINCT ps.phone_id) phones,
                   SUM(ps.review_count) reviews, SUM(ps.positive_count) positive,
                   SUM(ps.negative_count) negative
            FROM phone_summary ps
            JOIN phones_specifications s ON s.phone_id = ps.phone_id
            LEFT JOIN phones_product_intelligence pi ON pi.phone_id = ps.phone_id
            GROUP BY pi.price_segment, s.brand
            """
        )
        segment_brand_totals: dict[tuple[str, str], dict[str, float]] = defaultdict(lambda: {
            "phones": 0, "reviews": 0, "positive": 0, "negative": 0,
        })
        for row in segment_rows:
            segment = row.get("price_segment") or "Unclassified"
            key = (segment, normalize_brand(row.get("brand")))
            segment_brand_totals[key]["phones"] += _number(row.get("phones"))
            segment_brand_totals[key]["reviews"] += _number(row.get("reviews"))
            segment_brand_totals[key]["positive"] += _number(row.get("positive"))
            segment_brand_totals[key]["negative"] += _number(row.get("negative"))
        segment_groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for (segment, brand), totals in segment_brand_totals.items():
            reviews = max(totals["reviews"], 1)
            segment_groups[segment].append({
                "brand": brand,
                "phones": int(totals["phones"]),
                "reviews": int(reviews),
                "positive_percent": round(totals["positive"] * 100 / reviews, 1),
                "negative_percent": round(totals["negative"] * 100 / reviews, 1),
            })
        segments = []
        for segment, brands in segment_groups.items():
            total_reviews = sum(item["reviews"] for item in brands)
            weighted_positive = sum(item["positive_percent"] * item["reviews"] for item in brands) / max(total_reviews, 1)
            weighted_negative = sum(item["negative_percent"] * item["reviews"] for item in brands) / max(total_reviews, 1)
            ranked = sorted(brands, key=lambda item: (item["positive_percent"], item["reviews"]), reverse=True)
            segments.append({
                "segment": segment,
                "segment_label": segment_label(segment),
                "phones": sum(item["phones"] for item in brands),
                "reviews": total_reviews,
                "positive_percent": round(weighted_positive, 1),
                "negative_percent": round(weighted_negative, 1),
                "leader": ranked[0] if ranked else None,
                "brands": ranked,
            })
        segments.sort(key=lambda item: item["reviews"], reverse=True)

        phones = [phone for phone in IntelligenceEngine.phones() if phone["review_count"] > 0]
        opportunity_products = []
        for phone in phones:
            item = {
                "phone_id": phone["phone_id"], "phone_name": phone["phone_name"], "brand": phone["brand"],
                "segment_label": phone["segment_label"], "best_price": phone["best_price"],
                "reviews": phone["review_count"], "positive_percent": phone["positive_percent"],
                "negative_percent": phone["negative_percent"], "evidence_score": phone["evidence_score"],
                "image_url": phone["image_url"], "primary_issue": (phone["pain_points"] or ["Review the negative evidence cluster."])[0],
            }
            item["opportunity_index"] = round(item["negative_percent"] * item["evidence_score"] / 100, 1)
            opportunity_products.append(item)
        opportunity_products.sort(key=lambda item: (item["opportunity_index"], item["reviews"]), reverse=True)

        advocacy_products = sorted(
            [{
                "phone_id": phone["phone_id"], "phone_name": phone["phone_name"], "brand": phone["brand"],
                "positive_percent": phone["positive_percent"], "reviews": phone["review_count"],
                "evidence_score": phone["evidence_score"], "image_url": phone["image_url"],
                "strength": (phone["strengths"] or ["Positive customer reception."])[0],
                "advocacy_index": round(phone["positive_percent"] * phone["evidence_score"] / 100, 1),
            } for phone in phones],
            key=lambda item: (item["advocacy_index"], item["reviews"]), reverse=True,
        )

        strongest_aspect = max(aspect_landscape, key=lambda item: item["positive_mentions"], default={})
        systemic_risk = max(aspect_landscape, key=lambda item: item["negative_mentions"], default={})
        advantages = [
            {"brand": profile["brand"], **aspect}
            for profile in brand_profiles for aspect in profile["aspects"]
            if aspect["evidence"] >= 12
        ]
        brand_advantage = max(advantages, key=lambda item: item["market_gap"], default={})
        return {
            "market_average": competitive["market_average"],
            "aspect_landscape": aspect_landscape,
            "brand_profiles": brand_profiles,
            "segments": segments,
            "opportunity_products": opportunity_products[:10],
            "advocacy_products": advocacy_products[:10],
            "strategic_signals": {
                "strongest_aspect": strongest_aspect,
                "systemic_risk": systemic_risk,
                "brand_advantage": brand_advantage,
                "highest_risk_product": opportunity_products[0] if opportunity_products else None,
            },
        }

    @staticmethod
    @lru_cache(maxsize=1)
    def actions() -> list[dict[str, Any]]:
        rows = fetch_all(
            """
            SELECT aspect, SUM(negative_count) mentions,
                   COUNT(DISTINCT phone_id) phones, SUM(review_count) evidence
            FROM aspect_summary GROUP BY aspect ORDER BY mentions DESC
            """
        )
        actions = []
        max_mentions = max((int(_number(row["mentions"])) for row in rows), default=1)
        phone_count = max(int(_number(scalar("SELECT COUNT(*) FROM phones"))), 1)
        for index, row in enumerate(rows, start=1):
            mentions = int(_number(row["mentions"]))
            priority = "Critical" if mentions >= 250 else "Important" if mentions >= 100 else "Monitor"
            aspect = row["aspect"]
            affected_phones = int(_number(row["phones"]))
            evidence = int(_number(row["evidence"]))
            impact_score = round(mentions * 100 / max_mentions, 1)
            reach_score = round(affected_phones * 100 / phone_count, 1)
            confidence_score = _evidence_score(evidence)
            actions.append({
                "id": f"ACT-{index:02d}",
                "aspect": aspect,
                "priority": priority,
                "mentions": mentions,
                "phones": affected_phones,
                "evidence": evidence,
                "impact_score": impact_score,
                "reach_score": reach_score,
                "confidence_score": confidence_score,
                "urgency_score": round(impact_score * 0.6 + reach_score * 0.4, 1),
                "owner": ACTION_OWNERS.get(aspect, "Product experience"),
                "recommendation": ACTION_RECOMMENDATIONS.get(aspect, f"Investigate the recurring {aspect.lower()} evidence and validate the largest product clusters."),
            })
        return actions
