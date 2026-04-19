"""Tests for the intent-graph router."""

import pytest
from pydantic import ValidationError

from agent_router import ActionType, IntentRouter, ResourceType, RoutingIntent

# --- RoutingIntent validation ----


def test_intent_accepts_valid_action_and_resource():
    intent = RoutingIntent(action="find", resource="sales_report")
    assert intent.action == "find"
    assert intent.resource == "sales_report"
    # parameters defaults to an empty dict
    assert intent.parameters == {}


def test_intent_parameters_default_is_independent():
    """default_factory=dict must give each instance its own dict."""
    a = RoutingIntent(action="find", resource="sales_report")
    b = RoutingIntent(action="find", resource="sales_report")
    a.parameters["x"] = 1
    assert b.parameters == {}  # not shared!


def test_intent_rejects_unknown_action():
    with pytest.raises(ValidationError):
        RoutingIntent(action="delete", resource="sales_report")  # type: ignore[arg-type]


def test_intent_rejects_unknown_resource():
    with pytest.raises(ValidationError):
        RoutingIntent(action="find", resource="invoices")  # type: ignore[arg-type]


# ---- IntentRouter behavior ---


def test_router_dispatches_known_capability():
    """Happy path: a known (action, resource) pair is dispatched."""
    router = IntentRouter()
    intent = RoutingIntent(
        action="find", resource="sales_report", parameters={"q": "Q1"}
    )
    assert router.route_request(intent) == "Success"


def test_router_blocks_unknown_capability():
    """No matching edge in the graph -> request is blocked with an error string."""
    router = IntentRouter()
    # ("analyze", "server_log") is not in the default graph.
    intent = RoutingIntent(action="analyze", resource="server_log")
    result = router.route_request(intent)
    assert result.startswith("Error:")
    assert "analyze" in result
    assert "server_log" in result


def test_router_prints_breadcrumb(capsys):
    """dispatch_to_agent should print the routing decision."""
    router = IntentRouter()
    router.route_request(
        RoutingIntent(action="find", resource="document", parameters={"id": 7})
    )
    captured = capsys.readouterr()
    assert "Routing to ComplianceAgent" in captured.out
    assert "{'id': 7}" in captured.out


def test_dispatch_can_be_overridden():
    """Subclasses can swap the dispatch hook without touching route_request."""

    class RecordingRouter(IntentRouter):
        def __init__(self):
            super().__init__()
            self.calls: list[tuple[str, dict]] = []

        def dispatch_to_agent(self, agent_name, params):
            self.calls.append((agent_name, params))
            return f"handled-by-{agent_name}"

    router = RecordingRouter()
    out = router.route_request(
        RoutingIntent(action="create", resource="server_log", parameters={"lvl": "INFO"})
    )
    assert out == "handled-by-DevOpsAgent"
    assert router.calls == [("DevOpsAgent", {"lvl": "INFO"})]
