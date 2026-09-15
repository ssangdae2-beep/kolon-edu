# Evaluation recipe — Journey Success test cases

Once your agent is deployed and you've smoke-tested it in the hosted chat, the
next step is to upload a **Journey Success** test case so judges can grade your
agent against a known-good trajectory: did it call the right tools, in the right
order, with the right arguments, and did the final response contain the right
content?

Test cases live in the agent's "Tests" panel in the Orchestrate UI. Judges
press "Run" → the UI executes the conversation, grades it, and shows
pass/fail per goal.

## What Journey Success grades

For every test case the evaluator checks:

1. **Tool call coverage** — every `goal_details` entry of `type: "tool_call"`
   must be triggered by the agent.
2. **Tool call ordering** — the DAG in `goals` (e.g. `{"tool_a-1": ["tool_b-1"]}`)
   defines the required sequence. If the agent calls tools in the wrong order
   or skips a step, the journey fails.
3. **Argument matching** — for each tool call, each arg's `arg_matching` mode
   determines how strict the value check is:
   - `strict` — must equal exactly.
   - `fuzzy` — string distance match.
   - `optional` — present-but-don't-grade; missing is also OK.
4. **Text goal matching** — for every `type: "text"` goal, the final agent
   response is graded against `response` (fuzzy) and `keywords` (substring
   presence).

A test case passes only if every goal passes. This is unforgiving on purpose —
hackathon judges can compare teams objectively.

## Test case schema (v2)

The hosted endpoint stores test cases in this shape (verified against
`GET /v1/orchestrate/agent/<id>/test_case/v2/<test_case_id>`):

```json
{
  "agent": "<agent name from your YAML>",
  "story": "<one sentence, second person, becomes conversation_context>",
  "starting_sentence": "<the exact user prompt, becomes the test case name>",
  "response_summary": "<optional — semantic spec of the final response>",
  "goals": {
    "<goal-name-A>": ["<goal-name-B>", "..."]
  },
  "goal_details": [
    {
      "name": "<goal-name-A>",
      "type": "tool_call",
      "tool_name": "<exact @tool function name>",
      "args": { "<arg>": <value>, ... },
      "arg_matching": { "<arg>": "strict" | "fuzzy" | "optional" }
    },
    {
      "name": "<goal-name-B>",
      "type": "text",
      "summary": "<optional — semantic spec of what this turn should accomplish>",
      "response": "<optional — fuzzy-matched example response>",
      "keywords": ["substring", "to", "require"]
    }
  ]
}
```

Naming convention: tool-call goals get `<tool_name>-<n>` (e.g.
`get_cat_fact-1`) so the same tool called twice gets `-1` and `-2`. Text goals
can be named after their purpose (e.g. `summarize`, `confirm`, `apologize`).

Start from `references/evaluation_template.json` and edit.

## Three knobs for grading the agent's final response

Text goals (and the top-level `response_summary`) let you grade the agent's
actual output. Pick the right combination per agent — over-specifying causes
false failures, under-specifying lets bad responses pass:

| Field | What it checks | When to use |
|---|---|---|
| `keywords` (per text goal) | Substring presence — every entry must appear verbatim in the response. | **Default. Almost always include.** Cheapest, most reliable. Use for must-mention values: city names, currency codes, ticket IDs, the answer to a counted question. |
| `response` (per text goal) | Fuzzy string match against a near-verbatim example. Forgiving on phrasing but rewards similar wording. | When you want to nudge the evaluator toward a tone or template (e.g., "apologize and explain X"). Don't expect verbatim. |
| `summary` (per text goal) | LLM-judged: does the agent's response semantically accomplish what this summary describes? | QA-agent-only — same rule as `response_summary` below. |
| `response_summary` (top-level) | LLM-judged: does the agent's overall final response match this description? | **QA-style agents only.** Include when the answer is essentially the same every time (look up a fact, confirm a ticket, restate a balance). Skip for any agent whose output is intentionally varied. |

### When to include `response_summary` (and per-goal `summary`)

The decision lives at upload time — there is no reliable way to disable an
LLM-judged check in the UI's run config. So pick once, per test case.

**Include `response_summary` when:**
- The agent looks up a specific fact and reports it (QA-style).
- The agent confirms or echoes back a structured request (ticket created,
  appointment booked, refund processed).
- The agent produces a fixed-shape report from deterministic data (employee
  directory lookup, account balance, status check).

**Skip `response_summary` when:**
- The tool returns random/varied output (jokes, random facts, "tell me something").
- The tool wraps a live API whose output legitimately changes (exchange rates,
  weather, news headlines, recent issues).
- The agent has creative latitude (summarization, paraphrasing, recommendations).
- The output is open-ended in any way — listing options, drafting text,
  suggesting next steps.

When in doubt, leave it out and rely on `keywords` + the tool-call ordering
DAG. Those two together already catch most regressions, and they never
false-fail because of phrasing.

## Upload

There is **no `orchestrate` CLI command** for hosted test-case upload (the
`orchestrate evaluations *` commands run local evals, not hosted ones). You
hit the HTTP API directly. Helper script:

```bash
# upload_test_case.sh
set -euo pipefail

# Get a fresh JWT — staging uses the test IAM tenant (see remote_setup.md).
TOKEN=$(curl -fsS -X POST "$WO_IAM_URL/siusermgr/api/1.0/apikeys/token" \
    -H "Content-Type: application/json" \
    -d "{\"apikey\":\"$WO_INSTANCE_API_KEY\"}" \
    | python3 -c "import sys,json; print(json.load(sys.stdin)['token'])")

# Find the agent id by name.
AGENT_ID=$(curl -fsS -H "Authorization: Bearer $TOKEN" \
    "$WO_INSTANCE_URL/v1/orchestrate/agents" \
    | python3 -c "import sys,json; print(next(a['id'] for a in json.load(sys.stdin) if a['name']=='$1'))")

# Upload.
curl -fsS -X POST -H "Authorization: Bearer $TOKEN" \
    "$WO_INSTANCE_URL/v1/orchestrate/agent/$AGENT_ID/test_case/v2" \
    -F "file=@$2;type=application/json"
```

Usage:
```bash
bash upload_test_case.sh my_agent tests/my_test.json
```

Success returns:
```json
{"test_case_ids":["<uuid>"],"total_test_cases":1}
```

## Verify and run

List existing test cases:
```bash
curl -H "Authorization: Bearer $TOKEN" \
    "$WO_INSTANCE_URL/v1/orchestrate/agent/$AGENT_ID/test_case/v2" \
    | python3 -m json.tool
```

To run from the UI:
1. Open `$WO_INSTANCE_URL/manage/agents`.
2. Click your agent → **Tests** tab.
3. The test case appears as a row with the `starting_sentence` as its name.
4. Click **Run**. The UI sends the `starting_sentence` to the agent, captures
   the full trajectory, and grades each goal.
5. Results show per-goal pass/fail. Aggregate is the Journey Success rate.

## Writing tips

- **One test case per scenario, not per assertion.** Pack all the tool calls
  and final text expectations into one test case for a given user request.
- **Use `strict` arg matching for IDs and enums; `fuzzy` for free-text;
  `optional` for sort/page/limit knobs the LLM may set arbitrarily.**
- **Keep `keywords` to the few words a correct answer MUST contain.**
  Over-specifying causes false fails when the LLM phrases the same fact
  differently.
- **For manager agents**, the `tool_name` in goal_details should match the
  collaborator's tool — the manager itself doesn't call tools. The goal DAG
  encodes the routing sequence: e.g.
  `{"hr_lookup-1": ["it_provision-1"], "it_provision-1": ["confirm"]}`.
- **Always include at least one `type: "text"` goal at the end** so the test
  also checks that the agent finishes the conversation, not just dials tools.
- **Use `response_summary` only for QA-style agents** — ones that look up
  a specific fact, confirm a structured request, or report a fixed-shape
  status. Skip it for agents that hit live/changing APIs or have any
  creative latitude. The check can't be disabled at run time, so the
  upload-time decision is final. A travel briefing that depends on live
  FX rates does NOT qualify; an HR balance lookup does.

## Common failures

| Symptom | Likely cause |
|---|---|
| Upload returns 422 `{"detail":[{"type":"missing","loc":["body","file"]}]}` | You POST'ed JSON directly instead of multipart. Use `-F "file=@..."`. |
| Test case uploads but Journey Success is always 0 | `tool_name` doesn't match the deployed tool's function name. Cross-check with `orchestrate tools list`. |
| Tool call goal passes but text goal fails | `keywords` too specific — the LLM paraphrased and a required substring isn't there. Loosen the list. |
| Out-of-order tool calls flagged as wrong order | The agent's `instructions:` don't explicitly require the sequence. Add a "Tool Sequencing" section to the agent YAML's instructions. |
