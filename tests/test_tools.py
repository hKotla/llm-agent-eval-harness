"""The tools are deterministic. A failure here is a fixture bug, not a model."""

from support_agent.tools import default_registry
from support_agent.tools.bookings import lookup_booking
from support_agent.tools.faq import search_faq
from support_agent.tools.policies import get_policy


def test_lookup_is_case_insensitive() -> None:
    found = lookup_booking({"reference": "bk-1001"})
    assert found["found"] is True
    assert found["passenger"] == "Priya Shah"
    assert found["status"] == "confirmed"


def test_each_fixture_booking_has_a_distinct_status() -> None:
    statuses = {
        lookup_booking({"reference": reference})["status"]
        for reference in ("BK-1001", "BK-1002", "BK-1003")
    }
    assert statuses == {"confirmed", "cancelled", "pending"}


def test_unknown_booking() -> None:
    missing = lookup_booking({"reference": "BK-0000"})
    assert missing == {"found": False, "reference": "BK-0000"}


def test_cancellation_and_change_policies() -> None:
    cancellation = get_policy({"topic": "cancellation"})
    changes = get_policy({"topic": " Changes "})
    assert cancellation["found"] is True
    assert "£40" in cancellation["rule"]
    assert changes["found"] is True
    assert "7 days" in changes["rule"]


def test_unknown_policy_lists_the_known_topics() -> None:
    missing = get_policy({"topic": "pets"})
    assert missing["found"] is False
    assert missing["known_topics"] == ["baggage", "cancellation", "changes"]


def test_faq_contact_and_refund_timing() -> None:
    contact = search_faq({"query": "what is the support phone number?"})
    refunds = search_faq({"query": "how long do refunds take?"})
    assert contact["id"] == "contact"
    assert "7946" in contact["answer"]
    assert refunds["id"] == "refund-timing"
    assert "5 to 7" in refunds["answer"]


def test_faq_miss() -> None:
    missing = search_faq({"query": "zzzz"})
    assert missing["found"] is False


def test_registry_exposes_the_three_tools() -> None:
    names = [schema["function"]["name"] for schema in default_registry().schemas()]
    assert names == ["lookup_booking", "get_policy", "search_faq"]


def test_registry_reports_an_unknown_tool() -> None:
    output = default_registry().call("delete_booking", {})
    assert "unknown_tool" in output
