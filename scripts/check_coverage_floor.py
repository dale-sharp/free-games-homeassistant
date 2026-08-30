"""Fail CI if any module falls below the per-module coverage floor in CONTRIBUTING.md.

pytest-cov/coverage.py only supports a single overall `fail_under` threshold - it has no
built-in way to gate an individual file's coverage percentage. CONTRIBUTING.md documents two
separate thresholds ("95% overall, no module below ~90%"); the overall one is enforced by
`--cov-fail-under=95` in the pytest invocation, and this script enforces the per-module one
against the `coverage.json` report produced by the same run.
"""

from __future__ import annotations

import json
import sys

PER_MODULE_FLOOR = 90.0
COVERAGE_JSON_PATH = "coverage.json"


def main() -> int:
    with open(COVERAGE_JSON_PATH, encoding="utf-8") as f:
        report = json.load(f)

    failures = [
        (path, file_report["summary"]["percent_covered"])
        for path, file_report in report["files"].items()
        if file_report["summary"]["percent_covered"] < PER_MODULE_FLOOR
    ]

    if failures:
        print(f"Modules below the {PER_MODULE_FLOOR}% per-module coverage floor:")
        for path, percent in failures:
            print(f"  {path}: {percent:.1f}%")
        return 1

    print(f"All modules meet the {PER_MODULE_FLOOR}% per-module coverage floor.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
