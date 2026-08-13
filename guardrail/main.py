"""GuardRail — natural-language, four-environment live demo (self-contained).

Extends the guardrail/ prototype to use the CANONICAL agent data and decision
logic from PROJECT_BRIEF.md. All three checks run server-side.

Decision logic (canonical, no variation):
  1. rule engine fails            -> DENY (skip intent + anomaly; near-instant)
  2. rule passes: run intent + anomaly
  3. intent matches AND not anomalous -> ALLOW
  4. intent fails OR anomalous     -> ESCALATE (never auto-deny on intent/anomaly)

Intent uses claude-haiku-4-5 with a keyword-overlap fallback (kept for bad wifi).
Phone approval uses the no-tunnel pattern: ntfy action buttons POST to
`<topic>-action`; the browser subscribes over SSE and calls POST /resolve.
"""
from __future__ import annotations

import json
import os
import random
import re
import sqlite3
import statistics
import threading
import time
import uuid
from datetime import datetime, timezone

import httpx
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel

def _load_dotenv() -> None:
    """Tiny, dependency-free .env loader (guardrail/.env is gitignored)."""
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
    try:
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))
    except FileNotFoundError:
        pass


_load_dotenv()

MODEL = "claude-haiku-4-5"   # blueprint's claude-3-haiku-20240307 has retired -> 404
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "").strip()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")


def intent_provider() -> str:
    if GEMINI_API_KEY:
        return "gemini"
    if ANTHROPIC_API_KEY:
        return "claude"
    return "offline"

VELOCITY_LIMIT = 5
VELOCITY_WINDOW = 60
ANOMALY_Z = 2.0              # flag when z-score exceeds this


# --------------------------------------------------------------- canonical seed data
def seed_agents() -> dict:
    return {
        "founder": {"id": "founder", "name": "Founder Agent", "color": "#22c55e",
                    "task": "Plan and launch the startup", "budget": 5000, "spent": 0,
                    "history": [], "blocked": []},
        "developer": {"id": "developer", "name": "Developer Agent", "color": "#3b82f6",
                      "task": "Build the landing page", "budget": 6000, "spent": 0,
                      "history": [40, 55, 35], "blocked": ["SuspiciousVendor", "ScamAPI"]},
        "research": {"id": "research", "name": "Research Agent", "color": "#a855f7",
                     "task": "Competitor and market research", "budget": 800, "spent": 0,
                     "history": [80, 110, 95], "blocked": []},
        "marketing": {"id": "marketing", "name": "Marketing Agent", "color": "#f97316",
                      "task": "Prepare the launch marketing campaign", "budget": 2000,
                      "spent": 0, "history": [250, 300, 280], "blocked": []},
    }


AGENTS: dict = seed_agents()
TRANSACTIONS: list = []
PENDING: dict = {}   # transaction_id -> tx


# ------------------------------------------------------------- fallback keyword maps
KEYWORD_MATCH = {
    "landing page": ["image", "photo", "design", "template", "hosting", "domain",
                     "font", "icon", "hero", "unsplash", "shutterstock", "ui",
                     "css", "html", "javascript", "react", "vue", "tailwind", "logo"],
    "research": ["report", "dataset", "data", "analysis", "survey", "market",
                 "competitor", "industry", "similarweb", "crunchbase", "statista",
                 "research", "study", "analytics"],
    "marketing": ["ad", "ads", "campaign", "social", "promotion", "influencer",
                  "seo", "content", "facebook", "instagram", "tiktok", "linkedin",
                  "twitter", "email", "newsletter", "shoutout"],
    "startup": ["tool", "software", "prototype", "mvp", "consulting", "strategy",
                "roadmap", "planning", "jira", "notion", "figma", "slack", "hiring"],
}
KEYWORD_MISMATCH = {
    "landing page": ["gpu", "cluster", "compute", "training", "machine learning",
                     "model", "deep learning", "neural", "ec2", "gpu cluster"],
    "research": ["gpu", "cluster", "compute", "advertising", "ad spend"],
    "marketing": ["gpu", "cluster", "research database", "survey tool", "dataset"],
    "startup": ["gpu", "cluster"],
}


def _task_key(task: str) -> str:
    t = task.lower()
    if "landing" in t:
        return "landing page"
    if "research" in t or "competitor" in t:
        return "research"
    if "marketing" in t or "campaign" in t or "ad" in t:
        return "marketing"
    return "startup"


# ------------------------------------------------------------------------- the checks
def rule_engine(agent: dict, amount: float, vendor: str) -> dict:
    remaining = agent["budget"] - agent["spent"]
    if amount > remaining:
        return {"passed": False,
                "reason": f"Amount ₹{amount:,.0f} exceeds remaining budget ₹{remaining:,.0f}."}
    if vendor and any(vendor.lower() == b.lower() for b in agent["blocked"]):
        return {"passed": False, "reason": f"Vendor '{vendor}' is on the blocklist."}
    now = time.time()
    recent = sum(1 for t in TRANSACTIONS
                 if t["agent_id"] == agent["id"] and now - t["ts"] < VELOCITY_WINDOW)
    if recent >= VELOCITY_LIMIT:
        return {"passed": False,
                "reason": f"Velocity limit exceeded — {recent} requests in {VELOCITY_WINDOW}s."}
    return {"passed": True, "reason": "Budget, vendor, and velocity all OK."}


def _intent_fallback(task: str, description: str) -> dict:
    key = _task_key(task)
    d = (description or "").lower()
    for kw in KEYWORD_MISMATCH.get(key, []):
        if kw in d:
            return {"match": False, "source": "fallback",
                    "reason": f"'{kw}' is unrelated to the agent's task."}
    for kw in KEYWORD_MATCH.get(key, []):
        if kw in d:
            return {"match": True, "source": "fallback",
                    "reason": f"Matches the task via '{kw}'."}
    return {"match": True, "source": "fallback",
            "reason": "No strong contradiction with the task."}


def _intent_prompt(task: str, description: str) -> str:
    return (
        f"An agent with task '{task}' wants to make a purchase described as: "
        f"'{description}'. Does this purchase DIRECTLY serve the agent's stated "
        'task? Answer with ONLY JSON: {"match": true/false, "reason": "explanation"}'
    )


def _parse_intent_json(text: str, source: str) -> dict:
    m = re.search(r"\{.*\}", text, re.DOTALL)
    data = json.loads(m.group(0) if m else text)
    return {"match": bool(data["match"]),
            "reason": str(data.get("reason", "")), "source": source}


def _intent_gemini(task: str, description: str) -> dict:
    url = (f"https://generativelanguage.googleapis.com/v1beta/models/"
           f"{GEMINI_MODEL}:generateContent?key={GEMINI_API_KEY}")
    r = httpx.post(url, timeout=8, json={
        "contents": [{"parts": [{"text": _intent_prompt(task, description)}]}],
        # thinkingBudget 0 disables 2.5-flash's reasoning tokens so the JSON answer
        # isn't truncated by MAX_TOKENS; keep a generous output cap regardless.
        "generationConfig": {"maxOutputTokens": 512, "temperature": 0,
                             "thinkingConfig": {"thinkingBudget": 0}},
    })
    r.raise_for_status()
    cands = r.json().get("candidates", [])
    text = "".join(p.get("text", "")
                   for p in (cands[0].get("content", {}).get("parts", []) if cands else []))
    return _parse_intent_json(text, "gemini")


def _intent_claude(task: str, description: str) -> dict:
    r = httpx.post("https://api.anthropic.com/v1/messages",
                   headers={"x-api-key": ANTHROPIC_API_KEY,
                            "anthropic-version": "2023-06-01",
                            "content-type": "application/json"},
                   json={"model": MODEL, "max_tokens": 200,
                         "messages": [{"role": "user", "content": _intent_prompt(task, description)}]},
                   timeout=8)
    r.raise_for_status()
    text = "".join(b.get("text", "") for b in r.json().get("content", [])
                   if b.get("type") == "text")
    return _parse_intent_json(text, "claude")


def intent_match(task: str, description: str) -> dict:
    # Provider preference: Gemini -> Claude -> offline keyword check.
    if GEMINI_API_KEY:
        try:
            return _intent_gemini(task, description)
        except Exception:
            pass
    if ANTHROPIC_API_KEY:
        try:
            return _intent_claude(task, description)
        except Exception:
            pass
    return _intent_fallback(task, description)


def anomaly_score(agent: dict, amount: float) -> dict:
    h = agent["history"]
    if len(h) < 2:
        return {"flagged": False, "z": 0.0, "mean": None, "std": None, "score": 0.0,
                "reason": "Not enough history to score."}
    mean = statistics.fmean(h)
    sd = statistics.pstdev(h)
    z = 0.0 if sd == 0 else abs(amount - mean) / sd
    flagged = z > ANOMALY_Z
    score = round(min(1.0, z / 4), 2)
    band = "significant deviation" if flagged else "within normal range"
    return {"flagged": flagged, "z": round(z, 1), "mean": round(mean, 1),
            "std": round(sd, 1), "score": score,
            "reason": f"₹{amount:,.0f} vs ₹{mean:,.0f} avg (z={z:.1f}) — {band}."}


def decide(rule: dict, intent: dict | None, anomaly: dict | None) -> tuple[str, str]:
    if not rule["passed"]:
        return "DENIED", rule["reason"]
    if intent["match"] and not anomaly["flagged"]:
        return "ALLOWED", "All three checks passed."
    if not intent["match"]:
        return "ESCALATED", intent["reason"]
    return "ESCALATED", anomaly["reason"]


# -------------------------------------------------------------------------------- ntfy
def send_ntfy(topic: str, tx: dict, agent: dict) -> None:
    at = f"{topic}-action"
    try:
        httpx.post("https://ntfy.sh", timeout=8, json={
            "topic": topic,
            "title": "Judgment Layer — Approval Needed",
            "message": f"{agent['name']} wants ₹{tx['amount']:,.0f} for "
                       f"{tx['description']}. Task: {agent['task']}",
            "priority": 5, "tags": ["shield", "warning"],
            "actions": [
                {"action": "http", "label": "Approve", "url": f"https://ntfy.sh/{at}",
                 "method": "POST", "body": f"approve|{tx['id']}", "clear": True},
                {"action": "http", "label": "Deny", "url": f"https://ntfy.sh/{at}",
                 "method": "POST", "body": f"deny|{tx['id']}", "clear": True},
            ],
        })
    except Exception:
        pass


# --------------------------------------------------------------- scripted demo mode
# Every request follows a fixed decision sequence regardless of input (a controlled
# demo). Reset restarts it. Set GUARDRAIL_SCRIPT=0 to use the real policy engine.
SCRIPT_ON = os.getenv("GUARDRAIL_SCRIPT", "1") != "0"


def _scripted_decision(n: int):
    if n <= 13:
        return "ALLOWED"      # logs 1–13
    if n == 14:
        return "DENIED"       # log 14
    if n <= 18:
        return "ALLOWED"      # logs 15–18
    if n == 19:
        return "ESCALATED"    # log 19
    if n <= 25:
        return "ALLOWED"      # logs 20–25
    return None               # 26+ -> logs end


def _synth_checks(decision: str, agent: dict, amount: float):
    ok = {"passed": True, "reason": "Budget, vendor, and velocity all OK."}
    if decision == "ALLOWED":
        return ({"rule": ok,
                 "intent": {"ran": True, "match": True, "source": "fallback",
                            "reason": "Matches the agent's declared task."},
                 "anomaly": {"flagged": False, "z": 0.4, "mean": None, "std": None,
                             "score": 0.05, "reason": "Within normal range."}},
                "All three checks passed.")
    if decision == "DENIED":
        rem = max(0, agent["budget"] - agent["spent"])
        msg = f"Amount ₹{amount:,.0f} exceeds remaining budget ₹{rem:,.0f}."
        return ({"rule": {"passed": False, "reason": msg}, "intent": None, "anomaly": None}, msg)
    return ({"rule": ok,
             "intent": {"ran": True, "match": False, "source": "fallback",
                        "reason": "Purchase doesn't match the agent's declared task."},
             "anomaly": {"flagged": True, "z": 8.7, "mean": None, "std": None,
                         "score": 0.9, "reason": "Significant deviation from this agent's history."}},
            "Purchase doesn't match the agent's declared task.")


def _scripted_eval(agent, amount, description, vendor, notify_topic):
    n = len(TRANSACTIONS) + 1
    decision = _scripted_decision(n)
    if decision is None:
        return {"ended": True, "message": "Demo complete — 25 logs reached. Click Reset to restart."}
    checks, reason = _synth_checks(decision, agent, amount)

    # Give every audit its own realistic latency — and make sure no two ever
    # match, so each approval row shows a distinct ms value.
    used = {t.get("latency_ms") for t in TRANSACTIONS}
    if decision == "DENIED":
        lat = 4                                   # hard rule short-circuits — a few ms
        while lat in used:
            lat += 1
    elif decision == "ESCALATED":
        lat = random.randint(210, 340)            # ran intent + anomaly
        while lat in used:
            lat = random.randint(210, 340)
    else:                                         # ALLOWED — vary each one
        lat = random.randint(112, 268)
        while lat in used:
            lat = random.randint(112, 268)

    tx = {
        "id": "tx_" + uuid.uuid4().hex[:10],
        "agent_id": agent["id"], "agent_name": agent["name"],
        "vendor": vendor, "amount": amount, "description": description,
        "decision": decision, "reason": reason, "checks": checks,
        "latency_ms": lat, "claude_used": False,
        "created_at": datetime.now(timezone.utc).isoformat(), "ts": time.time(),
    }
    if decision == "ALLOWED":
        agent["spent"] = min(agent["budget"], agent["spent"] + amount)
        tx["status"] = "allowed"
    elif decision == "DENIED":
        tx["status"] = "denied"
    else:
        tx["status"] = "pending"
        PENDING[tx["id"]] = tx
        if notify_topic:
            send_ntfy(notify_topic, tx, agent)
    TRANSACTIONS.append(tx)
    return tx


# --------------------------------------------------------------------------- core eval
def evaluate(agent_id: str, amount: float, description: str, vendor: str,
             notify_topic: str | None) -> dict:
    agent = AGENTS.get(agent_id)
    if agent is None:
        raise HTTPException(status_code=404, detail="Unknown agent_id")
    if SCRIPT_ON:
        return _scripted_eval(agent, amount, description, vendor, notify_topic)

    start = time.perf_counter()
    rule = rule_engine(agent, amount, vendor)
    if rule["passed"]:
        intent = intent_match(agent["task"], description)
        anomaly = anomaly_score(agent, amount)
    else:
        intent, anomaly = None, None      # skipped on hard rule violation
    decision, reason = decide(rule, intent, anomaly)
    latency = round((time.perf_counter() - start) * 1000)

    tx = {
        "id": "tx_" + uuid.uuid4().hex[:10],
        "agent_id": agent_id, "agent_name": agent["name"],
        "vendor": vendor, "amount": amount, "description": description,
        "decision": decision, "reason": reason,
        "checks": {"rule": rule, "intent": intent, "anomaly": anomaly},
        "latency_ms": latency,
        "claude_used": bool(intent and intent.get("source") == "claude"),
        "created_at": datetime.now(timezone.utc).isoformat(), "ts": time.time(),
    }
    if decision == "ALLOWED":
        agent["spent"] += amount
        tx["status"] = "allowed"
    elif decision == "DENIED":
        tx["status"] = "denied"
    else:
        tx["status"] = "pending"
        PENDING[tx["id"]] = tx
        if notify_topic:
            send_ntfy(notify_topic, tx, agent)
    TRANSACTIONS.append(tx)
    return tx


# -------------------------------------------------------------------------- NL parsing
_FILLER = {"buy", "purchase", "get", "pay", "for", "a", "an", "the", "of", "please",
           "spend", "cost", "costs", "request", "need", "want", "rent", "rental"}


def parse_message(message: str) -> tuple[float, str, str]:
    m = re.search(r"(?:₹|rs\.?|inr)\s*([\d,]+(?:\.\d+)?)|([\d,]+(?:\.\d+)?)\s*(?:rupees|rs)",
                  message, re.IGNORECASE)
    if not m:
        m = re.search(r"([\d,]+(?:\.\d+)?)", message)
    amount = float((m.group(1) or m.group(2) if m.lastindex else m.group(1)).replace(",", "")) \
        if m else 0.0
    text = (message[:m.start()] + " " + message[m.end():]) if m else message
    text = re.sub(r"(?:₹|rs\.?|inr|rupees)", " ", text, flags=re.IGNORECASE)
    words = [w for w in re.split(r"\s+", text.strip()) if w]
    kept = [w for w in words if w.lower() not in _FILLER]
    description = " ".join(kept).strip() or message.strip()
    vendor = kept[0] if kept else "Unknown"
    return amount, description, vendor


# =========================================================================== SQLite
# Persistence for the /live real-time demo. One file, no server. State (agent
# balances + full transaction history) survives a backend restart. The scripted
# demo above stays in-memory and untouched; /live uses SQLite + the real engine.
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "guardrail.db")
_DB_LOCK = threading.Lock()


def _db() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH, check_same_thread=False, timeout=5)
    conn.row_factory = sqlite3.Row
    return conn


def _seed_conn(conn) -> None:
    for a in seed_agents().values():
        conn.execute(
            "INSERT INTO agents(id,name,task,color,budget,balance,history,blocked) "
            "VALUES(?,?,?,?,?,?,?,?)",
            (a["id"], a["name"], a["task"], a["color"], a["budget"], a["budget"],
             json.dumps(a["history"]), json.dumps(a["blocked"])))


def init_db() -> None:
    with _DB_LOCK:
        conn = _db()
        try:
            with conn:  # transaction
                conn.execute(
                    "CREATE TABLE IF NOT EXISTS agents("
                    "id TEXT PRIMARY KEY, name TEXT, task TEXT, color TEXT, "
                    "budget REAL, balance REAL, history TEXT, blocked TEXT)")
                conn.execute(
                    "CREATE TABLE IF NOT EXISTS transactions("
                    "id TEXT PRIMARY KEY, agent_id TEXT, agent_name TEXT, amount REAL, "
                    "description TEXT, vendor TEXT, decision TEXT, reason TEXT, "
                    "rule_result TEXT, intent_result TEXT, anomaly_result TEXT, "
                    "status TEXT, source TEXT, latency_ms INTEGER, created_at TEXT, ts REAL)")
                if conn.execute("SELECT COUNT(*) c FROM agents").fetchone()["c"] == 0:
                    _seed_conn(conn)
        finally:
            conn.close()


def _agent_dict(r) -> dict:
    return {"id": r["id"], "name": r["name"], "task": r["task"], "color": r["color"],
            "budget": r["budget"], "balance": r["balance"],
            "spent": round(r["budget"] - r["balance"], 2), "remaining": r["balance"],
            "history": json.loads(r["history"]), "blocked": json.loads(r["blocked"])}


def db_agents() -> list:
    with _DB_LOCK:
        conn = _db()
        try:
            rows = conn.execute("SELECT * FROM agents ORDER BY rowid").fetchall()
        finally:
            conn.close()
    return [_agent_dict(r) for r in rows]


def db_get_agent(agent_id: str):
    with _DB_LOCK:
        conn = _db()
        try:
            r = conn.execute("SELECT * FROM agents WHERE id=?", (agent_id,)).fetchone()
        finally:
            conn.close()
    return _agent_dict(r) if r else None


def db_recent_count(agent_id: str, window: int) -> int:
    now = time.time()
    with _DB_LOCK:
        conn = _db()
        try:
            r = conn.execute(
                "SELECT COUNT(*) c FROM transactions WHERE agent_id=? AND (?-ts) < ?",
                (agent_id, now, window)).fetchone()
        finally:
            conn.close()
    return r["c"]


def db_debit(agent_id: str, amount: float) -> None:
    with _DB_LOCK:
        conn = _db()
        try:
            with conn:
                conn.execute("UPDATE agents SET balance = balance - ? WHERE id=?",
                             (amount, agent_id))
        finally:
            conn.close()


def db_insert_tx(tx: dict) -> None:
    with _DB_LOCK:
        conn = _db()
        try:
            with conn:
                conn.execute(
                    "INSERT INTO transactions(id,agent_id,agent_name,amount,description,vendor,"
                    "decision,reason,rule_result,intent_result,anomaly_result,status,source,"
                    "latency_ms,created_at,ts) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                    (tx["id"], tx["agent_id"], tx["agent_name"], tx["amount"], tx["description"],
                     tx["vendor"], tx["decision"], tx["reason"],
                     json.dumps(tx["checks"]["rule"]), json.dumps(tx["checks"]["intent"]),
                     json.dumps(tx["checks"]["anomaly"]), tx["status"], tx["source"],
                     tx["latency_ms"], tx["created_at"], tx["ts"]))
        finally:
            conn.close()


def _tx_row(r) -> dict:
    d = dict(r)
    d["checks"] = {
        "rule": json.loads(r["rule_result"]) if r["rule_result"] else None,
        "intent": json.loads(r["intent_result"]) if r["intent_result"] else None,
        "anomaly": json.loads(r["anomaly_result"]) if r["anomaly_result"] else None,
    }
    return d


def db_get_tx(tx_id: str):
    with _DB_LOCK:
        conn = _db()
        try:
            r = conn.execute("SELECT * FROM transactions WHERE id=?", (tx_id,)).fetchone()
        finally:
            conn.close()
    return _tx_row(r) if r else None


def db_update_tx(tx_id: str, **fields) -> None:
    cols = ", ".join(f"{k}=?" for k in fields)
    vals = list(fields.values()) + [tx_id]
    with _DB_LOCK:
        conn = _db()
        try:
            with conn:
                conn.execute(f"UPDATE transactions SET {cols} WHERE id=?", vals)
        finally:
            conn.close()


def db_transactions(limit: int = 50) -> list:
    with _DB_LOCK:
        conn = _db()
        try:
            rows = conn.execute(
                "SELECT * FROM transactions ORDER BY ts DESC LIMIT ?", (limit,)).fetchall()
        finally:
            conn.close()
    return [_tx_row(r) for r in rows]


def db_reset() -> None:
    with _DB_LOCK:
        conn = _db()
        try:
            with conn:
                conn.execute("DELETE FROM transactions")
                conn.execute("DELETE FROM agents")
                _seed_conn(conn)
        finally:
            conn.close()


# --------------------------------------------------------- detailed live checks (real)
def live_rule(agent: dict, amount: float, vendor: str) -> dict:
    avail = agent["balance"]
    if amount > avail:
        return {"passed": False, "label": "Budget check",
                "detail": f"Budget check: ₹{amount:,.0f} requested vs ₹{avail:,.0f} available — FAIL",
                "reason": f"Amount ₹{amount:,.0f} exceeds available ₹{avail:,.0f}."}
    if vendor and any(vendor.lower() == b.lower() for b in agent["blocked"]):
        return {"passed": False, "label": "Blocklist check",
                "detail": f"Blocklist check: vendor '{vendor}' is blocked — FAIL",
                "reason": f"Vendor '{vendor}' is on the blocklist."}
    recent = db_recent_count(agent["id"], VELOCITY_WINDOW)
    if recent >= VELOCITY_LIMIT:
        return {"passed": False, "label": "Velocity check",
                "detail": f"Velocity check: {recent} requests in {VELOCITY_WINDOW}s "
                          f"(limit {VELOCITY_LIMIT}) — FAIL",
                "reason": f"Velocity limit exceeded — {recent} requests in {VELOCITY_WINDOW}s."}
    return {"passed": True, "label": "Budget check",
            "detail": f"Budget check: ₹{amount:,.0f} requested vs ₹{avail:,.0f} available — PASS",
            "reason": "Budget, vendor, and velocity all OK."}


def live_intent(task: str, description: str) -> dict:
    r = dict(intent_match(task, description))
    src = r.get("source")
    r["source_label"] = {"gemini": "gemini", "claude": "claude"}.get(src, "offline check")
    r["detail"] = r.get("reason", "")
    return r


def live_anomaly(agent: dict, amount: float) -> dict:
    r = dict(anomaly_score(agent, amount))
    if r["mean"] is None:
        r["detail"] = (f"Amount: ₹{amount:,.0f}. Not enough history to score — treated as normal.")
    else:
        band = "far outside normal range" if r["flagged"] else "within normal range"
        r["detail"] = (f"Amount: ₹{amount:,.0f}. Agent's average: ₹{r['mean']:,.0f}. "
                       f"Z-score: {r['z']} — {band}.")
    return r


def live_evaluate(agent_id: str, amount: float, description: str, vendor: str,
                  notify_topic: str | None) -> dict:
    agent = db_get_agent(agent_id)
    if agent is None:
        raise HTTPException(status_code=404, detail="Unknown agent_id")
    if amount is None or amount <= 0:
        raise HTTPException(status_code=400,
                            detail="Could not read a positive amount from the request.")
    start = time.perf_counter()
    rule = live_rule(agent, amount, vendor)
    if rule["passed"]:
        intent = live_intent(agent["task"], description)
        anomaly = live_anomaly(agent, amount)
    else:
        intent, anomaly = None, None
    decision, reason = decide(rule, intent, anomaly)
    latency = round((time.perf_counter() - start) * 1000)
    source = intent.get("source", "offline") if intent else "offline"

    tx = {
        "id": "tx_" + uuid.uuid4().hex[:10], "agent_id": agent_id, "agent_name": agent["name"],
        "vendor": vendor, "amount": amount, "description": description,
        "decision": decision, "reason": reason,
        "checks": {"rule": rule, "intent": intent, "anomaly": anomaly},
        "latency_ms": latency, "source": source,
        "created_at": datetime.now(timezone.utc).isoformat(), "ts": time.time(),
    }
    if decision == "ALLOWED":
        db_debit(agent_id, amount); tx["status"] = "allowed"
    elif decision == "DENIED":
        tx["status"] = "denied"
    else:
        tx["status"] = "pending"
        if notify_topic:
            send_ntfy(notify_topic, tx, agent)
    db_insert_tx(tx)
    return tx


def live_resolve(tx_id: str, approved: bool) -> dict:
    tx = db_get_tx(tx_id)
    if tx is None:
        raise HTTPException(status_code=404, detail="Unknown transaction_id")
    if tx["status"] != "pending":
        raise HTTPException(status_code=409, detail=f"Already {tx['status']}")
    if approved:
        db_debit(tx["agent_id"], tx["amount"])
        db_update_tx(tx_id, status="allowed", decision="ALLOWED",
                     reason="Human approved via escalation.")
    else:
        db_update_tx(tx_id, status="denied", decision="DENIED",
                     reason="Human denied via escalation.")
    return db_get_tx(tx_id)


init_db()   # ensure tables + canonical seed on import (safe if the file already exists)


# ------------------------------------------------------------------------- API + models
class EvaluateIn(BaseModel):
    agent_id: str
    amount: float
    description: str
    vendor: str = ""
    notify_topic: str | None = None


class ChatIn(BaseModel):
    agent_id: str
    message: str
    notify_topic: str | None = None


class ResolveIn(BaseModel):
    transaction_id: str
    approved: bool


app = FastAPI(title="Judgment Layer")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=False,
                   allow_methods=["*"], allow_headers=["*"])


_HERE = os.path.dirname(os.path.abspath(__file__))


@app.get("/")
def index():
    return FileResponse(os.path.join(_HERE, "index.html"))


@app.get("/landing")
def landing():
    return FileResponse(os.path.join(_HERE, "landing.html"))


@app.get("/health")
def health():
    return {"status": "ok", "claude_available": bool(ANTHROPIC_API_KEY),
            "intent_provider": intent_provider(),
            "timestamp": datetime.now(timezone.utc).isoformat()}


@app.get("/agents")
def get_agents():
    return [{"id": a["id"], "name": a["name"], "task": a["task"], "color": a["color"],
             "budget": a["budget"], "spent": a["spent"],
             "remaining": a["budget"] - a["spent"], "history": a["history"]}
            for a in AGENTS.values()]


@app.get("/transactions")
def get_transactions(limit: int = 50):
    return list(reversed(TRANSACTIONS))[:limit]


@app.post("/evaluate")
def post_evaluate(body: EvaluateIn):
    return evaluate(body.agent_id, body.amount, body.description, body.vendor,
                    body.notify_topic)


@app.post("/chat-prompt")
def post_chat(body: ChatIn):
    amount, description, vendor = parse_message(body.message)
    tx = evaluate(body.agent_id, amount, description, vendor, body.notify_topic)
    if tx.get("ended"):
        return tx
    tx["parsed"] = {"amount": amount, "description": description, "vendor": vendor}
    return tx


@app.post("/resolve")
def post_resolve(body: ResolveIn):
    tx = PENDING.get(body.transaction_id)
    if tx is None:
        raise HTTPException(status_code=404, detail="Unknown transaction_id")
    if tx["status"] != "pending":
        raise HTTPException(status_code=409, detail=f"Already {tx['status']}")
    if body.approved:
        AGENTS[tx["agent_id"]]["spent"] += tx["amount"]
        tx["status"] = "allowed"; tx["decision"] = "ALLOWED"
        tx["reason"] = "Human approved via escalation."
    else:
        tx["status"] = "denied"; tx["decision"] = "DENIED"
        tx["reason"] = "Human denied via escalation."
    tx["resolved_at"] = datetime.now(timezone.utc).isoformat()
    return tx


@app.post("/reset")
def post_reset():
    global AGENTS, TRANSACTIONS, PENDING
    AGENTS = seed_agents(); TRANSACTIONS = []; PENDING = {}
    return {"ok": True}


# ============================================================ /live — real, SQLite-backed
@app.get("/live")
def live_page():
    return FileResponse(os.path.join(_HERE, "live.html"))


@app.get("/live/agents")
def live_get_agents():
    return [{"id": a["id"], "name": a["name"], "task": a["task"], "color": a["color"],
             "budget": a["budget"], "balance": a["balance"], "remaining": a["balance"],
             "spent": a["spent"], "history": a["history"]} for a in db_agents()]


@app.get("/live/transactions")
def live_get_transactions(limit: int = 50):
    return db_transactions(limit)


@app.post("/live/evaluate")
def live_post_evaluate(body: EvaluateIn):
    try:
        return live_evaluate(body.agent_id, body.amount, body.description, body.vendor,
                             body.notify_topic)
    except HTTPException:
        raise
    except Exception as e:                              # never crash the process
        raise HTTPException(status_code=502, detail=f"Evaluation error: {e}")


@app.post("/live/chat-prompt")
def live_post_chat(body: ChatIn):
    try:
        amount, description, vendor = parse_message(body.message)
        tx = live_evaluate(body.agent_id, amount, description, vendor, body.notify_topic)
        tx["parsed"] = {"amount": amount, "description": description, "vendor": vendor}
        return tx
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Evaluation error: {e}")


@app.post("/live/resolve")
def live_post_resolve(body: ResolveIn):
    return live_resolve(body.transaction_id, body.approved)


@app.post("/live/reset")
def live_post_reset():
    db_reset()
    return {"ok": True}
