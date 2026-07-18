# Golden evaluation datasets

`golden_seed.jsonl` seeds the evaluation gate (Phase 6+): answerable,
unanswerable, malicious, PII, unauthorized, and irrelevant queries with
expected behaviors. Measured per release: retrieval hit rate, groundedness,
citation correctness, refusal correctness, guardrail block rate, latency,
token usage, and estimated cost. Thresholds are enforced in CI.
