# ADR 0002: Enforce tenant isolation at the retrieval layer

Status: Accepted (implemented, Milestone 2)

## Context
Prompt-level instructions cannot enforce authorization; anything placed in
model context is potentially exposed to the requester. Isolation must sit
below the model.

## Decision
Tenant and document-classification filters are applied in the vector query
itself. Two independent layers enforce this:

1. **Application layer** - `VectorStore.search` filters on `tenant_id`, the
   caller's allowed classifications, and the document's `allowed_roles` ACL
   inside the SQL `WHERE` clause, so unauthorized chunks are never fetched
   into application memory. Classification is the coarse sensitivity tier a
   role may read; `allowed_roles` is an optional per-document ACL that
   narrows access further (empty means classification alone governs). A
   caller must satisfy both.
2. **Database layer** - PostgreSQL row-level security on `document_chunks`,
   declared `FORCE` so it applies to the table owner as well. Each
   connection sets `app.tenant_id` through `set_config()`; the policy
   compares against `current_setting('app.tenant_id', true)`, which is NULL
   when unset, so the policy matches no rows. A connection that forgets to
   set the tenant sees nothing rather than everything.

   **The runtime role must be `NOSUPERUSER NOBYPASSRLS`.** PostgreSQL exempts
   superusers and `BYPASSRLS` roles from row security unconditionally, and
   `FORCE` removes only the table-owner exemption. Schema, policy and role
   provisioning therefore run under a separate administrative connection
   (`app/rag/schema.py`, `ADMIN_DATABASE_URL`) while the application uses a
   restricted runtime role granted DML only. `assert_no_rls_bypass()` fails
   initialization if that role can bypass the policy. This is not a detail:
   getting it wrong disables the layer silently while every
   application-layer test still passes (docs/security/FINDINGS.md, F-001).

Tenant identity is resolved server-side (`app/auth/tenancy.py`) and is never
read from the request body; request models set `extra="forbid"` so a
smuggled `tenant_id` is rejected with 422 rather than silently ignored.

## Alternatives
- Post-retrieval filtering: rejected - filtered content still transits the
  application and can leak through logs or errors.
- Prompt-level restrictions: rejected - not a security boundary.
- Schema or database per tenant: rejected - stronger isolation, but it
  breaks the single-table pgvector design and complicates migrations
  disproportionately at this scale.
- Application filter only (no RLS): rejected - a single missing predicate in
  future code would silently cross tenants.

## Consequences
Chunks carry `tenant_id`, `document_id`, `classification`, `allowed_roles`
and `source`; `document_id` is the replacement unit for re-ingestion.
Every retrieval requires tenant context; missing context returns 401 and an
unknown tenant returns 403. Ingestion is scoped to the caller's tenant and
a caller cannot ingest at a classification its role cannot read. RLS
correctness cannot be verified with mocks, so it is covered by integration
tests that run against a real pgvector service container in CI.

## Security impact
Retrieval is the authorization boundary - the platform's core claim - and it
holds even if the application layer regresses.

## Cost impact
Negligible: two indexed filter columns and one `set_config` round trip per
request.
