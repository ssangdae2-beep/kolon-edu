# Remote setup — registering the shared hackathon instance

One-time setup. Run this once at the start of the hackathon, then refer to
`deploy_recipe.md` for the deploy commands.

> This skill does not use `orchestrate server start` (the Docker-based Lite
> stack). The CLI talks directly to whatever env is active; with the hosted
> env active, every command goes straight to the hosted instance.

## What the organizer will give you

| Item | Example | Where it goes |
|---|---|---|
| `WO_INSTANCE_URL` | `https://api.staging-wa.watson-orchestrate.ibm.com/instances/<uuid>` | `.env`, used by `orchestrate env add --url` |
| `WO_INSTANCE_API_KEY` | MCSP-format key starting `k1:usr_...` | `.env`, used by `orchestrate env activate --api-key` |
| `WO_IAM_URL` | depends on instance tier — see table below | `.env`, used by `orchestrate env add --iam-url` |
| `WO_AUTH_TYPE` | `mcsp_v1` for staging, `mcsp` (default) for prod | `.env`, used by `orchestrate env add --type` |
| `WO_ENV_NAME` | `hackathon` | Local alias — short, snake_case |

Paste these into your `.env` (see `starter/env.example` for the file shape).

## ⚠️ The IAM-URL gotcha

The CLI auto-infers an auth type from the instance URL. For **production**
Orchestrate instances that inference is correct. For **staging / preprod / dev**
instances it is wrong: the URL looks production-shaped, so the CLI hits
production IAM, which doesn't know the user's identity → cryptic
`Scope not found` error.

You must override the IAM URL on `env add`. Use the table:

| Instance tier | URL pattern | `--iam-url` | `--type` |
|---|---|---|---|
| Production | `*.cloud.ibm.com` | (none — default works) | (none — default `mcsp`) |
| Pre-prod / test | `*.test.cloud.ibm.com` | `https://account-iam.platform.test.saas.ibm.com` | `mcsp_v2` |
| **Staging** | `staging-wa.watson-orchestrate.ibm.com` | `https://iam.platform.test.saas.ibm.com` | `mcsp_v1` |
| Dev | `dev-wa.watson-orchestrate.ibm.com` | ask the organizer | ask the organizer |
| Cloud Pak for Data | self-hosted | the `/icp4d-api` endpoint of your instance | `cpd` (also needs `--username` + `--password`) |

`--iam-url` is marked `hidden=True` in the ADK CLI, so `orchestrate env add --help`
won't show it. Don't omit it for non-production envs.

## Register and activate the env

```bash
# One-time: register the hosted instance under your chosen local alias.
# (Don't use --activate here — it tries to prompt for the API key
# interactively, which fails in non-TTY shells.)
orchestrate env add \
    --name $WO_ENV_NAME \
    --url $WO_INSTANCE_URL \
    --iam-url $WO_IAM_URL \
    --type $WO_AUTH_TYPE

# Activate, passing the key via flag (non-interactive).
orchestrate env activate $WO_ENV_NAME --api-key $WO_INSTANCE_API_KEY
```

Verify:
```bash
orchestrate env list
```
You should see the new env, marked `(active)`. If activation logged
`Environment '<name>' is now active`, you're in.

## How to diagnose a key whose tenant you don't know

If your organizer hands you a key but you don't know which IAM tenant it lives
in, you can probe directly with `curl`. The V1 token endpoint returns a JWT
when the key is valid, and an "identity not found" error when it isn't:

```bash
# Try production first
curl -s -X POST "https://iam.platform.saas.ibm.com/siusermgr/api/1.0/apikeys/token" \
    -H "Content-Type: application/json" \
    -d "{\"apikey\":\"$WO_INSTANCE_API_KEY\"}"

# If that returns "IdentitySpec ... not found", try test
curl -s -X POST "https://iam.platform.test.saas.ibm.com/siusermgr/api/1.0/apikeys/token" \
    -H "Content-Type: application/json" \
    -d "{\"apikey\":\"$WO_INSTANCE_API_KEY\"}"
```

Whichever endpoint returns `{"token":"eyJ..."}` is your `--iam-url` for `env add`.

The instance UUID (the path segment after `/instances/`) is the MCSP scope.
"Scope not found" with the right IAM URL means your user account doesn't have
permission on this instance — ask the organizer.

## Connections on hosted: Draft vs Live

The hosted UI splits every connection's credentials into two slots:

- **Draft** — what your agent uses while you iterate. `orchestrate connections set-credentials --env draft` writes here.
- **Live** — what other users (judges, demo audience) see. You must promote Draft → Live manually.

### Promotion flow

1. Browse to `$WO_INSTANCE_URL/manage/connectors` (or the matching UI URL — for
   staging that's typically `https://staging-wa.watson-orchestrate.ibm.com/manage/connectors`).
2. Find your connection (search by `app_id`).
3. In the **Draft** tab, verify the green "connected" check.
4. Switch to the **Live** tab.
5. Click **Paste Draft Credentials** → **Connect** → **Save**.

For OAuth connections, "Connect" pops a provider login window — complete the
OAuth dance once for Draft, once for Live.

This is the same pattern documented in `wxo-domains/how-to/auth/workday/guide.md`
(steps 3–6 of "Configuring Orchestrate Connection").

## Verify before every import

```bash
orchestrate env list
```

Should always show the hosted env as active before you run `tools import` or
`agents import`. If it doesn't, re-activate:

```bash
orchestrate env activate $WO_ENV_NAME --api-key $WO_INSTANCE_API_KEY
```

Running an import without an active env (or with the wrong env active) is the
#1 hosted-deploy bug — pitfall #7.

## Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| `Scope not found: Scope{scopeType='SERVICE', scopeId='<uuid>'}` | Wrong IAM URL (default points at prod, your instance is on test) — NOT a bad key. | Set `--iam-url` per the table above. See pitfall #8. |
| `Provided API key could not be found` | You set `--type ibm_iam` for a non-IBM-Cloud key, or vice versa. | Confirm the key format — MCSP keys start with `k1:`. Re-run `env add` with the right `--type`. |
| `ApiKey owner IdentitySpec{identityUid='...'} not found` | The key is valid but lives in a different IAM tenant. | Try the curl diagnostic above against test/prod IAM endpoints to find the right one. |
| `getpass.GetPassWarning: Can not control echo on the terminal` | You used `env add --activate` in a non-TTY shell. | Split into `env add` (no `--activate`) + `env activate --api-key`. |
| `env activate` succeeds but every subsequent call returns 401 | API key expired. | Re-issue from the Orchestrate UI; re-run activate with `--api-key`. |
| Agent imported but tool calls return "connection not found" | Connection exists only in Draft. | Promote Draft → Live in the UI. |
| OAuth Connect pop-up redirects to `localhost` and 404s | Redirect URI in the provider app doesn't match this instance. | Re-register the provider OAuth app with the right redirect URI for your instance tier — see `wxo-domains/how-to/auth/workday/guide.md` lines 46–59 for canonical URIs. |
| Agent missing from hosted chat | Either still on local env, or agent not deployed. | `orchestrate env list`; if env is correct, `orchestrate agents deploy --name my_agent`. |
