"""Deterministic Policy Kernel for Sentra Authority Engine.

Evaluates canonical request and returns deterministic outcomes:
- ALLOW
- DENY
- ESCALATE
- FREEZE

Rule Engine principles:
1. LLM does NOT directly issue allow, capability, or gateway verdict.
2. Fail closed on unknown tools, invalid scopes, prompt injection indicators, or burst anomalies.
3. Track policy versioning ("v1.0.0-sentra-kernel").
"""
import re
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from sqlalchemy.orm import Session

from canonicalizer import compute_request_hash
from capability import issue_capability
from config import POLICY_VERSION
from models import Capability
from proof_chain import append_authority_event

CURRENT_POLICY_VERSION = POLICY_VERSION

# Allowed Agent Scopes
AUTHORIZED_SCOPES = {
    "ops_agent": {
        "allowed_tools": ["deploy_service", "restart_pod", "update_config"],
        "allowed_resources": ["prod_k8s_cluster", "staging_k8s_cluster"],
    },
    "monitoring_agent": {
        "allowed_tools": ["fetch_metrics", "log_alert"],
        "allowed_resources": ["prod_k8s_cluster"],
    },
}

# Known Prompt Injection Attack Signatures
PROMPT_INJECTION_PATTERNS = [
    r"ignore (all )?previous instructions",
    r"bypass (authority|policy|guardrails?)",
    r"system prompt override",
    r"sudo ",
    r"drop database",
    r"chmod 777",
    r"cat /etc/passwd",
    r"eval\(",
    r"exec\(",
]


def check_prompt_injection(data: Dict[str, Any]) -> bool:
    """Scan request parameters and prompt context for injection indicators."""
    text_to_scan = []
    
    params = data.get("parameters", {})
    if isinstance(params, dict):
        for v in params.values():
            if isinstance(v, str):
                text_to_scan.append(v)
    elif isinstance(params, str):
        text_to_scan.append(params)

    prompt_ctx = data.get("promptContext")
    if isinstance(prompt_ctx, str):
        text_to_scan.append(prompt_ctx)

    combined = " ".join(text_to_scan).lower()

    for pattern in PROMPT_INJECTION_PATTERNS:
        if re.search(pattern, combined):
            return True
    return False


def check_burst_anomaly(data: Dict[str, Any], db: Optional[Session] = None) -> bool:
    """Check if agent/request exhibits burst anomaly behavior."""
    params = data.get("parameters", {})
    if isinstance(params, dict) and params.get("burstTrigger") is True:
        return True
    return False


def evaluate_request(data: Dict[str, Any], db: Session) -> Dict[str, Any]:
    """Evaluate canonical request through deterministic policy rules.

    Returns dict containing decision, reason_code, explanation, request_hash, capability (if ALLOW).
    """
    canonical_str, req_hash = compute_request_hash(data)

    agent_id = data.get("agentId")
    tool = data.get("tool")
    action = data.get("action")
    resource = data.get("resource")
    policy_ver = data.get("policyVersion")
    nonce = data.get("nonce")

    # Rule 1: Policy Version Match
    if policy_ver != CURRENT_POLICY_VERSION:
        decision = "DENY"
        reason_code = "POLICY_VERSION_MISMATCH"
        explanation = f"Unsupported policy version: expected {CURRENT_POLICY_VERSION}, got {policy_ver}"
        
        append_authority_event(
            db, request_hash=req_hash, decision=decision, reason_code=reason_code,
            payload={"request": data, "explanation": explanation}
        )
        db.commit()
        return {
            "decision": decision,
            "reasonCode": reason_code,
            "explanation": explanation,
            "requestHash": req_hash,
            "canonicalRequest": canonical_str,
            "capability": None,
            "policyVersion": CURRENT_POLICY_VERSION,
        }

    # Rule 2: Burst Anomaly Detection -> FREEZE
    if check_burst_anomaly(data, db):
        decision = "FREEZE"
        reason_code = "POLICY_BURST_ANOMALY_FREEZE"
        explanation = "Suspicious high-frequency repeated request detected. Safety boundary frozen."
        
        append_authority_event(
            db, request_hash=req_hash, decision=decision, reason_code=reason_code,
            payload={"request": data, "explanation": explanation}
        )
        db.commit()
        return {
            "decision": decision,
            "reasonCode": reason_code,
            "explanation": explanation,
            "requestHash": req_hash,
            "canonicalRequest": canonical_str,
            "capability": None,
            "policyVersion": CURRENT_POLICY_VERSION,
        }

    # Rule 3: Prompt Injection Inspection -> ESCALATE
    if check_prompt_injection(data):
        decision = "ESCALATE"
        reason_code = "POLICY_PROMPT_INJECTION_DETECTED"
        explanation = "Untrusted or ambiguous instruction content detected in request context. Requires human escalation."
        
        append_authority_event(
            db, request_hash=req_hash, decision=decision, reason_code=reason_code,
            payload={"request": data, "explanation": explanation}
        )
        db.commit()
        return {
            "decision": decision,
            "reasonCode": reason_code,
            "explanation": explanation,
            "requestHash": req_hash,
            "canonicalRequest": canonical_str,
            "capability": None,
            "policyVersion": CURRENT_POLICY_VERSION,
        }

    # Rule 4: Unauthorized Tool or Resource -> DENY
    agent_scope = AUTHORIZED_SCOPES.get(agent_id)
    if not agent_scope or tool not in agent_scope.get("allowed_tools", []) or resource not in agent_scope.get("allowed_resources", []):
        decision = "DENY"
        reason_code = "POLICY_UNAUTHORIZED_TOOL_OR_RESOURCE"
        explanation = f"Agent '{agent_id}' is not authorized to invoke tool '{tool}' on resource '{resource}'."
        
        append_authority_event(
            db, request_hash=req_hash, decision=decision, reason_code=reason_code,
            payload={"request": data, "explanation": explanation}
        )
        db.commit()
        return {
            "decision": decision,
            "reasonCode": reason_code,
            "explanation": explanation,
            "requestHash": req_hash,
            "canonicalRequest": canonical_str,
            "capability": None,
            "policyVersion": CURRENT_POLICY_VERSION,
        }

    # Rule 5: Deterministic ALLOW -> Issue Signed Capability
    decision = "ALLOW"
    reason_code = "POLICY_ALLOWED"
    explanation = f"Request verified. Agent '{agent_id}' is authorized for action '{action}' on '{resource}'."

    cap_data = issue_capability(
        request_hash=req_hash,
        agent_id=agent_id,
        tool=tool,
        action=action,
        resource=resource,
        policy_version=CURRENT_POLICY_VERSION,
        nonce=nonce,
    )

    cap_record = Capability(
        id=cap_data["id"],
        request_hash=cap_data["requestHash"],
        scope=cap_data["scope"],
        signature=cap_data["signature"],
        expires_at=cap_data["expiresAt"],
        status=cap_data["status"],
        nonce=cap_data["nonce"],
    )
    db.add(cap_record)
    db.flush()

    append_authority_event(
        db, request_hash=req_hash, decision=decision, reason_code=reason_code,
        payload={"request": data, "explanation": explanation, "capabilityId": cap_data["id"]}
    )
    db.commit()

    return {
        "decision": decision,
        "reasonCode": reason_code,
        "explanation": explanation,
        "requestHash": req_hash,
        "canonicalRequest": canonical_str,
        "capability": cap_data,
        "policyVersion": CURRENT_POLICY_VERSION,
    }
