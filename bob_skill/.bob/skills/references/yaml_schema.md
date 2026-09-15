# YAML schema cheat-sheet

One-page reference for the YAML shapes Orchestrate accepts. Verified against the
ADK source at `ibm_watsonx_orchestrate.cli.commands.*` and against the production
agents in the `wxo-domains` reference repo.

## Agent YAML

| Field | Required | Type | Notes |
|---|---|---|---|
| `spec_version` | yes | string | Always `v1`. |
| `kind` | yes | enum | `native` (built with this ADK) or `external` (Bee, LangGraph, AutoGen, etc.). For hackathons, always `native`. |
| `name` | yes | string | snake_case. Must match the filename stem. |
| `description` | yes | string | One sentence. The parent manager's router reads this to decide whether to delegate to you. |
| `instructions` | yes | string | Long-form markdown. Use `instructions: \|` for literal blocks (preserves newlines) or `instructions: >` for folded (collapses to a paragraph). |
| `llm` | yes | string | See LLM table below. Default: `groq/openai/gpt-oss-120b` (278/285 production agents use this). |
| `style` | yes | enum | `default` (almost always) or `react` (only for explicit chain-of-thought reasoning agents — 1/285 production agents). |
| `collaborators` | yes | list[string] | Names of child agents. Empty list `[]` for collaborator agents; non-empty for managers. |
| `tools` | yes | list[string] | EXACT snake_case `@tool` function names. Empty list `[]` for manager agents (always). |
| `context_access_enabled` | no | bool | Enable when the agent needs runtime context. |
| `context_variables` | no | list[string] | Common set: `wxo_email_id`, `wxo_user_name`, `channel`. |

### Recommended LLM values

| Value | When to use |
|---|---|
| `groq/openai/gpt-oss-120b` | **Default for this skill.** Tuned tool-call reliability for the instruction patterns the template uses. |
| `watsonx/meta-llama/llama-3-2-90b-vision-instruct` | When you need image input or are constrained to watsonx-hosted models. |

Other model strings exist but introduce silent tool-calling differences — only swap if you know why.

## Connection YAML

| Field | Required | Type | Notes |
|---|---|---|---|
| `spec_version` | yes | string | Always `v1`. |
| `kind` | yes | string | Always `connection` at the top level. |
| `app_id` | yes | string | snake_case. Referenced from the Python tool's `ExpectedCredentials(app_id="...")` and from `orchestrate connections add --app-id <id>`. |
| `environments.draft` | yes | object | Draft environment block — what you configure during dev. |
| `environments.live` | yes | object | Live environment block — what end users hit. |

Per-environment fields:

| Field | Required | Notes |
|---|---|---|
| `kind` | yes | One of `key_value`, `basic`, `bearer`, `api_key`, `oauth_auth_code_flow`, `oauth_auth_password_flow`, `oauth_auth_client_credentials_flow`, `oauth_auth_on_behalf_of_flow`. |
| `type` | yes | `team` (shared) or `member` (per-user). OAuth → almost always `member`. |
| `server_url` | when relevant | The base URL the connection hits. |
| `sso` | OAuth only | `true` if the OAuth flow goes through a SAML IDP. |
| `credentials` | yes | Map of placeholders like `"{MY_APP[token]}"`, resolved at import time from your local credentials/env. |

## Tool decorator (`@tool`) arguments

```python
@tool(
    expected_credentials=[ExpectedCredentials(app_id="...", type=ConnectionType.X)],
    enable_dynamic_input_schema=False,   # optional, for tools whose schema depends on runtime data
    enable_dynamic_output_schema=False,  # optional
    dynamic_input_schema=None,           # provide when enable_dynamic_input_schema=True
    dynamic_output_schema=None,          # provide when enable_dynamic_output_schema=True
)
def my_tool_function_name(arg1: str, arg2: int = 10) -> ToolResponse[Response]:
    """Google-style docstring required. See tool_template.py."""
```

`ConnectionType` enum values: `BASIC_AUTH`, `BEARER_TOKEN`, `API_KEY_AUTH`, `OAUTH2_AUTH_CODE`, `OAUTH2_PASSWORD`, `OAUTH2_CLIENT_CREDS`, `OAUTH_ON_BEHALF_OF_FLOW`, `KEY_VALUE`.
