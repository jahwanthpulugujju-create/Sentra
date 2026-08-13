"""Sentra — FastAPI app.

Endpoints: /health, /agents, /transactions, /evaluate-transaction,
/resolve-escalation, /reset, /metrics.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.orm import Session

import models  # noqa: F401  (registers ORM models on the Base metadata)
from config import LLM_CONFIGURED
from database import Base, SessionLocal, engine, get_db
from metrics import compute_metrics
from models import Agent, Transaction
from policy_engine import apply_resolution, evaluate
from schemas import (
    AgentBrief,
    AgentOut,
    DecisionOut,
    EvaluateRequest,
    MetricsOut,
    ResolveRequest,
    TransactionOut,
)
from seed import reset, seed

app = FastAPI(title="Sentra")

# CORS restricted to the Vite dev origin.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5174"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def _startup_seed() -> None:
    """Seed canonical data on first boot if the agents table is empty."""
    if SessionLocal is None or engine is None:
        return
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        if db.query(Agent).count() == 0:
            seed(db)
    finally:
        db.close()


@app.get("/health")
def health() -> dict:
    """Report service status. db_connected is a live SELECT 1 against the DB."""
    db_connected = False
    if engine is not None:
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            db_connected = True
        except Exception:
            db_connected = False
    return {
        "status": "ok",
        "llm_configured": LLM_CONFIGURED,
        "db_connected": db_connected,
    }


@app.get("/agents", response_model=list[AgentOut])
def list_agents(db: Session = Depends(get_db)):
    return db.query(Agent).order_by(Agent.id).all()


@app.get("/transactions", response_model=list[TransactionOut])
def list_transactions(limit: int = 50, db: Session = Depends(get_db)):
    return (
        db.query(Transaction)
        .order_by(Transaction.created_at.desc())
        .limit(limit)
        .all()
    )


@app.post("/evaluate-transaction", response_model=DecisionOut)
def evaluate_transaction(req: EvaluateRequest, db: Session = Depends(get_db)):
    agent = db.get(Agent, req.agent_id)
    if agent is None:
        raise HTTPException(status_code=404, detail="Unknown agent_id")
    tx = evaluate(agent, req.amount, req.description, db)
    return DecisionOut(
        transaction_id=str(tx.id),
        decision=tx.decision,
        status=tx.status,
        reason=tx.reason,
        triggered_by=tx.triggered_by,
        intent_source=tx.intent_source,
        checks=tx.checks,
        risk_score=tx.risk_score or 0.0,
        risk_factors=tx.risk_factors or [],
        llm_authority=tx.llm_authority or "not_consulted",
        processing_time_ms=tx.processing_time_ms,
        agent=AgentBrief(id=agent.id, name=agent.name, balance=float(agent.balance)),
    )


@app.post("/resolve-escalation")
def resolve_escalation(req: ResolveRequest, db: Session = Depends(get_db)):
    # Parse the id; a malformed id is treated as not-found.
    try:
        tx_id = uuid.UUID(req.transaction_id)
    except (ValueError, AttributeError, TypeError):
        raise HTTPException(status_code=404, detail="Unknown transaction_id")

    # Lock the row for the duration of the transaction so a concurrent resolve
    # (double-click) can't double-spend.
    tx = (
        db.query(Transaction)
        .filter(Transaction.id == tx_id)
        .with_for_update()
        .first()
    )
    if tx is None:
        raise HTTPException(status_code=404, detail="Unknown transaction_id")

    agent = db.get(Agent, tx.agent_id)
    res = apply_resolution(tx.status, float(agent.balance), float(tx.amount), req.action)
    if res is None:
        raise HTTPException(
            status_code=409, detail=f"Transaction is not pending (status: {tx.status})"
        )

    new_status, new_balance = res
    tx.status = new_status
    tx.resolved_at = datetime.now(timezone.utc)
    agent.balance = new_balance
    db.commit()  # balance + status + resolved_at flip atomically

    return {
        "transaction_id": str(tx.id),
        "status": new_status,
        "agent": {"id": agent.id, "balance": float(new_balance)},
    }


@app.get("/metrics", response_model=MetricsOut)
def get_metrics(db: Session = Depends(get_db)):
    """Live evaluation metrics computed from the transaction ledger."""
    return compute_metrics(db)


@app.post("/reset")
def reset_state(db: Session = Depends(get_db)) -> dict:
    reset(db)
    return {"ok": True}
