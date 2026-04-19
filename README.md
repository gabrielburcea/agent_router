# agent_router

A tiny Python library for **declarative, capability-graph routing** of requests
to agents.

You describe *what* the caller wants as a structured `RoutingIntent`
(`action` + `resource` + `parameters`), and `IntentRouter` looks the pair up in
a capability graph to find the agent that can handle it. Unknown capabilities
are blocked — never silently misrouted.

Built on [pydantic v2](https://docs.pydantic.dev/) for runtime validation.

## Install

```bash
pip install -e ".[dev]"
```

## Quick start

```python
from agent_router import IntentRouter, RoutingIntent

router = IntentRouter()

intent = RoutingIntent(
    action="find",
    resource="sales_report",
    parameters={"quarter": "Q1"},
)

print(router.route_request(intent))
# Routing to SalesAgent with params: {'quarter': 'Q1'}
# -> "Success"
```

## Concepts

### The vocabulary

Two `Literal` type aliases lock down the legal words:

```python
ActionType   = Literal["find", "analyze", "document", "create"]
ResourceType = Literal["sales_report", "server_log", "document"]
```

Any typo (`"finnd"`, `"sales-report"`, …) is rejected by pydantic at
construction time.

### The intent

`RoutingIntent` is a pydantic model with three fields:

| Field        | Type                      | Notes                                       |
|--------------|---------------------------|---------------------------------------------|
| `action`     | `ActionType`              | Required, must be one of the allowed verbs. |
| `resource`   | `ResourceType`            | Required, must be one of the allowed nouns. |
| `parameters` | `dict[str, Any]`          | Free-form payload, defaults to `{}`.        |

### The router

`IntentRouter` holds a `capability_graph` — a dict mapping
`(action, resource)` tuples to agent names:

```python
{
    ("find", "sales_report"):    "SalesAgent",
    ("analyze", "sales_report"): "SalesAgent",
    ("find", "document"):        "ComplianceAgent",
    ("create", "server_log"):    "DevOpsAgent",
}
```

`route_request(intent)`:

1. Builds the key `(intent.action, intent.resource)`.
2. Looks it up in the graph.
3. If **missing** → returns an `"Error: ..."` string (request is blocked).
4. If **found** → calls `dispatch_to_agent(agent_name, intent.parameters)`.

## Extending

### Custom capability graph

Pass your own graph when constructing the router, or mutate
`router.capability_graph` after the fact:

```python
router = IntentRouter()
router.capability_graph[("analyze", "server_log")] = "DevOpsAgent"
```

### Custom dispatch

Subclass and override `dispatch_to_agent` to plug in real agent logic:

```python
class MyRouter(IntentRouter):
    def dispatch_to_agent(self, agent_name, params):
        agent = AGENT_REGISTRY[agent_name]   # your lookup
        return agent.run(**params)            # your call
```

## Testing

```bash
pytest -q
```

## License

MIT

