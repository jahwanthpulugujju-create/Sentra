"""Policy engine — full three-check form with risk scoring and LLM authority.

Rules run first (hard deny). If rules pass, intent match + anomaly run; the three
combine into Allow / Escalate / Deny. Ambiguous cases (intent mismatch or anomaly)
Escalate to a human (status 'pending', no deduction) — they are never auto-denied.

Risk score (0–100) quantifies the composite risk across all three checks.
LLM authority tracks exactly what role the LLM played in each decision.
"""
from __future__ import annotations

import time

from anomaly import score_anomaly
from intent import check_intent
from models import Transaction
from rules import run_rules


def combine(rule: dict, intent: dict, anomaly: dict) -> tuple[str, str, str | None, str]:
    """Return (decision, status, triggered_by, reason) per BUILD_PLAN §6.4."""
    if not rule["passed"]:
        return "deny", "denied", "rule_engine", rule["reason"]
    if intent["match"] and not anomaly["flagged"]:
        return "allow", "allowed", None, "Passed all checks."
    # Escalate — reason/trigger from intent first, then anomaly.
    if not intent["match"]:
        return "escalate", "pending", "intent_match", intent["reason"]
    return "escalate", "pending", "anomaly", anomaly["reason"]


def compute_risk_score(rule: dict, intent: dict, anomaly: dict) -> float:
    """Compute a 0–100 composite risk score from all three checks."""
    # Rule engine: binary — 0 if passed, 100 if failed.
    rule_risk = 0.0 if rule["passed"] else 100.0

    # Intent match: based on confidence. Low confidence in a match = some risk.
    if not intent.get("ran"):
        intent_risk = 0.0  # didn't run (rules already denied)
    elif intent.get("match"):
        # Matched but might have low confidence.
        confidence = intent.get("confidence", 0.5)
        intent_risk = (1.0 - confidence) * 30  # low risk, scaled to max 30
    else:
        # Mismatched — high risk, confidence makes it worse.
        confidence = intent.get("confidence", 0.5)
        intent_risk = 60 + (1.0 - confidence) * 40  # 60–100

    # Injection detection adds extra risk.
    if intent.get("injection_detected"):
        intent_risk = min(intent_risk + 20, 100)

    # Anomaly: based on z-score.
    if not anomaly.get("ran") or not anomaly.get("flagged"):
        anomaly_risk = 0.0
    else:
        z = anomaly.get("z_score") or 0
        anomaly_risk = min(z * 25, 100)

    # Weighted composite: rules 40%, intent 35%, anomaly 25%.
    if not rule["passed"]:
        # Hard rule failure dominates.
        return round(rule_risk, 1)

    composite = 0.40 * rule_risk + 0.35 * intent_risk + 0.25 * anomaly_risk
    return round(min(composite, 100), 1)


def extract_risk_factors(rule: dict, intent: dict, anomaly: dict) -> list[str]:
    """Extract human-readable risk factors from the three checks."""
    factors = []

    if not rule["passed"]:
        factors.append(f"Rule violation: {rule['reason']}")
        return factors  # rule failure is the only relevant factor

    if intent.get("ran"):
        if not intent.get("match"):
            factors.append(f"Off-task purchase: {intent.get('reason', 'Intent mismatch')}")
        if intent.get("injection_detected"):
            factors.append("Prompt injection pattern detected in description")
        confidence = intent.get("confidence")
        if confidence is not None and confidence < 0.4:
            factors.append(f"Low intent confidence ({confidence:.0%})")

    if anomaly.get("ran") and anomaly.get("flagged"):
        z = anomaly.get("z_score")
        if z is not None:
            factors.append(f"Anomalous amount: {z:.1f}σ above agent average")
        else:
            factors.append("Amount deviates from agent history")

    return factors


def determine_llm_authority(rule: dict, intent: dict) -> str:
    """Determine what role the LLM played in this decision."""
    if not rule["passed"]:
        return "not_consulted"
    if not intent.get("ran"):
        return "not_consulted"
    if intent.get("source") == "fallback":
        return "fallback_used"
    return "advisory_only"


def apply_resolution(status: str, balance: float, amount: float, action: str):
    """Resolve a pending escalation.

    Returns (new_status, new_balance) for a currently-`pending` transaction, or
    None if it is NOT pending (the caller must then return 409 and change
    nothing). Deducts only on approve.
    """
    if status != "pending":
        return None
    if action == "approve":
        return "approved", balance - amount
    return "denied", balance


def evaluate(agent, amount: float, description: str, db) -> Transaction:
    start = time.perf_counter()

    rule = run_rules(agent, amount, description, db)

    if rule["passed"]:
        intent = check_intent(agent.task, amount, description)
        anomaly = score_anomaly(agent, amount, db)
    else:
        # Hard rule violation short-circuits — the smart checks don't run.
        intent = {"ran": False, "match": None, "source": None, "reason": None,
                  "confidence": None, "injection_detected": False}
        anomaly = {"ran": False, "flagged": None, "z_score": None, "mean": None, "std": None}

    checks = {
        "rule_engine": {
            "passed": rule["passed"],
            "failed_rule": rule["failed_rule"],
            "reason": rule["reason"],
        },
        "intent_match": {
            "ran": intent["ran"],
            "match": intent.get("match"),
            "source": intent.get("source"),
            "reason": intent.get("reason"),
            "confidence": intent.get("confidence"),
            "injection_detected": intent.get("injection_detected", False),
        },
        "anomaly": {
            "ran": anomaly["ran"],
            "flagged": anomaly.get("flagged"),
            "z_score": anomaly.get("z_score"),
            "mean": anomaly.get("mean"),
            "std": anomaly.get("std"),
        },
    }

    decision, status, triggered_by, reason = combine(rule, intent, anomaly)
    risk_score = compute_risk_score(rule, intent, anomaly)
    risk_factors = extract_risk_factors(rule, intent, anomaly)
    llm_authority = determine_llm_authority(rule, intent)

    if decision == "allow":
        agent.balance = float(agent.balance) - amount

    elapsed_ms = round((time.perf_counter() - start) * 1000, 1)

    tx = Transaction(
        agent_id=agent.id,
        amount=amount,
        description=description,
        decision=decision,
        status=status,
        reason=reason,
        triggered_by=triggered_by,
        intent_source=intent.get("source"),
        checks=checks,
        risk_score=risk_score,
        risk_factors=risk_factors,
        llm_authority=llm_authority,
        processing_time_ms=elapsed_ms,
    )
    db.add(tx)
    db.commit()
    db.refresh(tx)
    db.refresh(agent)
    return tx
