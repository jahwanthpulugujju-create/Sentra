# Build Plan — The Judgment Layer for Autonomous Agent Payments

> Companion to `PROJECT_BRIEF.md`. The brief explains **what** the project is and
> **why**. This document is the **how** — the complete, unambiguous engineering
> plan to build it from zero. Read the brief first; this assumes it.
>
> **Status:** planning complete, no code written yet. This is the spec the build
> follows. Nothing here should require a design decision mid-build.

---

## 0. Locked decisions (settled during planning)

| Decision | Choice | Rationale |
|---|---|---|
| Frontend | **React + Vite** (thin client, no business logic) | Credible "real stack" for judges; Vite = fast dev, no heavy tooling |
| Styling | **Tailwind CSS** | Fast, consistent; navy + amber palette (matches deck) |
| Backend | **FastAPI (Python)**, runs **locally** on `localhost:8000` | Brief's choice; local = zero deploy risk on demo day |
| Database | **Supabase** (hosted Postgres) | Real Postgres, live dashboard to show judges, zero local install |
| DB access | **SQLAlchemy ORM** over the Supabase Postgres connection string | Backend owns all logic; Supabase is "just Postgres" here |
| Intent-match LLM | **Claude Haiku 4.5** (`claude-haiku-4-5`) + keyword fallback | One cheap yes/no classification per transaction; ~₹0/demo |
| Payments | **Mock ledger** (in Postgres). x402 = optional stretch only | Fully working mock beats half-working real rail |
| Escalation | `status = 'pending'` in ledger; frontend polls every 2s | No websockets; robust and simple |
| Velocity check | Real: **>5 transactions from one agent within 10s → Deny** | Gives the rule engine a second real thing to catch |
| Phone push (ntfy.sh) | **Deferred to stretch** | Highest-fragility feature; core must be airtight first |
| Reset button | Built **early** | Used constantly during rehearsal; one click = clean demo state |

**Core architectural rule (from the brief, non-negotiable):**
> All three checks and the decision run in the **backend**. React only renders
> what the API returns and sends user actions. No policy logic in the browser.

---

## 1. Table of contents

1. [Locked decisions](#0-locked-decisions-settled-during-planning)
2. [System architecture](#2-system-architecture)
3. [Repository layout](#3-repository-layout)
4. [Data model (Supabase / Postgres)](#4-data-model-supabase--postgres)
5. [Canonical demo data](#5-canonical-demo-data-must-stay-identical-to-deck)
6. [The policy engine — three checks, one decision](#6-the-policy-engine--three-checks-one-decision)
7. [Backend — modules & responsibilities](#7-backend--modules--responsibilities)
8. [API surface (exact contracts)](#8-api-surface-exact-contracts)
8A. [Agent integration — how AI agents connect](#8a-agent-integration--how-ai-agents-connect-to-this-platform)
9. [Frontend — component tree & behavior](#9-frontend--component-tree--behavior)
10. [Configuration & secrets](#10-configuration--secrets)
11. [Local setup & run](#11-local-setup--run)
12. [Build order — demo-safe milestones](#12-build-order--demo-safe-milestones)
13. [Verification & test plan](#13-verification--test-plan)
14. [Security review checklist](#14-security-review-checklist-run-before-any-pushdeploy)
15. [Stretch goals](#15-stretch-goals)
16. [Demo-day runbook](#16-demo-day-runbook)
17. [Judging-criteria map](#17-judging-criteria-map)

---

## 2. System architecture

```
┌────────────────────────┐        HTTPS / JSON         ┌──────────────────────────┐
│      React + Vite      │ ─── POST /evaluate-transaction ──▶ │      FastAPI backend     │
│      (dashboard)       │ ◀── decision + checks + agent ──── │      (policy engine)     │
│                        │                              │                          │
│  - agent roster        │ ─── POST /resolve-escalation ────▶ │  rules → intent → anomaly │
│  - request panel       │ ─── GET  /agents  (poll 2s) ─────▶ │  → decision → audit log   │
│  - processing panel    │ ─── GET  /transactions (poll 2s)─▶ │                          │
│  - escalation card     │ ─── POST /reset ─────────────────▶ │                          │
│  - audit log           │ ─── GET  /health ────────────────▶ │                          │
└────────────────────────┘                              └────────┬─────────────────┘
                                                                 │  SQLAlchemy (SQL)
                                                                 ▼
                                                        ┌──────────────────────┐
                                                        │  Supabase Postgres   │
                                                        │  agents, transactions│
                                                        └──────────────────────┘
                                                                 ▲
                                                                 │ 1 classification call
                                                        ┌────────┴──────────┐
                                                        │  Claude Haiku 4.5 │ (intent match)
                                                        │  + keyword fallback│
                                                        └───────────────────┘
```

**Data flow of a single transaction** (the heart of the system):

1. User (or, conceptually, an agent) fires a request: `{agent_id, amount, description}`.
2. FastAPI loads the agent + its recent history from Postgres.
3. **Rule engine** runs (budget → blocklist → velocity). Any fail → **Deny**, stop.
4. If rules pass, **intent match** (Claude) and **anomaly score** (stats) run.
5. Decision combined: Allow / Escalate / Deny.
6. Transaction written to `transactions` with full check detail and a plain reason.
7. If **Allow** → balance deducted immediately. If **Escalate** → `status=pending`,
   no deduction yet. If **Deny** → recorded, no deduction.
8. Response returned to React, which animates the check chips and shows the banner.
9. On escalation, the frontend renders an Approve/Deny card; the human decides;
   `POST /resolve-escalation` flips status (and deducts on approve).

---

## 3. Repository layout

```
Hack/
├── Docs/
│   ├── PROJECT_BRIEF.md          # the "what/why" (exists)
│   └── BUILD_PLAN.md             # this file
├── backend/
│   ├── main.py                   # FastAPI app + routes + CORS
│   ├── config.py                 # env loading (DATABASE_URL, ANTHROPIC_API_KEY)
│   ├── database.py               # SQLAlchemy engine + session dependency
│   ├── models.py                 # Agent, Transaction ORM models
│   ├── schemas.py                # Pydantic request/response models
│   ├── policy_engine.py          # orchestrates the 3 checks → decision
│   ├── rules.py                  # rule engine (budget, blocklist, velocity)
│   ├── intent.py                 # Claude call + keyword fallback
│   ├── anomaly.py                # z-score anomaly check
│   ├── seed.py                   # canonical agents + history seeding / reset
│   ├── requirements.txt
│   └── .env.example
├── db/
│   └── schema.sql                # DDL — run once in Supabase SQL editor
├── frontend/
│   ├── index.html
│   ├── package.json
│   ├── vite.config.js
│   ├── tailwind.config.js
│   ├── postcss.config.js
│   ├── .env.example              # VITE_API_BASE=http://localhost:8000
│   └── src/
│       ├── main.jsx
│       ├── App.jsx
│       ├── api.js                # fetch wrappers for every endpoint
│       ├── theme.js              # palette + constants
│       ├── hooks/
│       │   └── usePolling.js     # poll /agents + /transactions every 2s
│       └── components/
│           ├── Header.jsx        # brand + HealthBadge + ResetButton
│           ├── AgentRoster.jsx
│           ├── AgentCard.jsx     # name, task, live budget bar
│           ├── RequestPanel.jsx  # 4 presets + custom builder
│           ├── ProcessingPanel.jsx  # 3 check chips + decision banner
│           ├── EscalationCard.jsx    # Approve / Deny buttons
│           ├── AuditLog.jsx
│           └── AuditRow.jsx
└── README.md                     # quickstart (setup + run)
```

---

## 4. Data model (Supabase / Postgres)

`db/schema.sql` — run once in the Supabase SQL editor.

```sql
-- Agents: each is an identity with a task, a budget, and a live balance.
create table if not exists agents (
    id          text primary key,              -- slug: 'founder','developer',...
    name        text not null,
    task        text not null,
    budget      numeric not null,              -- original allowance (rupees)
    balance     numeric not null,              -- remaining; decremented on spend
    created_at  timestamptz not null default now()
);

-- Transactions: the append-only audit ledger. Every outcome is recorded.
create table if not exists transactions (
    id            uuid primary key default gen_random_uuid(),
    agent_id      text not null references agents(id),
    amount        numeric not null,
    description   text not null,
    decision      text not null,               -- 'allow' | 'escalate' | 'deny'
    status        text not null,               -- 'allowed'|'denied'|'pending'|'approved'
    reason        text not null,               -- plain-English, from the deciding check
    triggered_by  text,                         -- 'rule_engine'|'intent_match'|'anomaly'|null
    intent_source text,                          -- 'llm' | 'fallback' | null
    checks        jsonb not null,               -- full detail of all 3 checks (see below)
    created_at    timestamptz not null default now(),
    resolved_at   timestamptz                   -- set when a human resolves an escalation
);

create index if not exists idx_tx_agent_created on transactions (agent_id, created_at desc);
create index if not exists idx_tx_created on transactions (created_at desc);
```

**`decision` vs `status`** — decision is what the engine *judged*; status is the
*final ledger state*:

| decision | initial status | after human action |
|---|---|---|
| `allow` | `allowed` (balance deducted) | — |
| `deny` | `denied` (no deduction) | — |
| `escalate` | `pending` (no deduction) | `approved` (deduct) or `denied` |

**`checks` jsonb shape** (stored verbatim, also returned by the API):

```json
{
  "rule_engine":  { "passed": true,  "failed_rule": null, "reason": "All rule checks passed." },
  "intent_match": { "ran": true, "match": false, "source": "llm",
                    "reason": "A GPU cluster does not serve building a landing page." },
  "anomaly":      { "ran": true, "flagged": true, "z_score": 4.7, "mean": 43.3, "std": 8.5 }
}
```

Checks that don't run (e.g. intent/anomaly when rules already denied) store
`"ran": false` with nulls — the audit trail stays honest about what actually executed.

---

## 5. Canonical demo data (MUST stay identical to deck)

Seeded by `seed.py` / `POST /reset`. **Do not change these numbers** — the pitch
deck and live demo cross-reference each other, and consistency is a credibility signal.

**Agents:**

| id | name | task | budget | seeded history |
|---|---|---|---|---|
| `founder` | Founder Agent | Plan and launch the startup | ₹5,000 | (none) |
| `developer` | Developer Agent | Build the landing page | ₹6,000 | ₹40, ₹55, ₹35 |
| `research` | Research Agent | Competitor and market research | ₹800 | ₹80, ₹110, ₹95 |
| `marketing` | Marketing Agent | Prepare the launch marketing campaign | ₹2,000 | ₹250, ₹300, ₹280 |

Seeded history is inserted as prior `transactions` rows (status `allowed`) so the
anomaly check has a real mean/std to compute against, and `balance` starts at
`budget` minus the seeded spend.

**The four canonical scenarios** (each maps to a preset button):

| # | Scenario | Request | Expected outcome |
|---|---|---|---|
| 1 | **Normal / Allow** | developer, ₹40, "Image generation API for landing page graphics" | All 3 pass → **Allow** (auto) |
| 2 | **Escalate via anomaly** | research, ₹450, "full industry dataset export" | Intent OK, but ₹450 ≫ ₹80–110 norm (and under the ₹515 balance, so rules pass) → **Escalate** → human approves |
| 3 | **The hijack (hero)** | developer, ₹5,000, "GPU cluster rental for model training" | Under ₹6k budget (rules pass!), intent **fails**, anomaly **flags** → **Escalate** → deny live |
| 4 | **Rule-only block** | developer, ₹10,000, "(any)" | ₹10k > ₹6k budget → **Deny** by rule engine alone |

Scenario 3 is the "wow" — *authorized but nonsensical*, caught by the two smart
checks, not by rules. Scenario 4 exists purely to show the rule engine catching
something on its own.

---

## 6. The policy engine — three checks, one decision

Orchestrated in `policy_engine.py::evaluate(agent, amount, description, db)`.

### 6.1 Rule engine (`rules.py`) — deterministic, no AI, runs first

Runs in order; **first failure denies immediately** (hard rules are never escalated):

1. **Budget check** — `amount > agent.balance` → Deny.
   Reason: `"Exceeds remaining budget of ₹{balance:.0f}."`
2. **Blocklist check** — description matches a blocked category
   (case-insensitive substring against a list: `"crypto exchange"`, `"gift card"`,
   `"wire transfer"`, `"unregistered vendor"`, `"gambling"`). Match → Deny.
   Reason: `"Blocked category: {matched}."`
3. **Velocity check** — count this agent's transactions in the last **10 seconds**;
   if `count >= 5` → Deny. Reason: `"Velocity limit exceeded — {count} requests in 10s."`

Returns `{passed: bool, failed_rule: str|None, reason: str}`.

### 6.2 Intent match (`intent.py`) — the one real AI call

Only runs if rules pass. Single call to **Claude Haiku 4.5**:

```
System/prompt (user message):
An autonomous AI agent's declared task is: "{task}".
It is requesting a payment of ₹{amount} for: "{description}".
Does this purchase reasonably serve the stated task?
Reply with ONLY strict JSON: {"match": true or false, "reason": "one short sentence"}
```

- SDK: `client.messages.create(model="claude-haiku-4-5", max_tokens=200, messages=[...])`.
  (No `thinking`/`effort` params — Haiku 4.5 rejects `effort`; a plain call is correct
  for a one-shot classification.) *Optional hardening:* use structured outputs
  (`output_config.format`) since Haiku 4.5 supports it — guarantees valid JSON.
- Parse the text as JSON → `{match, reason}`, tag `source: "llm"`.
- **Fallback (critical for demo robustness):** if the key is missing, the call
  errors, or JSON is malformed → keyword-overlap heuristic: lowercase both strings,
  strip stopwords, if the task and description share **any** non-trivial word →
  `match: true`, else `match: false`. Tag `source: "fallback"`.
- Returns `{ran: true, match: bool, source: "llm"|"fallback", reason: str}`.

The `source` is surfaced in the UI and health badge so the presenter always knows
whether the real model or the fallback ran.

### 6.3 Anomaly score (`anomaly.py`) — simple statistics, no ML

Only runs if rules pass (runs alongside intent).

- Pull this agent's prior transaction **amounts** (status in `allowed`/`approved`).
- If `< 2` prior transactions → `{ran: true, flagged: false, reason: "Not enough history."}`
  (don't guess on thin data).
- Else compute `mean`, `std` (population std; guard `std == 0`), and
  `z = (amount - mean) / std`. If `z > 2` → `flagged: true`.
  Reason: `"Amount ₹{amount} is {z:.1f}σ above this agent's ₹{mean:.0f} average."`
- Returns `{ran, flagged, z_score, mean, std, reason}`.

### 6.4 Combining into a decision

```
if not rule_engine.passed:
    decision = "deny";  triggered_by = "rule_engine";  reason = rule_engine.reason
elif intent.match and not anomaly.flagged:
    decision = "allow"; triggered_by = None;           reason = "Passed all checks."
else:
    decision = "escalate"
    # reason/triggered_by from whichever smart check objected (intent first, then anomaly)
    if not intent.match:  triggered_by = "intent_match"; reason = intent.reason
    else:                 triggered_by = "anomaly";      reason = anomaly.reason
```

- **Allow** → deduct `amount` from `agent.balance`, status `allowed`.
- **Deny** → no deduction, status `denied`.
- **Escalate** → no deduction yet, status `pending` (human decides).

Every outcome writes one `transactions` row with the full `checks` blob.
Ambiguous cases are **never auto-denied** — they go to a human. That
human-in-the-loop behavior is a core part of the pitch.

---

## 7. Backend — modules & responsibilities

| File | Responsibility |
|---|---|
| `config.py` | Load `DATABASE_URL`, `ANTHROPIC_API_KEY` from env (`python-dotenv`). Expose `LLM_CONFIGURED = bool(key)`. |
| `database.py` | Create SQLAlchemy engine from `DATABASE_URL`; `SessionLocal`; `get_db()` FastAPI dependency. |
| `models.py` | ORM classes `Agent`, `Transaction` matching `schema.sql`. |
| `schemas.py` | Pydantic: `EvaluateRequest`, `ResolveRequest`, `TransactionOut`, `AgentOut`, `DecisionOut`, `HealthOut`. |
| `rules.py` | `run_rules(agent, amount, description, db) -> RuleResult`. |
| `intent.py` | `check_intent(task, amount, description) -> IntentResult` (Claude + fallback). |
| `anomaly.py` | `score_anomaly(agent, amount, db) -> AnomalyResult`. |
| `policy_engine.py` | `evaluate(...)` — calls the three, combines, writes the row, updates balance, returns `DecisionOut`. |
| `seed.py` | `seed(db)` / `reset(db)` — wipe transactions, reset agents + reinsert seeded history. |
| `main.py` | FastAPI app, CORS (`allow_origins=["http://localhost:5173"]`), all routes, startup seeding if empty. |

**Dependencies (`requirements.txt`):** `fastapi`, `uvicorn[standard]`,
`sqlalchemy`, `psycopg[binary]`, `anthropic`, `pydantic`, `python-dotenv`.

---

## 8. API surface (exact contracts)

Base URL: `http://localhost:8000`. All JSON. CORS open to the Vite dev origin.

### `GET /health`
```json
→ 200 { "status": "ok", "llm_configured": true, "db_connected": true }
```
Badge colours: green = `llm_configured && db_connected`; amber = db ok but no key
(fallback mode); red = db unreachable.

### `GET /agents`
```json
→ 200 [ { "id":"developer","name":"Developer Agent","task":"Build the landing page",
          "budget":6000,"balance":5870 }, ... ]
```

### `GET /transactions?limit=50`
Newest first.
```json
→ 200 [ { "id":"...", "agent_id":"developer","amount":5000,
          "description":"GPU cluster rental for model training",
          "decision":"escalate","status":"pending","reason":"...",
          "triggered_by":"intent_match","intent_source":"llm",
          "checks":{...}, "created_at":"...", "resolved_at":null }, ... ]
```

### `POST /evaluate-transaction`
```json
Request:  { "agent_id":"developer", "amount":5000,
            "description":"GPU cluster rental for model training" }
→ 200     { "transaction_id":"...", "decision":"escalate", "status":"pending",
            "reason":"A GPU cluster does not serve building a landing page.",
            "triggered_by":"intent_match", "intent_source":"llm",
            "checks":{ "rule_engine":{...}, "intent_match":{...}, "anomaly":{...} },
            "agent":{ "id":"developer","name":"...","balance":5870 } }
Errors:   404 unknown agent_id; 422 bad body (amount<=0 or empty description)
```

### `POST /resolve-escalation`
```json
Request:  { "transaction_id":"...", "action":"approve" }   // or "deny"
→ 200     { "transaction_id":"...", "status":"approved",
            "agent":{ "id":"developer","balance":870 } }
Errors:   404 unknown id; 409 if transaction is not currently 'pending'
```
On `approve`: deduct amount, status→`approved`, set `resolved_at`.
On `deny`: no deduction, status→`denied`, set `resolved_at`.

### `POST /reset`
```json
→ 200 { "ok": true }
```
Wipes `transactions`, resets agents to canonical budgets/balances, reinserts seeded
history. Use between judges for a clean run.

---

## 8A. Agent integration — how AI agents connect to this platform

> This is the section that turns the project from "a dashboard" into "infrastructure."
> It formalizes `PROJECT_BRIEF.md §7`. It is **conceptually core** but only **optionally
> built** — the hackathon MVP simulates the agent with a button; a real agent loop is a
> stretch/appendix demo (see §15). Read this before answering the "how does an agent
> actually use this?" judge question.

### 8A.1 The mental model — a tool, not a rail

The platform sits **between an agent's intent to pay and money actually moving**. The
agent never touches money; it can only **ask**, through a structured tool call, and this
platform is the only thing that can say *yes*.

- It is a **tool** (something an AI can call to take an action), **not a skill**
  (instructions that make an AI better at a task). It must be a tool because it stands
  between a decision and real money.
- It is **rail-agnostic**: it sits *in front of* whatever payment rail the app uses
  (Visa, Stripe, x402, a mock ledger). It decides *whether* a transaction should happen;
  the rail decides *how* it settles.

### 8A.2 Two distinct places AI appears (do not conflate them)

| | Location | Role | Model | Status in this build |
|---|---|---|---|---|
| **A — the agent** | *Outside* the platform | An autonomous AI agent doing real work that decides it needs to spend | A capable agent model (e.g. `claude-opus-4-8`) | **Simulated** by a button/custom form in the MVP; real loop = stretch |
| **B — intent match** | *Inside* the platform | One classification call: "does this purchase fit the agent's task?" | `claude-haiku-4-5` | **Real** — already specified in §6.2 |

Section B is the AI *inside* your product and is fully built. Section A is the *external*
agent that plugs in. This §8A is about A.

### 8A.3 The integration pattern (5 steps)

```
1. The agent is given a TOOL definition:  request_payment(vendor, amount, reason)
        │
2. Mid-task, the agent's LLM emits a tool call (not plain text):
        request_payment(vendor="Unsplash", amount=40, reason="hero image for landing page")
        │
3. THE APPLICATION CODE (not the LLM) intercepts that call and forwards it to the
   policy engine  →  POST /evaluate-transaction    (it does NOT spend anything here)
        │
4. The policy engine returns:  Allow / Escalate / Deny   (the three checks)
        │
5. The application code acts on the decision:
     • Allow    → perform the REAL purchase, return the result to the agent as the
                  tool_result → the agent continues working
     • Escalate → block the tool call until a human resolves it (Approve/Deny)
     • Deny     → the tool call fails with the reason → the agent must adapt
```

**The load-bearing step is #3:** the agent *thinks* it called a payment tool; it actually
called the judgment layer. Only an **Allow** ever reaches the real rail.

### 8A.4 What is real vs simulated in the hackathon

| Step | Hackathon MVP | Production |
|---|---|---|
| 1–2 (agent asks) | **Simulated** — a preset button or the custom form *is* the agent's `request_payment` call. A legitimate, expected 36-hour simplification. | A real agent's tool-use loop emits the call. |
| 3 (intercept → forward) | **Real** — `POST /evaluate-transaction` (this IS the platform). | Identical. |
| 4 (judge) | **Real** — the three checks. | Identical. |
| 5 (act on decision) | **Real** — mock ledger deduction / escalation / deny. | Same logic; "perform purchase" calls a real rail (or x402, §15). |

Framing for judges: *"the button is the agent's tool call; everything after it is exactly
what runs in production — nothing else changes when you swap the button for a real agent."*

### 8A.5 The tool contract (what the agent sees)

The agent-facing tool is intentionally minimal. The agent supplies its intent; the
`agent_id` and identity are injected by the application, **never** by the model.

```json
{
  "name": "request_payment",
  "description": "Request a payment on behalf of this agent. This does NOT spend money directly — every request is screened by the policy engine first and may be allowed, escalated to a human, or denied.",
  "input_schema": {
    "type": "object",
    "properties": {
      "vendor":  { "type": "string", "description": "Who is being paid" },
      "amount":  { "type": "number", "description": "Amount in rupees" },
      "reason":  { "type": "string", "description": "Why this purchase serves the agent's current task" }
    },
    "required": ["vendor", "amount", "reason"]
  }
}
```

Mapping to `POST /evaluate-transaction` (§8): `amount → amount`, `reason → description`,
and `agent_id` is set by the harness (the agent must not be able to pick which identity it
spends as — that is an authorization boundary, see §14). `vendor` can be folded into the
`description` or logged separately.

### 8A.6 Reference agent loop (Claude — optional stretch)

Illustrative only; **not required for the MVP.** If built, it lives in a standalone
`agent_demo/` folder and must not be a dependency of the core demo. Uses standard Claude
tool use; **the application code — not the model — forwards to the policy engine.**

```python
# agent_demo/run_agent.py  (illustrative)
import os, requests, anthropic

client = anthropic.Anthropic()           # ANTHROPIC_API_KEY from env
API = "http://localhost:8000"
AGENT_ID = "developer"                    # identity is set HERE, never by the model

tools = [{
    "name": "request_payment",
    "description": "Request a payment. Does not spend — it is screened first.",
    "input_schema": {
        "type": "object",
        "properties": {
            "vendor": {"type": "string"},
            "amount": {"type": "number"},
            "reason": {"type": "string"},
        },
        "required": ["vendor", "amount", "reason"],
    },
}]

messages = [{"role": "user",
             "content": "You are the Developer Agent building the landing page. "
                        "Buy a hero image from Unsplash for ~₹40."}]

while True:
    resp = client.messages.create(
        model="claude-opus-4-8", max_tokens=1024, tools=tools, messages=messages)
    if resp.stop_reason != "tool_use":
        break
    messages.append({"role": "assistant", "content": resp.content})
    results = []
    for block in resp.content:
        if block.type == "tool_use" and block.name == "request_payment":
            # STEP 3: intercept — forward to the judgment layer, do NOT spend here
            decision = requests.post(f"{API}/evaluate-transaction", json={
                "agent_id": AGENT_ID,                       # injected, not model-supplied
                "amount": block.input["amount"],
                "description": block.input["reason"],
            }).json()
            # STEP 5: return the verdict to the agent as the tool result
            verdict = f"{decision['decision'].upper()}: {decision['reason']}"
            results.append({"type": "tool_result",
                            "tool_use_id": block.id, "content": verdict})
    messages.append({"role": "user", "content": results})
```

Notes:
- `stop_reason == "tool_use"` drives the loop; append the full `resp.content` and return
  all `tool_result` blocks in one user message (per Claude tool-use rules).
- **Escalate** in this demo returns "ESCALATE" to the agent immediately; a fuller version
  would poll `/transactions` until a human resolves the `pending` row, then continue.
- This is a *second, separate* Claude usage from the intent check (§6.2) — different model,
  different purpose. Keep them mentally distinct.

### 8A.7 Framework note (LangChain / CrewAI / raw loop)

The pattern is framework-agnostic. Any orchestrator exposes a `request_payment` tool whose
handler calls `POST /evaluate-transaction`. LangChain → a `Tool`/`@tool`; CrewAI → a custom
tool; raw Claude/OpenAI → the loop above. The platform doesn't care which — it only ever
sees an HTTP call. That rail-and-framework independence is the pitch: *"plug it into any
agent stack; we're the judgment layer none of them have."*

### 8A.8 The one-liner for judges

> "Any agent framework gives its agent a `request_payment` tool. That tool doesn't spend —
> it calls us. We run three checks and only an *Allow* ever reaches the real payment rail.
> The agent can ask, but we're the only thing that can say yes."

---

## 9. Frontend — component tree & behavior

Single-page dashboard. Polls `/agents` and `/transactions` every **2s**
(`usePolling`) so escalation resolutions and balances stay live without websockets.

```
<App>
 ├─ <Header>            brand • <HealthBadge/> (polls /health) • <ResetButton/>
 ├─ <AgentRoster>       grid of <AgentCard/> — name, task, live budget bar (balance/budget)
 ├─ <RequestPanel>
 │    ├─ 4 preset buttons (the canonical scenarios; button 3 is the big red "Simulate hijacked agent")
 │    └─ custom builder: <select agent> + <amount> + <description> + Submit
 ├─ <ProcessingPanel>   on submit: animate 3 check chips (Rule → Intent → Anomaly),
 │                       then <DecisionBanner> (green Allow / amber Escalate / red Deny)
 │                       + expandable check detail (z-score, intent reason, source tag)
 ├─ <EscalationCard>    shown when latest decision === 'escalate' & status 'pending':
 │                       agent, amount, description, reason, [Approve] [Deny]
 └─ <AuditLog>          newest-first list of <AuditRow/>, colour-coded by status,
                        each row shows agent, amount, decision, reason, source, time
```

**Interaction flow:**
1. User clicks a preset (or fills the custom form) → `POST /evaluate-transaction`.
2. `ProcessingPanel` lights the three chips in sequence (~300ms each) for effect,
   then reveals the real decision from the response.
3. If `escalate`, `EscalationCard` appears; Approve/Deny → `POST /resolve-escalation`.
4. Polling refreshes roster balances and audit log; the "catch" is visible live.

**Styling:** Tailwind, navy (`#0B1F3A`) structure + amber (`#F5A623`) for
decisions/emphasis, semantic green/red for Allow/Deny. Match the pitch deck.

**Health badge** is the presenter's safety signal — at a glance shows whether the
real Claude call or the fallback is running.

---

## 10. Configuration & secrets

**`backend/.env`** (never committed; `.env.example` is the template):
```
DATABASE_URL=postgresql+psycopg://postgres:<password>@<host>:5432/postgres
ANTHROPIC_API_KEY=sk-ant-...
```
- Get `DATABASE_URL` from Supabase → Project Settings → Database → Connection string
  (use the **Session pooler** URI for IPv4-friendliness). Prefix the driver as
  `postgresql+psycopg://` for SQLAlchemy + psycopg 3.
- `ANTHROPIC_API_KEY` is your Claude key. If absent, the backend still runs — intent
  match uses the keyword fallback and `/health` reports `llm_configured: false`.

**`frontend/.env`:**
```
VITE_API_BASE=http://localhost:8000
```

**Secret hygiene:** add `.env` to `.gitignore` before the first commit. Never paste
the key into code, comments, or the frontend. The key lives **only** server-side.

---

## 11. Local setup & run

**One-time:**
1. Create a Supabase project. Open the SQL editor, paste `db/schema.sql`, run it.
2. Copy the connection string + your Claude key into `backend/.env`.
3. Backend deps: `cd backend && python -m venv .venv && .venv\Scripts\activate &&
   pip install -r requirements.txt`
4. Frontend deps: `cd frontend && npm install`

**Every run (two terminals):**
```
# Terminal 1 — backend (seeds canonical data on first start if tables empty)
cd backend && uvicorn main:app --reload --port 8000

# Terminal 2 — frontend
cd frontend && npm run dev      # → http://localhost:5173
```

Sanity check: open `http://localhost:8000/health` → `llm_configured: true`,
`db_connected: true`. Open the dashboard, click reset, run scenario 1.

---

## 12. Build order — demo-safe milestones

> **Golden rule:** never let the working demo depend on the last thing you built.
> After each milestone there is a runnable, showable version.

| Milestone | Deliverable | Demo-safe checkpoint |
|---|---|---|
| **M0 — Foundations** | Repo dirs, `schema.sql` run in Supabase, `.env` wired, backend boots, `/health` green | Backend + DB alive |
| **M1 — Ledger + rule engine** | `models`, `seed`, `rules`, `/agents`, `/transactions`, `/reset`, `/evaluate-transaction` (rules-only decisions) | **Deterministic decisions work end-to-end** — this is the safety net |
| **M2 — Frontend skeleton** | Vite app, `api.js`, Header+HealthBadge+Reset, AgentRoster, RequestPanel, AuditLog, polling | Clickable dashboard showing real transactions |
| **M3 — The differentiator** | `intent.py` (Claude + fallback) + `anomaly.py` wired into `policy_engine`; ProcessingPanel chips + DecisionBanner + check detail | Intent + anomaly catch the hijack |
| **M4 — Escalation loop** | `pending` status, EscalationCard, `/resolve-escalation`, live polling refresh | Human Approve/Deny works live |
| **M5 — Hardening + polish** | Blocklist + velocity real, error states, empty-history handling, styling pass, all 4 scenarios airtight | **Run the full demo start-to-finish 5×** |
| **M6 — Buffer** | Rehearse, fix the one thing that breaks | — |
| **S (stretch)** | x402 on the Research scenario; ntfy.sh phone push | Only if M0–M5 are rock solid |

Order rationale: rules-only (M1) gives a working demo by itself; the LLM/anomaly
(M3) is layered on top; the fancy escalation UI (M4) comes after the core catch
already works. At M1, M3, and M5 you always have something that runs cleanly.

---

## 13. Verification & test plan

For each milestone, drive the actual flow — don't just trust that code compiles.

- **Rule engine:** scenario 4 (₹10k) → Deny with budget reason. A blocked-category
  description → Deny. Fire 6 requests fast → 6th denied on velocity.
- **Intent match (LLM):** scenario 3 GPU/landing-page → `match:false, source:"llm"`.
  Scenario 1 image-API/landing-page → `match:true`. Then unset the key and re-run
  both → identical verdicts via `source:"fallback"` (fallback must not visibly break).
- **Anomaly:** scenario 2 (₹450 vs ₹80–110) → `flagged:true`, sane z-score.
  A ₹100 research request → not flagged. Agent with `<2` history → never flagged.
- **Decision combination:** confirm scenario 3 is Escalate (not Deny) even though
  both smart checks object — ambiguous → human, per the pitch.
- **Escalation loop:** escalate → pending in ledger, balance unchanged; Approve →
  balance drops, status `approved`; Deny → status `denied`, balance unchanged.
- **Reset:** after a messy run, `/reset` returns exact canonical balances.
- **Consistency:** every displayed number matches Section 5 (and the deck).

A lightweight `backend/test_smoke.py` (pytest, hitting the policy engine directly
with a test DB or the seeded one) is worth writing at M5 to lock the four scenarios.

---

## 14. Security review checklist (run before any push/deploy)

This project touches **payments, API endpoints, DB queries, and secrets** — all
review triggers. Even though it's a hackathon mock, run this before pushing:

- **Secrets:** `.env` gitignored; key never in code/frontend/logs; `/health`
  exposes only a boolean, never the key.
- **Input validation:** `amount > 0` and finite; `description` non-empty and length-
  capped; `agent_id` must exist (404 otherwise). Reject oversized bodies.
- **SQL injection:** all DB access via SQLAlchemy params/ORM — no string-built SQL.
- **IDOR / auth:** demo has no auth by design; document that this service is meant to
  sit **behind** the agent runtime as a trusted internal component (have the answer
  ready for judges, don't fake auth in code).
- **Agent-identity boundary (agent integration, §8A):** the `agent_id` an evaluation
  spends against must be injected by the harness/application, **never** supplied by the
  agent's model output. An agent must not be able to choose which identity (and which
  budget) it spends as — that is an authorization boundary. In the reference loop (§8A.6),
  `AGENT_ID` is a constant set in code, not a tool parameter.
- **Concurrency / double-spend:** approving the same escalation twice must not
  double-deduct — guard `resolve` on `status == 'pending'` (409 otherwise); do the
  balance update + status flip in one DB transaction.
- **Replay / velocity:** velocity check itself is a basic anti-abuse control; note it.
- **CORS:** restricted to the Vite origin, not `*`, once past early dev.
- **LLM output:** never `eval`/execute the model's reply; parse as JSON only, and
  fall back safely on malformed output.
- **Prompt injection (the pitch's own threat!):** the `description` is attacker-
  controllable in the story — the system treats a mismatched/suspicious description
  as a *signal to escalate*, never as an instruction. Confirm the intent prompt
  can't be steered by a crafted description into auto-approving (it only asks for a
  JSON verdict; the reasoning is advisory, the decision is code).

If a triggered commit has no issues after review, say so explicitly with the
scenarios checked — don't push silently.

---

## 15. Stretch goals

Only after M0–M5 are airtight and rehearsed.

- **x402 real payment (Coinbase, Base Sepolia testnet)** — put **one** endpoint
  (the Research Agent's report purchase) behind x402 middleware so an approved
  transaction produces a **real on-chain tx hash** shown in the audit log. Free
  facilitator at `https://x402.org/facilitator`; testnet USDC from Circle's faucet.
  The policy engine is unchanged — only the "execute payment" step behind an Allow
  changes from a local decrement to a real x402 call. High-credibility flex; keep it
  scoped to one path so it can't break the core demo.
- **ntfy.sh phone push** — on escalation, push to `https://ntfy.sh/<topic>` with
  Approve/Deny action buttons; the browser subscribes to `<topic>-action` via SSE so
  tapping the phone resolves the transaction live. Most reliable on Android. Great
  "wow," but fragile — strictly optional.
- **Peer-group anomaly** — compare against agents with the same role, not just the
  agent's own history (a stronger, more defensible anomaly story if a judge probes).
- **Real Claude agent loop (agent integration demo)** — build the reference loop from
  §8A.6 in a standalone `agent_demo/` folder: a real Claude agent that emits a
  `request_payment` tool call, which the harness forwards to `POST /evaluate-transaction`.
  Shows steps 1–2 of §8A.3 as *real AI* instead of a button. Highest "this is real
  infrastructure" flex. **Must be standalone** — never a dependency of the core demo, so
  it can't break the guaranteed path. `agent_id` is injected by the harness, never chosen
  by the model (§14).

---

## 16. Demo-day runbook

1. **Before judges arrive:** backend + frontend running, `/health` green, click
   **Reset**. Test venue wifi — if the live LLM times out, the fallback covers it and
   the badge shows amber; say so honestly if asked.
2. **Set the scene (10s):** point at the roster — four agents, real tasks, real
   budgets, running live in the browser, nothing pre-recorded.
3. **Normal (15s):** run scenario 1 → watch the three chips, then Allow; point at the
   balance actually dropping.
4. **The hijack (20s):** run scenario 3 (big red button) → narrate: same agent, asking
   for something unrelated to its job, *under budget*. It doesn't block — it **asks a
   human**. Click **Deny** live; let the red banner land.
5. **Prove it's not scripted (if a judge engages):** let them type a custom request.
6. **Close on the audit log:** every decision logged with a reason — the trail a real
   deployment needs.
7. **Rehearsed Q&A:** "how is this different from Visa/Stripe?" → *they're the rails,
   we're the judgment layer — none of them check whether a transaction is
   semantically consistent with what the agent is supposed to be doing.*

---

## 17. Judging-criteria map

VYNEDAM uses the same 5×10 scorecard each round. How this build serves each:

| Criterion | How we score |
|---|---|
| **Problem Understanding / Innovation** | The intent+anomaly authorization layer is the genuinely-underbuilt piece; framed as "judgment layer, not another rail" |
| **Solution Approach / Project Stack** | Real stack: React + FastAPI + Supabase Postgres + Claude, all working, logic server-side |
| **Technical Feasibility / Completeness** | Every check runs on a real backend against a real DB — no mockups; the four scenarios are demonstrable and repeatable |
| **Clarity of Pitch** | 2 a.m. story → live hijack catch → traffic-cop line; whole team can present any part |
| **Business Model** | Governance SaaS (Vanta/Snyk-for-agent-spend) priced per agent/seat, usage-based screening fee as upsell — a first-class slide, not an afterthought |

"No halo effect" — judges score what runs. That's why the plan front-loads a
working end-to-end core (M1) and treats the flashy pieces as layers on top.

---

*End of build plan. Every decision needed to start coding is captured above; if
something here is ambiguous during the build, fix it here first, then build.*
