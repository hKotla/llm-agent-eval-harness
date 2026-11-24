"""Policy text for the three topics Harbor Air will talk about."""

POLICIES: dict[str, str] = {
    "cancellation": (
        "You can cancel for free until 24 hours before departure. "
        "After that the fee is £40. A non-refundable fare cannot be cancelled."
    ),
    "baggage": (
        "One cabin bag up to 8kg is included. "
        "A checked bag is £25 and must be 23kg or under."
    ),
    "changes": (
        "Date changes are free more than 7 days before departure. "
        "Inside 7 days the fee is £25."
    ),
}


def get_policy(arguments: dict) -> dict:
    topic = str(arguments.get("topic", "")).strip().lower()
    rule = POLICIES.get(topic)
    if rule is None:
        return {
            "found": False,
            "topic": topic,
            "known_topics": sorted(POLICIES),
        }
    return {"found": True, "topic": topic, "rule": rule}
