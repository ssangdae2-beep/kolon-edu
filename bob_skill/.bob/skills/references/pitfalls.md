# Seven pitfalls — wrong vs right

The traps that eat the most hackathon time. Read this before your first import,
not after the first failure.

---

## 1. `tools:` strings drift from `@tool` function names

The agent YAML's `tools:` list contains exact Python function names, not file
names or display labels. Renaming the function without updating YAML breaks the
binding silently — the agent loads, but tool calls 404.

**Wrong**
```python
# tools/weather.py
@tool(expected_credentials=[...])
def fetch_weather(city: str) -> ToolResponse[Weather]: ...
```
```yaml
# agents/weather_agent.yaml
tools:
  - get_weather   # name from the old version. Tool will silently not bind.
```

**Right** — three-way match: filename stem == function name == YAML string.
```python
# tools/get_weather.py
@tool(expected_credentials=[...])
def get_weather(city: str) -> ToolResponse[Weather]: ...
```
```yaml
tools:
  - get_weather
```

---

## 2. Manager agent with a non-empty `tools:` list

Manager agents route only. Mixing in tools confuses the routing prompt — the
agent starts answering directly instead of delegating, and child agents stop
getting invoked.

**Wrong**
```yaml
kind: native
name: hr_manager
collaborators: [pto_agent, onboarding_agent]
tools:
  - get_pto_balance   # manager should NEVER own tools
```

**Right**
```yaml
kind: native
name: hr_manager
collaborators: [pto_agent, onboarding_agent]
tools: []   # always empty for managers
```

---

## 3. Missing or partial Google docstring

ADK builds the tool schema the LLM sees from the docstring. Every arg must
appear under `Args:` with a non-empty description, plus a `Returns:` section.
Repo-wide docstring tests in the reference repo fail on violations; the ADK
import may accept the tool but the LLM won't know how to call it.

**Wrong**
```python
@tool(expected_credentials=[...])
def search(query: str, limit: int = 10) -> ToolResponse[Result]:
    """Search for things."""   # no Args:, no Returns:, agent guesses parameters
    ...
```

**Right**
```python
@tool(expected_credentials=[...])
def search(query: str, limit: int = 10) -> ToolResponse[Result]:
    """
    Searches the catalog for items matching the user's query.

    Args:
        query: Plain-English search string from the user.
        limit: Maximum number of results to return. Defaults to 10.

    Returns:
        A ToolResponse wrapping a Result list, or ErrorDetails on failure.
    """
    ...
```

---

## 4. Raising exceptions instead of returning `ToolResponse`

A bare `raise` inside a `@tool` bubbles up as an opaque agent failure. The
agent's "Error Handling" instructions never run because there's no
`error_details` field to read.

**Wrong**
```python
@tool(expected_credentials=[...])
def fetch(id: str) -> ToolResponse[Item]:
    response = requests.get(f"https://api.example.com/{id}", timeout=10)
    response.raise_for_status()   # raises on 500 → opaque agent failure
    return ToolResponse(error_details=None, tool_output=Item(**response.json()))
```

**Right**
```python
@tool(expected_credentials=[...])
def fetch(id: str) -> ToolResponse[Item]:
    try:
        response = requests.get(f"https://api.example.com/{id}", timeout=10)
        response.raise_for_status()
    except requests.exceptions.RequestException as exc:
        return ToolResponse(
            tool_output=None,
            error_details=ErrorDetails(
                status_code=getattr(exc.response, "status_code", None),
                url=f"https://api.example.com/{id}",
                reason=str(exc),
                details=getattr(exc.response, "text", None),
                recommendation="Verify the id and your network.",
            ),
        )
    return ToolResponse(error_details=None, tool_output=Item(**response.json()))
```

---

## 5. LLM string typos

`watsonx/openai/gpt-oss-120b` is the validated default (used by 278/285 production
agents in the reference repo). Guessing model strings is the #1 way to make
`orchestrate agents import` fail at validation.

**Wrong**
```yaml
llm: gpt-4o                    # not registered
llm: claude-sonnet-4-6         # not registered
llm: groq/gpt-oss-120b         # missing the `openai/` segment
```

**Right**
```yaml
llm: watsonx/openai/gpt-oss-120b
# Alternative for image input:
# llm: watsonx/meta-llama/llama-3-2-90b-vision-instruct
```

---

## 6. Import order

Order matters: **connections → tools → agents**. Importing the agent first
leaves dangling tool references — the agent loads, but every tool call 404s.

**Wrong**
```bash
orchestrate agents import --file agents/my_agent.yaml    # dangles
orchestrate tools import --kind python --file tools/my_tool.py --app-id my_app
orchestrate connections add --app-id my_app
```

**Right**
```bash
orchestrate connections add --app-id my_app
orchestrate connections configure --app-id my_app --env draft --type team --kind key_value
orchestrate connections set-credentials --app-id my_app --env draft -e token=$MY_APP_TOKEN
orchestrate tools import --kind python --file tools/my_tool.py --app-id my_app --requirements-file requirements.txt
orchestrate agents import --file agents/my_agent.yaml
```

---

## 7. Forgetting to activate the hosted env before import

`orchestrate tools import` and `agents import` go to whatever env is currently
active. If no env is active, or the wrong one is, the command may fail
confusingly — or worse, succeed against the wrong target.

**Wrong**
```bash
# fresh terminal, no env activated
orchestrate tools import --kind python --file tools/my_tool.py ...
# may error obscurely, or hit a default that isn't your demo target
```

**Right**
```bash
orchestrate env list                  # check what's active
orchestrate env activate $WO_ENV_NAME # if not already
orchestrate env list                  # confirm
orchestrate tools import --kind python --file tools/my_tool.py ...
```

Rule of thumb: run `orchestrate env list` immediately before any `import`
command. Make it muscle memory — it costs one second and prevents a category
of bugs that are otherwise hard to diagnose.

---

## 8. "Scope not found" on a non-production instance = wrong IAM URL, not wrong key

The CLI auto-infers an auth type from the instance URL. For staging / test /
dev instances, that inference points at the **production** IAM endpoint, which
doesn't know your user identity. The error you see is the cryptic
`Scope not found: Scope{scopeType='SERVICE', scopeId='<uuid>'}` — which sounds
like the instance is wrong, but is really "wrong IAM tenant."

Worse: `--iam-url` is marked `hidden=True` in the ADK CLI, so
`orchestrate env add --help` doesn't list it. You have to know it exists.

**Wrong** (default auth-type inference for staging):
```bash
orchestrate env add --name hackathon \
    --url https://api.staging-wa.watson-orchestrate.ibm.com/instances/<uuid>
# → "Scope not found" on activate
```

**Right** (explicit IAM URL + auth type for staging):
```bash
orchestrate env add --name hackathon \
    --url https://api.staging-wa.watson-orchestrate.ibm.com/instances/<uuid> \
    --iam-url https://iam.platform.test.saas.ibm.com \
    --type mcsp_v1
orchestrate env activate hackathon --api-key $WO_INSTANCE_API_KEY
# → "Environment 'hackathon' is now active"
```

See `remote_setup.md` for the full tier-by-tier table and a curl diagnostic
that tells you which IAM tenant your key belongs to.
