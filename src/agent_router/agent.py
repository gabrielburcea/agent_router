from pydantic import BaseModel, Field
from typing import Any, Literal

# ---------------------------------------------------------------------------
# Define the "Vocabulary" of the system.
# These type aliases lock down the legal actions and resources, so typos like
# "finnd" or "sales-report" are rejected at validation time.
# ---------------------------------------------------------------------------

# Allowed actions the router understands.
ActionType = Literal["find", "analyze", "document", "create"]
# Allowed resources the router can act on.
ResourceType = Literal["sales_report", "server_log", "document"]


class RoutingIntent(BaseModel):
    """Structured description of what the caller wants to do.

    Pydantic validates every field on construction, so invalid combinations
    raise `ValidationError` instead of silently routing to the wrong agent.
    """

    # What the caller wants to do — must be one of the ActionType strings.
    action: ActionType
    # What they want to do it on — must be one of the ResourceType strings.
    resource: ResourceType
    # Free-form payload the agent will consume. `default_factory=dict` means
    # each new intent gets its own fresh {} (avoids the mutable-default bug).
    parameters: dict[str, Any] = Field(default_factory=dict)


class IntentRouter:
    """Declarative router backed by a capability graph.

    The router itself is tiny: it's just a dict lookup (`(action, resource)`
    -> agent name) plus a safety check for unknown capabilities.
    """

    def __init__(self):
        # The capability graph: maps (Action, Resource) -> Agent Name.
        # Each entry is a single "this agent can do this" edge in the graph.
        self.capability_graph = {
            ("find", "sales_report"): "SalesAgent",
            ("analyze", "sales_report"): "SalesAgent",
            ("find", "document"): "ComplianceAgent",
            ("create", "server_log"): "DevOpsAgent",
        }

    def route_request(self, intent: RoutingIntent):
        """Resolve an intent to an agent and dispatch to it."""

        # 1. Lookup — build the tuple key and look it up in the graph.
        key = (intent.action, intent.resource)

        # `.get()` returns None if the key is absent (no KeyError raised).
        target_agent_name = self.capability_graph.get(key)

        # 2. Safety check — if the capability isn't registered, block the
        # request rather than guessing. Returning a string keeps the demo
        # simple; in production raise a dedicated exception instead.
        if not target_agent_name:
            return f"Error: No agent exists that can '{intent.action}' a '{intent.resource}'."

        # 3. Dispatch — hand off to the agent (simplified for now).
        return self.dispatch_to_agent(target_agent_name, intent.parameters)

    def dispatch_to_agent(self, agent_name, params):
        """Hook where the real agent invocation would happen.

        Override this in a subclass (or swap it out) to instantiate the
        concrete agent class, call its `.run(params)`, log metrics, etc.
        """

        # Debug breadcrumb so you can see routing decisions during dev.
        print(f"Routing to {agent_name} with params: {params}")

        # Placeholder return — real code would forward the agent's output.
        return "Success"
    
    