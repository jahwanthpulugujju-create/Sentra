"""Cryptographically Signed Capability Issuer & Verifier.

Capabilities bind authority to exact requestHash and scope with short TTL.
"""
import hmac
import hashlib
import json
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

from config import SECRET_KEY

DEFAULT_TTL_MINUTES = 5


def generate_signature(payload: Dict[str, Any]) -> str:
    """Generate HMAC-SHA256 signature for capability payload."""
    canonical_payload = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hmac.new(
        SECRET_KEY.encode("utf-8"),
        canonical_payload.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


def issue_capability(
    request_hash: str,
    agent_id: str,
    tool: str,
    action: str,
    resource: str,
    policy_version: str,
    nonce: str,
    ttl_minutes: int = DEFAULT_TTL_MINUTES,
) -> Dict[str, Any]:
    """Issue a signed capability after an ALLOW decision."""
    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(minutes=ttl_minutes)

    capability_id = f"cap_{uuid.uuid4().hex[:12]}"

    scope = {
        "capabilityId": capability_id,
        "requestHash": request_hash,
        "agentId": agent_id,
        "tool": tool,
        "action": action,
        "resource": resource,
        "policyVersion": policy_version,
        "nonce": nonce,
        "issuedAt": now.isoformat(),
        "expiresAt": expires_at.isoformat(),
    }

    sig = generate_signature(scope)

    return {
        "id": capability_id,
        "requestHash": request_hash,
        "scope": scope,
        "signature": sig,
        "expiresAt": expires_at,
        "status": "issued",
        "nonce": nonce,
    }


def verify_capability_signature(scope: Dict[str, Any], signature: str) -> bool:
    """Verify HMAC signature of given capability scope."""
    expected = generate_signature(scope)
    return hmac.compare_digest(expected, signature)
