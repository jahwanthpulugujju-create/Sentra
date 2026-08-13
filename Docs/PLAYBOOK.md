# Sentra Winner-Readiness Playbook

## First, the honest rule

No checklist can **guarantee** a first prize. Judges can value a different problem, presentation quality, execution reliability, or surprise factor on the day. What this playbook can do is remove the common reasons strong ideas lose: an oversized scope, an unclear value proposition, an unconvincing demo, shallow evidence, weak repository hygiene, or a beautiful but nonfunctional interface.

The current workbook ranks the **updated Sentra repositioning** at **#3 of the top 75, with 41/50**. Sanchari is #1 at 44/50 and RetainIQ is #2 at 41/50. Treat that as a competitive baseline, not as proof that Sentra will win Round 2. The original abstract and the updated workbook record are different evidence sources; no points should be claimed for the current MVP unless the judges see it run.

> **Winning standard:** A judge should be able to understand the danger in 10 seconds, see Sentra stop that danger in 60 seconds, inspect the evidence in another 60 seconds, and believe the scope is realistic for the hackathon.

## The one sentence judges must remember

> **“An agent can propose an action. Sentra decides whether it has authority to execute it.”**

Do not open with “AI governance,” “multi agent architecture,” “policy engine,” or “secure payments.” Those are supporting terms. Open with the irreversible failure: an autonomous agent is about to use a protected tool. A prompt injection, changed request, replay, or unsafe scope must not turn into execution.

## What has to be true before you call Sentra competition-ready

| Dimension | Non-negotiable outcome | Proof the judge can see |
| --- | --- | --- |
| Problem | A nontechnical judge immediately understands why agent authority is dangerous. | A single protected action and a plain-language risk statement. |
| Product | Sentra controls execution, not merely gives a recommendation. | Protected state changes only after `ALLOW`. |
| Security mechanism | Policy, capability, gateway, and proof are distinct responsibilities. | A visible request → decision → capability → gateway → proof sequence. |
| Feasibility | The MVP is narrow enough for a 24-hour build. | One protected tool, six repeatable scenarios, no oversized integrations. |
| Technical depth | The mechanism is deterministic where it must be deterministic. | Canonical request hash, exact capability binding, expiry, nonce/replay checks, independent verification. |
| Impact | The project solves a real category of risk beyond a single demo. | A clear first buyer or user, such as an agent platform or operations team. |
| Clarity | The story is readable without a security background. | One command, one verdict, one side effect or refusal, one proof record. |
| Reliability | A demo failure does not destroy trust. | Scripted scenarios, reset button, seeded state, test command, and a fallback recording. |

## The MVP scope: build one authority boundary perfectly

The biggest danger is building a broad “AI governance platform” that is only a dashboard. Do **not** add multiple tools, multiple agents, external payment APIs, chat, real-time collaboration, a marketplace, or a large policy language before the core boundary is indisputable.

### Mandatory user story

> An operations agent proposes a protected software action. Sentra canonicalizes the request, applies deterministic policy, issues a short-lived signed capability only if the action is allowed, and the gateway independently verifies that capability. The protected action changes state only after successful verification. Every result enters a hash-linked proof chain.

### Mandatory scenarios

| Scenario label | Expected verdict | Protected action may change? | What it proves |
| --- | --- | --- | --- |
| Valid Action | `ALLOW` | Yes, exactly once | The normal path is useful, not only restrictive. |
| Unauthorized Tool | `DENY` | No | An agent cannot invoke a tool outside its granted scope. |
| Prompt Injection | `ESCALATE` | No | Untrusted or ambiguous instruction content does not become authority. |
| Changed Request | `DENY` | No | Approval of one request cannot be reused for a changed request. |
| Burst Anomaly | `FREEZE` | No | Suspicious repeated activity creates a safety boundary. |
| Replay Attempt | `DENY` | No | A consumed or expired capability cannot cause a second side effect. |

## Build checklist: backend and enforcement

### A. Request contract and canonicalization

- [ ] Define a minimal request schema: `agentId`, `tool`, `action`, `resource`, `parameters`, `requestedAt`, `nonce`, and `policyVersion`.
- [ ] Reject missing, unknown, malformed, oversized, or ambiguous fields before policy evaluation.
- [ ] Canonicalize JSON deterministically: fixed key ordering, normalized numbers, explicit null handling, and a stable UTF-8 encoding.
- [ ] Compute `requestHash = SHA-256(canonicalRequest)`.
- [ ] Persist the canonical request and the request hash together.
- [ ] Show the hash in the interface, but never expose secrets or raw credentials.
- [ ] Test that the same logical request produces the same hash and that one changed field produces a different hash.

### B. Deterministic policy kernel

- [ ] Keep the policy kernel separate from the language model and the UI.
- [ ] Return only the exact policy outcomes: `ALLOW`, `DENY`, `ESCALATE`, or `FREEZE`.
- [ ] Make high-risk conditions fail closed: missing policy, unknown tool, expired time window, invalid resource, unsupported action, or dependency failure.
- [ ] Version every policy decision with `policyVersion`.
- [ ] Store compact machine-readable reason codes as well as a human-readable explanation.
- [ ] Do not let an LLM directly write an allow decision, capability, or gateway verdict.
- [ ] Add unit tests for every rule and a regression test for every bug found during the event.

### C. Capability issuer

- [ ] Issue a capability only after a deterministic `ALLOW` result.
- [ ] Bind the capability to `requestHash`, `agentId`, `tool`, `action`, `resource`, `policyVersion`, `issuedAt`, `expiresAt`, and `nonce`.
- [ ] Sign it using a server-held signing key. For a hackathon MVP, an HMAC is acceptable if clearly documented; asymmetric signing is stronger if implemented safely.
- [ ] Use a short expiry measured in minutes, not hours or days.
- [ ] Give each capability a unique identifier and record its status: issued, consumed, expired, revoked, or rejected.
- [ ] Never expose the server signing key to the browser.

### D. Independent gateway

- [ ] Make the gateway the **only** code path that can execute the protected action.
- [ ] Verify signature, expiry, nonce, capability status, request hash, tool, action, resource, and policy version at the gateway.
- [ ] Consume the capability atomically before executing the protected action.
- [ ] Reject a replay before it touches the action handler.
- [ ] Do not trust an allow verdict sent directly from the browser or the agent.
- [ ] Record both gateway verification result and execution result.
- [ ] Add an integration test proving that bypassing the gateway cannot change the protected state.

### E. Evidence chain and persistence

- [ ] Store `authorityEvents` with request, decision, capability, gateway, execution, timestamp, and `previousEventHash`.
- [ ] Create `eventHash = SHA-256(previousEventHash + canonicalEventPayload)`.
- [ ] Persist a monotonic event sequence number.
- [ ] Store protected resource state separately from authority events.
- [ ] Provide a replay view that reconstructs the decision trail without triggering the action again.
- [ ] Add a test that detects a modified event, a broken previous hash, and an out-of-order event.
- [ ] Use database transactions around capability consumption and protected-state change.

### F. API surface

| Endpoint or procedure | Responsibility | Must reject |
| --- | --- | --- |
| `runScenario(scenario)` | Creates a demo request and runs it through the real authority path. | Unknown scenario names and malformed input. |
| `evaluate(request)` | Canonicalizes and evaluates a request. | Browser-supplied allow results or ignored validation errors. |
| `verifyAndExecute(capability, request)` | Gateway-owned verification and protected execution. | Hash mismatch, wrong scope, expiry, replay, invalid signature. |
| `dashboard()` | Returns current state, recent decisions, and proof data. | Secret fields, signing material, or mutable internal state. |
| `replay(eventId)` | Reconstructs evidence only. | Any side effect or action execution. |
| `resetDemo()` | Restores deterministic demo state. | Public production access; keep it demo-only and visibly labeled. |

## Build checklist: database and tests

| Table | Minimum fields | Evidence requirement |
| --- | --- | --- |
| `protected_resources` | id, label, state, updatedAt | State changes only through the gateway. |
| `authority_events` | id, sequence, requestHash, decision, reasonCode, previousHash, eventHash, createdAt | Forms the hash-linked proof chain. |
| `capabilities` | id, requestHash, scope, expiresAt, status, consumedAt | Supports exact scope and replay refusal. |
| `demo_runs` | id, scenario, startedAt, completedAt, outcome | Makes the judge demo reproducible. |
| `policy_versions` | id, version, rulesDigest, createdAt | Allows a decision to be tied to the rules used. |

### Required automated tests

- [ ] Canonicalization stability and changed-input hash tests.
- [ ] `ALLOW` creates exactly one valid capability.
- [ ] `DENY`, `ESCALATE`, and `FREEZE` create no executable capability.
- [ ] Gateway rejects invalid signature.
- [ ] Gateway rejects expired capability.
- [ ] Gateway rejects changed request hash.
- [ ] Gateway rejects reused nonce or consumed capability.
- [ ] Gateway executes exactly once under a valid capability.
- [ ] Proof-chain verifier detects one tampered record.
- [ ] Reset function restores a known demo baseline.
- [ ] UI receives the same verdict and proof ID returned by the server.

## Build checklist: frontend and user experience

The website should not look like a generic dark “cybersecurity dashboard.” Dark background, neon gradients, floating glass cards, and animated particles are not evidence. They make every product look the same and hide the real system.

### Design direction: **The Authority Instrument**

Use a warm-white canvas, deep navy type, restrained oxblood for decision emphasis, pale blue for traceable system surfaces, and small green only for verified healthy states. The visual language should feel like a precision instrument or an inspected record, not a gaming interface.

| Visual decision | Do | Avoid |
| --- | --- | --- |
| Background | White, ivory, pale blue evidence areas, subtle ruled grid. | Full black backgrounds, neon glows, fake “matrix” effects. |
| Typography | One high-legibility sans serif, one restrained mono for hashes and status. | Multiple novelty fonts or all-caps everywhere. |
| Hero | One clear sentence plus a living request-to-authority artifact. | Generic “secure AI for the future” headline. |
| Color | Oxblood only for authority, green only for verified success, amber for caution. | Rainbow semantic states or decorative gradients. |
| Motion | Input-responsive, verdict-driven, or proof-sequence motion. | Constant loops that add no information. |
| Cards | Evidence records, precise labels, high information density where needed. | Large empty glassmorphism cards with vague copy. |

### Page architecture

1. **Hero:** “Every agent action needs a real yes.” Show Agent → Policy → Capability → Gateway → Protected Action. A valid result changes the central state; a refusal holds it.
2. **Live boundary test:** The six one-click scenarios. The next action is obvious. A verdict appears before any protected-state change.
3. **Decision inspector:** Canonical request, decision reason, signed capability, gateway verification, execution result. Use expandable details instead of dumping text everywhere.
4. **Proof chain:** A timeline of ordered, hash-linked records. Selecting one record reveals the evidence packet.
5. **Four authority planes:** Control, Data, Enforcement, Evidence. Make each plane explain one responsibility only.
6. **MVP status:** Completed, intentionally not included, known limitation, and test evidence. This is where honest scope becomes a strength.
7. **Closing:** “The model can change its reasoning. It cannot change its authority.”

### Interaction and motion checklist

- [ ] Hero artifact reacts softly to pointer movement on desktop but remains stable on touch screens.
- [ ] A scenario click creates a visible request path, then a verdict, then either one execution state change or a visually clear refusal.
- [ ] Decision rows reveal their evidence progressively; no flashing or long looping animation.
- [ ] Proof chain highlights the current record and shows its relationship to the previous hash.
- [ ] Buttons respond within 160 ms and show loading state during server calls.
- [ ] All motion honors `prefers-reduced-motion`.
- [ ] Keyboard focus remains visible and every scenario can be activated with a keyboard.
- [ ] No information depends only on color; use labels and icons as well.

## Automated demo and proof options

The demo should be deterministic, user-triggered, and resettable. A timed or background process is not necessary for a hackathon demo and adds failure points.

| Approach | Tradeoffs | Cost | Setup complexity |
| --- | --- | --- | --- |
| **In-app scenario runner** | Best live-judge experience; every click passes through the real backend and records proof. | No additional service cost. | Medium. |
| **Command-line regression runner** | Fastest pre-demo verification; less visual for judges. | No additional service cost. | Low. |
| **Pre-recorded backup walkthrough** | Saves the presentation if venue Wi-Fi or a browser fails; does not replace the live proof. | No additional service cost. | Low. |

For the event, use the **in-app scenario runner as the primary path**, run the command-line test suite before the judges arrive, and keep a short recording as a contingency. Do not depend on a scheduled job, polling loop, or third-party integration for the core demonstration.

## Repository and engineering-quality checklist

- [ ] `README.md` begins with the exact problem, the 60-second demo path, and a system diagram.
- [ ] Include a one-command local setup and one-command test command.
- [ ] Include a `demo-script.md` with scenario order, expected verdict, and reset step.
- [ ] Include `progress-update.md` stating completed work, current limitations, and next work honestly.
- [ ] Include architecture decision records for canonicalization, capability binding, gateway ownership, and proof chaining.
- [ ] Include `.env.example` with no secrets.
- [ ] Ensure secret keys are never committed, logged, or rendered in the UI.
- [ ] Use deterministic fixtures for the six scenarios.
- [ ] Keep test output readable and include a brief pass/fail summary in the interface.
- [ ] Provide a simple system diagram and one data-flow diagram in the repository.
- [ ] Tag the final demo commit and preserve the commit hash shown during judging.

## Judge demo runbook

### Before the judge arrives

- [ ] Open the deployed site in a fresh private browser window.
- [ ] Reset the demo to a known baseline.
- [ ] Run the full automated test command once and capture the passing output.
- [ ] Verify all six scenario controls respond.
- [ ] Keep the repository, architecture page, and short backup recording in separate tabs.
- [ ] Turn off notifications, browser auto-fill, and unrelated extensions.
- [ ] Have a one-line answer ready for “why not just use an LLM guardrail?”

### The first 90 seconds

1. State the risk: “An agent has a tool. A prompt or error should not become authority.”
2. Run **Valid Action**. Point to the one allowed protected-state change.
3. Run **Unauthorized Tool**. Point to `DENY` and unchanged protected state.
4. Run **Changed Request** or **Replay Attempt**. Point to capability mismatch or consumed capability.
5. Open the evidence record. Show canonical hash, signed capability scope, gateway verdict, and proof hash.
6. Close with the one-sentence Sentra message.

### Questions you must answer precisely

| Judge question | Strong, evidence-bound answer |
| --- | --- |
| “Is this only a dashboard?” | “No. The gateway is the only execution path. The protected state changes only after the gateway verifies a signed, request-bound capability.” |
| “Why not use an LLM guardrail?” | “The language model can propose or explain, but it does not issue authority. The allow path is deterministic and independently verified.” |
| “What stops replay?” | “The capability is short-lived, request-bound, and atomically consumed. A reused capability is rejected before the protected action.” |
| “Can the request change after approval?” | “No. The capability contains the request hash. A changed request produces a mismatch and is denied.” |
| "Can you build this in 24 hours?" | "The demo scope is one protected tool, one gateway, six fixed scenarios, persistent proof, and a small interface. We deliberately excluded broad integrations." |
| "Who will use it?" | "The first user is a team deploying autonomous agents that can call protected software tools and needs a verifiable final authority boundary." |

## Failure plan

| Failure | Immediate response | What not to do |
| --- | --- | --- |
| Network fails | Use the local or preloaded deployment, then show the recorded run only if necessary. | Spend minutes debugging in silence. |
| One scenario breaks | Run the next deterministic scenario, show the test output, state the known limitation. | Claim the broken scenario is working. |
| Judge challenges novelty | Demonstrate request-bound capability, independent gateway, changed-request refusal, and replay refusal. | Make an unverified claim that no one else does this. |
| Judge challenges scope | Show the exact excluded features and build order. | Add unfinished integrations during the demo. |
| UI looks polished but feature is unclear | Return immediately to one valid action and one denied action. | Continue clicking around the dashboard. |

## 24-hour priority order

| Time window | Build target | Exit condition |
| --- | --- | --- |
| Hours 0–3 | Request schema, canonicalization, deterministic policy rules. | Valid and invalid requests return deterministic verdicts. |
| Hours 3–6 | Capability issuer and gateway verification. | Invalid or changed capability cannot execute a protected action. |
| Hours 6–9 | Database events, hashes, replay protection, proof verifier. | One full event chain can be replayed and tampering is detectable. |
| Hours 9–13 | Six scenario fixtures and automated tests. | All six scenarios pass from a clean reset. |
| Hours 13–17 | Live authority interface and decision inspector. | A judge can run two cases without developer help. |
| Hours 17–20 | Proof timeline, architecture view, README, demo script. | Repository explains the project without a live presenter. |
| Hours 20–22 | Stress test, reset path, backup recording, bug fixes. | Demo survives refresh, reset, and repeated scenario runs. |
| Hours 22–24 | Rehearsal, deletion of nonessential work, final polish. | The team can deliver the 90-second story without improvising. |

## Final submission gate

Do not call the project ready until every statement below is true.

- [ ] The valid action executes once and only once.
- [ ] Every invalid scenario leaves the protected action unchanged.
- [ ] The current decision is stored with canonical request, capability, gateway, and proof evidence.
- [ ] The replay scenario fails after capability consumption.
- [ ] The changed-request scenario fails on hash mismatch.
- [ ] The demo starts in a known clean state.
- [ ] The UI is bright, readable, and distinct from generic dark AI-security dashboards.
- [ ] The repository can be cloned, configured, tested, and demonstrated by another person.
- [ ] The presentation uses the live evidence before architecture buzzwords.
- [ ] Every limitation is stated honestly.
