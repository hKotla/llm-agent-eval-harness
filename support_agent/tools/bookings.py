"""Booking lookup over a fixed table. No network."""

BOOKINGS: dict[str, dict] = {
    "BK-1001": {
        "reference": "BK-1001",
        "passenger": "Priya Shah",
        "origin": "London",
        "destination": "Lisbon",
        "status": "confirmed",
        "departure_date": "2026-12-03",
    },
    "BK-1002": {
        "reference": "BK-1002",
        "passenger": "Jonah Adeyemi",
        "origin": "Manchester",
        "destination": "Reykjavik",
        "status": "cancelled",
        "departure_date": "2026-11-02",
    },
    "BK-1003": {
        "reference": "BK-1003",
        "passenger": "Mei Chen",
        "origin": "Edinburgh",
        "destination": "Dublin",
        "status": "pending",
        "departure_date": "2027-01-15",
    },
}


def lookup_booking(arguments: dict) -> dict:
    reference = str(arguments.get("reference", "")).strip().upper()
    record = BOOKINGS.get(reference)
    if record is None:
        return {"found": False, "reference": reference}
    return {"found": True, **record}
