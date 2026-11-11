"""
Units-aware quantity checks: real physics on the numbers a premise states.

Added 2026-10-27 (F-013). Before this module the pipeline extracted numbers,
dropped their units, summed them into one "magnitude", and never compared
them. `"The motor is 120% efficient"` returned CLEAN.

What this module does
---------------------
1. Extracts every number that carries a recognised unit, converts it to SI,
   and keeps the source span it came from (`text[start:end]` reproduces it).
2. Runs a fixed set of known-answer physics checks over those quantities.
3. Returns one finding per check that applied, in one of three states:

       VIOLATION   the stated numbers break a physical limit (computed)
       CONSISTENT  the stated numbers were checked and sit inside the limit
       UNRESOLVED  quantities were found but their roles are not stated,
                   so no limit can be applied without guessing

   A check that does not apply returns nothing. `overall()` returns
   NOT_APPLICABLE when no check applied. That is a scope statement, never
   a pass.

What it does NOT do
-------------------
- It does not read meaning. Role assignment ("which number is the input")
  uses a short list of verbs and is stated per check. Paraphrase steps
  around it; an unassigned role becomes UNRESOLVED, never a guess.
- It does not model losses, friction or real-device curves. Every limit
  is an upper bound from first or second law; a claim inside the bound is
  CONSISTENT with that law only, not shown to be achievable.

Checks (all limits are textbook, constants stated below):
    Q1 efficiency_over_unity   efficiency <= 1            (first law)
    Q2 carnot_engine           eta <= 1 - Tc/Th           (second law)
    Q3 heat_pump_cop           COP <= Th/(Th - Tc)        (second law)
                               (refrigerator: Tc/(Th-Tc))
    Q4 output_exceeds_input    out <= in, same dimension  (first law)
    Q5 free_fall_energy        KE <= m g h, v <= sqrt(2gh)(first law)

Stdlib only. CC0.
"""

import math
import re
from dataclasses import dataclass, field

G = 9.80665  # m/s^2, standard gravity (CGPM 1901 conventional value)
C_TO_K = 273.15
REL_TOL = 1e-9  # float tolerance only; no physical slack is granted

# unit token -> (dimension, factor to SI, offset to SI)
UNITS = {
    # power
    "gw": ("power", 1e9, 0.0), "mw": ("power", 1e6, 0.0), "kw": ("power", 1e3, 0.0),
    "w": ("power", 1.0, 0.0), "watt": ("power", 1.0, 0.0), "watts": ("power", 1.0, 0.0),
    "hp": ("power", 745.69987, 0.0), "horsepower": ("power", 745.69987, 0.0),
    # energy
    "j": ("energy", 1.0, 0.0), "joule": ("energy", 1.0, 0.0), "joules": ("energy", 1.0, 0.0),
    "kj": ("energy", 1e3, 0.0), "mj": ("energy", 1e6, 0.0), "gj": ("energy", 1e9, 0.0),
    "wh": ("energy", 3600.0, 0.0), "kwh": ("energy", 3.6e6, 0.0), "mwh": ("energy", 3.6e9, 0.0),
    "kcal": ("energy", 4184.0, 0.0), "btu": ("energy", 1055.056, 0.0),
    # irradiance / power flux
    "w/m2": ("irradiance", 1.0, 0.0), "w/m^2": ("irradiance", 1.0, 0.0), "w/m²": ("irradiance", 1.0, 0.0),
    "kw/m2": ("irradiance", 1e3, 0.0), "kw/m^2": ("irradiance", 1e3, 0.0), "kw/m²": ("irradiance", 1e3, 0.0),
    # temperature (absolute SI = kelvin)
    "k": ("temperature", 1.0, 0.0), "kelvin": ("temperature", 1.0, 0.0),
    "c": ("temperature", 1.0, C_TO_K), "°c": ("temperature", 1.0, C_TO_K),
    "ºc": ("temperature", 1.0, C_TO_K), "celsius": ("temperature", 1.0, C_TO_K),
    "degrees c": ("temperature", 1.0, C_TO_K), "degrees celsius": ("temperature", 1.0, C_TO_K),
    "°f": ("temperature_f", 1.0, 0.0), "f": ("temperature_f", 1.0, 0.0),
    "fahrenheit": ("temperature_f", 1.0, 0.0),
    # mass, length, speed
    "kg": ("mass", 1.0, 0.0), "g": ("mass", 1e-3, 0.0), "tonne": ("mass", 1e3, 0.0),
    "tonnes": ("mass", 1e3, 0.0),
    "m": ("length", 1.0, 0.0), "km": ("length", 1e3, 0.0), "cm": ("length", 1e-2, 0.0),
    "m/s": ("speed", 1.0, 0.0), "km/h": ("speed", 1 / 3.6, 0.0),
    # ratio
    "%": ("fraction", 0.01, 0.0), "percent": ("fraction", 0.01, 0.0),
}

# Longest unit first so "kwh" wins over "kw" and "w/m2" over "w".
_UNIT_ALT = "|".join(re.escape(u) for u in sorted(UNITS, key=len, reverse=True))
_QTY_RE = re.compile(
    r"(?<![\w.])(-?\d+(?:\.\d+)?)\s*(" + _UNIT_ALT + r")(?![\w/^²])",
    re.IGNORECASE,
)
_COP_RE = re.compile(r"\bCOP\s*(?:of|=|:|is)?\s*(\d+(?:\.\d+)?)", re.IGNORECASE)


@dataclass
class Quantity:
    value_si: float
    dimension: str
    raw: str
    start: int
    end: int


@dataclass
class Finding:
    check: str
    state: str          # VIOLATION | CONSISTENT | UNRESOLVED
    law: str
    limit: float = None    # physical bound (SI or dimensionless)
    claimed: float = None  # stated value in the same unit as limit
    formula: str = ""
    detail: str = ""
    spans: list = field(default_factory=list)

    def to_dict(self):
        return {
            "check": self.check, "state": self.state, "law": self.law,
            "limit": self.limit, "claimed": self.claimed,
            "formula": self.formula, "detail": self.detail, "spans": self.spans,
        }


def extract_quantities(text: str) -> list:
    """Every number that carries a recognised unit, converted to SI."""
    out = []
    for m in _QTY_RE.finditer(text):
        num, unit = m.group(1), m.group(2).lower()
        dim, factor, offset = UNITS[unit]
        v = float(num)
        if dim == "temperature_f":
            dim, v_si = "temperature", (v - 32.0) * 5.0 / 9.0 + C_TO_K
        else:
            v_si = v * factor + offset
        out.append(Quantity(v_si, dim, m.group(0), m.start(), m.end()))
    for m in _COP_RE.finditer(text):
        out.append(Quantity(float(m.group(1)), "cop", m.group(0), m.start(), m.end()))
    out.sort(key=lambda q: q.start)
    return out


def _has(text, *words):
    t = text.lower()
    return any(re.search(r"\b" + re.escape(w), t) for w in words)


def _span(q):
    return {"raw": q.raw, "start": q.start, "end": q.end}


# -- Q1 ------------------------------------------------------------------------

def _q1_efficiency(text, qs):
    if not _has(text, "efficien"):
        return []
    fracs = [q for q in qs if q.dimension == "fraction"]
    temps = [q for q in qs if q.dimension == "temperature"]
    if not fracs or (len(temps) >= 2 and _has(text, "engine", "turbine")):
        return []  # Carnot (Q2) is the sharper check when two temperatures exist
    out = []
    for q in fracs:
        state = "VIOLATION" if q.value_si > 1.0 + REL_TOL else "CONSISTENT"
        out.append(Finding(
            "efficiency_over_unity", state, "first_law_thermodynamics",
            limit=1.0, claimed=q.value_si, formula="eta = E_out / E_in <= 1",
            detail=(f"stated efficiency {q.value_si:.4g} exceeds 1: output exceeds input"
                    if state == "VIOLATION" else
                    f"stated efficiency {q.value_si:.4g} <= 1 (first law only; "
                    "second-law limit needs the process and temperatures)"),
            spans=[_span(q)]))
    return out


# -- Q2 / Q3 -------------------------------------------------------------------

def _two_temps(qs):
    temps = [q for q in qs if q.dimension == "temperature"]
    if len(temps) != 2:
        return None
    lo, hi = sorted(temps, key=lambda q: q.value_si)
    return lo, hi


def _q2_carnot(text, qs):
    if not _has(text, "engine", "turbine"):
        return []
    pair = _two_temps(qs)
    fracs = [q for q in qs if q.dimension == "fraction"]
    if not pair or len(fracs) != 1:
        return []
    lo, hi = pair
    eta = fracs[0].value_si
    if lo.value_si <= 0 or hi.value_si <= lo.value_si:
        return [Finding("carnot_engine", "UNRESOLVED", "second_law_thermodynamics",
                        detail="temperatures not above absolute zero or not distinct",
                        spans=[_span(lo), _span(hi), _span(fracs[0])])]
    limit = 1.0 - lo.value_si / hi.value_si
    state = "VIOLATION" if eta > limit + REL_TOL else "CONSISTENT"
    return [Finding(
        "carnot_engine", state, "second_law_thermodynamics",
        limit=limit, claimed=eta, formula="eta <= 1 - Tc/Th",
        detail=f"Tc={lo.value_si:.2f} K, Th={hi.value_si:.2f} K, Carnot limit {limit:.4f}, stated {eta:.4f}",
        spans=[_span(lo), _span(hi), _span(fracs[0])])]


def _q3_cop(text, qs):
    cops = [q for q in qs if q.dimension == "cop"]
    if not cops:
        return []
    pair = _two_temps(qs)
    if not pair:
        return [Finding("heat_pump_cop", "UNRESOLVED", "second_law_thermodynamics",
                        detail="COP stated without two reservoir temperatures; no limit computable",
                        spans=[_span(cops[0])])]
    lo, hi = pair
    if lo.value_si <= 0 or hi.value_si <= lo.value_si:
        return [Finding("heat_pump_cop", "UNRESOLVED", "second_law_thermodynamics",
                        detail="temperatures not above absolute zero or not distinct",
                        spans=[_span(lo), _span(hi), _span(cops[0])])]
    dT = hi.value_si - lo.value_si
    cooling = _has(text, "refrigerat", "freezer", "air condition", "cooling", "chiller")
    heating = _has(text, "heat pump", "heating")
    if cooling and not heating:
        limit, formula = lo.value_si / dT, "COP_cool <= Tc/(Th-Tc)"
    else:
        # Heating limit is the larger of the two, so a breach of it is a breach
        # under either reading; unlabelled COP is tested against it.
        limit, formula = hi.value_si / dT, "COP_heat <= Th/(Th-Tc)"
    cop = cops[0].value_si
    state = "VIOLATION" if cop > limit + REL_TOL else "CONSISTENT"
    return [Finding(
        "heat_pump_cop", state, "second_law_thermodynamics",
        limit=limit, claimed=cop, formula=formula,
        detail=f"Tc={lo.value_si:.2f} K, Th={hi.value_si:.2f} K, Carnot COP limit {limit:.3f}, stated {cop:.3g}",
        spans=[_span(lo), _span(hi), _span(cops[0])])]


# -- Q4 ------------------------------------------------------------------------

_IN_VERBS = r"(?:consumes?|draws?|uses?|takes?\s+in|stores?|absorbs?|receives?|converts?|input\s+of|from)"
_OUT_VERBS = r"(?:delivers?|produces?|outputs?|yields?|generates?|provides?|returns?|gives?\s+back|into|releases?)"


def _q4_out_over_in(text, qs):
    out = []
    for dim in ("power", "energy", "irradiance"):
        same = [q for q in qs if q.dimension == dim]
        if len(same) != 2:
            continue
        a, b = same
        before_a = text[max(0, a.start - 40):a.start]
        between = text[a.end:b.start]
        in_role = re.search(_IN_VERBS, before_a + " " + between[:20], re.IGNORECASE)
        out_role = re.search(_OUT_VERBS, between, re.IGNORECASE)
        if not (in_role and out_role):
            out.append(Finding(
                "output_exceeds_input", "UNRESOLVED", "first_law_thermodynamics",
                detail=(f"two {dim} values ({a.raw}, {b.raw}) with no stated input/output roles; "
                        "a device rating can be input or output"),
                spans=[_span(a), _span(b)]))
            continue
        state = "VIOLATION" if b.value_si > a.value_si * (1 + REL_TOL) else "CONSISTENT"
        ratio = b.value_si / a.value_si if a.value_si else math.inf
        out.append(Finding(
            "output_exceeds_input", state, "first_law_thermodynamics",
            limit=a.value_si, claimed=b.value_si, formula="output <= input (same dimension)",
            detail=f"input {a.raw} -> output {b.raw}, output/input = {ratio:.4g}",
            spans=[_span(a), _span(b)]))
    return out


# -- Q5 ------------------------------------------------------------------------

def _q5_fall(text, qs):
    if not _has(text, "drop", "fall", "fell", "released from"):
        return []
    masses = [q for q in qs if q.dimension == "mass"]
    heights = [q for q in qs if q.dimension == "length"]
    energies = [q for q in qs if q.dimension == "energy"]
    speeds = [q for q in qs if q.dimension == "speed"]
    if len(heights) != 1:
        return []
    h = heights[0].value_si
    out = []
    if len(masses) == 1 and len(energies) == 1:
        limit = masses[0].value_si * G * h
        e = energies[0].value_si
        state = "VIOLATION" if e > limit * (1 + REL_TOL) else "CONSISTENT"
        out.append(Finding(
            "free_fall_energy", state, "first_law_thermodynamics",
            limit=limit, claimed=e, formula="KE <= m g h (no drag)",
            detail=f"m g h = {limit:.4g} J, stated {e:.4g} J",
            spans=[_span(masses[0]), _span(heights[0]), _span(energies[0])]))
    if len(speeds) == 1:
        limit = math.sqrt(2 * G * h)
        v = speeds[0].value_si
        state = "VIOLATION" if v > limit * (1 + REL_TOL) else "CONSISTENT"
        out.append(Finding(
            "free_fall_energy", state, "first_law_thermodynamics",
            limit=limit, claimed=v, formula="v <= sqrt(2 g h) (no drag)",
            detail=f"sqrt(2gh) = {limit:.4g} m/s, stated {v:.4g} m/s",
            spans=[_span(heights[0]), _span(speeds[0])]))
    return out


CHECKS = (_q1_efficiency, _q2_carnot, _q3_cop, _q4_out_over_in, _q5_fall)


def check_quantities(text: str) -> list:
    """Run every check; return the findings of those that applied."""
    qs = extract_quantities(text)
    findings = []
    for fn in CHECKS:
        findings.extend(fn(text, qs))
    return findings


def overall(findings: list) -> str:
    """VIOLATION > CONSISTENT > UNRESOLVED > NOT_APPLICABLE. Never a pass by default."""
    states = {f.state for f in findings}
    for s in ("VIOLATION", "CONSISTENT", "UNRESOLVED"):
        if s in states:
            return s
    return "NOT_APPLICABLE"


def to_results(findings: list) -> list:
    """Convert computed findings into conservation-checker result dicts.

    UNRESOLVED findings produce no result: an unassigned role is not a
    measurement and must not enter a score in either direction.
    """
    from core.conservation_checker import _compute_severity
    results = []
    for f in findings:
        if f.state == "UNRESOLVED":
            continue
        lhs, rhs = f.limit, f.claimed
        passed = f.state == "CONSISTENT"
        delta = 0.0 if passed else abs(rhs - lhs)
        results.append({
            "law": f.law,
            "passed": passed,
            "delta": delta,
            "severity": 0.0 if passed else _compute_severity(lhs, rhs, delta, 0.0),
            "lhs": lhs,
            "rhs": rhs,
            "detail": f"{f.law} [{f.check}]: {f.detail} ({f.formula})",
            "quantity_check": True,
        })
    return results


if __name__ == "__main__":
    import sys
    if "--selftest" in sys.argv:
        print("quantity_checker has no selftest flag; run: pytest tests/test_quantity_checker.py")
        sys.exit(2)
    for line in sys.argv[1:]:
        fs = check_quantities(line)
        print(overall(fs), "|", line)
        for f in fs:
            print("   ", f.check, f.state, f.detail)
