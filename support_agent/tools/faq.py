"""Keyword search over a three-entry FAQ. Overlap wins; ties keep list order."""

import re

FAQ: list[dict[str, str]] = [
    {
        "id": "hours",
        "question": "What are your opening hours?",
        "answer": "Support is open Monday to Friday, 08:00 to 18:00 UK time.",
    },
    {
        "id": "contact",
        "question": "How do I contact support?",
        "answer": "Email support@harborair.example or phone +44 20 7946 0991.",
    },
    {
        "id": "refund-timing",
        "question": "How long do refunds take?",
        "answer": (
            "Approved refunds take 5 to 7 business days to reach the original payment method."
        ),
    },
]

_STOPWORDS = {
    "a",
    "an",
    "the",
    "is",
    "are",
    "i",
    "do",
    "to",
    "of",
    "for",
    "my",
    "your",
    "me",
    "what",
    "how",
    "when",
    "where",
    "does",
    "can",
    "please",
}


def search_faq(arguments: dict) -> dict:
    query = str(arguments.get("query", "")).strip()
    query_tokens = _tokens(query)
    best: dict[str, str] | None = None
    best_score = 0
    for entry in FAQ:
        haystack = f"{entry['question']} {entry['answer']}"
        score = len(query_tokens & _tokens(haystack))
        if score > best_score:
            best = entry
            best_score = score
    if best is None:
        return {"found": False, "query": query}
    return {
        "found": True,
        "id": best["id"],
        "question": best["question"],
        "answer": best["answer"],
    }


def _tokens(text: str) -> set[str]:
    words = re.findall(r"[a-z0-9]+", text.lower())
    return {word for word in words if word not in _STOPWORDS and len(word) > 1}
