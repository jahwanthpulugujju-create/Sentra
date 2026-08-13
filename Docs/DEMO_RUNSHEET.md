# Demo Run-Sheet & Pitch Cue-Card

> Printable rehearsal aid for **M6** (`Docs/agents/M6.md`). Everything here is
> assembled from `BUILD_PLAN.md §16/§17` and `PROJECT_BRIEF.md §1/§8` — no new
> claims. Rehearse with this until the delivery is automatic. (Rehearsal itself is
> the team's job; this is the script.)

---

## 0. Pre-demo checklist (run right before judges — 60 seconds)

- [ ] Backend running (`/health` shows `db_connected: true`).
- [ ] Frontend open at `http://localhost:5173`, **full screen**.
- [ ] Click **Reset demo** → roster shows the 4 agents at full/expected balances.
- [ ] Wifi tested. If the LLM is slow/unreachable, the intent check uses the local
      fallback and the badge goes **amber** — that's fine, say so if asked.
- [ ] Hijack preset (the red "Simulate hijacked agent — GPU cluster ₹5,000") in view.

---

## 1. The ~90-second demo (narrate present-tense; adapt length to your slot)

**① Opening hook — the 2 a.m. scene (10–15s).** *(say, don't click)*
> "It's 2 a.m. Your startup's AI agents are working while you sleep — one's
> building your landing page, one's doing research, one's running marketing. You
> wake up to a notification: **₹40,000 gone.** One agent got prompt-injected and
> 'bought' a service that doesn't exist. It was authorized. It was under budget.
> Every payment rail on earth would have approved it — because none of them ask
> *does this make sense?*"

**② Set the scene (10s).** *(point at the roster)*
> "These are four AI agents — each with a real task and a real budget. This is
> running live in the browser right now. Nothing here is pre-recorded."

**③ Normal transaction (15s).** *(click preset 1 — Developer buys image API ₹40)*
> "Watch — the rule engine checks the budget, then intent match and anomaly score
> run." *(chips light → **Allow**)* "That's a real decision, and the balance
> actually dropped."

**④ The hijack — your moment (20s).** *(click the red hijack preset)*
> "Same developer agent — but now it's asking for a GPU cluster. It's *under
> budget*, so every rail would approve it. But it has **nothing to do with its
> job.**" *(chips → intent fails, anomaly flags → **Escalate**)* "It doesn't block
> your business — it **asks a human.**" *(click **Deny** — let the red land)*
> "Caught in under a second, and it can tell you exactly why."

**⑤ Prove it's not scripted (only if a judge leans in).** *(offer the custom form)*
> "Try your own — any agent, any amount, any description."

**⑥ Close on the audit log (10s).** *(scroll to it)*
> "Every decision — allowed, escalated, denied — is logged with a reason. That's
> the audit trail a real deployment needs." Then the one-liner:
> **"Visa and Stripe are building the roads. We're the traffic cop."**

---

## 2. Q&A cheat-sheet (say these instantly, word-for-word)

**"How is this different from Visa / Stripe / Mastercard?"** *(the one that matters)*
> "They're the **rails** — identity and authorization. We're the **judgment
> layer** — none of them check whether a transaction is *semantically consistent
> with what the agent is supposed to be doing.* We sit in front of any rail."

**"Isn't this what Visa/Stripe already launched?"**
> "They launched the rails — 'is this agent authorized and under budget?' We answer
> the question they don't: 'does this payment make sense?' Authorized ≠ safe."

**"Who pays for this? / What's the business model?"** *(BUILD_PLAN §17, PROJECT_BRIEF §8)*
> "Governance SaaS — think **Vanta or Snyk, but for agent spend.** Priced per agent
> or per compliance seat, with a usage-based screening fee as the upsell. Buyers:
> fintechs building agent checkout, enterprises rolling out internal agent fleets,
> and agent-orchestration platforms who need a safety story to sell to enterprise."

**"What's the use case — why does anyone need this?"**
> "No serious company lets an autonomous agent hold a company card without an audit
> trail and a kill switch. That's the blocker between 'agents that chat' and 'agents
> that spend.' We're selling the thing that has to exist first."

**"What if the injected purchase looks plausible?"** *(the hard one)*
> "No single check is complete — that's why there are three. Intent match catches
> off-task spend, anomaly catches abnormal amounts, and the rule engine's velocity
> limits and blocklists catch what semantics miss. Layered defense."

**"Could a crafted description trick it into approving?"** *(prompt-injection)*
> "No — the model only returns a verdict; the **decision is made in code.** A
> suspicious description can only ever *escalate to a human*, never auto-approve."

---

## 3. If the wifi dies mid-demo

Stay calm — it's designed for this. The intent check falls back to a local keyword
heuristic, the health badge turns **amber**, and the demo still runs (the hijack
still escalates). Honest line: *"we're on the local fallback right now — the badge
shows it — and the judgment still fires."*

---

## 4. Judging map (what each moment earns — BUILD_PLAN §17)

| Criterion | Your proof |
|---|---|
| Problem / Innovation | "judgment layer, not another rail" |
| Solution / Stack | React + FastAPI + Supabase + LLM, all live, logic server-side |
| Completeness | three checks on a real backend + DB; the catch is repeatable |
| Clarity of Pitch | the 2 a.m. story + the traffic-cop line; whole team can present |
| Business Model | governance SaaS — a real slide, not an afterthought |

---

*Rehearse the §1 script + §2 answers until they're automatic. The demo isn't "ready"
until it has run 5× clean start-to-finish (M6 acceptance). "Works on my machine" ≠
"ran 5× clean."*
