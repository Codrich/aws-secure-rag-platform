# NIST AI RMF 1.0 Mapping

This document maps platform controls to the NIST AI Risk Management
Framework 1.0 and its Generative AI Profile. This is an alignment
exercise for a reference implementation — not a certification, audit,
or formal compliance claim.

## GOVERN

| RMF theme | Platform implementation |
|-----------|------------------------|
| Accountability and roles | Single-maintainer project; production guidance documented in runbooks; human review required for releases (manual approval gate) |
| Risk management processes | THREAT_MODEL.md reviewed each phase; AI risk items tracked alongside issues |
| Transparency documentation | Model ID surfaced in every response and log entry; architecture and data flows documented |

## MAP

| RMF theme | Platform implementation |
|-----------|------------------------|
| Context and intended use | Grounded Q&A over a controlled synthetic knowledge base; out-of-scope uses refused (scope-refusal eval cases) |
| Risk identification | STRIDE + OWASP LLM Top 10 threat model; AI-specific risks enumerated per trust boundary |
| Impact characterization | Synthetic data eliminates real-world privacy impact; production impact assumptions stated in threat model |

## MEASURE

| RMF theme | Platform implementation |
|-----------|------------------------|
| Performance measurement | Golden dataset: retrieval hit rate, groundedness, citation correctness, refusal correctness |
| Safety measurement | Guardrail block rate, prompt-attack detections, PII detections tracked as metrics |
| Regression detection | CI evaluation gates fail the pipeline when thresholds regress |

## MANAGE

| RMF theme | Platform implementation |
|-----------|------------------------|
| Risk response | Blocking pipeline gates; rollback via ECS deployment; incident runbook for AI-specific events |
| Monitoring | Token, cost, latency, and safety-event dashboards; alarms on anomalies |
| Incident response | AI_INCIDENT_RESPONSE_RUNBOOK.md covers injection, leakage, and cost-abuse scenarios |

Note: NIST AI RMF 1.0 is under revision; this mapping tracks the 1.0
release and will be updated as the framework evolves.
