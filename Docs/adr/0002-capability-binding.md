# ADR 0002: Cryptographic Capability Binding

## Context
When policy rules return an `ALLOW` verdict, the system must issue an execution credential that cannot be forged, altered, or reused across different resources or tools.

## Decision
The Capability Issuer signs an HMAC-SHA256 signature over a scope payload containing `capabilityId`, `requestHash`, `agentId`, `tool`, `action`, `resource`, `policyVersion`, `nonce`, `issuedAt`, and `expiresAt`. Capabilities have a short TTL (5 minutes).

## Consequences
- Possessing a capability grants authority ONLY for the exact request hash and scope.
- Capabilities expire automatically after TTL.
- Browser/agent cannot forge capabilities without server signing secret.
