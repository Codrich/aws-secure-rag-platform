# Engineering Case Studies

Feature-to-evidence map. Rows reference only implemented, verified work.

| Topic | What this project demonstrates | Evidence |
|---|---|---|
| Retrieval as an authorization boundary | Tenant, classification and per-document ACL filters applied inside the vector query, so unauthorized chunks are never fetched and can never reach the model | `app/rag/retrieval.py`, `app/tests/test_tenant_isolation.py`, ADR 0002 |
| Finding and fixing a defect in my own control | Row security was silently inert because the runtime role was a superuser, and a false-passing test hid it; found on first real database run, fixed with privilege separation and a preflight check | `docs/security/FINDINGS.md` (F-001) |
| Least privilege at the data layer | DDL under an admin connection; runtime role granted DML only and provisioned `NOSUPERUSER NOBYPASSRLS` | `app/rag/schema.py`, `scripts/initialize_database.py` |
| Defense in depth | PostgreSQL row-level security enforces the same boundary independently of application code, and fails closed when the tenant is unset | `app/rag/retrieval.py` (SCHEMA_SQL), `app/tests/test_rls_integration.py` |
| Identity handling | Tenant identity resolved server-side and never accepted from the caller; smuggled fields rejected rather than ignored | `app/auth/tenancy.py`, `app/models/requests.py` |
| Testing a security control properly | RLS cannot be proven with mocks, so it runs against a real pgvector container in a dedicated CI job with a non-privileged role; negative tests assert one specific error, not any error | `.github/workflows/ci.yml` (`integration-tests`) |
| Security boundaries | Refusal-before-model-call when retrieval yields nothing; injected chunk content confined to user role | `app/rag/service.py`, `evaluations/tests/` |
| Fail-closed design | Store outage and model throttling return controlled errors; model never called on retrieval failure | `app/tests/test_failure_modes.py`, ADR 0003 |
| AI behavioral testing in CI | Blocking offline evaluation gates with a scorecard built from real test results | `.github/workflows/ci.yml`, `scripts/run_evaluations.py`, ADR 0004 |
| Risk-to-control traceability | Every claimed control links to its implementation and test | `docs/security/CONTROL_TRACEABILITY.md` |
| Cost-aware architecture | pgvector over OpenSearch Serverless with the trade-off documented | ADR 0001, `docs/architecture/VECTOR_STORE_DECISION.md` |
| Supply-chain hygiene | Secret scanning and IaC scanning on every push | `.github/workflows/security.yml` |
