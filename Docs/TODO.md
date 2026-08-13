# TODO — Complete Project Checklist

> **Purpose:** a step-by-step, checkbox-driven task list. When every box here is
> checked, the project is done. Ordered so that each milestone leaves a runnable,
> demoable state (never let the demo depend on the last thing built).
>
> **Grounding rule:** every task traces to `BUILD_PLAN.md` (the how) or
> `PROJECT_BRIEF.md` (the what/why). **Nothing here is invented.** Anything that
> depends on a value only you have (secrets, Supabase details) is listed under
> **§0 Inputs required from you** — do NOT guess those; get them from you or the
> referenced document.
>
> **How to use:** work top to bottom. Do not start a milestone until the previous
> milestone's "Acceptance" boxes are all checked. Tick `[x]` as you go.
>
> **Legend:** `[ ]` todo · `[x]` done · 🔑 needs an input from §0 · ✅ acceptance
> check (must pass before moving on) · 📄 see this doc/section.

---

## §0. Inputs required from you (do not guess these)

These are the only unknowns. Collect them before M0. If any is unavailable, STOP
and ask — do not fabricate a value.

- [ ] 🔑 **Supabase project** created (or confirm you'll create one). Ref: BUILD_PLAN §10.
- [ ] 🔑 **`DATABASE_URL`** — Supabase → Project Settings → Database → Connection
      string (Session pooler URI). Will be rewritten to `postgresql+psycopg://…`.
- [ ] 🔑 **`ANTHROPIC_API_KEY`** — your Claude API key (`sk-ant-…`). Confirmed you
      have one. Used only server-side. If absent → fallback mode (see §Intent).
- [ ] 🔑 **Final project name** — brief says "GuardRail" is an internal placeholder
      only; deck uses the long formal title. Confirm the short name to use in code
      (page title, comments). Until confirmed, code uses a neutral placeholder.
      Ref: PROJECT_BRIEF §1.
- [ ] 🔑 **Currency symbol rendering** — plan uses `₹`. Confirm keep `₹` (vs `Rs`).
      Ref: canonical data BUILD_PLAN §5.
- [ ] 🔑 **Stretch scope** — confirm whether x402 and/or ntfy.sh are in scope at all,
      or strictly "only if time." (Plan default: strictly optional.) Ref: BUILD_PLAN §15.

> Everything below is fully specified by the plan and needs no further input.

---

## §0b. Prerequisites (verify installed; do not assume)

- [x] ✅ **Python** available — verified **3.10.0** via the `py` launcher (`python` is
      not on PATH; use `py` or the venv python). Meets 3.10+.
- [ ] ✅ **Node.js + npm** available (`node --version`, `npm --version`) — need Node 18+
      for Vite. (Not needed until M2 — verify then.)
- [x] ✅ **git** available and repo initialized (`git status` works).
- [ ] Decide package manager for frontend: `npm` (plan default). Confirm if you prefer
      `pnpm`/`yarn`; otherwise proceed with `npm`. (M2.)

---

## §1. Repo hygiene (do first, once)

- [x] Create `.gitignore` at repo root — done (excludes both `.env` files, `.venv`,
      `node_modules`, build dirs, caches).
- [x] ✅ Confirmed `backend/.env` (and `frontend/.env`) are ignored **before** any commit
      via `git check-ignore`. Ref: BUILD_PLAN §10, §14.
- [ ] Create top-level directories: `backend/` + `db/` done; `frontend/` created in M2.
- [ ] Do **not** commit anything yet — commit gates are per milestone and require the
      security review (§14). (Nothing committed so far.)

---

## §2. M0 — Foundations (backend boots, DB reachable, /health green)

Goal: FastAPI runs locally, connects to Supabase, `/health` returns green.
📄 BUILD_PLAN §3 (layout), §4 (schema), §7 (modules), §10 (config), §11 (setup).

### Database
- [x] Write `db/schema.sql` exactly per BUILD_PLAN §4 (both tables + two indexes). Done.
- [ ] 🔑 In Supabase SQL editor, paste and run `db/schema.sql`. **← PENDING (your step)**
- [ ] ✅ Confirm both tables exist in Supabase. **← PENDING (after the step above)**

### Backend scaffold
- [x] Create `backend/requirements.txt` with the exact 7 deps (BUILD_PLAN §7). Done.
- [x] Create `backend/.env.example` with placeholders. Done.
- [ ] 🔑 Create `backend/.env` with the real `DATABASE_URL` (prefix
      `postgresql+psycopg://…`) and `ANTHROPIC_API_KEY`. **← PENDING: file exists with
      empty placeholders; fill it yourself (don't paste secrets into chat).**
- [x] Create virtualenv (`backend/.venv`) and install deps. Done (install OK).
- [x] Implement `backend/config.py` (loads env; `LLM_CONFIGURED`). Done.
- [x] Implement `backend/database.py` (engine/SessionLocal/get_db; lazy engine). Done.
- [x] Implement `backend/models.py` (`Agent`, `Transaction` matching schema). Done.
- [x] Implement `backend/main.py` minimal app: CORS + `GET /health`. Done.
- [x] Run backend — booted in-process (TestClient); `/health` returns 200. Done.

### Acceptance (all must pass to leave M0)
- [ ] ✅ `GET http://localhost:8000/health` → `200` with `db_connected: true`.
      **← PENDING: currently 200 but `db_connected:false` until `backend/.env` +
      Supabase schema are done (the two 🔑 PENDING items above).**
- [x] ✅ `llm_configured` reflects the key — observed `false` (key blank); correct.
- [x] ✅ No secrets printed in logs; `.env` not tracked by git (verified `check-ignore`).

---

## §3. M1 — Ledger + rule engine (deterministic decisions end-to-end)

Goal: the safety-net demo — transactions evaluated by the rule engine, written to
the ledger, balances update. **This alone is a working demo.**
📄 BUILD_PLAN §5 (seed data), §6.1 (rules), §6.4 (combine), §8 (API).

### Seed data
- [x] Implement `backend/seed.py` — `seed(db)` / `reset(db)` that:
      wipe `transactions`, upsert the four canonical agents with exact
      budgets/tasks, insert the seeded history rows (Developer ₹40/55/35,
      Research ₹80/110/95, Marketing ₹250/300/280; Founder none) as prior
      `allowed` transactions, and set each `balance = budget − seeded spend`.
      **Numbers must match BUILD_PLAN §5 exactly.**
- [x] Wire startup seeding in `main.py`: if `agents` empty on boot, call `seed(db)`.
- [ ] ✅ After boot, `agents` table has 4 rows with the exact budgets/balances from §5.

### Pydantic schemas
- [x] Implement `backend/schemas.py` — `EvaluateRequest`, `ResolveRequest`,
      `AgentOut`, `TransactionOut`, `DecisionOut`, `HealthOut` matching the exact
      JSON shapes in BUILD_PLAN §8. Include validation: `amount > 0` & finite,
      `description` non-empty & length-capped.

### Rule engine
- [x] Implement `backend/rules.py::run_rules(agent, amount, description, db)`:
      1) budget check → Deny if `amount > balance`;
      2) blocklist check (case-insensitive substring vs the list in §6.1) → Deny;
      3) velocity check → Deny if ≥5 of this agent's tx in the last 10s.
      Return `{passed, failed_rule, reason}` with the exact reason strings in §6.1.

### Policy engine (rules-only for now)
- [x] Implement `backend/policy_engine.py::evaluate(...)` in a rules-only form:
      run rules; if fail → `deny`; if pass → `allow` (intent/anomaly stubbed as
      "not yet implemented / ran:false"). Write the `transactions` row with the
      `checks` jsonb, update balance on allow, per BUILD_PLAN §6.4 & §4.

### Endpoints
- [x] Implement `POST /evaluate-transaction` (BUILD_PLAN §8) → calls `evaluate`,
      returns `DecisionOut`. Handle 404 unknown agent, 422 bad body.
- [x] Implement `GET /agents` (roster with live balances).
- [x] Implement `GET /transactions?limit=50` (newest first).
- [x] Implement `POST /reset` → `reset(db)` → `{ok:true}`.

### Acceptance
- [ ] ✅ Scenario 4 (developer, ₹10,000) → **Deny** by rule engine, budget reason.
- [ ] ✅ A blocked-category description → **Deny** with the matched category.
- [ ] ✅ Fire 6 quick requests for one agent → 6th **Deny** on velocity.
- [ ] ✅ Scenario 1 (developer, ₹40, image API) → **Allow**; balance drops by ₹40.
- [ ] ✅ `GET /transactions` shows the rows newest-first with reasons.
- [ ] ✅ `POST /reset` restores exact canonical balances (§5).

---

## §4. M2 — Frontend skeleton (clickable dashboard on real data)

Goal: React app that renders roster + audit log from the backend and can submit
requests. No business logic in the browser.
📄 BUILD_PLAN §9 (components), §10 (frontend env), §11 (run).

### Scaffold
- [x] Create Vite React app in `frontend/` (React + Vite 8, React 19). Done.
- [x] Install Tailwind v3 + PostCSS; configured `tailwind.config.js`, `postcss.config.js`
      (ESM), base CSS. `npm run build` passes. Ref: BUILD_PLAN §9.
- [x] Create `frontend/.env.example` and `frontend/.env` with `VITE_API_BASE`. Done.
- [x] Implement `src/theme.js` — plan-default palette (navy `#0B1F3A`, amber `#F5A623`,
      semantic green/red) as the single swap point. **Premium navy+brass is a 1-file swap
      if you prefer it — say the word.**
- [x] Implement `src/api.js` — wrappers for every §8 endpoint (`getHealth`, `getAgents`,
      `getTransactions`, `evaluate`, `reset`; `resolve` defined for M4).

### Components (per BUILD_PLAN §9 tree)
- [x] `Header.jsx` — brand + `HealthBadge` (polls `/health`) + `ResetButton` (`/reset`).
- [x] `AgentRoster.jsx` + `AgentCard.jsx` — name, task, live budget bar (ratio-colored).
- [x] `RequestPanel.jsx` — 4 preset buttons (§5 scenarios; #3 = red "Simulate hijacked
      agent") + custom builder. (No animated ProcessingPanel/DecisionBanner — that's M3.)
- [x] `AuditLog.jsx` + `AuditRow.jsx` — newest-first, color-coded by status; shows
      agent, amount, status, reason, source, time.
- [x] `hooks/usePolling.js` — polls `/agents` and `/transactions` every 2s.
- [x] Wire `App.jsx` to compose the above (+ offline banner when backend unreachable).

### Acceptance
- [ ] ✅ Dashboard loads at `http://localhost:5173`; health badge shows correct color.
- [ ] ✅ Roster shows the 4 agents with live budgets from the backend.
- [ ] ✅ Clicking a preset fires `/evaluate-transaction`; the audit log updates within 2s.
- [ ] ✅ Reset button restores canonical state visibly.

---

## §5. M3 — The differentiator (intent match + anomaly)

Goal: the two "smart" checks that make it more than an if-statement. This is where
the hijack gets caught.
📄 BUILD_PLAN §6.2 (intent), §6.3 (anomaly), §6.4 (combine), §9 (ProcessingPanel).

### Intent match (Claude Haiku 4.5 + fallback)
- [x] Implement `backend/intent.py::check_intent(task, amount, description)` — plain
      `claude-haiku-4-5` call with the §6.2 prompt (no thinking/effort), strict-JSON
      parse tagged `source:"llm"`, keyword-overlap **fallback** (never raises) tagged
      `source:"fallback"`. Done (fallback offline-verified: s1 match, s3 no-match).
      *(Structured-outputs hardening not used — plain call + json parse, per §6.2 default.)*
- [x] ✅ Model id `claude-haiku-4-5` matches the claude-api skill (no date suffix).

### Anomaly score
- [x] Implement `backend/anomaly.py::score_anomaly(agent, amount, db)` per §6.3
      (`<2`→not flagged; else pop mean/std with std==0 guard; `z>2` flags). Offline-
      verified: s1 z=-0.39 (not flagged), s2 & s3 flagged, `<2` history not flagged.

### Wire into the policy engine
- [x] Update `policy_engine.evaluate` to run intent + anomaly on rule-pass and combine
      per §6.4 (extracted `combine()` helper; escalate→`pending`, reason from intent
      then anomaly; real `checks` blob; `intent_source` set). All 4 branches offline-verified.

### Frontend processing panel
- [x] `ProcessingPanel.jsx` — 3 animated check chips (Rule → Intent → Anomaly) then a
      `DecisionBanner` + detail (z-score, intent reason, source). Wired via App state
      (`RequestPanel` delegates to `App.runEvaluate`). `npm run build` passes.

### Acceptance
- [ ] ✅ Scenario 3 (developer, ₹5,000, GPU cluster): rules **pass**, intent
      `match:false source:"llm"`, anomaly `flagged:true` → decision **Escalate**
      (NOT deny — ambiguous goes to human).
- [ ] ✅ Scenario 1 (image API) → intent `match:true` → **Allow**.
- [ ] ✅ Scenario 2 (research, ₹450): intent `match:true`, anomaly `flagged:true`
      → **Escalate**.
- [ ] ✅ **Fallback test:** temporarily unset the key, re-run scenarios 1 & 3 →
      identical verdicts via `source:"fallback"`; badge goes amber; nothing visibly breaks.
- [ ] ✅ Agent with `<2` history is never anomaly-flagged.

---

## §6. M4 — Escalation loop (human-in-the-loop)

Goal: escalations sit as `pending`, a human clicks Approve/Deny, ledger + balance
update live. This is the "it asks a human" moment.
📄 BUILD_PLAN §4 (status), §6.4, §8 (/resolve-escalation), §9 (EscalationCard).

- [x] Confirm `evaluate` writes `status:'pending'` (no deduction) on escalate. (Done in M3.)
- [x] Implement `POST /resolve-escalation` (§8): approve→deduct+`approved`+`resolved_at`,
      deny→`denied`+`resolved_at` (no deduct). **409 guard** if not `pending`; balance +
      status flipped in **one DB transaction**, with **row lock** (`with_for_update`) so
      concurrent double-clicks can't double-spend (§14). Offline-verified: approve 5870→870,
      deny no-change, repeat→None(409), route registered.
- [x] `EscalationCard.jsx` — shown on latest `escalate`/`pending`: agent, amount,
      description, reason, `[Approve]`/`[Deny]` → `resolve()`. `npm run build` passes.
- [x] Ensure polling refreshes roster balance + audit status after resolution
      (`onResolved` clears the card + triggers an immediate refresh, plus the 2s poll).

### Acceptance
- [ ] ✅ Escalate → ledger row `pending`, balance unchanged.
- [ ] ✅ Approve → balance drops by amount, status `approved`, `resolved_at` set.
- [ ] ✅ Deny → status `denied`, balance unchanged.
- [ ] ✅ Approving the same escalation twice does **not** double-deduct (2nd → 409).
- [ ] ✅ Full scenario 3 runs: hijack → escalate → **Deny live** → red banner + audit.

---

## §7. M5 — Hardening + polish (all four scenarios airtight)

Goal: production-feel for a demo; nothing janky when a judge watches.
📄 BUILD_PLAN §6.1 (blocklist/velocity), §9 (styling), §13 (verify).

- [x] Confirm blocklist + velocity fully implemented (not stubs) — verified in M1
      offline; blocklist covered by the smoke test. Done.
- [x] Add graceful error states in the UI — offline banner (backend down),
      ProcessingPanel error banner (now red), EscalationCard inline error. Done.
- [x] Confirm empty-history and `std==0` edge cases handled (no divide-by-zero) —
      verified offline in `anomaly.py` (`<2`→not flagged; `std==0` guarded). Done.
- [ ] Styling pass to match the pitch deck (navy/amber/green-red; projector-legible).
      **← PENDING: needs the live app rendered + your palette choice (plan navy/amber
      vs premium navy+brass). Safe: I won't overhaul styling blind.**
- [x] Write `backend/test_smoke.py` (pytest) locking the four canonical scenarios +
      a blocklist deny (5 tests). Skips cleanly without a DB; `pytest` added to
      requirements. Ref: BUILD_PLAN §13. (File valid — collects 5, skips w/o DATABASE_URL.)
- [x] ✅ Run `pytest` — **5/5 pass** against the live Supabase DB (all four canonical
      scenarios + blocklist). Verified after the scenario-2 ₹450 fix.
- [x] Write repo-root `README.md` quickstart (setup + run), derived from BUILD_PLAN §11. Done.
- [x] ✅ **Consistency audit:** verified at code level — frontend preset amounts
      (40/450/5000/10000) and backend seed all match BUILD_PLAN §5 exactly; agent
      budgets/balances render from the API (no hardcoded UI numbers to drift). Done.

### Acceptance (the big one)
- [ ] ✅ Run the **entire demo start-to-finish 5 times** with a Reset between each —
      no glitches, chips fire cleanly, the "catch" lands every time.

---

## §8. M6 — Buffer & rehearsal

- [ ] Rehearse the runbook (BUILD_PLAN §16) end-to-end, timed.
- [ ] Memorize the "how is this different from Visa/Stripe" answer (rails vs judgment
      layer). Ref: BUILD_PLAN §16, PROJECT_BRIEF §1.
- [ ] Fix the single most-likely-to-break thing found in rehearsal.
- [ ] Test on the actual venue wifi if possible; confirm fallback + amber badge behave.

---

## §8A. Agent integration (concept = CORE · real agent loop = STRETCH)

Goal: be able to explain and, optionally, demonstrate how a real AI agent plugs into
the platform. The **concept and the judge answer are required**; the **built real-agent
loop is optional** (stretch). 📄 BUILD_PLAN §8A (all subsections), §14 (identity boundary).

### 8A-a. Concept & framing (REQUIRED — no code)
- [x] ✅ Understand the mental model: the platform is a **tool, not a rail** — it sits
      between the agent's intent to pay and money moving; the agent can only *ask*, and
      this platform is the only thing that can say yes. Ref: BUILD_PLAN §8A.1.
- [x] ✅ Keep the **two AI locations** straight: (A) the external **agent** that spends
      = simulated by a button in the MVP; (B) the internal **intent-match** call
      (`claude-haiku-4-5`) = real, already built. Ref: BUILD_PLAN §8A.2.
- [x] ✅ Know the **5-step integration pattern** cold: tool def → agent emits tool call →
      **app code intercepts & forwards to `POST /evaluate-transaction`** → Allow/Escalate/
      Deny → app acts (spend / block for human / fail). Ref: BUILD_PLAN §8A.3.
- [x] ✅ Be able to say **what is real vs simulated** in the demo: the button *is* the
      agent's `request_payment` call; steps 3–5 are exactly production. Ref: BUILD_PLAN §8A.4.
- [x] Memorize the one-liner (BUILD_PLAN §8A.8): *"Any agent framework gives its agent a
      `request_payment` tool. That tool doesn't spend — it calls us. Only an Allow ever
      reaches the real rail. The agent can ask, but we're the only thing that can say yes."*
- [x] Confirm the tool contract maps cleanly to the API: `amount→amount`, `reason→
      description`, and **`agent_id` is injected by the harness, never by the model**.
      Ref: BUILD_PLAN §8A.5.

### 8A-b. Security boundary carried into the build (REQUIRED)
- [x] ✅ **Audited & PASSES:** `agent_id` enters only via `EvaluateRequest.agent_id`
      (HTTP body, harness-supplied); the LLM call `check_intent(task, amount, description)`
      never receives `agent_id`, so the model can't pick the identity/budget charged. No
      agent code passes it from model output. Ref: BUILD_PLAN §14.

### 8A-c. Real Claude agent loop (STRETCH — only if M0–M6 rock solid) 🔑 §0
> Do NOT build until the core demo is airtight and rehearsed. Must be **standalone** —
> never a dependency of the guaranteed demo path. Ref: BUILD_PLAN §8A.6, §15.
- [x] Create a separate `agent_demo/` folder (isolated from `backend/`, `frontend/`). Done.
- [x] Add `agent_demo/requirements.txt`: `anthropic`, `requests`. Done.
- [x] Implement `agent_demo/run_agent.py` per BUILD_PLAN §8A.6 — `request_payment` tool
      (vendor/amount/reason, **no `agent_id`**), Claude tool-use loop (`claude-opus-4-8`,
      safety-capped), harness POSTs to `/evaluate-transaction` with **hardcoded `AGENT_ID`**.
      Syntax-verified (`py_compile`); security-audited (no `agent_id` in tool schema). Done.
- [ ] (Optional deeper) On **Escalate**, poll `GET /transactions` until resolved. Left as a
      documented comment in `run_agent.py`; not implemented (optional).
- [ ] ✅ Run it against the live backend. **← PENDING: needs live backend
      (`db_connected:true`) + `ANTHROPIC_API_KEY` (the agent has no fallback).**
- [x] ✅ Killing `agent_demo/` has **zero effect** on the core demo — structurally
      isolated (imports nothing from backend/frontend; nothing imports it).

---

## §9. Security review (REQUIRED before any push/deploy)

This project touches payments, API endpoints, DB, and secrets — all review triggers
(user's global rule). Run the full BUILD_PLAN §14 checklist and record the result.
📄 BUILD_PLAN §14; the `/security-review` skill may assist.

- [ ] Secrets: `.env` gitignored; key never in code/frontend/logs; `/health` exposes
      only booleans.
- [ ] Input validation: amount > 0 & finite; description non-empty & length-capped;
      unknown agent → 404; oversized body rejected.
- [ ] SQL injection: all access via SQLAlchemy params/ORM; no string-built SQL.
- [ ] Auth/IDOR: documented as trusted-internal (behind the agent runtime); don't fake
      auth in code; have the judge answer ready.
- [ ] Agent-identity boundary (§8A): `agent_id` is injected by the harness/app, never
      chosen by an agent's model output — an agent must not pick which budget it spends
      as. In any agent code, `AGENT_ID` is a code constant, not a tool parameter.
      Ref: BUILD_PLAN §14, §8A.5.
- [ ] Concurrency/double-spend: resolve guarded on `status=='pending'`; balance+status
      in one transaction.
- [ ] Prompt injection (the pitch's own threat): a crafted `description` can only
      **escalate**, never steer the engine to auto-approve — confirm the intent prompt
      returns only a JSON verdict and the decision is made in code, not by the model.
- [ ] CORS restricted to the Vite origin (not `*`).
- [ ] LLM output never executed; parsed as JSON only; safe fallback on malformed output.
- [ ] ✅ Record findings. If none, state the scenarios checked explicitly (don't push
      silently). Get user confirmation before pushing per the global rule.

---

## §10. Commit & push gates

> Commit/push only when the user asks. Do not add AI/Claude attribution to commits or
> PRs (user's global rule). Run §9 before any push that touches trigger areas.

- [ ] Confirm `.gitignore` excludes both `.env` files and build/venv dirs.
- [ ] Stage only intended files (no secrets, no `node_modules`, no `.venv`).
- [ ] Write a plain commit message (subject + optional body), no AI attribution.
- [ ] 🔑 Get user go-ahead to commit/push (and confirm branch — main is default here).

---

## §11. Stretch goals (ONLY if M0–M6 rock solid) 🔑 confirm scope in §0

📄 BUILD_PLAN §15.

- [ ] **x402 (Base Sepolia testnet)** on the Research Agent's report purchase only:
      one endpoint behind x402 middleware; approved tx produces a real on-chain hash
      shown in the audit log. Policy engine unchanged; only the "execute payment" step
      changes. Facilitator `https://x402.org/facilitator`; testnet USDC from Circle
      faucet. 🔑 Needs a testnet wallet address (throwaway) — ask user.
- [x] **ntfy.sh phone push** — BUILT: `frontend/src/ntfy.js` + `NotifyPanel.jsx`,
      wired in `App.jsx`. On escalation, publishes an Approve/Deny prompt to
      `ntfy.sh/<topic>`; browser subscribes to `<topic>-action` via SSE and resolves
      live on a phone tap. Round-trip **verified headlessly** (publish → tap →
      `approve|<txid>` received). Live phone tap = user's step. Additive (doesn't touch
      the core path — the in-dashboard EscalationCard still works if push is off).
- [ ] **Peer-group anomaly** — compare against same-role agents, not just own history
      (stronger story if a judge probes).

---

## §12. Definition of Done (final gate — all must be true)

- [ ] ✅ Backend runs locally; `/health` green with the real Claude key.
- [ ] ✅ Supabase holds the canonical agents + a live audit ledger that persists across
      backend restarts.
- [ ] ✅ All three checks run **server-side**; the browser holds no policy logic.
- [ ] ✅ All four canonical scenarios (§5) behave exactly as specified, repeatably.
- [ ] ✅ The hijack demo (scenario 3) catches, escalates, and denies live, cleanly.
- [ ] ✅ Fallback mode works with no key (amber badge, `source:"fallback"`).
- [ ] ✅ Reset gives a clean canonical run every time.
- [ ] ✅ Numbers in UI == BUILD_PLAN §5 == pitch deck (consistency).
- [ ] ✅ Security review (§9) completed and recorded.
- [ ] ✅ Agent integration concept + judge answer understood (§8A-a/b); if the real agent
      loop (§8A-c) was built, it's standalone and doesn't touch the core demo.
- [ ] ✅ README quickstart present; demo rehearsed 5×.

**When every box above is checked, the project is complete.**

---

*Any ambiguity discovered while executing a task: fix it in `BUILD_PLAN.md` first (or
ask the user), then continue — never guess.*
