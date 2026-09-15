# Agent Mode — Coding Rules

Non-obvious patterns required when writing or modifying code in this repository.

## Tool authoring

- Copy `references/tool_template.py` as the base — it contains the inlined `ToolResponse`/`ErrorDetails` classes. Do NOT import these from a shared utils path; they are intentionally inlined per-tool.
- The three-way match must be maintained atomically: if you rename a `@tool` function, you must also rename the `.py` file AND update every agent YAML that lists it under `tools:`.
- Never use `schema` as a parameter name in a `@tool` function — it shadows `BaseModel.schema()` and breaks ADK tool registration silently.
- All `@tool` functions must catch exceptions and return `ToolResponse(tool_output=None, error_details=ErrorDetails(...))`. Raising propagates as an opaque agent failure.
- Docstrings must include `Args:` and `Returns:` sections — ADK builds the LLM-visible schema from the docstring. A missing `Args:` entry = the LLM doesn't know that parameter exists.
- Docstrings in the Presto toolkit are written in Korean. Match this convention.

## Presto toolkit specifics (`presto-text-to-sql-toolkit/`)

- `cursor.description` is `None` after non-SELECT statements — always guard before iterating.
- `prestodb` returns `Row` objects, not plain tuples — serialize with `[list(row) for row in rows]`.
- Token and SSL cert are cached at module level behind `threading.Lock()` — do not move the cert to a file path without updating this caching logic.
- `max_rows` must be clamped to 1000 before use: `min(max_rows, 1000)`.

## Deployment commands

Tool update pattern (no in-place update supported):
```bash
orchestrate tools remove <function_name>
orchestrate tools import --kind python --file tools/<file>.py --app-id <app_id> --requirements-file requirements.txt
```

Always run `orchestrate env list` before any import — importing to the wrong env is silent.

## YAML authoring

- Agent `name:` must be snake_case and match the filename stem.
- `llm:` must be exactly `watsonx/openai/gpt-oss-120b` (or `watsonx/meta-llama/llama-3-2-90b-vision-instruct` for vision). Any other string either fails validation or changes tool-calling behavior silently.
- Manager agents: `tools: []` always. Any non-empty `tools:` on a manager breaks delegation routing.
- Connection `app_id` in YAML must exactly match the `app_id` in `ExpectedCredentials(app_id="...")`.
