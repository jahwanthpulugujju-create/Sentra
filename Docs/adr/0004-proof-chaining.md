# ADR 0004: Hash-Linked Audit Proof Chaining

## Context
Auditing agent actions requires guarantee that logs cannot be altered, inserted out-of-order, or deleted after execution.

## Decision
Every authority verdict, capability event, and gateway execution appends an entry to the `authority_events` table.
Each record contains a monotonic `sequence` number, `previous_hash`, and `event_hash`.
`eventHash = SHA256(previousHash + canonicalEventPayload)`.

The system includes a verification procedure `verify_proof_chain()` that audits the hash chain across all historical events and flags any modified payload or broken hash link.

## Consequences
- Modifying a single historical audit record invalidates all subsequent event hashes.
- Instant automated verification confirms log integrity.
