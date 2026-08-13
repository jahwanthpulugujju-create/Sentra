"""ORM models — column-for-column mirror of db/schema.sql (BUILD_PLAN.md §4)."""
import uuid

from sqlalchemy import ForeignKey, JSON, Numeric, String, Text, UUID, Float, func
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import DateTime

from database import Base


class Agent(Base):
    __tablename__ = "agents"

    id: Mapped[str] = mapped_column(String, primary_key=True)  # slug id
    name: Mapped[str] = mapped_column(String, nullable=False)
    task: Mapped[str] = mapped_column(String, nullable=False)
    budget: Mapped[float] = mapped_column(Numeric, nullable=False)
    balance: Mapped[float] = mapped_column(Numeric, nullable=False)
    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class Transaction(Base):
    __tablename__ = "transactions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    agent_id: Mapped[str] = mapped_column(
        String, ForeignKey("agents.id"), nullable=False
    )
    amount: Mapped[float] = mapped_column(Numeric, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    decision: Mapped[str] = mapped_column(Text, nullable=False)      # allow|escalate|deny
    status: Mapped[str] = mapped_column(Text, nullable=False)        # allowed|denied|pending|approved
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    triggered_by: Mapped[str | None] = mapped_column(Text, nullable=True)
    intent_source: Mapped[str | None] = mapped_column(Text, nullable=True)
    checks: Mapped[dict] = mapped_column(JSON, nullable=False)
    risk_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    risk_factors: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    llm_authority: Mapped[str | None] = mapped_column(Text, nullable=True)
    processing_time_ms: Mapped[float | None] = mapped_column(Float, nullable=True)
    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    resolved_at: Mapped[DateTime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
