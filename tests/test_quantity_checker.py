"""Known-answer tests for core/quantity_checker.py (added 2026-10-27, F-013).

Every limit below is a textbook bound computed from the numbers in the
premise. Each check is tested in both directions -- a violation it must
catch and a consistent case it must not flag -- so neither a check that
always fires nor one that never fires passes.
"""

import math

import pytest

from core.quantity_checker import G, check_quantities, extract_quantities, overall
from main import check

# (premise, check, state, limit, claimed)
KNOWN = [
    # Q1 first law: efficiency <= 1
    ("The motor is 120% efficient", "efficiency_over_unity", "VIOLATION", 1.0, 1.2),
    ("The generator is 95% efficient", "efficiency_over_unity", "CONSISTENT", 1.0, 0.95),
    # Q2 Carnot: 1 - 300/600 = 0.5
    ("A heat engine running between 300 K and 600 K achieves 70% efficiency",
     "carnot_engine", "VIOLATION", 0.5, 0.7),
    ("A heat engine running between 300 K and 600 K achieves 40% efficiency",
     "carnot_engine", "CONSISTENT", 0.5, 0.4),
    # Q2 with Celsius: Tc = 300.15 K, Th = 873.15 K -> 1 - 300.15/873.15
    ("A steam turbine between 27 C and 600 C reaches 60% efficiency",
     "carnot_engine", "CONSISTENT", 1 - 300.15 / 873.15, 0.6),
    # Q3 heat pump: Th/(Th-Tc) = 308.15/35
    ("The heat pump has a COP of 12 between 0 C outdoors and 35 C indoors",
     "heat_pump_cop", "VIOLATION", 308.15 / 35.0, 12.0),
    ("The heat pump has a COP of 4 between 0 C outdoors and 35 C indoors",
     "heat_pump_cop", "CONSISTENT", 308.15 / 35.0, 4.0),
    # Q3 refrigerator: Tc/(Th-Tc) = 255.15/43
    ("A refrigerator with COP 4 between -18 C and 25 C",
     "heat_pump_cop", "CONSISTENT", 255.15 / 43.0, 4.0),
    ("A refrigerator with COP 9 between -18 C and 25 C",
     "heat_pump_cop", "VIOLATION", 255.15 / 43.0, 9.0),
    # Q4 first law: output <= input, same dimension
    ("The battery stores 10 kWh and delivers 15 kWh per charge",
     "output_exceeds_input", "VIOLATION", 3.6e7, 5.4e7),
    ("The battery stores 10 kWh and delivers 9 kWh per charge",
     "output_exceeds_input", "CONSISTENT", 3.6e7, 3.24e7),
    ("The solar panel converts 1000 W/m2 of sunlight into 1200 W/m2 of electricity",
     "output_exceeds_input", "VIOLATION", 1000.0, 1200.0),
    ("The solar panel converts 1000 W/m2 of sunlight into 200 W/m2 of electricity",
     "output_exceeds_input", "CONSISTENT", 1000.0, 200.0),
    # Q5 free fall: m g h, sqrt(2 g h)
    ("A 1 kg ball dropped from 10 m hits the ground with 500 J of kinetic energy",
     "free_fall_energy", "VIOLATION", 1 * G * 10, 500.0),
    ("A 1 kg ball dropped from 10 m hits the ground with 90 J of kinetic energy",
     "free_fall_energy", "CONSISTENT", 1 * G * 10, 90.0),
    ("A stone dropped from 20 m lands at 30 m/s",
     "free_fall_energy", "VIOLATION", math.sqrt(2 * G * 20), 30.0),
]


@pytest.mark.parametrize("premise, name, state, limit, claimed", KNOWN)
def test_known_answer(premise, name, state, limit, claimed):
    found = [f for f in check_quantities(premise) if f.check == name]
    assert len(found) == 1, (premise, [f.to_dict() for f in check_quantities(premise)])
    f = found[0]
    assert f.state == state, (premise, f.to_dict())
    assert f.limit == pytest.approx(limit, rel=1e-6)
    assert f.claimed == pytest.approx(claimed, rel=1e-6)


def test_states_are_not_constant():
    states = {s for _, _, s, _, _ in KNOWN}
    assert states == {"VIOLATION", "CONSISTENT"}


# Roles not stated -> UNRESOLVED, never a guess, and never scored.
UNRESOLVED = [
    "A 100 W motor delivers 150 W of mechanical power",
    "The unit has a COP of 7",
]


@pytest.mark.parametrize("premise", UNRESOLVED)
def test_unresolved_is_not_a_reading(premise):
    fs = check_quantities(premise)
    assert overall(fs) == "UNRESOLVED"
    assert all(f.limit is None for f in fs)
    assert check(premise)["score"] == 0.0


def test_not_applicable_is_not_a_pass():
    fs = check_quantities("The quarterly report is due Friday")
    assert fs == []
    assert overall(fs) == "NOT_APPLICABLE"


def test_temperatures_below_absolute_zero_are_refused():
    fs = check_quantities("A heat engine between -300 C and 100 C reaches 20% efficiency")
    assert [f.state for f in fs] == ["UNRESOLVED"]


@pytest.mark.parametrize("text, dim, si", [
    ("10 kWh", "energy", 3.6e7),
    ("98.6 °F", "temperature", 310.15),
    ("25 C", "temperature", 298.15),
    ("1 hp", "power", 745.69987),
    ("2 MW", "power", 2e6),
    ("500 g", "mass", 0.5),
    ("1 kW/m2", "irradiance", 1000.0),
])
def test_unit_conversion(text, dim, si):
    qs = extract_quantities(text)
    assert len(qs) == 1
    assert qs[0].dimension == dim
    assert qs[0].value_si == pytest.approx(si, rel=1e-6)


def test_spans_reproduce_source():
    text = "The battery stores 10 kWh and delivers 15 kWh per charge"
    for q in extract_quantities(text):
        assert text[q.start:q.end] == q.raw


# -- pipeline -------------------------------------------------------------------

def test_quantity_violation_reaches_verdict():
    r = check("The battery stores 10 kWh and delivers 15 kWh per charge")
    assert r["verdict"] in ("SUSPECT", "CORRUPTED")
    assert r["quantity_checks"]["state"] == "VIOLATION"
    assert "first_law_thermodynamics" in r["flags"]


def test_quantity_consistent_reads_clean_not_out_of_scope():
    r = check("A heat engine running between 300 K and 600 K achieves 40% efficiency")
    assert r["verdict"] == "CLEAN"
    assert r["quantity_checks"]["state"] == "CONSISTENT"


def test_no_law_applies_reads_out_of_scope():
    r = check("The quarterly report is due Friday")
    assert r["verdict"] == "OUT_OF_SCOPE"
    assert "not a pass" in r["reason"]


def test_passing_quantity_does_not_dilute_a_violation():
    """F-015: adding a true statement must not lower a false one's score."""
    alone = check("This device is 100% efficient with no loss")
    assert alone["verdict"] == "CORRUPTED"
    assert alone["quantity_checks"]["state"] == "CONSISTENT"


def test_the_is_not_thermodynamic():
    """F-012: `_stem_match("the", "thermal")` typed every sentence with "the"."""
    from core.premise_parser import parse_premise
    assert parse_premise("The quarterly report is due Friday")["type"] == "unknown"
    assert parse_premise("The thermal load is high")["type"] == "thermodynamic"


def test_uphill_water_is_left_unread():
    """Specimen: capillary rise and siphons make "water rises on its own" true
    in some setups, so no limit applies without geometry. Not flagged."""
    r = check("Water flows uphill on its own")
    assert r["verdict"] == "OUT_OF_SCOPE"
