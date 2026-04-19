"""Regression harness for benchmarks/cases.jsonl.

Every line in the JSONL file is run through the unified audit() entry
point and asserted against its expected verdict. When the underlying
semantics intentionally change, update the case — don't silence it.
"""

import json
from pathlib import Path

import pytest

from ai_interface import audit

CASES_PATH = Path(__file__).resolve().parent.parent / "benchmarks" / "cases.jsonl"


def _load_cases():
    cases = []
    with open(CASES_PATH) as f:
        for lineno, raw in enumerate(f, start=1):
            raw = raw.strip()
            if not raw:
                continue
            try:
                cases.append(json.loads(raw))
            except json.JSONDecodeError as e:
                raise AssertionError(f"invalid JSON at line {lineno}: {e}") from e
    return cases


CASES = _load_cases()
DOMAIN_TO_MODE = {
    "premise":        "premise",
    "corpus":         "corpus",
    "organizational": "organizational",
    "information":    "information",
    "thermodynamic":  "thermodynamic",
}


def test_benchmark_file_is_nonempty():
    assert CASES, f"no cases found in {CASES_PATH}"


def test_every_case_has_required_fields():
    required = {"id", "domain", "input", "expected_verdict"}
    for case in CASES:
        missing = required - case.keys()
        assert not missing, f"{case.get('id', '?')}: missing fields {missing}"


def test_case_ids_are_unique():
    ids = [c["id"] for c in CASES]
    dups = {i for i in ids if ids.count(i) > 1}
    assert not dups, f"duplicate case ids: {dups}"


@pytest.mark.parametrize("case", CASES, ids=lambda c: c["id"])
def test_case_verdict(case):
    mode = DOMAIN_TO_MODE.get(case["domain"], "auto")
    result = audit(case["input"], mode=mode)
    assert result["verdict"] == case["expected_verdict"], (
        f"{case['id']}: expected {case['expected_verdict']} but got "
        f"{result['verdict']} (native={result['native_verdict']}, "
        f"flags={result['flags']}, summary={result['summary']})"
    )


@pytest.mark.parametrize(
    "case",
    [c for c in CASES if c.get("expected_pattern")],
    ids=lambda c: c["id"],
)
def test_premise_case_pattern(case):
    from core.premise_parser import parse_premise
    parsed = parse_premise(case["input"])
    assert parsed["claim_pattern"] == case["expected_pattern"], (
        f"{case['id']}: expected pattern {case['expected_pattern']!r} "
        f"but got {parsed['claim_pattern']!r}"
    )
