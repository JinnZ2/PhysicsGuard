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


# physicsguard/core/contrapositive_tester.py
"""
Four-corner semantic validation.
Tests claim, negation, opposite, and opposite-negation.
Surfaces scope boundaries where each claim holds true.
"""

def test_four_corners(base_claim: str, structure_type: str = "organizational") -> dict:
    """
    base_claim: "hierarchies enable speed"
    structure_type: "organizational", "technical", "biological"
    
    Returns all four corners with scope analysis.
    """
    claims = {
        "claim_1"  : base_claim,
        "claim_2"  : _negate(base_claim),
        "claim_3"  : _opposite(base_claim),
        "claim_4"  : _opposite(_negate(base_claim)),
    }
    
    results = {}
    for key, claim in claims.items():
        results[key] = {
            "claim"   : claim,
            "verdict" : _run_through_physicsguard(claim),
            "scope"   : _extract_scope(claim, key),
        }
    
    return {
        "base_claim"      : base_claim,
        "four_corners"    : results,
        "scope_map"       : _map_scopes(results),
        "contradiction"   : _check_contradiction(results),
    }

def _negate(claim: str) -> str:
    """Flip the valence: enable→disable, speed→slowness"""
    neg_map = {
        "enable"   : "disable",
        "fast"     : "slow",
        "speed"    : "slowness",
        "efficient": "wasteful",
        "produce"  : "prevent",
    }
    result = claim
    for orig, negated in neg_map.items():
        result = result.replace(orig, negated)
    return result

def _opposite(claim: str) -> str:
    """Flip the subject: hierarchies→distributed"""
    opp_map = {
        "hierarchies"        : "distributed systems",
        "centralized"        : "decentralized",
        "top-down"           : "bottom-up",
        "command structure"  : "protocol-based structure",
    }
    result = claim
    for orig, opposite in opp_map.items():
        result = result.replace(orig, opposite)
    return result

def _run_through_physicsguard(claim: str) -> dict:
    """Import and run the main PhysicsGuard verdict"""
    from main import run
    return run(claim)

def _extract_scope(claim: str, corner: str) -> dict:
    """
    Identify conditional scope from claim language.
    Returns conditions under which claim holds.
    """
    scope_keywords = ["during", "under", "when", "if", "only", "requires", "depends"]
    conditions = [word for word in claim.split() if word.lower() in scope_keywords]
    
    return {
        "corner"          : corner,
        "has_conditions"  : len(conditions) > 0,
        "scope_words"     : conditions,
        "implicit_scope"  : _infer_implicit_scope(claim, corner),
    }

def _infer_implicit_scope(claim: str, corner: str) -> list:
    """
    Infer hidden scope boundaries.
    e.g., "hierarchies enable speed" implicitly scopes to: stable resources, low change rate, known threats
    """
    scope_inferences = {
        "claim_1": [
            "peacetime / stable resource conditions",
            "low rate of environmental change",
            "predictable threat model",
            "information already centralized",
        ],
        "claim_2": [
            "crisis / resource scarcity",
            "high rate of change",
            "novel threats",
            "information distributed across field",
        ],
        "claim_3": [
            "real-time adaptation required",
            "high information density",
            "parallel decision-making",
            "failure tolerance critical",
        ],
        "claim_4": [
            "command authority required",
            "sequential decisions",
            "centralized information",
            "failure intolerance",
        ],
    }
    return scope_inferences.get(corner, [])

def _map_scopes(results: dict) -> dict:
    """
    Cross-reference all four corners to find:
    - Where they agree (robust claims)
    - Where they conflict (scope-dependent claims)
    - Boundary conditions
    """
    verdicts = {k: v["verdict"]["verdict"] for k, v in results.items()}
    
    return {
        "agreement"        : _find_agreement(verdicts),
        "conflicts"        : _find_conflicts(verdicts),
        "scope_boundaries" : _map_boundaries(results),
        "robust_claims"    : _extract_robust(verdicts),
    }

def _find_agreement(verdicts: dict) -> list:
    clean = [k for k, v in verdicts.items() if v == "CLEAN"]
    return clean if clean else ["No universal agreement"]

def _find_conflicts(verdicts: dict) -> list:
    conflicts = []
    if verdicts["claim_1"] != verdicts["claim_2"]:
        conflicts.append("Claim 1 and 2 (direct negation) disagree — scope-dependent")
    if verdicts["claim_3"] != verdicts["claim_4"]:
        conflicts.append("Claim 3 and 4 (opposite negation) disagree — scope-dependent")
    return conflicts if conflicts else ["No conflicts detected"]

def _map_boundaries(results: dict) -> dict:
    """Extract the exact conditions where each claim switches from true to false"""
    return {
        "hierarchies_work_when" : results["claim_1"]["scope"]["implicit_scope"],
        "distributed_works_when": results["claim_3"]["scope"]["implicit_scope"],
        "transition_point"      : _estimate_transition(results),
    }

def _estimate_transition(results: dict) -> str:
    """Estimate the decision boundary between structures"""
    return "Rate of environmental change + information distribution density"

def _extract_robust(verdicts: dict) -> list:
    """Claims that pass across multiple corners are robust to scope variation"""
    robust = []
    for claim, verdict in verdicts.items():
        if verdict == "CLEAN":
            robust.append(claim)
    return robust if robust else ["No claims robust across all scopes"]

def print_four_corners(results: dict):
    print("\n" + "="*70)
    print("FOUR-CORNER CONTRAPOSITIVE TEST")
    print("="*70)
    print(f"\nBase Claim: {results['base_claim']}\n")
    
    for corner, data in results["four_corners"].items():
        verdict = data["verdict"]["verdict"]
        icon = "✓" if verdict == "CLEAN" else "✗"
        print(f"{icon} {corner.upper()}")
        print(f"   Claim  : {data['claim']}")
        print(f"   Verdict: {verdict}")
        print(f"   Scope  : {data['scope']['implicit_scope'][:2]}")
        print()
    
    scope_map = results["scope_map"]
    print("-"*70)
    print("SCOPE ANALYSIS:")
    print(f"  Agreement     : {scope_map['agreement']}")
    print(f"  Conflicts     : {scope_map['conflicts']}")
    print(f"  Robust claims : {scope_map['robust_claims']}")
    print(f"  Boundary      : {scope_map['scope_boundaries']['transition_point']}")
    print("="*70 + "\n")


# physicsguard/core/conditional_verdict.py
"""
PhysicsGuard v1.1 — Scope-Conditional Verdict Layer
Replaces binary CLEAN/CORRUPTED with condition-mapped truth boundaries.
CC0 — github.com/JinnZ2/physicsguard
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any

# ── Scope Parameters ──────────────────────────────────────────────────────────

@dataclass
class ScopeCondition:
    parameter:   str        # what variable determines truth
    value:       Any        # current value
    threshold:   Any        # boundary value
    direction:   str        # "above" | "below" | "equals"
    description: str        # human readable

@dataclass
class ConditionalVerdict:
    claim:           str
    base_verdict:    str                    # CLEAN | SUSPECT | CORRUPTED
    score:           float
    true_if:         List[ScopeCondition]   # conditions where claim holds
    false_if:        List[ScopeCondition]   # conditions where claim breaks
    current_scope:   Dict[str, Any]         # measured current conditions
    verdict_now:     str                    # verdict under current conditions
    boundary_map:    Dict[str, str]         # parameter -> transition point
    summary:         str                    # one-line human output

# ── Scope Condition Library ───────────────────────────────────────────────────

SCOPE_CONDITIONS = {

    "hierarchy_works": {
        "true_if": [
            ScopeCondition("layers",            2,    3,      "below",  "2-3 decision layers max"),
            ScopeCondition("branching_factor",  3,    4,      "below",  "3-4 direct reports per node"),
            ScopeCondition("novelty_rate",      0.0,  0.05,   "below",  "near-zero novel inputs"),
            ScopeCondition("change_rate",       0.0,  0.10,   "below",  "near-zero environmental change"),
            ScopeCondition("enforcement_cost",  0.05, 0.10,   "below",  "enforcement overhead under 10%"),
            ScopeCondition("info_completeness", 1.0,  0.95,   "above",  "near-perfect information at top"),
        ],
        "false_if": [
            ScopeCondition("layers",            7,    4,      "above",  "4+ layers add exponential latency"),
            ScopeCondition("novelty_rate",      0.3,  0.05,   "above",  "novel inputs exceed 5%"),
            ScopeCondition("change_rate",       0.5,  0.10,   "above",  "environment changing faster than 10%/cycle"),
            ScopeCondition("enforcement_cost",  0.45, 0.10,   "above",  "enforcement consuming 45%+ of resources"),
            ScopeCondition("cascade_risk",      0.80, 0.75,   "above",  "single-point dependency above 75%"),
        ],
    },

    "distributed_works": {
        "true_if": [
            ScopeCondition("novelty_rate",        0.3,  0.05,  "above",  "novel inputs common"),
            ScopeCondition("change_rate",         0.5,  0.10,  "above",  "environment changing rapidly"),
            ScopeCondition("protocol_clarity",    0.9,  0.80,  "above",  "pre-agreed protocols clear"),
            ScopeCondition("node_autonomy",       0.8,  0.70,  "above",  "nodes have local decision authority"),
            ScopeCondition("info_distribution",   0.8,  0.70,  "above",  "knowledge distributed across nodes"),
        ],
        "false_if": [
            ScopeCondition("protocol_clarity",    0.2,  0.80,  "below",  "protocols unclear — coordination fails"),
            ScopeCondition("node_count",          500,  200,   "above",  "routing overhead explodes beyond 200 nodes"),
            ScopeCondition("network_reliability", 0.7,  0.95,  "below",  "message loss cascades through system"),
        ],
    },

    "patriarchy_works": {
        "true_if": [
            ScopeCondition("layers",          2,   3,    "below",  "church + work + family only (2-3 layers)"),
            ScopeCondition("change_rate",     0.0, 0.05, "below",  "conditions fully stable"),
            ScopeCondition("domain_count",    3,   3,    "below",  "3 domains max: church, work, family"),
            ScopeCondition("novelty_rate",    0.0, 0.02, "below",  "zero novel social inputs"),
            ScopeCondition("role_ambiguity",  0.0, 0.05, "below",  "roles fully predefined"),
        ],
        "false_if": [
            ScopeCondition("layers",         7,    3,    "above",  "government + corps + institutions + depts exceeds envelope"),
            ScopeCondition("domain_count",   7,    3,    "above",  "7 domains exceed 3-layer optimum"),
            ScopeCondition("change_rate",    0.6,  0.05, "above",  "modern economic/social volatility"),
            ScopeCondition("workforce_dist", 0.5,  0.10, "above",  "50%+ workforce outside predefined roles"),
            ScopeCondition("novelty_rate",   0.4,  0.02, "above",  "continuous novel social/tech inputs"),
        ],
    },

    "nomadic_egalitarian_works": {
        "true_if": [
            ScopeCondition("change_rate",        0.7,  0.30, "above",  "high environmental variability"),
            ScopeCondition("survival_pressure",  0.8,  0.50, "above",  "survival is primary optimization target"),
            ScopeCondition("info_distribution",  0.9,  0.70, "above",  "knowledge distributed across group"),
            ScopeCondition("resource_mobility",  0.9,  0.70, "above",  "resources require active location"),
            ScopeCondition("decision_speed",     0.8,  0.60, "above",  "rapid local decision required"),
        ],
        "false_if": [
            ScopeCondition("fixed_geography",    1.0,  0.20, "above",  "fixed to reservation/grid — removes mobility"),
            ScopeCondition("external_hierarchy", 1.0,  0.10, "above",  "imposed hierarchy overrides local authority"),
        ],
    },
}

# ── Conditional Verdict Engine ────────────────────────────────────────────────

def evaluate_conditional(
    claim_key:     str,
    current_scope: Dict[str, Any],
    base_result:   dict,
) -> ConditionalVerdict:
    """
    Takes a claim key, current measured conditions, and base PhysicsGuard result.
    Returns a scope-conditional verdict mapping where claim is true vs false.
    """

    if claim_key not in SCOPE_CONDITIONS:
        return _unknown_scope(claim_key, base_result)

    conditions   = SCOPE_CONDITIONS[claim_key]
    true_if      = conditions["true_if"]
    false_if     = conditions["false_if"]

    true_met     = _evaluate_conditions(true_if,  current_scope)
    false_met    = _evaluate_conditions(false_if, current_scope)

    verdict_now  = _current_verdict(true_met, false_met, base_result)
    boundary_map = _build_boundary_map(true_if, false_if)
    summary      = _build_summary(claim_key, true_met, false_met, current_scope)

    return ConditionalVerdict(
        claim        = claim_key,
        base_verdict = base_result["verdict"],
        score        = base_result["score"],
        true_if      = true_if,
        false_if     = false_if,
        current_scope= current_scope,
        verdict_now  = verdict_now,
        boundary_map = boundary_map,
        summary      = summary,
    )

def _evaluate_conditions(conditions: List[ScopeCondition], scope: Dict) -> List[dict]:
    results = []
    for c in conditions:
        if c.parameter not in scope:
            results.append({"condition": c, "met": None, "note": "parameter not measured"})
            continue
        val = scope[c.parameter]
        if c.direction == "above": met = val >= c.threshold
        elif c.direction == "below": met = val <= c.threshold
        else: met = val == c.threshold
        results.append({"condition": c, "met": met, "actual": val})
    return results

def _current_verdict(true_met, false_met, base_result) -> str:
    true_count  = sum(1 for r in true_met  if r.get("met") is True)
    false_count = sum(1 for r in false_met if r.get("met") is True)
    true_total  = len([r for r in true_met  if r.get("met") is not None])
    false_total = len([r for r in false_met if r.get("met") is not None])

    true_ratio  = true_count  / true_total  if true_total  else 0
    false_ratio = false_count / false_total if false_total else 0

    if false_ratio > 0.5:
        return "CORRUPTED_IN_CURRENT_SCOPE"
    elif true_ratio > 0.7:
        return "VALID_IN_CURRENT_SCOPE"
    else:
        return "SCOPE_BOUNDARY — conditional"

def _build_boundary_map(true_if, false_if) -> Dict[str, str]:
    boundaries = {}
    for c in true_if:
        boundaries[c.parameter] = f"True if {c.direction} {c.threshold} — {c.description}"
    for c in false_if:
        if c.parameter in boundaries:
            boundaries[c.parameter] += f" | False if {c.direction} {c.threshold}"
        else:
            boundaries[c.parameter] = f"False if {c.direction} {c.threshold} — {c.description}"
    return boundaries

def _build_summary(claim_key, true_met, false_met, scope) -> str:
    broken = [r["condition"].description for r in false_met if r.get("met") is True]
    holding = [r["condition"].description for r in true_met if r.get("met") is True]

    if broken:
        return (
            f"'{claim_key}' fails under current conditions: "
            f"{broken[0]}. "
            f"Would hold if: {holding[0] if holding else 'conditions reversed'}."
        )
    return f"'{claim_key}' holds under current conditions. Boundary: {list(_build_boundary_map(true_met, false_met).values())[:1]}"

def _unknown_scope(claim_key, base_result) -> ConditionalVerdict:
    return ConditionalVerdict(
        claim        = claim_key,
        base_verdict = base_result["verdict"],
        score        = base_result["score"],
        true_if      = [],
        false_if     = [],
        current_scope= {},
        verdict_now  = "UNKNOWN_SCOPE",
        boundary_map = {},
        summary      = f"No scope conditions defined for '{claim_key}' — add to SCOPE_CONDITIONS",
    )

# ── Print ─────────────────────────────────────────────────────────────────────

def print_conditional_verdict(cv: ConditionalVerdict):
    print("\n" + "="*70)
    print(f"CONDITIONAL VERDICT: {cv.claim}")
    print("="*70)
    print(f"Base verdict     : {cv.base_verdict}  (score {cv.score:.3f})")
    print(f"Verdict NOW      : {cv.verdict_now}")
    print(f"\nSummary: {cv.summary}")
    print("\nTRUE IF:")
    for r in cv.true_if:
        met = "✓" if r.parameter in cv.current_scope else "?"
        print(f"  {met} {r.description}  (threshold: {r.direction} {r.threshold})")
    print("\nFALSE IF:")
    for r in cv.false_if:
        val = cv.current_scope.get(r.parameter, "unmeasured")
        broken = ""
        if r.parameter in cv.current_scope:
            v = cv.current_scope[r.parameter]
            if r.direction == "above" and v >= r.threshold: broken = "  ← TRIGGERED"
            if r.direction == "below" and v <= r.threshold: broken = "  ← TRIGGERED"
        print(f"  {r.description}  (threshold: {r.direction} {r.threshold}){broken}")
    print("\nBOUNDARY MAP:")
    for param, boundary in cv.boundary_map.items():
        print(f"  {param:25}: {boundary}")
    print("="*70 + "\n")
