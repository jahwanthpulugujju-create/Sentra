# Sentra , The Authority Boundary for Autonomous Agents

> **“An agent can propose an action. Sentra decides whether it has authority to execute it.”**


## Problem Statement

When an autonomous AI agent is given access to software tools, prompt injections, ambiguous requests, corrupted payloads, or burst loops must **never** automatically become execution. Model guardrails and prompt filters can suggest or explain, but they do **not** issue cryptographic execution authority. 

Sentra sits between the agent and protected tools as an independent, deterministic authority boundary.


## 60-Second Demo Path

1. **Start Backend Server**:
   ```bash
   cd backend
   .venv\Scripts\python.exe -m uvicorn main:app --reload --port 8000
   ```
2. **Start Frontend Instrument**:
   ```bash
   cd frontend
   npm run dev
   ```
3. **Open Browser**: Open `http://localhost:5173`.
4. **Run Live Boundary Scenarios**:
   - Click **1. Valid Action** ➔ Verdict `ALLOW` ➔ Gateway executes protected deployment (State Changed 1x).
   - Click **2. Unauthorized Tool** ➔ Verdict `DENY` ➔ Blocked before execution.
   - Click **3. Prompt Injection** ➔ Verdict `ESCALATE` ➔ Escalated before capability issuance.
   - Click **4. Changed Request** ➔ Verdict `DENY` ➔ Gateway detects request hash mismatch.
   - Click **5. Burst Anomaly** ➔ Verdict `FREEZE` ➔ Safety boundary frozen.
   - Click **6. Replay Attempt** ➔ Verdict `DENY` ➔ Gateway blocks reused capability.
5. **Audit Proof Chain**: Click **Audit Proof Chain** to verify SHA-256 event hash integrity.


## System Architecture

```
[ Operations Agent ]
        │
        ▼
┌────────────────────────────────────────┐
│ 1. CANONICALIZER                       │
│    Sorts JSON keys, normalizes params, │
│    computes requestHash = SHA-256(...) │
└───────────────────┬────────────────────┘
                    │
                    ▼
┌────────────────────────────────────────┐
│ 2. DETERMINISTIC POLICY KERNEL (v1.0)  │
│    Fail-closed evaluation rules:       │
│    ALLOW | DENY | ESCALATE | FREEZE    │
└───────────────────┬────────────────────┘
                    │ (If ALLOW)
                    ▼
┌────────────────────────────────────────┐
│ 3. CAPABILITY ISSUER                   │
│    Issues HMAC-SHA256 signed capability│
│    bound to requestHash, TTL, nonce    │
└───────────────────┬────────────────────┘
                    │
                    ▼
┌────────────────────────────────────────┐
│ 4. INDEPENDENT GATEWAY                 │
│    Only code path that mutates state.  │
│    Atomically consumes capability.     │
└───────────────────┬────────────────────┘
                    │
                    ▼
┌────────────────────────────────────────┐
│ 5. PROOF CHAIN                         │
│    eventHash = SHA256(prevHash + data) │
│    Immutable tamper-evident ledger     │
└────────────────────────────────────────┘
```


## Automated Test Command

Run the complete test suite verifying all 11 Playbook enforcement rules:
```bash
backend\.venv\Scripts\python.exe -m pytest backend/test_playbook.py -v
```


## Repository Structure

- `backend/`: FastAPI authority engine, canonicalizer, policy kernel, capability issuer, gateway, and proof chain.
- `frontend/`: React + Vite "Authority Instrument" UI.
- `demo-script.md`: Step-by-step judge runbook.
- `progress-update.md`: Completed scope, limitations, and future roadmap.
- `Docs/adr/`: Architecture Decision Records.
