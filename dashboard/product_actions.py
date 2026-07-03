import pandas as pd

from consumer_intelligence import (
    get_consumer_dataset,
    pain_point_intelligence,
    PAIN_POINT_KEYWORDS,
)
from review_explorer import get_review_dataset


ACTION_PRIORITY = {
    "High": "Critical",
    "Medium": "Important",
    "Low": "Monitor",
}


OWNER_MAP = {
    "Software": "Product + Engineering",
    "Performance": "Product + Engineering",
    "Heating": "Product + QA",
    "Charging": "Product + Accessories",
    "Battery Drain": "Product + Engineering",
    "Camera": "Camera + Product",
    "Connectivity": "Network QA",
    "Display": "Product + QA",
    "Build Quality": "Product + Design",
}


IMPACT_MAP = {
    "Software": "Improve reliability perception and reduce repeat complaints.",
    "Performance": "Improve everyday usability and reduce frustration in reviews.",
    "Heating": "Reduce negative sentiment around gaming, charging and heavy usage.",
    "Charging": "Improve trust in charging claims and accessory experience.",
    "Battery Drain": "Improve endurance perception and reduce support complaints.",
    "Camera": "Improve social-use satisfaction and marketing credibility.",
    "Connectivity": "Improve call, network and 5G experience confidence.",
    "Display": "Improve viewing and touch experience satisfaction.",
    "Build Quality": "Improve durability and premium-feel perception.",
}


def _review_evidence(issue, limit=3):
    reviews = get_review_dataset()
    keywords = PAIN_POINT_KEYWORDS.get(issue, [])

    if reviews.empty or not keywords:
        return []

    issue_negative_terms = {
        "Software": ["bug", "bugs", "glitch", "software issue", "update issue", "ui issue", "os issue", "software problem", "after update"],
        "Performance": ["lag", "slow", "hang", "stutter", "performance issue", "not smooth"],
        "Heating": ["heating", "heat", "warm", "thermal"],
        "Charging": ["slow charging", "charging issue", "charger issue", "not charging", "charge problem"],
        "Battery Drain": ["battery drain", "drains", "battery issue", "poor backup", "backup issue"],
        "Camera": ["camera issue", "poor camera", "bad camera", "blur", "low light", "photo quality"],
        "Connectivity": ["network issue", "signal issue", "call issue", "5g issue", "wifi issue"],
        "Display": ["display issue", "screen issue", "brightness issue", "touch issue"],
        "Build Quality": ["build issue", "quality issue", "body issue", "poor build", "cheap quality"],
    }

    required_terms = issue_negative_terms.get(issue, keywords)

    negative_words = [
        "not", "poor", "bad", "issue", "problem", "worst", "slow",
        "lag", "hang", "heating", "drain", "bug", "glitch",
        "disappointed", "average", "doesn't", "dont", "don't",
        "fails", "weak", "mark", "complaint"
    ]

    def is_relevant_negative_review(text):
        text = str(text).lower()

        has_issue_term = any(term in text for term in required_terms)
        has_negative_signal = any(word in text for word in negative_words)

        return has_issue_term and has_negative_signal

    matched = reviews[
        reviews["search_text"].apply(is_relevant_negative_review)
    ]

    evidence = []

    for _, row in matched.head(limit).iterrows():
        text = row["review_text"] if row["review_text"] else row["clean_review"]

        evidence.append({
            "phone_name": row["phone_name"],
            "brand": row["brand"],
            "platform": row["platform"],
            "review": text,
        })

    return evidence


def get_action_dataset():
    consumer_df = get_consumer_dataset()
    issues = pain_point_intelligence(consumer_df)

    if issues.empty:
        return pd.DataFrame()

    rows = []

    for _, row in issues.iterrows():
        issue = row["issue"]
        severity = row["severity"]

        rows.append({
            "issue": issue,
            "priority": ACTION_PRIORITY.get(severity, "Monitor"),
            "severity": severity,
            "mentions": row["mentions"],
            "phones": row["phones"],
            "brands": row["brands"],
            "owner": OWNER_MAP.get(issue, "Product Team"),
            "affected_brands": row.get("affected_brands", "Not available"),
            "example_phones": row["example_phones"],
            "recommended_action": row["recommendation"],
            "business_impact": IMPACT_MAP.get(
                issue,
                "Improve consumer satisfaction and reduce negative feedback.",
            ),
            "evidence": _review_evidence(issue),
        })

    return pd.DataFrame(rows).sort_values(
        ["mentions", "phones"],
        ascending=False,
    )


def get_action_summary(actions_df):
    if actions_df.empty:
        return "No major product actions detected yet."

    critical = actions_df[actions_df["priority"] == "Critical"]
    top = actions_df.iloc[0]

    return (
        f"The highest-priority issue is **{top['issue']}**, with around "
        f"**{top['mentions']} estimated negative mentions** across "
        f"**{top['phones']} phones**. The recommended owner is "
        f"**{top['owner']}**. "
        f"There are **{len(critical)} critical issues** requiring immediate attention."
    )