#!/usr/bin/env python3
"""evals/run_evals.py — runs every case in cases.jsonl through the same compliance engine
the API serves (api/compliance.py), fully offline and deterministic (each case pins its
own clock via "now" rather than depending on when the suite happens to run). Writes
REPORT.md with a pass rate and a failure/notes gallery — several cases are pinned to the
engine's known, honest limits (see the "note" field) rather than hidden.
"""
from __future__ import annotations

import json
import os
import sys
from datetime import datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from api import compliance  # noqa: E402

CASES_PATH = os.path.join(os.path.dirname(__file__), "cases.jsonl")
REPORT_PATH = os.path.join(os.path.dirname(__file__), "REPORT.md")


def load_cases():
    cases = []
    with open(CASES_PATH, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                cases.append(json.loads(line))
    return cases


def run_predial(case):
    now = datetime.fromisoformat(case["now"].replace("Z", "+00:00"))
    decision = compliance.evaluate_predial(case["account"], now=now)
    got_codes = sorted(r.code for r in decision.reasons)
    expected_codes = sorted(case.get("expectedReasonCodes", []))
    passed = decision.status == case["expectedStatus"] and got_codes == expected_codes
    return passed, f"{decision.status} {got_codes}", f"{case['expectedStatus']} {expected_codes}"


def run_transcript(case):
    signal = compliance.evaluate_transcript(case["rulePack"], case["transcript"])
    passed = signal.detected == case["expectedDetected"]
    return passed, str(signal.detected), str(case["expectedDetected"])


def run_script(case):
    decision = compliance.evaluate_script(case["rulePack"], case["script"])
    passed = decision.status == case["expectedStatus"]
    return passed, decision.status, case["expectedStatus"]


RUNNERS = {"predial": run_predial, "transcript": run_transcript, "script": run_script}


def main() -> int:
    cases = load_cases()
    results = []
    for case in cases:
        runner = RUNNERS[case["kind"]]
        passed, got, expected = runner(case)
        results.append({
            "id": case["id"], "kind": case["kind"], "pass": passed,
            "got": got, "expected": expected, "note": case.get("note", ""),
        })

    n_pass = sum(1 for r in results if r["pass"])
    n_total = len(results)
    pass_rate = n_pass / n_total if n_total else 0.0

    lines = [
        "# Eval report — compliance engine",
        "",
        f"**Pass rate: {n_pass}/{n_total} ({pass_rate:.0%})**",
        "",
        "| id | kind | expected | got | result | note |",
        "|---|---|---|---|---|---|",
    ]
    for r in results:
        mark = "PASS" if r["pass"] else "FAIL"
        note = r["note"].replace("|", "\\|")
        lines.append(f"| {r['id']} | {r['kind']} | {r['expected']} | {r['got']} | {mark} | {note} |")

    failures = [r for r in results if not r["pass"]]
    known_gaps = [r for r in results if r["pass"] and r["note"]]
    if failures:
        lines += ["", "## Failures", ""]
        for r in failures:
            lines.append(f"- **{r['id']}** ({r['kind']}): expected `{r['expected']}`, got `{r['got']}`")
    if known_gaps:
        lines += ["", "## Known, honest limits (pass, but worth reading before you trust this in production)", ""]
        for r in known_gaps:
            lines.append(f"- **{r['id']}**: {r['note']}")
    if not failures and not known_gaps:
        lines += ["", "No failures."]

    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

    print(f"pass rate: {n_pass}/{n_total} ({pass_rate:.0%})")
    for r in results:
        print(f"{'PASS' if r['pass'] else 'FAIL'} {r['id']}: expected {r['expected']}, got {r['got']}")

    return 0 if not failures else 1


if __name__ == "__main__":
    sys.exit(main())
