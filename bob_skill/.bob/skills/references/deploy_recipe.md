# Deploy recipe

End-to-end command sequence verified against the ADK CLI source
(`ibm_watsonx_orchestrate.cli.commands.*`). Each step lists what success looks like.

> **No local server.** We skip `orchestrate server start` (which spins up a
> Docker-based Lite stack) entirely. The ADK CLI talks directly to whatever
> environment is active. With the hosted instance active, every
> `tools import` / `agents import` / `connections add` goes straight to the
> hosted instance — no Docker, no `localhost`, no Lite UI.
>
> **What you lose:** local chat (`orchestrate chat start` at
> `http://localhost:3000/chat-lite`) and offline iteration. Every change is a
> round-trip to the hosted instance.
>
> **What you keep:** unit tests (`pytest tools/`) run locally with no server.
> Most tool bugs are caught there. The hosted chat UI is your integration test.

You'll receive from the hackathon organizer:
- `WO_INSTANCE_URL` — e.g. `https://api.staging-wa.watson-orchestrate.ibm.com/instances/<uuid>`.
- `WO_INSTANCE_API_KEY` — your personal API key for the instance.
- `WO_IAM_URL` — IAM endpoint for the instance tier. Required for non-prod.
- `WO_AUTH_TYPE` — `mcsp_v1` for staging, `mcsp` (default) for production.
- `WO_ENV_NAME` — a name you'll use locally to reference the instance (e.g. `hackathon`).

Put these in `.env` (see `starter/env.example`) and `source .env` before running any CLI commands below, or pass values inline.

> **Read `remote_setup.md` first** if you don't already know the right
> `--iam-url` and `--type` for your instance tier. The default auth detection
> is correct for production but wrong for staging/test/dev — symptom is a
> cryptic `Scope not found` error (pitfall #8).

---

## 1. Register the hosted env (one-time)

```bash
# Don't use --activate here — it prompts for the API key interactively,
# which fails in non-TTY shells. Split into add + activate.
orchestrate env add \
    --name $WO_ENV_NAME \
    --url $WO_INSTANCE_URL \
    --iam-url $WO_IAM_URL \
    --type $WO_AUTH_TYPE

orchestrate env activate $WO_ENV_NAME --api-key $WO_INSTANCE_API_KEY
```
You should see: `Environment '<name>' is now active`, and `orchestrate env list`
shows the new env marked `(active)`.

For production instances, you can omit `--iam-url` and `--type` — the defaults
work. For everything else, fill them per the table in `remote_setup.md`.

## 2. Verify the active env (do this before every import)

```bash
orchestrate env list
```
You should see your hosted env name with an active marker. **If it's not active,
your imports go nowhere useful** — see pitfall #7.

## 3. Run unit tests locally

```bash
pytest tools/
```
You should see: all happy-path and error-path tests pass. This is your only
fast feedback loop — exercise it aggressively.

## 4. Register a connection (only if your tool hits an external API)

```bash
orchestrate connections add --app-id my_app

orchestrate connections configure \
    --app-id my_app \
    --env draft \
    --type team \
    --kind key_value

orchestrate connections set-credentials \
    --app-id my_app \
    --env draft \
    -e token=$MY_APP_TOKEN
```
You should see: `orchestrate connections list` shows `my_app` with credentials set in Draft.

## 5. Import your tool

```bash
orchestrate tools import \
    --kind python \
    --file tools/my_tool.py \
    --app-id my_app \
    --requirements-file requirements.txt
```
You should see: `orchestrate tools list` shows `my_tool_function_name`.

> Forgetting `--requirements-file` is the most common quiet failure — the ADK
> packages the tool's deps from this file. Without it, your tool may import
> but break at runtime when it can't find `requests` / `pydantic` / etc.

## 6. Import your agent

```bash
orchestrate agents import --file agents/my_agent.yaml
```
You should see: `orchestrate agents list` shows `my_agent`.

## 7. Promote the connection from Draft to Live

The hosted UI keeps two copies of each connection's credentials: **Draft** (dev)
and **Live** (production). Step 4 wrote credentials to Draft. To make them
visible to end users / judges, promote to Live:

1. Open `$WO_INSTANCE_URL/manage/connectors` in your browser.
2. Find your `my_app` connection. Confirm Draft shows "connected" (green check).
3. Click into the connection, switch to the **Live** tab.
4. Click **Paste Draft Credentials**.
5. Click **Connect**, then **Save**.

This pattern mirrors the documented Workday auth flow in
`wxo-domains/how-to/auth/workday/guide.md` steps 3–6.

## 8. Test in the hosted chat

Navigate to the hosted chat URL for your instance (the path differs by tier —
typically `$WO_INSTANCE_URL/chat`). Pick your agent and send a demo prompt.

If the prompt doesn't invoke your tool, the agent's `instructions:` aren't
specific enough — refine the "How To Use Tools" section and re-run step 6.

---

## Iteration loop

After the initial setup, every code change is:

```bash
pytest tools/                                                                 # fast local check
orchestrate env list                                                          # confirm hosted env active
orchestrate tools import --kind python --file tools/my_tool.py \
    --app-id my_app --requirements-file requirements.txt                      # re-import tool
orchestrate agents import --file agents/my_agent.yaml                         # re-import agent
# refresh the hosted chat tab and re-test
```

Connections only need re-running when their credentials or auth kind change.

---

## Common failure → fix

| Symptom | Fix |
|---|---|
| `orchestrate tools list` is empty after import | You probably forgot `--requirements-file`. |
| Agent imports but tool calls 404 in chat | Import order was wrong. Order is **connections → tools → agents**. (pitfall #6) |
| `agents import` errors on the `llm:` field | Typo'd model string. Stick to `watsonx/openai/gpt-oss-120b`. (pitfall #5) |
| Connection works in Draft but agent fails in hosted chat for other users | Connection wasn't promoted to Live. Do step 7. |
| Hosted import looks like it succeeded but `agents list` returns nothing | No env is active, or wrong env. Run `orchestrate env list`. (pitfall #7) |
| Tool imports but errors at runtime with `ModuleNotFoundError` | Missing dep in `requirements.txt`, or `--requirements-file` wasn't passed. |
