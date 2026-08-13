"""Canonical seed / reset. Numbers are EXACT per Docs/BUILD_PLAN.md §5.

Seeded history rows are written with a PAST created_at (1 day ago) so they
represent history and do NOT interfere with the 10-second velocity window
(BUILD_PLAN §6.1). Their filler reason/checks values are labels, not
spec-critical (BUILD_PLAN §5; flagged in Docs/agents/M1.md §1).
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from models import Agent, Transaction

# id, name, task, budget, seeded history amounts (BUILD_PLAN §5).
CANONICAL = [
    {"id": "founder", "name": "Founder Agent",
     "task": "Plan and launch the startup", "budget": 5000, "history": []},
    {"id": "developer", "name": "Developer Agent",
     "task": "Build the landing page", "budget": 6000, "history": [40, 55, 35]},
    {"id": "research", "name": "Research Agent",
     "task": "Competitor and market research", "budget": 800, "history": [80, 110, 95]},
    {"id": "marketing", "name": "Marketing Agent",
     "task": "Prepare the launch marketing campaign", "budget": 2000,
     "history": [250, 300, 280]},
]


def _populate(db) -> None:
    past = datetime.now(timezone.utc) - timedelta(days=1)  # history lives in the past
    for a in CANONICAL:
        spent = sum(a["history"])
        db.add(Agent(
            id=a["id"], name=a["name"], task=a["task"],
            budget=a["budget"], balance=a["budget"] - spent,
        ))
        for amount in a["history"]:
            db.add(Transaction(
                agent_id=a["id"],
                amount=amount,
                description="Seeded historical transaction",
                decision="allow",
                status="allowed",
                reason="Seeded historical spend",
                triggered_by=None,
                intent_source=None,
                checks={},
                created_at=past,
            ))
    db.commit()


def reset(db) -> None:
    """Wipe the ledger and reseed to the exact canonical state."""
    from database import Base, engine
    if engine is not None:
        Base.metadata.create_all(bind=engine)
    db.query(Transaction).delete()
    db.query(Agent).delete()
    db.commit()
    _populate(db)


def seed(db) -> None:
    """Seed canonical state (used on startup when the DB is empty)."""
    reset(db)
