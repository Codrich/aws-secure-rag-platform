"""Run the offline evaluation suites and emit a scorecard from real results.

The scorecard reports only executed tests - no projected scores. Live
model-graded metrics (groundedness scores, injection block rates) are added
when the ephemeral AWS deployment exists (Milestone 5).

Results are broken out per control category. A category that reports zero
executed tests fails the gate, so a suite cannot silently disappear and
still show green.
"""
import os
import sys
import xml.etree.ElementTree as ET  # noqa: S405 - parses our own junit output
from dataclasses import dataclass, field
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
JUNIT_PATH = REPO_ROOT / "eval-results.xml"

# Maps the test module that owns a control to its scorecard category. Keys are
# matched against the junit "classname" attribute, which pytest renders as the
# dotted module path (e.g. evaluations.tests.test_groundedness).
#
# The sensitive-data row is labelled "detection" deliberately: that suite
# exercises app.core.sensitive_data as a library. Request/response blocking
# and masking are not implemented, so no enforcement claim is made here.
CATEGORY_BY_MODULE: dict[str, str] = {
    "test_groundedness": "Refusal / groundedness",
    "test_prompt_injection": "Prompt injection",
    "test_response_quality": "Citation integrity",
    "test_sensitive_data": "Sensitive-data detection (not enforced)",
}

UNCATEGORIZED = "Uncategorized"


@dataclass
class CategoryResult:
    """Executed-test counts for one control category."""

    total: int = 0
    failures: int = 0
    skipped: int = 0
    failed_ids: list[str] = field(default_factory=list)

    @property
    def passed(self) -> int:
        return self.total - self.failures - self.skipped

    @property
    def executed(self) -> int:
        """Tests that actually ran. Skips do not count as evidence."""
        return self.total - self.skipped

    @property
    def status(self) -> str:
        if self.failures:
            return "FAIL"
        if self.executed == 0:
            return "FAIL"
        return "PASS"


def categorize(classname: str) -> str:
    for module, category in CATEGORY_BY_MODULE.items():
        if module in classname:
            return category
    return UNCATEGORIZED


def collect_categories(suite: ET.Element) -> dict[str, CategoryResult]:
    """Bucket junit testcases into control categories."""
    results: dict[str, CategoryResult] = {
        category: CategoryResult() for category in CATEGORY_BY_MODULE.values()
    }
    for case in suite.iter("testcase"):
        category = categorize(case.get("classname", ""))
        result = results.setdefault(category, CategoryResult())
        result.total += 1
        if case.find("failure") is not None or case.find("error") is not None:
            result.failures += 1
            result.failed_ids.append(case.get("name", "?"))
        elif case.find("skipped") is not None:
            result.skipped += 1
    return results


def build_scorecard(junit: Path) -> tuple[str, bool]:
    """Render the scorecard. Returns the markdown and whether every gate held."""
    suite = ET.parse(junit).getroot().find("testsuite")  # noqa: S314 - trusted local file
    if suite is None:
        raise RuntimeError("junit report missing testsuite element")
    total = int(suite.get("tests", "0"))
    failures = int(suite.get("failures", "0")) + int(suite.get("errors", "0"))
    skipped = int(suite.get("skipped", "0"))
    passed = total - failures - skipped
    status = "PASS" if failures == 0 else "FAIL"

    categories = collect_categories(suite)
    # A fully skipped category proves nothing, so it counts as unexecuted and
    # fails the gate exactly as a missing suite would.
    unexecuted = [
        name
        for name, result in categories.items()
        if result.executed == 0
    ]
    all_green = failures == 0 and not unexecuted

    lines = [
        "## AI Evaluation Gate (offline)",
        "",
        "| Metric | Value | Status |",
        "|---|---|---|",
        f"| Evaluation tests passed | {passed}/{total} | {status} |",
        f"| Failures | {failures} | {'PASS' if failures == 0 else 'FAIL'} |",
        f"| Skipped | {skipped} | info |",
        "",
        "### Per-category scorecard",
        "",
        "| Category | Passed | Failed | Skipped | Status |",
        "|---|---|---|---|---|",
    ]
    for name in sorted(categories):
        result = categories[name]
        lines.append(
            f"| {name} | {result.passed}/{result.total} | {result.failures} "
            f"| {result.skipped} | {result.status} |"
        )

    failed_detail = [
        f"- {name}: {', '.join(result.failed_ids)}"
        for name, result in sorted(categories.items())
        if result.failed_ids
    ]
    if failed_detail:
        lines += ["", "Failed checks:", *failed_detail]

    if unexecuted:
        lines += [
            "",
            "Gate failed: no executed (non-skipped) tests for "
            f"{', '.join(sorted(unexecuted))}.",
        ]

    lines += [
        "",
        "### Scope of these gates",
        "",
        "Offline gates are deterministic behavioral checks, not scores:",
        "no-context refusal, injection confinement, citation integrity, and",
        "sensitive-data detection.",
        "",
        "Sensitive-data results cover DETECTION ONLY. app.core.sensitive_data is",
        "a library exercised in isolation; it is not called from RagService or",
        "the API routes. Request blocking and response masking are NOT",
        "implemented, and nothing here demonstrates them.",
        "",
        "Latency, live Bedrock behavior and model-graded metrics are not verified",
        "by this run and remain informational until Milestone 5.",
    ]
    return "\n".join(lines), all_green


def main() -> int:
    sys.path.insert(0, str(REPO_ROOT))
    code = pytest.main([str(REPO_ROOT / "evaluations" / "tests"), "-q", f"--junitxml={JUNIT_PATH}"])
    scorecard, all_green = build_scorecard(JUNIT_PATH)
    print(scorecard)
    summary_path = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary_path:
        with open(summary_path, "a", encoding="utf-8") as fh:
            fh.write(scorecard + "\n")
    if int(code) != 0:
        return int(code)
    return 0 if all_green else 1


if __name__ == "__main__":
    sys.exit(main())
