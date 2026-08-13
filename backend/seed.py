"""Database Seeding & Clean Baseline Reset.

Seeds default Protected Resources and Policy Version records.
`reset(db)` restores a clean baseline for reproducible judging demos.
"""
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from models import AuthorityEvent, Capability, DemoRun, PolicyVersion, ProtectedResource
from policy_engine import CURRENT_POLICY_VERSION
from proof_chain import GENESIS_HASH


def seed(db: Session) -> None:
    """Seed initial protected resources and policy version."""
    # Seed policy version
    if db.query(PolicyVersion).filter(PolicyVersion.version == CURRENT_POLICY_VERSION).count() == 0:
        pv = PolicyVersion(
            version=CURRENT_POLICY_VERSION,
            rules_digest="sha256-deterministic-sentra-kernel-v1",
            created_at=datetime.now(timezone.utc),
        )
        db.add(pv)

    # Seed default protected resource
    if db.query(ProtectedResource).filter(ProtectedResource.id == "prod_k8s_cluster").count() == 0:
        res = ProtectedResource(
            id="prod_k8s_cluster",
            label="Production Kubernetes Cluster",
            state={
                "status": "idle",
                "version": "v1.28.0",
                "deployCount": 0,
                "lastDeployBy": "none",
                "activePods": 12,
                "environment": "production",
            },
            updated_at=datetime.now(timezone.utc),
        )
        db.add(res)

    db.commit()


def reset(db: Session) -> None:
    """Reset all database tables to clean demo state."""
    db.query(AuthorityEvent).delete()
    db.query(Capability).delete()
    db.query(DemoRun).delete()
    db.query(PolicyVersion).delete()
    db.query(ProtectedResource).delete()
    db.commit()

    seed(db)
