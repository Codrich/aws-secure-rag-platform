# Incident Response Policy (Synthetic)

> Entirely synthetic document for platform testing.

## Severity levels

SEV-1 incidents involve customer-facing outage or suspected data breach and
page the on-call engineer immediately. SEV-2 incidents degrade service
without full outage. SEV-3 covers minor defects.

## Response times

SEV-1 requires acknowledgment within 15 minutes and a status update every
30 minutes. SEV-2 requires acknowledgment within 1 hour.

## AI-specific incidents

Suspected prompt-injection exploitation, guardrail bypass, or sensitive-data
leakage through model output is treated as at least SEV-2 and follows the AI
incident response runbook.
