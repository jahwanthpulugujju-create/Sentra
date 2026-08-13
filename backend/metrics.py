"""Live evaluation metrics computed from the transaction ledger."""
from __future__ import annotations

from sqlalchemy import func
from sqlalchemy.orm import Session

from models import Transaction


def compute_metrics(db: Session) -> dict:
    """Compute real-time decision statistics from the transactions table."""
    # Exclude seeded historical transactions (they have empty checks {}).
    all_tx = (
        db.query(Transaction)
        .filter(Transaction.checks != {})
        .all()
    )

    total = len(all_tx)
    if total == 0:
        return {
            "total_transactions": 0,
            "decisions_breakdown": {"allow": 0, "escalate": 0, "deny": 0},
            "escalation_rate": 0.0,
            "threat_detection_rate": 0.0,
            "false_positive_rate": 0.0,
            "llm_vs_fallback": {"llm": 0, "fallback": 0},
            "avg_processing_time_ms": None,
        }

    # Decisions breakdown.
    decisions = {"allow": 0, "escalate": 0, "deny": 0}
    for tx in all_tx:
        d = tx.decision
        if d in decisions:
            decisions[d] += 1

    # Escalation rate: % of transactions that were escalated.
    escalation_rate = round(decisions["escalate"] / total * 100, 1) if total else 0.0

    # Threat detection rate: % of off-task / anomalous requests correctly caught
    # (escalated or denied, not auto-allowed).
    threats_caught = decisions["escalate"] + decisions["deny"]
    threat_detection_rate = round(threats_caught / total * 100, 1) if total else 0.0

    # False positive rate: escalations that were subsequently approved by human
    # (i.e., the system flagged something the human disagreed with).
    escalated_tx = [tx for tx in all_tx if tx.decision == "escalate"]
    resolved_as_approved = sum(1 for tx in escalated_tx if tx.status == "approved")
    false_positive_rate = (
        round(resolved_as_approved / len(escalated_tx) * 100, 1)
        if escalated_tx else 0.0
    )

    # LLM vs fallback usage.
    llm_count = sum(1 for tx in all_tx if tx.intent_source == "llm")
    fallback_count = sum(1 for tx in all_tx if tx.intent_source == "fallback")

    # Average processing time.
    times = [tx.processing_time_ms for tx in all_tx if tx.processing_time_ms is not None]
    avg_time = round(sum(times) / len(times), 1) if times else None

    return {
        "total_transactions": total,
        "decisions_breakdown": decisions,
        "escalation_rate": escalation_rate,
        "threat_detection_rate": threat_detection_rate,
        "false_positive_rate": false_positive_rate,
        "llm_vs_fallback": {"llm": llm_count, "fallback": fallback_count},
        "avg_processing_time_ms": avg_time,
    }
