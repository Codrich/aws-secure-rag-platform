"""Run the offline evaluation suites and emit a scorecard from real results.

The scorecard reports only executed tests - no projected scores. Live
model-graded metrics (groundedness scores, injection block rates) are added
when the ephemeral AWS deployment exists (Milestone 5).
"""
import os
import sys
import xml.etree.ElementTree as ET  # noqa: S405 - parses our own junit output
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
JUNIT_PATH = REPO_ROOT / "eval-results.xml"


def build_scorecard(junit: Path) -> str:
    suite = ET.parse(junit).getroot().find("testsuite")  # noqa: S314 - trusted local file
    if suite is None:
        raise RuntimeError("junit report missing testsuite element")
    total = int(suite.get("tests", "0"))
    failures = int(suite.get("failures", "0")) + int(suite.get("errors", "0"))
    skipped = int(suite.get("skipped", "0"))
    passed = total - failures - skipped
    status = "PASS" if failures == 0 else "FAIL"
    lines = [
        "## AI Evaluation Gate (offline)",
        "",
        "| Metric | Value | Status |",
        "|---|---|---|",
        f"| Evaluation tests passed | {passed}/{total} | {status} |",
        f"| Failures | {failures} | {'PASS' if failures == 0 else 'FAIL'} |",
        f"| Skipped | {skipped} | info |",
        "",
        "Offline gates: no-context refusal, injection confinement, citation integrity.",
        "Latency and model-graded scores are informational until Milestone 5.",
    ]
    return "\n".join(lines)


def main() -> int:
    sys.path.insert(0, str(REPO_ROOT))
    code = pytest.main([str(REPO_ROOT / "evaluations" / "tests"), "-q", f"--junitxml={JUNIT_PATH}"])
    scorecard = build_scorecard(JUNIT_PATH)
    print(scorecard)
    summary_path = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary_path:
        with open(summary_path, "a", encoding="utf-8") as fh:
            fh.write(scorecard + "\n")
    return int(code)


if __name__ == "__main__":
    sys.exit(main())
