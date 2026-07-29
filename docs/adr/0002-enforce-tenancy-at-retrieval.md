# ADR 0002: Enforce tenant isolation at the retrieval layer

Status: Accepted (implementation planned - Milestone 2)

## Context
Prompt-level instructions cannot enforce authorization; anything placed in
model context is potentially exposed to the requester.

## Decision
Tenant and document-classification filters are applied in the vector query
itself (`WHERE tenant_id = ... AND classification = ANY(...)`). Chunks the
requester cannot access are never retrieved, so they can never be leaked by
the model.

## Alternatives
Post-retrieval filtering (rejected: filtered content still transits the
application); prompt-level restrictions (rejected: not a security boundary).

## Consequences
Every retrieval requires tenant context; missing context fails with 401/403
per the failure-mode contract.

## Security impact
Retrieval becomes the authorization boundary - the platform's core claim.

## Cost impact
Negligible (indexed filter columns).
