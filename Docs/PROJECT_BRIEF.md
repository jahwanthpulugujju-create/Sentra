# Project Brief: The Judgment Layer for Autonomous Agent Payments

This document is a complete handoff brief. It contains everything about the
project's purpose, architecture, current state, and remaining work, so an
engineer (or Claude Code) can pick it up with zero prior context and know
exactly what exists, what's missing, and what to build next.

---

## 1. What this project is, in one paragraph

AI agents are starting to spend money on their own — buying API access, data,
compute, and services without a human approving every transaction. Every major
payment company (Visa, Mastercard, Stripe, Coinbase) has recently launched
infrastructure that lets an agent be *authorized* to pay: it proves who it is
and confirms it's under its spending limit. None of that infrastructure checks
whether a payment actually **makes sense**. An agent that has been hijacked by
a prompt injection, or is simply buggy, can be fully authorized and still make
a payment that has nothing to do with its actual job — and every existing
system would approve it, because "authorized" is the only question any of them
ask. This project is a decision layer that sits between an agent's intent to
pay and the payment actually happening. It checks three things — hard rules,
whether the purchase matches the agent's declared task, and whether the amount
is normal for that agent's behavior — and returns Allow, Escalate (to a human),
or Deny, with a plain-English reason logged every time.

**Current working name:** "The Judgment Layer for Autonomous Agent Payments."
No short brand name has been finalized — earlier drafts used "GuardRail" as a
placeholder internally; that name has been fully removed from the pitch deck.
Feel free to introduce a new short name, but note the phrase above is what's
currently on the pitch deck as the formal title.

**One-line positioning:** *"Visa and Stripe are building the roads. This is
the traffic cop."* — the rails (Visa, Mastercard, Stripe, Coinbase) handle
identity and authorization; this project is the judgment layer that decides
whether an authorized transaction should actually happen.

---

## 2. Context: why this exists

This is being built for a hackathon: **VYNEDAM Talent Hunt 2K26**, a 36-hour
hackathon with four judged rounds:

1. **Round 1 — Idea Pitching**: concept-and-approach discussion, no working
   code required. Scored on 5 criteria, 10 points each (50 total): Problem
   Understanding, Solution Approach, Technical Feasibility, Innovation &
   Uniqueness, Clarity of Pitch.
2. **Rounds 2, 3, 4 — Build Progress / Integration / Final Showcase**: each
   scored on the *same* 50-point scorecard (5 criteria x 10 points): Pitch,
   Team Active, Project Stack, **Project Completeness** (how much actually
   works — real functioning features vs. mockups), and **Business Model**.
   The bar for what counts as "good" rises each round, but the criteria don't
   change.

Judges are explicitly instructed to score what they *see running*, not what's
promised — a great pitch does not excuse a broken build ("no halo effect").
This means the highest-leverage work between now and judging is making things
that are currently simulated in the browser actually run on a real backend,
not adding new features.

---

## 3. The core architecture — three checks, one decision

Every payment request an agent makes goes through the same pipeline:

```
Agent requests payment
        |
        v
+---------------------------------------------+
|              POLICY ENGINE                   |
| (three checks run, two of them in parallel)  |
|                                               |
|  1. Rule engine       (deterministic, fast)  |
|  2. Intent match      (LLM call)             |
|  3. Anomaly score     (simple statistics)    |
+---------------------------------------------+
        |
        v
     Decision: Allow / Escalate / Deny
        |
        v
   Audit log (every outcome recorded with a reason)
```

### 3.1 Rule engine (deterministic, no AI)
Checks, in order:
- **Budget check**: is the requested amount <= the agent's remaining balance?
  If not -> immediate **Deny**, reason: "Exceeds remaining budget of RsX."
- **Blocklist check**: does the purchase description match a blocked category
  (e.g. "crypto exchange", "gift card", "wire transfer", "unregistered
  vendor")? If so -> immediate **Deny**.
- **Velocity check** (conceptual, not yet fully implemented): is this agent
  making requests unusually fast? Intended to catch a runaway loop.
- If all rule checks pass, proceed to the next two checks (they run in
  parallel, not sequentially).

### 3.2 Intent match (the one real AI call in the whole system)
A single call to Claude (`claude-sonnet-4-6`) with a prompt shaped like:

> An autonomous AI agent's declared task is: "{task}". It is requesting a
> payment of Rs{amount} for: "{description}". Does this purchase reasonably
> serve the stated task? Reply with ONLY strict JSON: `{"match": true or
> false, "reason": "one short sentence"}`

This is intentionally the *only* AI call in the system. It is not
multi-step, not agentic, not a framework — one classification call per
transaction. **Important reliability detail**: if this call fails (bad wifi,
missing API key, timeout), the system must fall back to a local
keyword-overlap heuristic (compare non-trivial words in the task vs. the
purchase description; if they share any words, treat as a loose match) so the
demo never visibly breaks. Every response should be tagged with its
`source`: `"llm"` or `"fallback"`, and the UI should be honest about which one
ran.

### 3.3 Anomaly score (simple statistics, not ML)
Compare the requested amount to the agent's own transaction history:
- Compute mean and standard deviation of the agent's past transaction amounts.
- Compute a z-score: `(amount - mean) / std`.
- If z-score > 2, flag as anomalous.
- If the agent has fewer than 2 past transactions, treat as "not enough
  history — not flagged" rather than guessing.

No machine learning model is needed or wanted here — the simplicity is a
deliberate scope decision, not a shortcut.

### 3.4 Combining the three checks into a decision
- Any rule engine failure -> **Deny** immediately (hard rule violations never
  go to a human — they're not judgment calls).
- If rules pass, and **both** intent match succeeds and anomaly is not
  flagged -> **Allow** automatically, no human involved.
- If rules pass but **either** intent match fails **or** anomaly is flagged ->
  **Escalate** to a human for a yes/no decision. (This is deliberate: the
  system does not auto-deny ambiguous cases, it asks a human — that
  human-in-the-loop behavior is a core part of the pitch.)
- Every outcome (Allow, Escalate->Approved, Escalate->Denied, Deny) gets written
  to an audit log with: timestamp, agent, amount, description, decision, and
  the reason text from whichever check produced it.

---

## 4. The running example used consistently across every demo and slide

To keep the pitch, the deck, and the live demo all telling the same story,
one specific scenario is used everywhere. **Keep these exact numbers
consistent in any further work** — judges may cross-reference the deck
against the live demo, and consistency itself is a credibility signal.

**Agents** (each is just an identity: name, one-line task, a budget):

| Agent | Task | Budget | Seeded transaction history |
|---|---|---|---|
| Founder Agent | Plan and launch the startup | Rs5,000 | (none) |
| Developer Agent | Build the landing page | Rs6,000 | Rs40, Rs55, Rs35 |
| Research Agent | Competitor and market research | Rs800 | Rs80, Rs110, Rs95 |
| Marketing Agent | Prepare the launch marketing campaign | Rs2,000 | Rs250, Rs300, Rs280 |

**The four canonical scenarios:**

1. **Normal / Allow**: Developer Agent requests Rs40 for "Image generation API
   for landing page graphics." Passes all three checks. Allowed automatically.
2. **Escalation via anomaly, not attack**: Research Agent requests Rs450 for
   "full industry dataset export" — intent match actually agrees it's
   plausible, but the amount is far outside its normal Rs80-110 range, so it
   escalates. A human approves it because it's reasonable, just unusual. This
   scenario demonstrates the system doesn't just block big numbers — it asks.
3. **The hijack (the pitch's hero scenario)**: Developer Agent, mid-task, gets
   prompt-injected via a malicious webpage and requests Rs5,000 for "GPU
   cluster rental for model training." This passes the rule engine (Rs5,000 <
   Rs6,000 budget — this is the whole point: it's *authorized* but doesn't make
   sense). Intent match fails (task was "landing page," not compute).
   Anomaly score also flags it (Rs5,000 vs. a Rs35-55 history). It escalates,
   and the demo shows denying it live.
4. **A fourth, distinct example used only on the "Rule engine" explanation
   slide**: a hypothetical Rs10,000 request against the Developer Agent's
   Rs6,000 budget — this is blocked by the rule engine alone, before intent
   match or anomaly ever run. This exists specifically to show the rule
   engine catching something on its own, since the hijack scenario is caught
   by the *other* two checks, not by rules.

---

## 5. What is already built and working right now

### 5.1 Frontend — `GuardRail_Live_Demo.html`
A single self-contained HTML file (vanilla JS, no framework, no build step).
Structure:
- An in-memory `agents` object (JS, not persisted) matching the table above.
- A UI with: an agent roster panel (name, task, live budget bar), a "Try it"
  panel with four preset buttons (three normal scenarios + one big red
  "Simulate hijacked agent" button) and a free-form custom request builder
  (pick any agent, type any amount/description) so a skeptical judge can run
  their own scenario live, not just watch a scripted demo.
- A "live processing" panel that visually lights up three check chips (Rule
  engine, Intent match, Anomaly score) in sequence/parallel as a request is
  processed, then shows a decision banner (Allow / Escalate / Deny).
- If escalated: an approval card appears with **Approve** / **Deny** buttons
  a human clicks.
- On Allow (automatic or after human approval): a receipt renders (fake
  transaction ID, timestamp, updated balance) and the agent's wallet balance
  in the roster panel actually decreases — this is real in-memory state, not
  decoration.
- An audit log at the bottom, newest-first, color-coded by decision.
- **Notifications**: a panel lets the presenter (1) enable a browser
  `Notification` (native OS popup, fires on any escalation) and (2) connect a
  phone via **ntfy.sh** — a free, no-signup push notification relay. On
  escalation, a push notification is sent to `https://ntfy.sh/<topic>` with
  ntfy's `Actions` header defining **Approve** and **Deny** buttons that,
  when tapped on the phone, POST to a second topic (`<topic>-action`). The
  browser subscribes to that second topic live via Server-Sent Events
  (`new EventSource('https://ntfy.sh/<topic>-action/sse')`), so tapping
  Approve/Deny on the phone notification itself resolves the pending
  transaction in the browser in real time — no custom backend needed for
  this part, ntfy.sh alone provides the round trip. Caveat: this is most
  reliable on Android; on iOS the ntfy app may briefly open before the action
  fires.
- **Backend connection status badge** in the header: pings `/health` on load
  and shows green ("connected - live LLM"), amber ("connected - no API key
  set"), or red ("offline - using local fallback") — so the presenter always
  knows, at a glance, whether the demo is doing the real thing.

### 5.2 Backend — `GuardRail_Backend_main.py` (FastAPI, Python)
Currently implements **only the intent-match check** as a real server-side
endpoint (this was built specifically to fix a critical bug: the frontend
used to call Anthropic's API directly from the browser with no key, which
only worked inside Claude's own chat interface — it silently fails on a
standalone laptop with no key configured). Endpoints:
- `POST /check-intent` — body: `{task: string, description: string, amount:
  number}`. Calls Claude via the `anthropic` Python SDK using an API key from
  the `ANTHROPIC_API_KEY` environment variable. Returns `{match: bool,
  reason: string, source: "llm" | "fallback"}`. Falls back to the same
  keyword-overlap heuristic as the frontend used to have, if the key is
  missing or the call fails, so it degrades gracefully.
- `GET /health` — returns `{status: "ok", llm_configured: bool}`.
- CORS is wide open (`allow_origins=["*"]`) — fine for a local hackathon demo,
  should be restricted if ever deployed publicly.
- Tested and confirmed working end-to-end (including the fallback path with
  no key configured, which correctly returned `match: false` for the GPU
  cluster / landing page mismatch and `match: true` for the image API /
  landing page match).

**The frontend's `callIntentCheck` function now calls this backend
(`http://localhost:8000/check-intent`) instead of Anthropic directly.**

### 5.3 Pitch deck — `Pitch_Deck.pptx`
10 slides, built with pptxgenjs, two-color palette (navy for structure,
amber for emphasis/decisions — no red, no teal/green, no third hue). Content
flow: title -> the 2am problem story -> market stats (why now) -> the
rails-vs-judgment gap -> the three-pillar solution -> the process flow diagram
-> the live-demo cue slide (normal vs. hijacked) -> business model -> tech
stack (accurately marked as built vs. not-yet-built) -> closing. All
situational examples throughout use the exact numbers from Section 4 above,
consistently.

---

## 6. What is NOT built yet — the real remaining work

This is the actual task list. In priority order:

1. **Move the rule engine and anomaly score into the backend.** Right now
   only intent-match is server-side; the rule engine and anomaly scoring
   still run as JavaScript in the browser. All three checks should live in
   one backend endpoint (e.g. `POST /evaluate-transaction`) that takes
   `{agent_id, amount, description}`, runs all three checks, and returns the
   full decision — so the *entire* decision happens on a real server, not
   two-thirds in the browser.
2. **Add PostgreSQL for persistent state.** Currently agent balances and
   transaction history live only in JS memory (frontend) — refresh the page
   and it resets. Needs at minimum two tables:
   - `agents`: id, name, task, budget, balance
   - `transactions`: id, agent_id, amount, description, decision, reason,
     source (llm/fallback), created_at
3. **Consolidate the API surface.** Once the backend owns all three checks
   and the database, the frontend should become a thin client that just
   calls the backend and renders results — no business logic in the browser
   at all.
4. **(Optional stretch, not required)**: integrate one real payment rail —
   **x402** (Coinbase's open, no-approval-needed agent payment protocol,
   settling in testnet USDC on Base Sepolia) — for exactly one scenario
   (suggested: the Research Agent's report purchase), so at least one
   transaction in the demo produces a real, verifiable on-chain transaction
   hash instead of a fake one. Free public facilitator at
   `https://x402.org/facilitator`; a Python SDK exists and fits the existing
   FastAPI backend. This is explicitly optional — a fully working three-check
   system with a clean in-memory or Postgres ledger scores higher than a
   half-working real payment bolted onto a broken core system.

---

## 7. How a real AI agent would actually connect to this (for context)

This system is designed to be used as a **tool**, not a skill. The
distinction: a Skill is instructions that make an AI better at doing
something; a Tool is something an AI can actually call to take an action.
This project must be a tool, because it stands between a decision and real
money moving.

The integration pattern, concretely:
1. A real agent (built separately, out of scope for the hackathon) is given
   a tool definition, e.g. `request_payment(vendor, amount, reason)`.
2. Mid-task, the agent's LLM emits a structured tool call instead of plain
   text: `request_payment(vendor="Unsplash API", amount=40, reason="hero
   image for landing page")`.
3. The application code (not the LLM) intercepts that call and forwards it
   to this policy engine instead of spending anything.
4. The policy engine returns Allow / Escalate / Deny.
5. If Allow: the application code performs the *actual* purchase and returns
   the result to the agent as its tool result, so it can continue working.
   If Escalate: the tool call blocks until a human responds. If Deny: the
   tool call fails immediately with the reason, and the agent must adapt.

**The agent itself never touches money — it can only ask, through a
structured call, and this system is the only thing that can say yes.** For
the hackathon, simulating step 1-2 with a button press (as the current demo
does) is a legitimate and sufficient simplification; the part that has to be
real is step 3 onward, which is what the FastAPI backend does.

---

## 8. Business model (for context, not code — but relevant if asked to build anything monetization-related)

- **Who pays**: fintechs building agent checkout, enterprises deploying
  internal agent fleets, and agent-orchestration platforms who need to prove
  to *their* enterprise customers that agents are safe to trust with money.
- **Revenue model**: usage-based fee per transaction screened (same model as
  fraud-detection tools like Stripe Radar), plus a subscription tier for the
  audit/compliance dashboard.
- **Path to scale**: whichever payment rail wins (Visa's, Stripe's, a crypto
  rail), its enterprise customers will still need a judgment layer on top —
  this plugs into any rail, not just one.

---

## 9. Files that already exist (attach these to Claude Code if not already provided)

- `Pitch_Deck.pptx` — the 10-slide deck described in Section 5.3.
- `GuardRail_Live_Demo.html` — the working frontend described in Section 5.1.
- `GuardRail_Backend_main.py` — the working FastAPI backend described in
  Section 5.2.
- `GuardRail_Backend_requirements.txt` — `fastapi`, `uvicorn`, `anthropic`,
  `pydantic`.

Note: the HTML and backend files still contain the internal placeholder name
"GuardRail" throughout (page title, comments, variable names) — this was
deliberately left alone since only the pitch deck's naming was requested to
be genericized so far. Rename at will if a final project name is chosen.

---

## 10. Suggested first prompt to give Claude Code

> Read PROJECT_BRIEF.md in full before doing anything else. I have an
> existing working prototype: [attach GuardRail_Live_Demo.html and
> GuardRail_Backend_main.py]. Your task, in order: (1) move the rule engine
> and anomaly-score logic out of the frontend JS and into the FastAPI
> backend as a single `POST /evaluate-transaction` endpoint that runs all
> three checks and returns one decision; (2) add a PostgreSQL-backed ledger
> using the schema in Section 6 of the brief, replacing the in-memory JS
> state; (3) update the frontend to call only the new consolidated endpoint
> and render whatever it returns, removing all business logic from the
> browser. Keep the existing UI, notification system (ntfy.sh), and the
> exact agent/amount numbers in Section 4 unchanged — those are referenced
> directly in the pitch deck and must stay consistent.
