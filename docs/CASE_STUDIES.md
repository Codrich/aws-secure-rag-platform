# Engineering Case Studies

Feature-to-evidence map. Rows reference only implemented, verified work.

| Topic | What this project demonstrates | Evidence |
|---|---|---|
| Security boundaries | Refusal-before-model-call when retrieval yields nothing; injected chunk content confined to user role | `app/rag/service.py`, `evaluations/tests/` |
| Fail-closed design | Store outage and model throttling return controlled errors; model never called on retrieval failure | `app/tests/test_failure_modes.py`, ADR 0003 |
| AI behavioral testing in CI | Blocking offline evaluation gates with a scorecard built from real test results | `.github/workflows/ci.yml`, `scripts/run_evaluations.py`, ADR 0004 |
| Risk-to-control traceability | Every claimed control links to its implementation and test | `docs/security/CONTROL_TRACEABILITY.md` |
| Cost-aware architecture | pgvector over OpenSearch Serverless with the trade-off documented | ADR 0001, `docs/architecture/VECTOR_STORE_DECISION.md` |
| Supply-chain hygiene | Secret scanning and IaC scanning on every push | `.github/workflows/security.yml` |
