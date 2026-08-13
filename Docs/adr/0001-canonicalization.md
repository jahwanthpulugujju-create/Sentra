# ADR 0001: Request Canonicalization and Hashing

## Context
Agent requests can vary in whitespace, key ordering, or parameter formatting. To cryptographically bind execution authority to an exact request, the payload must produce a deterministic byte representation.

## Decision
We enforce strict request schema validation (`agentId`, `tool`, `action`, `resource`, `parameters`, `requestedAt`, `nonce`, `policyVersion`) and canonicalize JSON using alphabetic key sorting, standard number normalization, explicit null handling, and compact UTF-8 formatting.
We compute `requestHash = SHA256(canonicalRequest)`.

## Consequences
- Any modification to parameter values or keys produces a different `requestHash`.
- Gateway can independently verify whether a request matches the capability approval hash.
