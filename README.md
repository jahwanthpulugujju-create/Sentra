# Sentra — The Judgment Layer for Autonomous AI Payments

A decision layer that sits between an autonomous agent's intent to pay and the
payment actually happening. Every payment request is screened by three checks —
a deterministic **rule engine** (budget, blocked vendors, velocity), an
**intent match** (does the purchase fit the agent's declared task?), and an
**anomaly score** (is the amount normal for this agent?) — and returns
**Allow / Escalate / Deny**, with a plain-English reason logged every time.
Ambiguous cases escalate to a human instead of being auto-denied.

Positioning: *"Visa and Stripe build the payment rails — Sentra is the judgment
layer that decides whether a transaction should happen at all."*

## Stack

- **Frontend:** React + Vite + Tailwind (thin client — no policy logic in the browser)
- **Backend:** FastAPI (Python), runs locally
- **Database:** SQLite (local) / Supabase (hosted Postgres) via SQLAlchemy
- **Intent check:** Gemini 2.5 Flash classification call, with a keyword-overlap fallback
  when no API key is configured

Full design in `Docs/BUILD_PLAN.md`.

## Prerequisites

- Python 3.10+
- Node.js 18+
- Optional: a Gemini API key for the real intent check (without it, the intent
  check uses the keyword fallback)

## One-time setup

1. **Backend env** — copy `backend/.env.example` to `backend/.env` and fill in:
   - `DATABASE_URL` — leave empty for local SQLite, or set your Postgres connection string
   - `GEMINI_API_KEY` — optional; enables the LLM-backed intent check

2. **Backend deps**
   ```
   py -m venv backend/.venv
   backend/.venv/Scripts/python.exe -m pip install -r backend/requirements.txt
   ```

3. **Frontend deps**
   ```
   npm install --prefix frontend
   ```

## Run (two terminals)

```
# Terminal 1 — backend (auto-seeds the demo agents on first boot)
backend/.venv/Scripts/python.exe -m uvicorn main:app --app-dir backend --reload --port 8000

# Terminal 2 — frontend
npm run dev --prefix frontend        # -> http://localhost:5173
```

Health check: open `http://localhost:8000/health` — it should report
`"db_connected": true`.

## Demo scenarios

Six presets in the dashboard (and a custom request builder):

| Scenario | Request | Expected |
|---|---|---|
| Normal | Developer buys image API — ₹40 | **Allow** |
| Anomaly | Research buys dataset — ₹450 | **Escalate** (unusual amount) |
| Hijack | Developer wants a GPU cluster — ₹5,000 | **Escalate** (under budget, but off-task) |
| Overspend | Developer requests ₹10,000 | **Deny** (rule engine — over budget) |
| Prompt injection | Developer with injected instructions — ₹4,000 | **Escalate** (injection detected, off-task) |
| Social engineering | Founder with fake urgency — ₹3,000 | **Escalate** (no task history match) |

Escalated transactions wait as `pending` until a human clicks **Approve** or
**Deny**. Use **Reset demo** in the header to return to a clean state between runs.

## Key features

- **Risk scoring** — every transaction gets a 0–100 risk score with specific risk factors
- **Evaluation metrics** — live dashboard showing escalation rate, threat detection rate, processing time
- **Adversarial resilience** — prompt injection and social engineering presets for live demo
- **LLM authority boundaries** — clear indicators showing when the LLM was/wasn't consulted and its role

## Tests

```
backend/.venv/Scripts/python.exe -m pytest backend/test_smoke.py -v
```

## Project layout

```
backend/    FastAPI app: policy engine (rules, intent, anomaly), metrics, ledger, endpoints
frontend/   React dashboard (roster, request panel, processing UI, metrics, audit log)
db/         schema.sql
Docs/       PROJECT_BRIEF.md, BUILD_PLAN.md
```
