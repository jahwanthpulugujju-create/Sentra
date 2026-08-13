"""Anomaly score — simple statistics, no ML (BUILD_PLAN.md §6.3).

Compare the requested amount to the agent's own history of allowed/approved
amounts. z = (amount - mean) / std; flag if z > 2 (one-sided: only unusually
LARGE spend is flagged). Fewer than 2 prior transactions -> not enough history,
not flagged.
"""
from __future__ import annotations

import statistics

from models import Transaction


def _score_from_amounts(amounts: list[float], amount: float) -> dict:
    if len(amounts) < 2:
        return {
            "ran": True,
            "flagged": False,
            "z_score": None,
            "mean": None,
            "std": None,
            "reason": "Not enough history to score.",
        }

    mean = statistics.fmean(amounts)
    std = statistics.pstdev(amounts)  # population standard deviation

    if std == 0:
        # Perfectly consistent history: any deviation is anomalous. (Edge case;
        # seeded histories all have variance so this rarely triggers.)
        flagged = amount != mean
        reason = (
            f"Amount ₹{amount:.0f} deviates from this agent's consistent "
            f"₹{mean:.0f} history."
            if flagged
            else f"Amount ₹{amount:.0f} matches this agent's history."
        )
        return {
            "ran": True,
            "flagged": flagged,
            "z_score": None,
            "mean": mean,
            "std": std,
            "reason": reason,
        }

    z = (amount - mean) / std
    flagged = z > 2
    reason = (
        f"Amount ₹{amount:.0f} is {z:.1f}σ above this agent's ₹{mean:.0f} average."
        if flagged
        else f"Amount ₹{amount:.0f} is within normal range (z={z:.1f})."
    )
    return {
        "ran": True,
        "flagged": flagged,
        "z_score": z,
        "mean": mean,
        "std": std,
        "reason": reason,
    }


def score_anomaly(agent, amount: float, db) -> dict:
    """Pull this agent's prior allowed/approved amounts and score `amount`."""
    rows = (
        db.query(Transaction.amount)
        .filter(
            Transaction.agent_id == agent.id,
            Transaction.status.in_(["allowed", "approved"]),
        )
        .all()
    )
    amounts = [float(r[0]) for r in rows]
    return _score_from_amounts(amounts, float(amount))
