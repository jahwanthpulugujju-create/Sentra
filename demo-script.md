# Sentra Judge Demo Runbook

## Setup Before Judges Arrive
1. Open `http://localhost:5173` in a fresh browser tab.
2. Click **Reset Baseline State** to ensure clean demo state.
3. Open a secondary tab with `http://localhost:8000/dashboard` and terminal ready with pytest command.

---

## 90-Second Judging Script

### 1. The Opening Hook (10 Seconds)
> “An agent can propose an action. Sentra decides whether it has authority to execute it.”

### 2. Valid Action Demo (20 Seconds)
1. Click **1. Valid Action**.
2. Point out:
   - Request canonicalized into SHA-256 hash.
   - Policy kernel returns `ALLOW`.
   - HMAC-SHA256 capability issued.
   - Independent Gateway verifies capability and executes state change (`deployCount: 1`).

### 3. Attack & Boundary Refusals (40 Seconds)
1. Click **2. Unauthorized Tool** ➔ Point out `DENY` verdict and 0 capabilities issued.
2. Click **3. Prompt Injection** ➔ Point out `ESCALATE` verdict on instruction context override.
3. Click **4. Changed Request** ➔ Point out `DENY` verdict at Gateway due to request hash mismatch.
4. Click **6. Replay Attempt** ➔ Point out `DENY` verdict blocking consumed capability reuse.

### 4. Proof Chain Evidence (15 Seconds)
1. Scroll to **Hash-Linked Proof Chain Ledger**.
2. Click **Audit Proof Chain** ➔ Point to green `Chain Verified` status badge.
3. Select an event row to display its SHA-256 hash link to `previous_hash`.

### 5. Closing Statement (5 Seconds)
> “The model can change its reasoning. It cannot change its authority.”
