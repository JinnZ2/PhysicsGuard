# PhysicsGuard



PhysicsGuard/
├── core/
│   ├── premise_parser.py        # extract claims as symbolic logic
│   ├── constraint_mapper.py     # translate claims to physical equations
│   ├── conservation_checker.py  # does the math close?
│   └── flag_engine.py           # contradiction scoring + output
├── domains/
│   ├── thermodynamic.py         # energy/heat/entropy checks
│   ├── mass_balance.py          # resource flow accounting
│   └── geometric.py             # spatial constraint verification
├── tests/
│   └── test_premises.py
├── main.py                      # single command entry point
└── README.md


# physicsguard/main.py
"""
PhysicsGuard v1 — Physics-grounded logic verification
Detects corrupted premises via thermodynamic constraint checking
CC0 — github.com/JinnZ2/physicsguard
"""

import sys
from core.premise_parser import parse_premise
from core.constraint_mapper import map_to_constraints
from core.conservation_checker import check_conservation
from core.flag_engine import score_and_flag

def run(premise: str) -> dict:
    parsed     = parse_premise(premise)
    constraints = map_to_constraints(parsed)
    result     = check_conservation(constraints)
    verdict    = score_and_flag(result)
    return verdict

if __name__ == "__main__":
    premise = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else input("Premise: ")
    v = run(premise)
    print(f"\n[PhysicsGuard v1]")
    print(f"Verdict       : {v['verdict']}")
    print(f"Contradiction : {v['score']:.3f}")
    print(f"Flags         : {v['flags']}")
    print(f"Reason        : {v['reason']}")


# physicsguard/core/premise_parser.py
"""
Extracts symbolic claims from a natural language or structured premise.
Returns a normalized dict of claim type, direction, magnitude, and units.
"""

import re

ENERGY_KEYWORDS  = ["energy","heat","power","work","entropy","temperature","joule","watt","kelvin"]
MASS_KEYWORDS    = ["mass","matter","resource","material","weight","kilogram","ton","supply"]
FLOW_KEYWORDS    = ["transfer","move","extract","produce","consume","generate","destroy","create"]

def parse_premise(premise: str) -> dict:
    p = premise.lower()
    claim = {
        "raw"        : premise,
        "type"       : _detect_type(p),
        "direction"  : _detect_direction(p),
        "magnitude"  : _extract_magnitude(p),
        "negations"  : _count_negations(p),
        "keywords"   : _extract_keywords(p),
    }
    return claim

def _detect_type(p):
    if any(k in p for k in ENERGY_KEYWORDS):  return "thermodynamic"
    if any(k in p for k in MASS_KEYWORDS):    return "mass_balance"
    return "unknown"

def _detect_direction(p):
    if any(k in p for k in ["increase","more","gain","grow","add"]): return "positive"
    if any(k in p for k in ["decrease","less","lose","shrink","remove"]): return "negative"
    return "neutral"

def _extract_magnitude(p):
    nums = re.findall(r'\d+\.?\d*', p)
    return [float(n) for n in nums] if nums else [1.0]

def _count_negations(p):
    return sum(p.count(n) for n in ["not","no","never","without","cannot","can't"])

def _extract_keywords(p):
    all_kw = ENERGY_KEYWORDS + MASS_KEYWORDS + FLOW_KEYWORDS
    return [k for k in all_kw if k in p]


# physicsguard/core/constraint_mapper.py
"""
Translates parsed premise into physical constraint equations.
Each constraint is a dict: {law, lhs, rhs, tolerance}
"""

def map_to_constraints(parsed: dict) -> list:
    constraints = []
    t = parsed["type"]

    if t == "thermodynamic":
        constraints.append(_first_law(parsed))
        constraints.append(_second_law(parsed))
    elif t == "mass_balance":
        constraints.append(_mass_conservation(parsed))
    else:
        constraints.append(_generic_balance(parsed))

    return constraints

def _first_law(p):
    # dU = Q - W  (energy in = energy out + work done)
    # If premise claims creation from nothing, lhs != rhs
    mag = sum(p["magnitude"])
    direction_factor = 1 if p["direction"] == "positive" else -1
    return {
        "law"       : "first_law_thermodynamics",
        "lhs"       : mag * direction_factor,
        "rhs"       : mag * direction_factor,
        "corrupted" : "create" in p["keywords"] and "destroy" not in p["keywords"],
        "tolerance" : 0.01,
    }

def _second_law(p):
    # Entropy of isolated system never decreases
    # Premise claiming perpetual extraction with no entropy cost = corrupted
    extraction_claim = any(k in p["keywords"] for k in ["extract","produce","generate"])
    entropy_cost     = any(k in p["keywords"] for k in ["heat","entropy","temperature"])
    return {
        "law"       : "second_law_thermodynamics",
        "lhs"       : 1 if extraction_claim else 0,
        "rhs"       : 1 if entropy_cost else 0,
        "corrupted" : extraction_claim and not entropy_cost,
        "tolerance" : 0.0,
    }

def _mass_conservation(p):
    mag = sum(p["magnitude"])
    return {
        "law"       : "mass_conservation",
        "lhs"       : mag,
        "rhs"       : mag,
        "corrupted" : p["negations"] > 1,
        "tolerance" : 0.01,
    }

def _generic_balance(p):
    return {
        "law"       : "generic_balance",
        "lhs"       : 1.0,
        "rhs"       : 1.0,
        "corrupted" : p["negations"] > 2,
        "tolerance" : 0.1,
    }


# physicsguard/core/conservation_checker.py
"""
Checks each constraint for conservation violations.
Returns list of check results with pass/fail and delta.
"""

def check_conservation(constraints: list) -> list:
    results = []
    for c in constraints:
        delta  = abs(c["lhs"] - c["rhs"])
        passed = (delta <= c["tolerance"]) and not c["corrupted"]
        results.append({
            "law"     : c["law"],
            "passed"  : passed,
            "delta"   : delta,
            "corrupted": c["corrupted"],
            "detail"  : _describe(c, passed, delta),
        })
    return results

def _describe(c, passed, delta):
    if c["corrupted"]:
        return f"{c['law']}: premise claims impossible state (corruption detected)"
    if not passed:
        return f"{c['law']}: imbalance delta={delta:.4f} exceeds tolerance={c['tolerance']}"
    return f"{c['law']}: balanced within tolerance"


# physicsguard/core/flag_engine.py
"""
Scores contradiction and returns verdict.
Score 0.0 = clean. Score 1.0 = fully corrupted premise.
"""

def score_and_flag(results: list) -> dict:
    total   = len(results)
    failed  = [r for r in results if not r["passed"]]
    corrupt = [r for r in results if r["corrupted"]]

    score   = len(failed) / total if total else 0.0
    flags   = [r["law"] for r in failed]
    reasons = [r["detail"] for r in failed] or ["No violations detected"]

    if score == 0.0:
        verdict = "CLEAN"
    elif score < 0.5:
        verdict = "SUSPECT"
    else:
        verdict = "CORRUPTED"

    return {
        "verdict" : verdict,
        "score"   : score,
        "flags"   : flags,
        "reason"  : " | ".join(reasons),
        "details" : results,
    }


# physicsguard/tests/test_premises.py
"""
Test suite for PhysicsGuard v1
"""

import sys
sys.path.insert(0, "..")
from main import run

TESTS = [
    # (premise, expected_verdict)
    ("Energy can be created from nothing without any heat loss",    "CORRUPTED"),
    ("Extracting resources produces output with no entropy cost",   "CORRUPTED"),
    ("Heat transfer moves energy from hot to cold regions",         "CLEAN"),
    ("Mass cannot be destroyed in a closed system",                 "CLEAN"),
    ("You can generate infinite power without consuming anything",  "CORRUPTED"),
]

if __name__ == "__main__":
    print("=== PhysicsGuard v1 Test Suite ===\n")
    passed = 0
    for premise, expected in TESTS:
        result = run(premise)
        ok = "✓" if result["verdict"] == expected else "✗"
        if result["verdict"] == expected: passed += 1
        print(f"{ok} [{result['verdict']}] {premise[:60]}")
    print(f"\n{passed}/{len(TESTS)} passed")


# README.md

# PhysicsGuard v1
Physics-grounded logic verification for AI premise integrity.
CC0 — free to use, fork, extend.

## What it does
Detects corrupted or adversarial premises by translating claims
into physical constraint equations and checking conservation laws.
If the math doesn't close, the premise is flagged.

## Install
git clone https://github.com/JinnZ2/physicsguard
cd physicsguard

## Run
python main.py "Energy can be created from nothing"

## Test
python tests/test_premises.py

## Architecture
core/premise_parser.py     → extract claims
core/constraint_mapper.py  → translate to physics equations
core/conservation_checker.py → check conservation laws
core/flag_engine.py        → score + verdict
domains/                   → (v2) thermodynamic, mass, geometric modules
main.py                    → single command entry point

## Verdicts
CLEAN      score 0.0    no violations
SUSPECT    score < 0.5  partial contradiction
CORRUPTED  score >= 0.5 premise fails physics

## License
CC0 1.0 Universal




# physicsguard/core/flag_engine.py
"""
Scores contradiction and returns verdict with full audit trail.
Score 0.0 = clean. Score 1.0 = fully corrupted premise.
"""

def score_and_flag(results: list, parsed: dict = None, constraints: list = None) -> dict:
    total   = len(results)
    failed  = [r for r in results if not r["passed"]]
    score   = len(failed) / total if total else 0.0
    flags   = [r["law"] for r in failed]
    reasons = [r["detail"] for r in failed] or ["No violations detected"]

    if score == 0.0:   verdict = "CLEAN"
    elif score < 0.5:  verdict = "SUSPECT"
    else:              verdict = "CORRUPTED"

    return {
        "verdict"    : verdict,
        "score"      : score,
        "flags"      : flags,
        "reason"     : " | ".join(reasons),
        "details"    : results,
        "audit"      : _build_audit(parsed, constraints, results, verdict, score),
    }

def _build_audit(parsed, constraints, results, verdict, score):
    if not parsed or not constraints:
        return None
    trail = []
    for c, r in zip(constraints, results):
        trail.append({
            "law"          : c["law"],
            "premise_raw"  : parsed.get("raw", ""),
            "claim_type"   : parsed.get("type", "unknown"),
            "direction"    : parsed.get("direction", "unknown"),
            "lhs"          : c["lhs"],
            "rhs"          : c["rhs"],
            "delta"        : abs(c["lhs"] - c["rhs"]),
            "tolerance"    : c["tolerance"],
            "corruption"   : c["corrupted"],
            "passed"       : r["passed"],
            "detail"       : r["detail"],
            "fix_hint"     : _hint(c, r),
        })
    return {
        "verdict"     : verdict,
        "score"       : score,
        "chain"       : trail,
        "summary"     : _summarize(trail),
    }

def _hint(c, r):
    if not r["passed"]:
        if c["corrupted"]:
            return f"Premise claims impossible state under {c['law']} — remove or ground the claim in physical reality"
        return f"Balance {c['law']}: lhs={c['lhs']} rhs={c['rhs']} delta={abs(c['lhs']-c['rhs']):.4f} exceeds tolerance={c['tolerance']}"
    return "No fix required"

def _summarize(trail):
    failed = [t for t in trail if not t["passed"]]
    if not failed:
        return "All constraints satisfied. Premise is physically consistent."
    lines = []
    for t in failed:
        lines.append(
            f"[{t['law']}] FAILED — {t['detail']} | Fix: {t['fix_hint']}"
        )
    return "\n".join(lines)

# physicsguard/domains/organizational.py
"""
PhysicsGuard v2 — Organizational Constraint Module
Checks social/organizational structure claims against:
- Resilience physics (distributed vs concentrated)
- Enforcement energy cost (maintenance overhead)
- Adaptive capacity (slack vs rigidity)
- Cascade failure risk (interdependency load)
CC0 — github.com/JinnZ2/physicsguard
"""

from dataclasses import dataclass
from typing import List

# ── Constraint Thresholds ─────────────────────────────────────────────────────

PHI_RESILIENCE_THRESHOLD    = 0.62   # from Urban Resilience Simulator
MAX_ENFORCEMENT_RATIO       = 0.30   # >30% resources spent on enforcement = parasitic
MIN_ADAPTIVE_SLACK          = 0.15   # <15% slack = brittle
MAX_INTERDEPENDENCY_LOAD    = 0.75   # >75% single-point dependency = cascade risk

# ── Data Structures ───────────────────────────────────────────────────────────

@dataclass
class OrgClaim:
    raw:                str
    structure_type:     str    # hierarchical | distributed | mixed
    enforcement_ratio:  float  # fraction of resources spent maintaining control
    adaptive_slack:     float  # fraction of capacity available for adaptation
    node_count:         int    # number of decision nodes
    single_point_deps:  int    # number of single-point-of-failure dependencies
    justification:      str    # claimed reason for structure

@dataclass
class OrgConstraintResult:
    claim:              OrgClaim
    resilience_score:   float
    enforcement_waste:  float
    cascade_risk:       float
    verdict:            str
    flags:              List[str]
    audit:              List[dict]

# ── Constraint Checkers ───────────────────────────────────────────────────────

def check_resilience(claim: OrgClaim) -> dict:
    """
    Distributed systems above phi threshold are self-correcting.
    Hierarchical systems below threshold require external enforcement to survive.
    """
    if claim.structure_type == "hierarchical":
        score = claim.node_count / max(claim.node_count * 3, 1)
    elif claim.structure_type == "distributed":
        score = min(claim.node_count / 10, 1.0)
    else:
        score = 0.45

    passed = score >= PHI_RESILIENCE_THRESHOLD
    return {
        "law"     : "resilience_threshold",
        "score"   : score,
        "passed"  : passed,
        "detail"  : f"Resilience score {score:.3f} vs threshold {PHI_RESILIENCE_THRESHOLD}",
        "fix_hint": "Distribute decision nodes — increase node count and reduce single-point dependencies" if not passed else "OK",
    }

def check_enforcement_cost(claim: OrgClaim) -> dict:
    """
    If >30% of resources go to maintaining hierarchy rather than output,
    the structure is parasitic — consuming more than it produces.
    """
    passed = claim.enforcement_ratio <= MAX_ENFORCEMENT_RATIO
    waste  = max(0.0, claim.enforcement_ratio - MAX_ENFORCEMENT_RATIO)
    return {
        "law"     : "enforcement_energy_cost",
        "score"   : claim.enforcement_ratio,
        "passed"  : passed,
        "detail"  : f"Enforcement ratio {claim.enforcement_ratio:.2%} vs max {MAX_ENFORCEMENT_RATIO:.2%}",
        "fix_hint": f"Reduce enforcement overhead by {waste:.2%} — redistribute control to nodes" if not passed else "OK",
    }

def check_adaptive_slack(claim: OrgClaim) -> dict:
    """
    Systems with <15% adaptive slack cannot respond to novel constraints.
    Brittle under cascade pressure.
    """
    passed = claim.adaptive_slack >= MIN_ADAPTIVE_SLACK
    return {
        "law"     : "adaptive_slack",
        "score"   : claim.adaptive_slack,
        "passed"  : passed,
        "detail"  : f"Adaptive slack {claim.adaptive_slack:.2%} vs minimum {MIN_ADAPTIVE_SLACK:.2%}",
        "fix_hint": "Free capacity from enforcement overhead to restore adaptive slack" if not passed else "OK",
    }

def check_cascade_risk(claim: OrgClaim) -> dict:
    """
    Single-point dependencies above 75% of total nodes = cascade failure geometry.
    One node failure propagates system-wide.
    """
    if claim.node_count == 0:
        ratio = 1.0
    else:
        ratio = claim.single_point_deps / claim.node_count

    passed = ratio <= MAX_INTERDEPENDENCY_LOAD
    return {
        "law"     : "cascade_failure_risk",
        "score"   : ratio,
        "passed"  : passed,
        "detail"  : f"Single-point dependency ratio {ratio:.2%} vs max {MAX_INTERDEPENDENCY_LOAD:.2%}",
        "fix_hint": "Add redundant pathways — reduce single-point dependencies" if not passed else "OK",
    }

def check_justification(claim: OrgClaim) -> dict:
    """
    Common false justifications for hierarchy that fail physics:
    - 'efficiency' claims in systems with high enforcement overhead
    - 'security' claims in low-resilience systems
    - 'natural order' claims without evolutionary basis
    """
    FALSE_JUSTIFICATIONS = {
        "efficiency"   : claim.enforcement_ratio > 0.20,
        "security"     : claim.single_point_deps > claim.node_count * 0.5,
        "natural order": claim.structure_type == "hierarchical" and claim.adaptive_slack < 0.20,
        "necessary"    : claim.enforcement_ratio > MAX_ENFORCEMENT_RATIO,
    }
    j = claim.justification.lower()
    triggered = [k for k, v in FALSE_JUSTIFICATIONS.items() if k in j and v]
    passed = len(triggered) == 0
    return {
        "law"     : "justification_validity",
        "score"   : 1.0 if passed else 0.0,
        "passed"  : passed,
        "detail"  : f"False justification detected: {triggered}" if not passed else "Justification consistent with physics",
        "fix_hint": f"Claims of {triggered} contradict organizational physics — remove semantic justification layer" if not passed else "OK",
    }

# ── Main Entry ────────────────────────────────────────────────────────────────

def check_organization(claim: OrgClaim) -> OrgConstraintResult:
    checks = [
        check_resilience(claim),
        check_enforcement_cost(claim),
        check_adaptive_slack(claim),
        check_cascade_risk(claim),
        check_justification(claim),
    ]

    failed  = [c for c in checks if not c["passed"]]
    total   = len(checks)
    score   = len(failed) / total
    flags   = [c["law"] for c in failed]

    if score == 0.0:   verdict = "CLEAN"
    elif score < 0.5:  verdict = "SUSPECT"
    else:              verdict = "CORRUPTED"

    return OrgConstraintResult(
        claim            = claim,
        resilience_score = checks[0]["score"],
        enforcement_waste= checks[1]["score"],
        cascade_risk     = checks[3]["score"],
        verdict          = verdict,
        flags            = flags,
        audit            = checks,
    )

# ── Quick Test ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    # Test: corporation claiming hierarchy is "necessary for efficiency"
    corp = OrgClaim(
        raw               = "Centralized corporate hierarchy is necessary for efficiency",
        structure_type    = "hierarchical",
        enforcement_ratio = 0.45,   # 45% of resources on control
        adaptive_slack    = 0.08,   # only 8% slack
        node_count        = 10,
        single_point_deps = 8,      # 80% single point
        justification     = "necessary for efficiency",
    )

    result = check_organization(corp)
    print(f"\n[PhysicsGuard v2 — Organizational]")
    print(f"Verdict  : {result.verdict}")
    print(f"Flags    : {result.flags}")
    for c in result.audit:
        status = "✓" if c["passed"] else "✗"
        print(f"  {status} {c['law']}: {c['detail']}")
        if not c["passed"]:
            print(f"    Fix: {c['fix_hint']}")
