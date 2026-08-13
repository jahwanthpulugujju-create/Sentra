"""Rule engine — deterministic, no AI. Runs first; first failure denies.

Spec: Docs/BUILD_PLAN.md §6.1 (order, categories, threshold, reason strings).
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from models import Transaction

# BUILD_PLAN §6.1 blocked categories (case-insensitive substring match).
BLOCKED_CATEGORIES = [
    "crypto exchange",
    "gift card",
    "wire transfer",
    "unregistered vendor",
    "gambling",
]

# BUILD_PLAN §0 / §6.1: >5 transactions from one agent within 10s -> Deny.
VELOCITY_LIMIT = 5
VELOCITY_WINDOW_SECONDS = 10


def run_rules(agent, amount: float, description: str, db) -> dict:
    """Return {'passed': bool, 'failed_rule': str|None, 'reason': str}."""
    # 1. Budget check
    if amount > float(agent.balance):
        return {
            "passed": False,
            "failed_rule": "budget",
            "reason": f"Exceeds remaining budget of ₹{float(agent.balance):.0f}.",
        }

    # 2. Blocklist check
    desc = (description or "").lower()
    for category in BLOCKED_CATEGORIES:
        if category in desc:
            return {
                "passed": False,
                "failed_rule": "blocklist",
                "reason": f"Blocked category: {category}.",
            }

    # 3. Velocity check
    cutoff = datetime.now(timezone.utc) - timedelta(seconds=VELOCITY_WINDOW_SECONDS)
    recent = (
        db.query(Transaction)
        .filter(Transaction.agent_id == agent.id, Transaction.created_at >= cutoff)
        .count()
    )
    if recent >= VELOCITY_LIMIT:
        return {
            "passed": False,
            "failed_rule": "velocity",
            "reason": f"Velocity limit exceeded — {recent} requests in 10s.",
        }

    return {"passed": True, "failed_rule": None, "reason": "All rule checks passed."}
