# Plan Mode — Architecture Constraints

Non-obvious architectural constraints and decisions to account for when planning changes.

## Deployment model

- There is **no local runtime** — every artifact (tool, agent, connection) exists only on the hosted WXO instance after `orchestrate import`. Local Python code is the source of truth; the remote instance is the only execution environment.
- Import order is a hard constraint enforced by the platform: **connections → tools → agents**. Importing an agent before its tools creates dangling references that are silent (agent loads, tool calls 404 at runtime).
- Updating a tool requires remove + re-import (the platform has no in-place update). This means any plan involving tool changes must include a removal step.

## Three-way coupling (structural constraint)

The `@tool` function name, the `.py` filename stem, and the `tools:` entry in every agent YAML that uses the tool form a **three-way identity**. Any refactoring that changes a function name must touch all three simultaneously. There is no runtime enforcement — drift is silent.

## Connection credentials: Draft vs Live

Every connection has two independent credential slots (Draft / Live) on the hosted instance. Draft is set via CLI; Live requires manual promotion through the hosted UI (`$WO_INSTANCE_URL/manage/connectors`). Any plan that adds a new external API integration must account for both this CLI step and the manual UI promotion step before end-user testing works.

## Agent topology constraints

- **Manager agents** must have `tools: []` — the routing logic is broken if a manager owns tools directly.
- **Collaborator agents** must have `collaborators: []` — nesting collaborators inside collaborators is not supported.
- Agent `description:` is the routing signal for a parent manager — it must be a precise one-sentence summary of the agent's domain.

## ToolResponse is the error protocol

The ADK has no middleware error layer. A `@tool` function that raises an exception produces an opaque failure with no actionable information. All error handling must flow through `ToolResponse(error_details=ErrorDetails(...))`. Plans that add new tools must account for this — no exceptions should escape a `@tool` function.

## Presto connection architecture

- No connection pooling — a fresh Presto connection is created per tool call. This is intentional; pooling adds complexity not warranted by the call frequency pattern.
- The SSL certificate is embedded in source code as a string constant and cached to a temp file. Externalizing it to a file path would require updating the module-level caching logic (threading.Lock + single-write pattern).

## Python version constraint

Requires Python ≥ 3.9. The `@dataclass` + `Generic[T]` pattern for `ToolResponse` depends on this minimum version.
