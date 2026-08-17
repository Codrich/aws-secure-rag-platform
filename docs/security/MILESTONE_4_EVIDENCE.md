# Milestone 4 Evidence: Supply Chain Security, SBOMs & DevSecOps Gates

This document records the security controls, supply chain integrity gates, vulnerability policies, and build evidence established in **Milestone 4 (Make the release trustworthy)**.

Controls documented here are verified by automated CI workflows. Planned Milestone 5 controls, including Cosign container signing, cryptographic provenance and attestations, ECR publishing, live AWS deployment smoke tests, latency validation, and live/model-graded evaluations, are explicitly identified as future work to prevent premature claims.

---

## 1. Summary of Executed Security Controls

| Control Domain                     | Tool / Mechanism               | Pinned Version / Commit                                                                                    | Trigger   | Enforcement Level                                    |
| ---------------------------------- | ------------------------------ | ---------------------------------------------------------------------------------------------------------- | --------- | ---------------------------------------------------- |
| **IaC Static Analysis**            | Checkov                        | `bridgecrewio/checkov-action@9b70310bcd306d11740313070b940167d6b23085`                                     | Push / PR | Blocking (`soft_fail: false`)                        |
| **Secret Scanning (Full History)** | TruffleHog                     | `trufflesecurity/trufflehog@24c98ca20e421a6807518f79c5cdd063400774f2`                                      | Push / PR | Blocking (`--results=verified,unknown`)              |
| **Secret Scanning (Git Diffs)**    | Gitleaks                       | `gitleaks/gitleaks-action@ff98106e4c7b2bc287b24eaf42907196329070c7` (`v2.3.9`)                             | Push / PR | Blocking                                             |
| **Dependency CVE Audit**           | pip-audit                      | `pip-audit==2.10.0`                                                                                        | Push / PR | Blocking (`--require-hashes`)                        |
| **Container CVE Scan**             | Trivy                          | `aquasecurity/trivy-action@a9c7b0f06e461e9d4b4d1711f154ee024b8d7ab8` (`v0.36.0`)                           | Push / PR | Blocking (`exit-code: 1`, `HIGH,CRITICAL`)           |
| **Terraform Policy-as-Code**       | Open Policy Agent / Conftest   | `openpolicyagent/conftest:v0.68.2@sha256:5fd81e332d7e4bc01daf3ef35371800a9a9720a30c0c37a78de0c5fbe4b6d622` | Push / PR | Blocking (`NET-001`, `DB-001`, `NET-002`, `NET-003`) |
| **Application SBOM**               | CycloneDX Python               | `cyclonedx-bom==4.1.2`                                                                                     | Push / PR | CycloneDX JSON artifact generated and validated      |
| **Container SBOM**                 | Trivy CycloneDX                | `aquasecurity/trivy-action@a9c7b0f06e461e9d4b4d1711f154ee024b8d7ab8`                                       | Push / PR | CycloneDX JSON artifact generated and validated      |
| **Build Evidence & Digest**        | Docker image archive + SHA-256 | `docker save` + `sha256sum`                                                                                | Push / PR | Build metadata, checksums, and archived artifacts    |

---

## 2. Software Bill of Materials (SBOM)

### Python Application SBOM

* **Standard:** CycloneDX JSON format
* **Source:** Generated from locked production dependencies exported from `uv.lock` into requirements format. Dependency auditing separately enforces package hashes using `pip-audit --require-hashes`.
* **File:** `sbom-python.cdx.json`
* **Verification:** Automated JSON validation verifies:

  * `bomFormat == "CycloneDX"`
  * accepted CycloneDX specification version (`1.4`, `1.5`, or `1.6`)
  * populated component inventory

### Container Image SBOM

* **Standard:** CycloneDX JSON format
* **Source:** Generated from the multi-stage, non-root runtime image `aws-secure-rag-platform:${{ github.sha }}` using Trivy.
* **File:** `sbom-container.cdx.json`
* **Verification:** Automated validation confirms the document is a valid CycloneDX SBOM with an accepted specification version and a non-empty component inventory. The generated container SBOM inventories operating-system and application/runtime packages detected in the built image.

---

## 3. Docker Image Archiving & Build Evidence

For every applicable CI build on `main` or pull request:

1. The container image is built from the locked Dockerfile:

   ```bash
   docker build --tag aws-secure-rag-platform:${{ github.sha }} .
   ```

2. The image is exported as a compressed Docker image archive and the generated SBOMs are staged into `artifacts/`:

   ```bash
   docker save aws-secure-rag-platform:${{ github.sha }} \
     | gzip > artifacts/aws-secure-rag-platform-${{ github.sha }}.tar.gz

   cp sbom-python.cdx.json sbom-container.cdx.json artifacts/
   ```

3. SHA-256 digests are calculated for the image archive and SBOM documents:

   ```bash
   cd artifacts

   sha256sum \
     aws-secure-rag-platform-${{ github.sha }}.tar.gz \
     > aws-secure-rag-platform-${{ github.sha }}.tar.gz.sha256

   sha256sum \
     sbom-python.cdx.json \
     sbom-container.cdx.json \
     > sboms.sha256
   ```

4. Checksums are verified immediately in CI:

   ```bash
   sha256sum -c aws-secure-rag-platform-${{ github.sha }}.tar.gz.sha256
   sha256sum -c sboms.sha256
   ```

5. A machine-readable `build-metadata.json` is generated recording:

   * Git commit SHA
   * Git reference
   * repository identifier
   * UTC build timestamp
   * GitHub runner information recorded by the workflow
   * container image tag
   * image archive reference
   * Python SBOM reference
   * container SBOM reference

6. All generated artifacts are published using:

   ```text
   actions/upload-artifact@4cec3d8aa04e39d1a68397de0c4cd6fb99baeddf
   ```

   Version: `v4.6.1`

The Milestone 4 build evidence provides integrity hashes and traceable build metadata. It does **not** constitute signed or cryptographically verifiable provenance; signed provenance and attestations remain Milestone 5 work.

---

## 4. Container Vulnerability Exception Policy

Container vulnerability scanning with Trivy is blocking for `HIGH` and `CRITICAL` findings.

Unfixed upstream base-image CVEs may be temporarily handled through explicit entries in [`.trivyignore.yaml`](../../.trivyignore.yaml).

### Rules for Exceptions

1. **Explicit CVE ID:** Every exception must specify an exact vulnerability identifier. Wildcard vulnerability suppression is not permitted.

2. **Mandatory Expiration Date (`expired_at`):** Every approved exception must include an explicit expiration date. Once the exception expires, the finding is no longer ignored and is again subject to the blocking vulnerability gate.

3. **Justification Statement:** Every exception must include a documented reason, including applicable upstream/vendor status and risk context.

4. **Ownership:** Exception ownership must be documented as part of the associated security evidence or governance record so responsibility for review and renewal is explicit.

Exceptions are temporary risk-management decisions and do not convert affected vulnerabilities into accepted permanent risk.

---

## 5. Policy-as-Code (OPA / Conftest) Controls

Terraform plan representations are evaluated against OPA/Rego policies defined in [`policy/terraform/security.rego`](../../policy/terraform/security.rego).

The current Milestone 4 policies enforce:

* **`NET-001`** — ECS services must not assign public IP addresses to tasks (`assign_public_ip == false`).
* **`DB-001`** — RDS instances must not be publicly accessible (`publicly_accessible == false`).
* **`NET-002`** — Security groups must not permit unrestricted IPv4 ingress (`0.0.0.0/0`).
* **`NET-003`** — Security groups must not permit unrestricted IPv6 ingress (`::/0`).

The gate is tested using deterministic Terraform plan JSON fixtures:

* Positive/compliant fixture: [`policy/fixtures/terraform-plan-compliant.json`](../../policy/fixtures/terraform-plan-compliant.json)
* Negative/noncompliant fixture: [`policy/fixtures/terraform-plan-noncompliant.json`](../../policy/fixtures/terraform-plan-noncompliant.json)

The compliant fixture must pass, while the noncompliant fixture must be rejected by the policy gate.

This Milestone 4 control validates deterministic plan fixtures. Validation against a live Terraform plan remains Milestone 5 work.

---

## 6. Scope Boundaries: Milestone 4 vs. Milestone 5

To ensure documented claims match implemented controls:

| Capability                       | Milestone 4 Status                                                | Milestone 5 Target                                                           |
| -------------------------------- | ----------------------------------------------------------------- | ---------------------------------------------------------------------------- |
| Dependency Lockfile              | **Implemented** (`uv.lock`)                                       | Active                                                                       |
| Dependency Hash Audit            | **Implemented** (`pip-audit --require-hashes`)                    | Active                                                                       |
| Secret Scanning                  | **Implemented** (TruffleHog + Gitleaks)                           | Active                                                                       |
| IaC Misconfiguration Scanning    | **Implemented** (Checkov)                                         | Active                                                                       |
| Container Image Hardening        | **Implemented** (non-root, multi-stage)                           | Active                                                                       |
| Container CVE Gate               | **Implemented** (Trivy + explicit expiring exceptions)            | Active                                                                       |
| Policy-as-Code Gate              | **Implemented** (Conftest + Rego + deterministic fixtures)        | Live Terraform plan validation                                               |
| CycloneDX SBOMs                  | **Implemented** (Python + container JSON)                         | Active                                                                       |
| Build Evidence & Digests         | **Implemented** (Docker image archive + SHA-256 + build metadata) | Signed attestations                                                          |
| Container Image Signing          | *Not implemented in M4*                                           | **Milestone 5** — Cosign signing and verification                            |
| Signed Provenance / Attestations | *Not implemented in M4; metadata and hashes only*                 | **Milestone 5** — GitHub Artifact Attestations / in-toto-compatible evidence |
| Container Registry Push          | *Not implemented in M4*                                           | **Milestone 5** — AWS ECR publishing and verification                        |
| Live Terraform Plan Validation   | *Not implemented in M4; fixture plans only*                       | **Milestone 5** — policy validation against generated Terraform plan         |
| Live AWS Deployment              | *Not implemented in M4*                                           | **Milestone 5** — Terraform apply and ECS smoke testing                      |
| Live Bedrock Integration         | *Not implemented in M4*                                           | **Milestone 5** — live AWS Bedrock execution                                 |
| Latency Validation               | *Not implemented in M4*                                           | **Milestone 5** — measured runtime latency                                   |
| Model-Graded Evaluations         | *Not implemented in M4; deterministic offline evaluations only*   | **Milestone 5** — live/model-graded evaluation evidence                      |
