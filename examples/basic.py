"""End-to-end example of the intent-graph router.

Demonstrates:
  * constructing typed `RoutingIntent` objects
  * routing known capabilities (dispatched to an agent)
  * routing unknown capabilities (blocked with an error string)
  * subclassing `IntentRouter` to plug in real dispatch logic
"""

from __future__ import annotations

from typing import Any

from agent_router import IntentRouter, RoutingIntent

# ---------------------------------------------------------------------------
# A custom router that records every dispatch instead of just printing.
# ---------------------------------------------------------------------------
class RecordingRouter(IntentRouter):
    """Same graph as the default, but tracks what got dispatched where."""

    def __init__(self) -> None:
        super().__init__()
        self.calls: list[tuple[str, dict[str, Any]]] = []

    def dispatch_to_agent(self, agent_name: str, params: dict[str, Any]) -> str:
        # Fall back to the parent's behaviour (which prints a breadcrumb)...
        result = super().dispatch_to_agent(agent_name, params)
        # ...then record the call so callers can inspect it afterwards.
        self.calls.append((agent_name, params))
        return result


def main() -> None:
    router = RecordingRouter()

    # A mix of valid + invalid intents to exercise both code paths.
    intents: list[RoutingIntent] = [
        RoutingIntent(
            action="find", resource="sales_report", parameters={"quarter": "Q1"}
        ),
        RoutingIntent(
            action="analyze", resource="sales_report", parameters={"metric": "ARR"}
        ),
        RoutingIntent(
            action="find", resource="document", parameters={"id": 42}
        ),
        RoutingIntent(
            action="create", resource="server_log", parameters={"level": "INFO"}
        ),
        # Not registered in the capability graph -> should be blocked.
        RoutingIntent(action="analyze", resource="server_log"),
    ]

    print("=== Routing ===")
    for intent in intents:
        result = router.route_request(intent)
        print(f"{intent.action:>8} {intent.resource:<14} -> {result}")

    print("\n=== Dispatch log ===")
    for agent, params in router.calls:
        print(f"  {agent}({params})")


if __name__ == "__main__":
    main()

