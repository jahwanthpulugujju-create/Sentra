"""Hash-linked Proof Chain for Sentra Authority Engine.

Every authority verdict, capability event, and gateway execution enters an immutable,
SHA-256 hash-linked audit ledger.
"""
import hashlib
import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import func
from sqlalchemy.orm import Session

from models import AuthorityEvent

GENESIS_HASH = "0" * 64


def canonicalize_event_payload(payload: Dict[str, Any]) -> str:
    """Canonical string for hashing an event."""
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def compute_event_hash(previous_hash: str, payload_str: str) -> str:
    """eventHash = SHA-256(previousHash + canonicalEventPayload)"""
    combined = f"{previous_hash}:{payload_str}"
    return hashlib.sha256(combined.encode("utf-8")).hexdigest()


def append_authority_event(
    db: Session,
    request_hash: str,
    decision: str,
    reason_code: str,
    payload: Dict[str, Any],
) -> AuthorityEvent:
    """Append a new hash-linked event to the authority proof chain."""
    # Get last event for sequence & previous_hash
    last_event = (
        db.query(AuthorityEvent)
        .order_by(AuthorityEvent.sequence.desc())
        .first()
    )

    if last_event is None:
        next_seq = 1
        prev_hash = GENESIS_HASH
    else:
        next_seq = last_event.sequence + 1
        prev_hash = last_event.event_hash

    payload_str = canonicalize_event_payload(payload)
    event_hash = compute_event_hash(prev_hash, payload_str)

    event = AuthorityEvent(
        sequence=next_seq,
        request_hash=request_hash,
        decision=decision,
        reason_code=reason_code,
        previous_hash=prev_hash,
        event_hash=event_hash,
        payload=payload,
        created_at=datetime.now(timezone.utc),
    )
    db.add(event)
    db.flush()
    return event


def verify_proof_chain(db: Session) -> Tuple[bool, Optional[str], int]:
    """Verify integrity of all events in the chain.

    Returns (is_valid, error_message, total_events_verified).
    """
    events = (
        db.query(AuthorityEvent)
        .order_by(AuthorityEvent.sequence.asc())
        .all()
    )

    if not events:
        return True, None, 0

    expected_prev_hash = GENESIS_HASH
    expected_seq = 1

    for ev in events:
        if ev.sequence != expected_seq:
            return False, f"Sequence gap at event ID {ev.id}: expected {expected_seq}, got {ev.sequence}", len(events)

        if ev.previous_hash != expected_prev_hash:
            return False, f"Previous hash mismatch at sequence {ev.sequence}: expected {expected_prev_hash}, got {ev.previous_hash}", len(events)

        payload_str = canonicalize_event_payload(ev.payload)
        recalculated_hash = compute_event_hash(ev.previous_hash, payload_str)
        if recalculated_hash != ev.event_hash:
            return False, f"Event hash tampering detected at sequence {ev.sequence}: recorded {ev.event_hash}, calculated {recalculated_hash}", len(events)

        expected_prev_hash = ev.event_hash
        expected_seq += 1

    return True, None, len(events)
