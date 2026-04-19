"""Tests for the thermodynamic accountability domain."""

import pytest

from domains.thermodynamic_accountability import (
    TAFClaim,
    check_collapse_distance,
    check_energy_balance,
    check_friction_ratio,
    check_parasitic_debt,
    check_thermodynamic_accountability,
)


@pytest.fixture
def extractive_workplace():
    # Classic parasitic structure: compensation under-covers the real load,
    # friction is high, unpaid hours are accumulating.
    return TAFClaim(
        raw="Workers are lazy — we need more enforcement to keep productivity up",
        energy_in=100.0,
        productive_work=60.0,
        friction_losses=60.0,
        hidden_overhead=20.0,
        unpaid_hours=10.0,
        friction_events=4,
        justification="workers are lazy, enforcement is necessary for efficiency",
    )


@pytest.fixture
def sustainable_workplace():
    return TAFClaim(
        raw="Well-compensated cooperative with clear protocols",
        energy_in=100.0,
        productive_work=70.0,
        friction_losses=10.0,
        hidden_overhead=5.0,
        unpaid_hours=0.0,
        friction_events=0,
        justification="cooperative governance",
    )


def test_extractive_workplace_is_corrupted(extractive_workplace):
    result = check_thermodynamic_accountability(extractive_workplace)
    assert result.verdict == "CORRUPTED"
    assert "energy_balance" in result.flags
    assert "friction_ratio" in result.flags


def test_sustainable_workplace_is_clean(sustainable_workplace):
    result = check_thermodynamic_accountability(sustainable_workplace)
    assert result.verdict == "CLEAN"
    assert result.flags == []


def test_energy_balance_flags_negative_yield(extractive_workplace):
    check = check_energy_balance(extractive_workplace)
    assert check["passed"] is False
    assert check["score"] < 0


def test_friction_ratio_flags_parasitic_regime(extractive_workplace):
    check = check_friction_ratio(extractive_workplace)
    assert check["passed"] is False
    assert check["score"] > 0.30


def test_collapse_distance_classifies_regime(extractive_workplace):
    check = check_collapse_distance(extractive_workplace)
    # load = 60 + 60 + 20 = 140 vs E_in = 100 → load_factor 1.4 → degraded/safety
    assert check["passed"] is False
    assert 0.0 <= check["score"] <= 1.0


def test_collapse_distance_is_one_when_load_is_zero():
    claim = TAFClaim(raw="idle", energy_in=100.0)
    check = check_collapse_distance(claim)
    assert check["score"] == pytest.approx(1.0)


def test_parasitic_debt_scales_with_friction_events():
    low  = TAFClaim(raw="", energy_in=0, unpaid_hours=10, friction_events=0)
    high = TAFClaim(raw="", energy_in=0, unpaid_hours=10, friction_events=4)
    assert check_parasitic_debt(high)["score"] > check_parasitic_debt(low)["score"]


def test_narrative_cover_flagged_when_math_disagrees(extractive_workplace):
    result = check_thermodynamic_accountability(extractive_workplace)
    assert "justification_validity" in result.flags


def test_audit_trail_length(extractive_workplace):
    result = check_thermodynamic_accountability(extractive_workplace)
    assert len(result.audit) == 5
