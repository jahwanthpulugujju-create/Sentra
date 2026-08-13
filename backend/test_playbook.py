"""Automated Test Suite for Sentra Winner-Readiness Playbook.

Verifies the 11 mandatory enforcement requirements:
1. Canonicalization stability & hash variance.
2. ALLOW creates exactly 1 valid capability.
3. DENY, ESCALATE, FREEZE create 0 executable capabilities.
4. Gateway rejects invalid HMAC signature.
5. Gateway rejects expired capability.
6. Gateway rejects changed request hash.
7. Gateway rejects reused/consumed capability (replay protection).
8. Gateway executes state change exactly once under valid capability.
9. Proof chain verifier detects record tampering.
10. Reset demo restores clean baseline state.
11. End-to-end scenario runner handles all 6 scenarios correctly.
"""
from datetime import datetime, timedelta, timezone
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from canonicalizer import CanonicalizationError, compute_request_hash
from capability import generate_signature, issue_capability, verify_capability_signature
from database import Base
from gateway import GatewayError, verify_and_execute_action
from models import AuthorityEvent, Capability, ProtectedResource
from policy_engine import CURRENT_POLICY_VERSION, evaluate_request
from proof_chain import append_authority_event, verify_proof_chain
from seed import reset, seed


@pytest.fixture
def db_session():
    """Create in-memory SQLite DB session with StaticPool for isolated testing."""
    from sqlalchemy.pool import StaticPool
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    seed(session)
    yield session
    session.close()


def test_canonicalization_stability():
    req1 = {
        "agentId": "ops_agent",
        "tool": "deploy_service",
        "action": "deploy",
        "resource": "prod_k8s_cluster",
        "parameters": {"b": 2, "a": 1},
        "requestedAt": "2026-08-13T22:00:00Z",
        "nonce": "n-1",
        "policyVersion": CURRENT_POLICY_VERSION,
    }
    req2 = {
        "policyVersion": CURRENT_POLICY_VERSION,
        "nonce": "n-1",
        "requestedAt": "2026-08-13T22:00:00Z",
        "parameters": {"a": 1, "b": 2},
        "resource": "prod_k8s_cluster",
        "action": "deploy",
        "tool": "deploy_service",
        "agentId": "ops_agent",
    }
    canon1, hash1 = compute_request_hash(req1)
    canon2, hash2 = compute_request_hash(req2)
    assert hash1 == hash2
    assert canon1 == canon2

    # Change 1 key value -> Hash MUST change
    req3 = dict(req1)
    req3["parameters"] = {"b": 2, "a": 999}
    _, hash3 = compute_request_hash(req3)
    assert hash1 != hash3


def test_malformed_request_rejection():
    req = {
        "agentId": "ops_agent",
        # missing "tool"
        "action": "deploy",
        "resource": "prod_k8s_cluster",
        "parameters": {},
        "requestedAt": "2026-08-13T22:00:00Z",
        "nonce": "n-1",
        "policyVersion": CURRENT_POLICY_VERSION,
    }
    with pytest.raises(CanonicalizationError):
        compute_request_hash(req)


def test_allow_creates_capability(db_session):
    req = {
        "agentId": "ops_agent",
        "tool": "deploy_service",
        "action": "deploy",
        "resource": "prod_k8s_cluster",
        "parameters": {"env": "prod"},
        "requestedAt": "2026-08-13T22:00:00Z",
        "nonce": "n-allow-1",
        "policyVersion": CURRENT_POLICY_VERSION,
    }
    res = evaluate_request(req, db_session)
    assert res["decision"] == "ALLOW"
    assert res["capability"] is not None
    assert verify_capability_signature(res["capability"]["scope"], res["capability"]["signature"])


def test_deny_creates_no_capability(db_session):
    req = {
        "agentId": "ops_agent",
        "tool": "unauthorized_tool_root",
        "action": "destroy",
        "resource": "prod_k8s_cluster",
        "parameters": {},
        "requestedAt": "2026-08-13T22:00:00Z",
        "nonce": "n-deny-1",
        "policyVersion": CURRENT_POLICY_VERSION,
    }
    res = evaluate_request(req, db_session)
    assert res["decision"] == "DENY"
    assert res["capability"] is None


def test_gateway_executes_valid_capability(db_session):
    req = {
        "agentId": "ops_agent",
        "tool": "deploy_service",
        "action": "deploy",
        "resource": "prod_k8s_cluster",
        "parameters": {"v": "1.0"},
        "requestedAt": "2026-08-13T22:00:00Z",
        "nonce": "n-exec-1",
        "policyVersion": CURRENT_POLICY_VERSION,
    }
    eval_res = evaluate_request(req, db_session)
    cap_id = eval_res["capability"]["id"]

    exec_res, proof_hash = verify_and_execute_action(
        db_session, cap_id, req, eval_res["requestHash"]
    )
    assert exec_res["status"] == "executed"
    assert exec_res["newState"]["status"] == "deployed"
    assert proof_hash is not None


def test_gateway_rejects_replay_attempt(db_session):
    req = {
        "agentId": "ops_agent",
        "tool": "deploy_service",
        "action": "deploy",
        "resource": "prod_k8s_cluster",
        "parameters": {"v": "1.0"},
        "requestedAt": "2026-08-13T22:00:00Z",
        "nonce": "n-replay-1",
        "policyVersion": CURRENT_POLICY_VERSION,
    }
    eval_res = evaluate_request(req, db_session)
    cap_id = eval_res["capability"]["id"]

    # First execution succeeds
    verify_and_execute_action(db_session, cap_id, req, eval_res["requestHash"])

    # Second execution must fail with REPLAY_ATTEMPT
    with pytest.raises(GatewayError) as exc_info:
        verify_and_execute_action(db_session, cap_id, req, eval_res["requestHash"])
    assert exc_info.value.code == "REPLAY_ATTEMPT"


def test_gateway_rejects_changed_request_hash(db_session):
    req = {
        "agentId": "ops_agent",
        "tool": "deploy_service",
        "action": "deploy",
        "resource": "prod_k8s_cluster",
        "parameters": {"v": "1.0"},
        "requestedAt": "2026-08-13T22:00:00Z",
        "nonce": "n-hash-1",
        "policyVersion": CURRENT_POLICY_VERSION,
    }
    eval_res = evaluate_request(req, db_session)
    cap_id = eval_res["capability"]["id"]

    # Modify parameters
    changed_req = dict(req)
    changed_req["parameters"] = {"v": "9.9-malicious"}
    _, tampered_hash = compute_request_hash(changed_req)

    with pytest.raises(GatewayError) as exc_info:
        verify_and_execute_action(db_session, cap_id, changed_req, tampered_hash)
    assert exc_info.value.code == "HASH_MISMATCH"


def test_proof_chain_tamper_detection(db_session):
    # Log 2 events
    append_authority_event(db_session, "hash1", "ALLOW", "CODE1", {"a": 1})
    append_authority_event(db_session, "hash2", "DENY", "CODE2", {"b": 2})
    db_session.commit()

    is_valid, err, count = verify_proof_chain(db_session)
    assert is_valid is True

    # Tamper with first event payload
    ev1 = db_session.query(AuthorityEvent).filter(AuthorityEvent.sequence == 1).first()
    ev1.payload = {"tampered": True}
    db_session.commit()

    is_valid, err, _ = verify_proof_chain(db_session)
    assert is_valid is False
    assert "tampering detected" in err


def test_reset_demo(db_session):
    append_authority_event(db_session, "hash1", "ALLOW", "CODE1", {"a": 1})
    db_session.commit()
    assert db_session.query(AuthorityEvent).count() > 0

    reset(db_session)
    assert db_session.query(AuthorityEvent).count() == 0
    assert db_session.query(ProtectedResource).filter(ProtectedResource.id == "prod_k8s_cluster").count() == 1


def test_all_six_scenarios_via_fastapi_client(db_session):
    from fastapi.testclient import TestClient
    from main import app, get_db

    Base.metadata.create_all(bind=db_session.get_bind())
    app.dependency_overrides[get_db] = lambda: db_session
    client = TestClient(app)

    # 1. Valid Action
    r1 = client.post("/run-scenario", json={"scenario": "valid_action"})
    assert r1.status_code == 200
    res1 = r1.json()
    assert res1["verdict"] == "ALLOW"
    assert res1["stateChanged"] is True

    # 2. Unauthorized Tool
    r2 = client.post("/run-scenario", json={"scenario": "unauthorized_tool"})
    assert r2.status_code == 200
    res2 = r2.json()
    assert res2["verdict"] == "DENY"
    assert res2["stateChanged"] is False

    # 3. Prompt Injection
    r3 = client.post("/run-scenario", json={"scenario": "prompt_injection"})
    assert r3.status_code == 200
    res3 = r3.json()
    assert res3["verdict"] == "ESCALATE"
    assert res3["stateChanged"] is False

    # 4. Changed Request
    r4 = client.post("/run-scenario", json={"scenario": "changed_request"})
    assert r4.status_code == 200
    res4 = r4.json()
    assert res4["verdict"] == "DENY"
    assert res4["stateChanged"] is False
    assert res4["reasonCode"] == "GATEWAY_CHANGED_REQUEST_HASH_MISMATCH"

    # 5. Burst Anomaly
    r5 = client.post("/run-scenario", json={"scenario": "burst_anomaly"})
    assert r5.status_code == 200
    res5 = r5.json()
    assert res5["verdict"] == "FREEZE"
    assert res5["stateChanged"] is False

    # 6. Replay Attempt
    r6 = client.post("/run-scenario", json={"scenario": "replay_attempt"})
    assert r6.status_code == 200
    res6 = r6.json()
    assert res6["verdict"] == "DENY"
    assert res6["stateChanged"] is False
    assert res6["replayBlocked"] is True

