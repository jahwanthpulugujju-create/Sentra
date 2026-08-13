"""Independent Gateway for Sentra Authority Engine.

The Gateway is the ONLY authorized execution path for protected software tools/resources.
It independently verifies signed capabilities, checks request hashes, prevents replays,
consumes capabilities atomically, and logs to the proof chain.
"""
from datetime import datetime, timezone
from typing import Any, Dict, Tuple

from sqlalchemy.orm import Session

from capability import verify_capability_signature
from models import Capability, ProtectedResource
from proof_chain import append_authority_event


class GatewayError(ValueError):
    """Raised when gateway verification or execution fails."""
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code
        self.message = message


def verify_and_execute_action(
    db: Session,
    capability_id: str,
    request: Dict[str, Any],
    provided_request_hash: str,
) -> Tuple[Dict[str, Any], str]:
    """Independently verify capability and execute protected action.

    Returns (execution_result_dict, proof_event_hash).
    """
    # 1. Fetch Capability with row locking where supported
    cap = (
        db.query(Capability)
        .filter(Capability.id == capability_id)
        .with_for_update()
        .first()
    )

    if not cap:
        raise GatewayError("INVALID_CAPABILITY", f"Capability ID {capability_id} not found.")

    scope = cap.scope
    now = datetime.now(timezone.utc)

    # 2. Status Check
    if cap.status == "consumed":
        append_authority_event(
            db,
            request_hash=provided_request_hash,
            decision="DENY",
            reason_code="GATEWAY_REPLAY_ATTEMPT",
            payload={"gatewayError": "Capability already consumed", "capabilityId": capability_id},
        )
        db.commit()
        raise GatewayError("REPLAY_ATTEMPT", f"Capability {capability_id} has already been consumed.")

    if cap.status != "issued":
        raise GatewayError("CAPABILITY_INACTIVE", f"Capability {capability_id} is in status '{cap.status}'.")

    # 3. Expiry Check
    expires_at = cap.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)

    if now > expires_at:
        cap.status = "expired"
        db.commit()
        append_authority_event(
            db,
            request_hash=provided_request_hash,
            decision="DENY",
            reason_code="GATEWAY_EXPIRED_CAPABILITY",
            payload={"gatewayError": "Capability expired", "capabilityId": capability_id},
        )
        db.commit()
        raise GatewayError("CAPABILITY_EXPIRED", f"Capability {capability_id} expired at {expires_at.isoformat()}.")

    # 4. Signature Check
    if not verify_capability_signature(scope, cap.signature):
        cap.status = "rejected"
        db.commit()
        raise GatewayError("INVALID_SIGNATURE", "Capability HMAC signature verification failed.")

    # 5. Request Hash Binding Check
    if scope.get("requestHash") != provided_request_hash:
        cap.status = "rejected"
        db.commit()
        append_authority_event(
            db,
            request_hash=provided_request_hash,
            decision="DENY",
            reason_code="GATEWAY_CHANGED_REQUEST_HASH_MISMATCH",
            payload={
                "gatewayError": "Request hash mismatch",
                "expected": scope.get("requestHash"),
                "provided": provided_request_hash,
            },
        )
        db.commit()
        raise GatewayError("HASH_MISMATCH", f"Request hash mismatch: expected {scope.get('requestHash')}, got {provided_request_hash}.")

    # 6. Scope matching check (tool, action, resource)
    if scope.get("tool") != request.get("tool"):
        raise GatewayError("SCOPE_MISMATCH_TOOL", f"Tool mismatch: capability for {scope.get('tool')}, requested {request.get('tool')}.")
    if scope.get("action") != request.get("action"):
        raise GatewayError("SCOPE_MISMATCH_ACTION", f"Action mismatch: capability for {scope.get('action')}, requested {request.get('action')}.")
    if scope.get("resource") != request.get("resource"):
        raise GatewayError("SCOPE_MISMATCH_RESOURCE", f"Resource mismatch: capability for {scope.get('resource')}, requested {request.get('resource')}.")

    # 7. Atomic Capability Consumption
    cap.status = "consumed"
    cap.consumed_at = now

    # 8. Execute Protected Action (State Change)
    res_id = request.get("resource", "prod_k8s_cluster")
    resource_obj = (
        db.query(ProtectedResource)
        .filter(ProtectedResource.id == res_id)
        .with_for_update()
        .first()
    )

    if not resource_obj:
        resource_obj = ProtectedResource(
            id=res_id,
            label="Production Kubernetes Cluster",
            state={"status": "idle", "version": "v1.28.0", "deployCount": 0, "lastDeployBy": "none"},
        )
        db.add(resource_obj)

    curr_state = dict(resource_obj.state or {})
    curr_state["status"] = "deployed"
    curr_state["deployCount"] = curr_state.get("deployCount", 0) + 1
    curr_state["lastDeployBy"] = request.get("agentId", "ops_agent")
    curr_state["lastAction"] = request.get("action")
    curr_state["lastExecutedAt"] = now.isoformat()
    curr_state["parameters"] = request.get("parameters", {})

    resource_obj.state = curr_state
    resource_obj.updated_at = now

    # 9. Record Gateway Execution in Proof Chain
    exec_event = append_authority_event(
        db,
        request_hash=provided_request_hash,
        decision="ALLOW",
        reason_code="GATEWAY_EXECUTION_SUCCESS",
        payload={
            "gatewayStatus": "verified_and_executed",
            "capabilityId": capability_id,
            "agentId": request.get("agentId"),
            "tool": request.get("tool"),
            "action": request.get("action"),
            "resource": res_id,
            "newState": curr_state,
        },
    )

    db.commit()

    return {
        "status": "executed",
        "resourceId": res_id,
        "newState": curr_state,
        "capabilityId": capability_id,
        "consumedAt": now.isoformat(),
        "proofEventHash": exec_event.event_hash,
    }, exec_event.event_hash
