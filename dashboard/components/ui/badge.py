def verdict_badge(verdict):
    verdict = str(verdict)

    if "Highly" in verdict or "Positive" in verdict:
        return f"🟢 {verdict}"

    if "Mixed" in verdict:
        return f"🟡 {verdict}"

    if "Not" in verdict:
        return f"🔴 {verdict}"

    if "Limited" in verdict:
        return f"⚪ {verdict}"

    return f"⚪ {verdict}"