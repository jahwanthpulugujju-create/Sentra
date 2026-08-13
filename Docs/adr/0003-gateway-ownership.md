# ADR 0003: Independent Gateway Execution Ownership

## Context
A major security flaw in guardrail systems is allowing frontend components or agents to directly trigger side effects after receiving a policy verdict.

## Decision
The Independent Gateway (`gateway.py`) is the sole execution path authorized to mutate state on `ProtectedResource` objects.
Before executing an action, the Gateway independently verifies:
1. HMAC signature validity.
2. Capability status is `issued` (not `consumed`, `expired`, or `rejected`).
3. TTL expiry timestamp.
4. Nonce / replay prevention.
5. Exact match between `requestHash` and canonical payload hash.

The Gateway atomically marks the capability as `consumed` prior to executing the protected action.

## Consequences
- Bypassing the gateway cannot modify protected resources.
- Replaying a consumed capability is blocked before action execution.
- Tampered request payloads are rejected by hash mismatch.
