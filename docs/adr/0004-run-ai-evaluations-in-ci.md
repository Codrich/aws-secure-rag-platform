# ADR 0004: Run AI evaluations as blocking CI gates

Status: Accepted (offline gates implemented; model-graded gates at Milestone 5)

## Context
Unit tests verify code paths; they do not verify AI behavior (refusals,
citation integrity, injection resistance).

## Decision
`evaluations/tests` runs on every push/PR as a blocking step, with a
scorecard published to the workflow summary generated only from executed
tests. Offline gates today: no-context refusal, injection confinement,
citation integrity. Live model-graded metrics (groundedness scores, injection
block rates, latency gates) are added when the ephemeral deployment exists.

## Alternatives
Manual eval runs (rejected: unverifiable); publishing projected scores
(rejected: fabricated evidence).

## Consequences
Prompt or retrieval changes that alter safety behavior fail the pipeline.

## Security impact
Behavioral regressions become build failures.

## Cost impact
Zero (offline gates run on GitHub runners with mocks).
