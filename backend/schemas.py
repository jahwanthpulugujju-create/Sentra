"""Pydantic request/response models. Shapes per Docs/BUILD_PLAN.md §8."""
from __future__ import annotations

import math
from datetime import datetime
from typing import Any, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class HealthOut(BaseModel):
    status: str
    llm_configured: bool
    db_connected: bool


class EvaluateRequest(BaseModel):
    agent_id: str = Field(min_length=1)
    amount: float = Field(gt=0)
    description: str = Field(min_length=1, max_length=500)

    @field_validator("amount")
    @classmethod
    def _finite(cls, v: float) -> float:
        if not math.isfinite(v):
            raise ValueError("amount must be a finite number")
        return v


class ResolveRequest(BaseModel):
    transaction_id: str
    action: Literal["approve", "deny"]


class AgentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    name: str
    task: str
    budget: float
    balance: float


class AgentBrief(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    name: str
    balance: float


class TransactionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    agent_id: str
    amount: float
    description: str
    decision: str
    status: str
    reason: str
    triggered_by: Optional[str] = None
    intent_source: Optional[str] = None
    checks: dict[str, Any]
    risk_score: Optional[float] = None
    risk_factors: Optional[list[str]] = None
    llm_authority: Optional[str] = None
    processing_time_ms: Optional[float] = None
    created_at: datetime
    resolved_at: Optional[datetime] = None

    @field_validator("id", mode="before")
    @classmethod
    def _id_to_str(cls, v: Any) -> str:
        return str(v)


class DecisionOut(BaseModel):
    transaction_id: str
    decision: str
    status: str
    reason: str
    triggered_by: Optional[str] = None
    intent_source: Optional[str] = None
    checks: dict[str, Any]
    risk_score: float
    risk_factors: list[str]
    llm_authority: str
    processing_time_ms: Optional[float] = None
    agent: AgentBrief


class MetricsOut(BaseModel):
    total_transactions: int
    decisions_breakdown: dict[str, int]
    escalation_rate: float
    threat_detection_rate: float
    false_positive_rate: float
    llm_vs_fallback: dict[str, int]
    avg_processing_time_ms: Optional[float] = None
