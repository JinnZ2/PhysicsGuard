"""
PhysicsGuard — Thermodynamic Accountability Domain

Checks institutional / extraction / labor claims against energy conservation
applied at the organism-plus-environment scale. Ports the EnergyAccountant
equations from the Thermodynamic Accountability Framework
(github.com/JinnZ2/thermodynamic-accountability-framework) into the
PhysicsGuard constraint-check idiom.

Core law (first-law accounting at the worker/system boundary):

    net_yield = compensation - productive_work - friction_losses

A system is non-viable (physically, not morally) when:

    (E_out - E_in) < minimum_reserve

Friction ratio (fraction of total energy that is uncompensated loss):

    friction = uncompensated_loss / total_energy

Collapse thresholds (load as fraction of energy input):

    load <= 1.00 E_in   → sustainable
    load >  1.20 E_in   → productivity degradation
    load >  1.40 E_in   → safety-system breakdown
    load >  1.60 E_in   → imminent health collapse

Distance-to-collapse (0 = at the cliff, 1 = well inside the envelope):

    d_collapse = clamp(0, 1, (1.6 * E_in - load) / (1.6 * E_in))

Parasitic energy debt (uncompensated metabolic draw):

    debt = unpaid_hours * metabolic_rate * (1 + 0.15 * friction_events)

All thresholds are falsifiable and overridable.

CC0 — github.com/JinnZ2/physicsguard
"""

from dataclasses import dataclass, field
from typing import List

# -- Thresholds ----------------------------------------------------------------

MIN_ENERGY_RESERVE         = 0.0    # J; net_yield must exceed this to be viable
MAX_FRICTION_RATIO         = 0.30   # >30% friction = parasitic regime
LOAD_DEGRADATION_FACTOR    = 1.20   # load/E_in above this = productivity loss
LOAD_SAFETY_FACTOR         = 1.40   # load/E_in above this = safety breakdown
LOAD_COLLAPSE_FACTOR       = 1.60   # load/E_in above this = imminent collapse
METABOLIC_RATE_DEFAULT     = 300.0  # kJ/hr baseline human metabolic floor
FRICTION_EVENT_PENALTY     = 0.15   # multiplier per friction event on debt

# -- Data Structures -----------------------------------------------------------

@dataclass
class TAFClaim:
    """An institutional / labor / extraction claim in energy-accounting form.

    All energy quantities are in the same unit (conventionally joules or
    kilojoules). The checker only cares about ratios, so unit choice is free
    as long as it is consistent within a single claim.
    """
    raw:                 str
    energy_in:           float = 0.0    # compensation + inputs supplied to organism/system
    productive_work:     float = 0.0    # useful output produced
    friction_losses:     float = 0.0    # uncompensated loss: signal blocking, theater, rework
    hidden_overhead:     float = 0.0    # unaccounted-for costs (commute, emotional labor, etc.)
    unpaid_hours:        float = 0.0    # hours of draw not reflected in energy_in
    metabolic_rate:      float = METABOLIC_RATE_DEFAULT
    friction_events:     int   = 0      # count of discrete friction incidents
    justification:       str   = ""     # claimed reason the extraction is legitimate


@dataclass
class TAFConstraintResult:
    claim:              TAFClaim
    net_yield:          float
    friction_ratio:     float
    load_factor:        float
    distance_to_collapse: float
    energy_debt:        float
    verdict:            str
    flags:              List[str] = field(default_factory=list)
    audit:              List[dict] = field(default_factory=list)


# -- Constraint Checkers -------------------------------------------------------

def check_energy_balance(claim: TAFClaim) -> dict:
    """First law applied at the organism/system boundary.

    net_yield = E_in - productive_work - friction_losses - hidden_overhead
    Negative net_yield means the system is drawing down stored capacity
    (capital, health, soil, goodwill) — unsustainable by definition.
    """
    total_out = claim.productive_work + claim.friction_losses + claim.hidden_overhead
    net_yield = claim.energy_in - total_out
    passed = net_yield >= MIN_ENERGY_RESERVE
    return {
        "law":      "energy_balance",
        "score":    net_yield,
        "passed":   passed,
        "detail":   f"Net yield {net_yield:.3f} (in={claim.energy_in:.3f}, out={total_out:.3f})",
        "fix_hint": (
            "Net yield negative — either raise compensation, reduce friction, "
            "or reduce hidden overhead. System is drawing down reserves."
            if not passed else "OK"
        ),
    }


def check_friction_ratio(claim: TAFClaim) -> dict:
    """Fraction of total energy lost to uncompensated friction.

    Above 30%, the structure is parasitic: more energy goes to maintaining
    the structure than to the work it claims to enable.
    """
    total = claim.energy_in + claim.productive_work + claim.friction_losses + claim.hidden_overhead
    if total <= 0:
        ratio = 0.0
    else:
        ratio = (claim.friction_losses + claim.hidden_overhead) / total
    passed = ratio <= MAX_FRICTION_RATIO
    return {
        "law":      "friction_ratio",
        "score":    ratio,
        "passed":   passed,
        "detail":   f"Friction ratio {ratio:.2%} vs max {MAX_FRICTION_RATIO:.2%}",
        "fix_hint": (
            f"Friction exceeds max by {ratio - MAX_FRICTION_RATIO:.2%} — "
            "reduce uncompensated loss or document it as productive work."
            if not passed else "OK"
        ),
    }


def check_collapse_distance(claim: TAFClaim) -> dict:
    """Distance-to-collapse on the 1.0 / 1.2 / 1.4 / 1.6 E_in ladder.

    load = productive_work + friction_losses + hidden_overhead
    Above 1.6 * E_in, health collapse is imminent.
    """
    load = claim.productive_work + claim.friction_losses + claim.hidden_overhead
    if claim.energy_in <= 0:
        load_factor = float("inf") if load > 0 else 0.0
        d = 0.0 if load > 0 else 1.0
    else:
        load_factor = load / claim.energy_in
        ceiling = LOAD_COLLAPSE_FACTOR * claim.energy_in
        d = max(0.0, min(1.0, (ceiling - load) / ceiling))
    passed = load_factor <= LOAD_DEGRADATION_FACTOR
    regime = _classify_load(load_factor)
    return {
        "law":      "distance_to_collapse",
        "score":    d,
        "passed":   passed,
        "detail":   f"Load factor {load_factor:.2f}x E_in ({regime}); distance={d:.3f}",
        "fix_hint": (
            f"Load is in {regime} regime — reduce demands or raise energy input."
            if not passed else "OK"
        ),
    }


def check_parasitic_debt(claim: TAFClaim) -> dict:
    """Parasitic energy debt from unpaid draw on metabolic reserves.

    debt = unpaid_hours * metabolic_rate * (1 + 0.15 * friction_events)
    Nonzero debt = extraction beyond what compensation covers.
    """
    debt = (
        claim.unpaid_hours
        * claim.metabolic_rate
        * (1.0 + FRICTION_EVENT_PENALTY * claim.friction_events)
    )
    passed = debt <= 0.0 or claim.unpaid_hours <= 0.0
    return {
        "law":      "parasitic_debt",
        "score":    debt,
        "passed":   passed,
        "detail":   (
            f"Energy debt {debt:.1f} from {claim.unpaid_hours:.1f} unpaid hours "
            f"and {claim.friction_events} friction events"
        ),
        "fix_hint": (
            "Unpaid metabolic draw detected — compensate the hours "
            "or count them as productive work."
            if not passed else "OK"
        ),
    }


def check_justification(claim: TAFClaim) -> dict:
    """Common narrative covers for energy imbalance that fail the math.

    Matches the style of domains/organizational.check_justification — the
    justification is flagged only when the narrative conflicts with the
    measured physics.
    """
    j = claim.justification.lower()
    total = claim.energy_in + claim.productive_work + claim.friction_losses + claim.hidden_overhead
    friction_ratio = 0.0 if total <= 0 else (claim.friction_losses + claim.hidden_overhead) / total
    net_yield = claim.energy_in - (claim.productive_work + claim.friction_losses + claim.hidden_overhead)

    FALSE_JUSTIFICATIONS = {
        "efficiency":   friction_ratio > 0.20,
        "productivity": net_yield < 0,
        "lazy":         friction_ratio > MAX_FRICTION_RATIO,
        "necessary":    net_yield < 0 and friction_ratio > MAX_FRICTION_RATIO,
        "meritocracy":  net_yield < 0,
    }
    triggered = [k for k, v in FALSE_JUSTIFICATIONS.items() if k in j and v]
    passed = len(triggered) == 0
    return {
        "law":      "justification_validity",
        "score":    1.0 if passed else 0.0,
        "passed":   passed,
        "detail":   (
            f"Narrative cover conflicts with energy accounting: {triggered}"
            if not passed else "Justification consistent with measured energy flow"
        ),
        "fix_hint": (
            f"Claims of {triggered} contradict the measured energy balance — "
            "either the numbers are wrong or the narrative is."
            if not passed else "OK"
        ),
    }


# -- Main Entry ----------------------------------------------------------------

def check_thermodynamic_accountability(claim: TAFClaim) -> TAFConstraintResult:
    checks = [
        check_energy_balance(claim),
        check_friction_ratio(claim),
        check_collapse_distance(claim),
        check_parasitic_debt(claim),
        check_justification(claim),
    ]

    failed = [c for c in checks if not c["passed"]]
    score  = len(failed) / len(checks)
    flags  = [c["law"] for c in failed]

    if   score == 0.0: verdict = "CLEAN"
    elif score < 0.5:  verdict = "SUSPECT"
    else:              verdict = "CORRUPTED"

    total = claim.energy_in + claim.productive_work + claim.friction_losses + claim.hidden_overhead
    friction_ratio = 0.0 if total <= 0 else (claim.friction_losses + claim.hidden_overhead) / total
    load = claim.productive_work + claim.friction_losses + claim.hidden_overhead
    load_factor = float("inf") if claim.energy_in <= 0 and load > 0 else (
        0.0 if claim.energy_in <= 0 else load / claim.energy_in
    )

    return TAFConstraintResult(
        claim                = claim,
        net_yield            = claim.energy_in - load,
        friction_ratio       = friction_ratio,
        load_factor          = load_factor,
        distance_to_collapse = checks[2]["score"],
        energy_debt          = checks[3]["score"],
        verdict              = verdict,
        flags                = flags,
        audit                = checks,
    )


# -- Helpers -------------------------------------------------------------------

def _classify_load(load_factor: float) -> str:
    if load_factor <= 1.0:                        return "sustainable"
    if load_factor <= LOAD_DEGRADATION_FACTOR:    return "strained"
    if load_factor <= LOAD_SAFETY_FACTOR:         return "degraded"
    if load_factor <= LOAD_COLLAPSE_FACTOR:       return "safety_breakdown"
    return "collapse_imminent"
