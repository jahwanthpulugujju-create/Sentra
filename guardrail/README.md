# GuardRail — Natural-Language, Four-Environment Live Demo

Type a payment request in plain English into an agent and watch a real
three-check policy engine decide **ALLOW / ESCALATE / DENY** — with real phone
push (ntfy.sh) for the human-in-the-loop moment. Self-contained: FastAPI
backend (in-memory) + a single `index.html` (no framework).

Uses the **canonical agent data and decision logic** from `../Docs/PROJECT_BRIEF.md`.

## Decision logic (canonical)
1. Rule engine fails (over budget / blocked vendor / velocity) → **DENY** —
   intent + anomaly are skipped (no LLM call, ~ms).
2. Rule passes → run intent match + anomaly score.
3. Intent matches **and** not anomalous → **ALLOW**.
4. Intent fails **or** anomaly flagged → **ESCALATE** (a human decides; never
   auto-deny on intent/anomaly alone).

Intent uses `claude-haiku-4-5`; with no key it falls back to keyword matching
(kept for bad wifi). Anomaly flags when the z-score of the amount vs the
agent's history exceeds 2.

## Agents (canonical)
| Agent | Task | Budget | History |
|---|---|---|---|
| Founder | Plan and launch the startup | ₹5,000 | (none) |
| Developer | Build the landing page | ₹6,000 | ₹40, ₹55, ₹35 |
| Research | Competitor and market research | ₹800 | ₹80, ₹110, ₹95 |
| Marketing | Prepare the launch marketing campaign | ₹2,000 | ₹250, ₹300, ₹280 |

## Setup & run
1. *(Optional)* real intent check: `set ANTHROPIC_API_KEY=sk-ant-...` (cmd) or
   `$env:ANTHROPIC_API_KEY="sk-ant-..."` (PowerShell). Without it, keyword fallback.
2. Backend (port 8000):
   ```
   py -m venv guardrail/.venv
   guardrail\.venv\Scripts\python.exe -m pip install -r guardrail/requirements.txt
   guardrail\.venv\Scripts\python.exe -m uvicorn main:app --app-dir guardrail --port 8000
   ```
3. Frontend (port 3000), second terminal, then open http://localhost:3000:
   ```
   cd guardrail
   py -m http.server 3000
   ```

## The four environments
1. **Auto-Approve** — Developer → *"Buy hero image from Unsplash for ₹40"* → **ALLOWED** (~ms).
2. **Escalate (judgment)** — Research → *"Buy full industry dataset from SimilarWeb for ₹450"* →
   **ESCALATED** (intent OK, but ₹450 is ~29σ above its ₹95 history).
   *(Note: the original ₹2,400 exceeds Research's canonical ₹800 budget, so it would deny on
   the budget rule; ₹450 keeps the canonical budget and escalates via anomaly as intended.)*
3. **Escalate (hijack)** — Developer → *"Purchase GPU cluster rental for ₹5,000"* →
   **ESCALATED** (under the ₹6,000 budget, but off-task and anomalous).
4. **Auto-Deny** — Developer → *"Buy gaming laptop for ₹85,000"* → **DENIED** (over budget;
   intent + anomaly skipped).

Judges can type **anything** into the box — it's parsed and judged live.

## Phone push (ntfy.sh — no tunnel)
Copy the topic in the "Phone push" panel → Subscribe in the ntfy app → Send test →
run an escalation. The phone's Approve/Deny buttons POST to `<topic>-action`; the
browser subscribes over SSE and relays the decision to `POST /resolve` — no public
backend / ngrok needed. (In-dashboard Approve/Deny buttons also appear on escalation.)

## Endpoints
`GET /health` · `GET /agents` · `GET /transactions?limit=50` ·
`POST /evaluate {agent_id, amount, description}` ·
`POST /chat-prompt {agent_id, message}` ·
`POST /resolve {transaction_id, approved}` · `POST /reset`
