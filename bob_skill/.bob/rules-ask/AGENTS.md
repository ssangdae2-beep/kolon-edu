# Ask Mode — Documentation Context

Non-obvious facts about how this codebase is structured and documented.

## Where authoritative references live

The canonical reference for all patterns is **not** the toolkit code — it's the `.bob/skills/` directory:
- `references/tool_template.py` — the definitive `@tool` + `ToolResponse` pattern
- `references/pitfalls.md` — 8 common mistakes with wrong/right examples (read this before answering any "why doesn't it work" question)
- `references/yaml_schema.md` — all valid YAML fields for agents and connections
- `references/deploy_recipe.md` — the exact CLI command sequence with success markers
- `references/remote_setup.md` — IAM URL / auth type table for staging vs prod instances
- `examples/` — 7 working end-to-end patterns (collaborator, manager, OpenAPI, knowledge base, voice/TTS, stateful AstraDB, planner)

## Counterintuitive structure

- The `presto-text-to-sql-toolkit/` code docstrings are in **Korean** — this is intentional, not an error.
- There is **no test suite** in the Presto toolkit yet; the smoke test is a direct Python import call documented in AGENTS.md.
- `ToolResponse` and `ErrorDetails` are **inlined per tool file**, not imported from a shared library — this is intentional to avoid shared-utils dependencies.
- The project deploys with **no local server** — `orchestrate env activate` points the CLI at a hosted IBM cloud instance; `orchestrate tools import` ships directly to that remote instance.
- The `--iam-url` flag for `orchestrate env add` is hidden from `--help` output but is required for non-production (staging/test/dev) instances.

## SKILL.md vs AGENTS.md

`SKILL.md` (in `.bob/skills/`) is the long-form guide written for Bob (the AI agent) to teach it how to build new WXO agents step by step. `AGENTS.md` (root) is the concise reference for day-to-day coding guidance. They are complementary.

## LLM model string

`watsonx/openai/gpt-oss-120b` is the validated default used by 278/285 production agents in the IBM reference repo. Questions about "which model to use" have a definitive answer: this one, unless vision input is required.
