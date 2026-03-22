"""Test suite for PhysicsGuard v1 core pipeline."""

import pytest

from main import run


@pytest.mark.parametrize("premise,expected", [
    ("Energy can be created from nothing without any heat loss", "CORRUPTED"),
    ("Extracting resources produces output with no entropy cost", "CORRUPTED"),
    ("Heat transfer moves energy from hot to cold regions", "CLEAN"),
    ("Mass cannot be destroyed in a closed system", "CLEAN"),
    ("You can generate infinite power without consuming anything", "CORRUPTED"),
])
def test_premise_verdict(premise, expected):
    result = run(premise)
    assert result["verdict"] == expected, (
        f"Expected {expected} for: {premise!r}, got {result['verdict']}"
    )


def test_result_structure():
    result = run("Energy can be created from nothing")
    assert "verdict" in result
    assert "score" in result
    assert "flags" in result
    assert "reason" in result
    assert "details" in result
    assert "audit" in result


def test_score_range():
    result = run("Some arbitrary claim about physics")
    assert 0.0 <= result["score"] <= 1.0


def test_clean_has_no_flags():
    result = run("Heat transfer moves energy from hot to cold regions")
    assert result["verdict"] == "CLEAN"
    assert result["flags"] == []


def test_corrupted_has_flags():
    result = run("Energy can be created from nothing without any heat loss")
    assert result["verdict"] == "CORRUPTED"
    assert len(result["flags"]) > 0


def test_audit_trail_present():
    result = run("Energy can be created from nothing")
    audit = result["audit"]
    assert audit is not None
    assert "chain" in audit
    assert "summary" in audit
    assert len(audit["chain"]) > 0
