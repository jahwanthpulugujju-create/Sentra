"""Deterministic Request Canonicalization & Hashing.

Rules:
1. Strict schema validation (reject missing/unknown fields).
2. Key-sorted, whitespace-compact, deterministic JSON serialization.
3. SHA-256 request hash generation.
"""
import hashlib
import json
from typing import Any, Dict

REQUIRED_FIELDS = {
    "agentId",
    "tool",
    "action",
    "resource",
    "parameters",
    "requestedAt",
    "nonce",
    "policyVersion",
}

ALL_ALLOWED_FIELDS = REQUIRED_FIELDS | {"promptContext"}


class CanonicalizationError(ValueError):
    """Raised when a request is malformed, missing required fields, or oversized."""
    pass


def validate_request_schema(data: Dict[str, Any]) -> None:
    """Validate request fields against strict authority contract."""
    if not isinstance(data, dict):
        raise CanonicalizationError("Request body must be a JSON object.")

    missing = REQUIRED_FIELDS - data.keys()
    if missing:
        raise CanonicalizationError(f"Missing required fields: {', '.join(sorted(missing))}")

    unknown = set(data.keys()) - ALL_ALLOWED_FIELDS
    if unknown:
        raise CanonicalizationError(f"Unknown fields rejected: {', '.join(sorted(unknown))}")

    if not isinstance(data["agentId"], str) or not data["agentId"].strip():
        raise CanonicalizationError("agentId must be a non-empty string.")
    if not isinstance(data["tool"], str) or not data["tool"].strip():
        raise CanonicalizationError("tool must be a non-empty string.")
    if not isinstance(data["action"], str) or not data["action"].strip():
        raise CanonicalizationError("action must be a non-empty string.")
    if not isinstance(data["resource"], str) or not data["resource"].strip():
        raise CanonicalizationError("resource must be a non-empty string.")
    if not isinstance(data["parameters"], dict):
        raise CanonicalizationError("parameters must be a dict.")
    if not isinstance(data["requestedAt"], str) or not data["requestedAt"].strip():
        raise CanonicalizationError("requestedAt must be an ISO timestamp string.")
    if not isinstance(data["nonce"], str) or not data["nonce"].strip():
        raise CanonicalizationError("nonce must be a non-empty string.")
    if not isinstance(data["policyVersion"], str) or not data["policyVersion"].strip():
        raise CanonicalizationError("policyVersion must be a non-empty string.")


def canonicalize_json(data: Any) -> str:
    """Recursively convert data into canonical key-sorted JSON string."""
    return json.dumps(
        data,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    )


def compute_request_hash(data: Dict[str, Any]) -> tuple[str, str]:
    """Validate, canonicalize, and return (canonical_json_str, sha256_hash)."""
    validate_request_schema(data)

    # Filter to exact expected object structure with explicit key order
    canonical_dict = {
        "agentId": data["agentId"],
        "tool": data["tool"],
        "action": data["action"],
        "resource": data["resource"],
        "parameters": data["parameters"],
        "requestedAt": data["requestedAt"],
        "nonce": data["nonce"],
        "policyVersion": data["policyVersion"],
    }
    if "promptContext" in data and data["promptContext"] is not None:
        canonical_dict["promptContext"] = data["promptContext"]

    canonical_str = canonicalize_json(canonical_dict)
    req_hash = hashlib.sha256(canonical_str.encode("utf-8")).hexdigest()
    return canonical_str, req_hash
