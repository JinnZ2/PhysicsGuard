"""
knowledge_transmission_substrate

CC0 / public domain. JinnZ2.

Companion module - different shape from trait_waveform_validator.

## Purpose

Capture what text-based knowledge documentation cannot: the
DEVELOPMENTAL LOADING REGIME that shapes the substrate on which
encoded knowledge operates.

Most attempts to preserve traditional/landscape-encoded knowledge
treat it as content (recipes, names, stories, techniques). This is
incomplete because the knowledge presupposes a person whose:

    - hands have done the work since childhood
    - body has carried the loads
    - eyes have read the same landscape across seasons
    - relationships have taught reality-testing rather than
      consensus-seeking
    - decisions have had material consequences with real feedback
    - cognition has been calibrated by outcome, not by status

Content + substrate = functional knowledge.
Content alone     = museum artifact.

This module models knowledge transmission as a TWO-LAYER system:

    layer 1: CONTENT   (encodable as text, code, recipes, schemas)
    layer 2: SUBSTRATE (encodable only as DEVELOPMENTAL PATTERN)

A KnowledgeBundle that captures both is portable.
A KnowledgeBundle that captures only content degrades when
transmitted to a person whose substrate doesn't match.

The module provides:
    - KnowledgeUnit: an encodable atom (technique, principle, story)
    - SubstrateRequirement: what developmental loading must be present
      for the unit to operate correctly
    - TransmissionAudit: estimate degradation when transmitted to
      different substrate
    - SubstrateProfile: describe a person's developmental loading
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

# ---------------------------------------------------------------------
# SUBSTRATE DIMENSIONS
# ---------------------------------------------------------------------

class SubstrateAxis(Enum):
    """Dimensions along which developmental loading varies."""
    PHYSICAL_LOAD = "physical_load"
    REAL_CONSEQUENCE = "real_consequence"
    LANDSCAPE_TIME = "landscape_time"          # years observing same place
    MULTI_SKILL_INTEGRATION = "multi_skill_integration"
    REALITY_TESTING = "reality_testing"        # vs consensus-seeking
    SENSORY_CALIBRATION = "sensory_calibration"  # tracking, smell, weather-read
    MATERIAL_FAMILIARITY = "material_familiarity"  # hands-on hours per material
    GENERATIONAL_CONTINUITY = "generational_continuity"  # taught by elders
    EMBODIED_REPETITION = "embodied_repetition"  # motor pattern depth
    UNCERTAINTY_TOLERANCE = "uncertainty_tolerance"
    SLOW_TIME_EXPOSURE = "slow_time_exposure"  # waiting, watching, no urgency


# ---------------------------------------------------------------------
# SUBSTRATE PROFILE (a person)
# ---------------------------------------------------------------------

@dataclass
class SubstrateProfile:
    """
    Quantified developmental loading for a person (or population).

    Each axis: 0 = no exposure, 1 = saturated exposure

    The values are estimates. Honest profile-building requires
    knowing the person's history, not just their credentials.
    """
    name: str
    values: dict = field(default_factory=dict)
    notes: str = ""

    def get(self, axis: SubstrateAxis) -> float:
        return self.values.get(axis, 0.0)

    def gap_from(self, requirement: "SubstrateRequirement") -> dict:
        """
        Per-axis gap between this profile and what a knowledge unit needs.
        Negative gap = profile exceeds requirement (no degradation).
        Positive gap = profile is short  = degradation expected.
        """
        gaps = {}
        for axis, needed in requirement.minimums.items():
            have = self.get(axis)
            gaps[axis] = needed - have
        return gaps


# ---------------------------------------------------------------------
# SUBSTRATE REQUIREMENT (for a knowledge unit)
# ---------------------------------------------------------------------

@dataclass
class SubstrateRequirement:
    """
    The substrate loading required for a knowledge unit to operate
    correctly when transmitted.
    """
    minimums: dict = field(default_factory=dict)
    notes: str = ""


# ---------------------------------------------------------------------
# KNOWLEDGE UNIT
# ---------------------------------------------------------------------

class UnitKind(Enum):
    TECHNIQUE = "technique"          # hide tanning, cement work
    PRINCIPLE = "principle"          # fire geometry, edge thermodynamics
    PATTERN_LITERACY = "pattern_literacy"  # weather reading, animal tracks
    DECISION_HEURISTIC = "decision_heuristic"  # when to cross, when to wait
    STORY = "story"                  # generational hypothesis test
    SONG = "song"                    # landscape constraint document
    LAW = "law"                      # validated tradition rule
    RELATIONSHIP_GRAMMAR = "relationship_grammar"  # how people work together


@dataclass
class KnowledgeUnit:
    """
    An encodable knowledge atom. The 'content' field captures what
    text/code can hold. The 'substrate_requirement' captures what
    text/code cannot.
    """
    name: str
    kind: UnitKind
    content: str                                    # encodable layer
    substrate_requirement: SubstrateRequirement      # non-encodable layer
    prerequisite_units: tuple = ()                   # other units required first
    landscape_specificity: float = 0.0   # 0=portable, 1=location-bound
    notes: str = ""


# ---------------------------------------------------------------------
# TRANSMISSION AUDIT
# ---------------------------------------------------------------------

@dataclass
class TransmissionResult:
    unit_name: str
    receiver_name: str
    per_axis_gap: dict
    expected_function: float          # 0..1
    failure_modes: list
    advisory: str


class TransmissionAuditor:
    """
    Audit knowledge transmission from a unit to a substrate profile.
    Reports expected functional integrity at the receiving end.
    """

    def audit(self, unit: KnowledgeUnit, receiver: SubstrateProfile) -> TransmissionResult:
        gaps = receiver.gap_from(unit.substrate_requirement)

        # functional integrity = product of per-axis sufficiency
        # each axis: if gap > 0, multiplier = (1 - gap)
        function = 1.0
        failure_modes = []
        for axis, gap in gaps.items():
            if gap > 0:
                multiplier = max(0.0, 1.0 - gap)
                function *= multiplier
                failure_modes.append(self._failure_mode(unit, axis, gap))

        # landscape specificity: location-bound knowledge degrades
        # further in displaced contexts (proxy: assume mismatch unless
        # receiver explicitly has high LANDSCAPE_TIME on the same land)
        if unit.landscape_specificity > 0.5:
            landscape_score = receiver.get(SubstrateAxis.LANDSCAPE_TIME)
            if landscape_score < unit.landscape_specificity:
                landscape_factor = max(0.2, landscape_score / unit.landscape_specificity)
                function *= landscape_factor
                if landscape_factor < 0.7:
                    failure_modes.append(
                        f"landscape-specificity mismatch: unit needs "
                        f"{unit.landscape_specificity:.2f}, receiver has "
                        f"{landscape_score:.2f} years of same-place observation"
                    )

        advisory = self._advisory_for_function(function, failure_modes)

        return TransmissionResult(
            unit_name=unit.name,
            receiver_name=receiver.name,
            per_axis_gap=gaps,
            expected_function=function,
            failure_modes=failure_modes,
            advisory=advisory,
        )

    def _failure_mode(self, unit: KnowledgeUnit,
                      axis: SubstrateAxis, gap: float) -> str:
        templates = {
            SubstrateAxis.PHYSICAL_LOAD: (
                "receiver lacks load-bearing capacity assumed by unit. "
                "technique will be performed but body won't sustain it."
            ),
            SubstrateAxis.REAL_CONSEQUENCE: (
                "receiver's calibration is consequence-light. heuristic "
                "may be applied but not weighted correctly under risk."
            ),
            SubstrateAxis.LANDSCAPE_TIME: (
                "receiver has not observed this landscape across seasons. "
                "pattern-literacy is unreadable without that time depth."
            ),
            SubstrateAxis.MULTI_SKILL_INTEGRATION: (
                "receiver is specialized; unit assumes ability to "
                "integrate technique with adjacent skills as one act."
            ),
            SubstrateAxis.REALITY_TESTING: (
                "receiver is calibrated to consensus rather than outcome. "
                "may apply unit but ignore feedback signals."
            ),
            SubstrateAxis.SENSORY_CALIBRATION: (
                "receiver's senses are not tuned to the relevant signals "
                "(weather, tracks, smell, wind). technique becomes blind."
            ),
            SubstrateAxis.MATERIAL_FAMILIARITY: (
                "receiver has not handled this material across enough "
                "states. recognition of when technique is going wrong "
                "will be late."
            ),
            SubstrateAxis.GENERATIONAL_CONTINUITY: (
                "receiver did not learn from elder hands. correction "
                "loop that catches subtle errors is missing."
            ),
            SubstrateAxis.EMBODIED_REPETITION: (
                "receiver has not done the motor pattern enough times. "
                "will perform consciously rather than fluently, slowing "
                "and breaking under load."
            ),
            SubstrateAxis.UNCERTAINTY_TOLERANCE: (
                "receiver collapses to premature decision under "
                "ambiguity. unit assumes ability to hold open state."
            ),
            SubstrateAxis.SLOW_TIME_EXPOSURE: (
                "receiver lacks experience of slow-time observation. "
                "will rush phases that need to be witnessed at the "
                "land's pace."
            ),
        }
        base = templates.get(
            axis,
            f"receiver insufficient on {axis.value} (gap {gap:.2f})"
        )
        return f"[{axis.value}] {base} (gap={gap:.2f})"

    def _advisory_for_function(self, function: float,
                               failure_modes: list) -> str:
        if function >= 0.85:
            return (
                "transmission likely functional. content + substrate "
                "match closely."
            )
        if function >= 0.6:
            return (
                "transmission partial. content will land but operate "
                "below capacity. some failure modes present."
            )
        if function >= 0.3:
            return (
                "transmission degraded. content received as words/steps "
                "but underlying function compromised. receiver will "
                "miss when application is wrong for context."
            )
        return (
            "transmission near-symbolic. receiver has the words and "
            "may repeat them, but does not have the substrate that "
            "lets the knowledge function. risk: knowledge becomes "
            "performance/heritage rather than working tool."
        )


# ---------------------------------------------------------------------
# AGGREGATE: KNOWLEDGE BUNDLE
# ---------------------------------------------------------------------

@dataclass
class KnowledgeBundle:
    """A collection of knowledge units, transmissible as a set."""
    name: str
    units: list = field(default_factory=list)
    description: str = ""

    def audit_transmission(self, receiver: SubstrateProfile) -> dict:
        """Audit all units against receiver's substrate."""
        auditor = TransmissionAuditor()
        results = [auditor.audit(u, receiver) for u in self.units]
        if not results:
            return {"bundle": self.name, "n_units": 0, "results": []}

        functions = [r.expected_function for r in results]
        avg = sum(functions) / len(functions)
        weakest = min(results, key=lambda r: r.expected_function)
        strongest = max(results, key=lambda r: r.expected_function)

        return {
            "bundle": self.name,
            "receiver": receiver.name,
            "n_units": len(results),
            "average_expected_function": avg,
            "weakest_unit": weakest.unit_name,
            "weakest_function": weakest.expected_function,
            "strongest_unit": strongest.unit_name,
            "strongest_function": strongest.expected_function,
            "results": results,
            "advisory": (
                f"average transmission function: {avg:.2f}. "
                f"weakest: {weakest.unit_name} ({weakest.expected_function:.2f}). "
                f"strongest: {strongest.unit_name} ({strongest.expected_function:.2f})."
            ),
        }


# ---------------------------------------------------------------------
# REFERENCE PROFILES (for comparison)
# ---------------------------------------------------------------------

def text_only_recipient() -> SubstrateProfile:
    """A person who has read everything and done very little."""
    return SubstrateProfile(
        name="text_only_recipient",
        values={
            SubstrateAxis.PHYSICAL_LOAD: 0.1,
            SubstrateAxis.REAL_CONSEQUENCE: 0.1,
            SubstrateAxis.LANDSCAPE_TIME: 0.0,
            SubstrateAxis.MULTI_SKILL_INTEGRATION: 0.2,
            SubstrateAxis.REALITY_TESTING: 0.3,
            SubstrateAxis.SENSORY_CALIBRATION: 0.1,
            SubstrateAxis.MATERIAL_FAMILIARITY: 0.1,
            SubstrateAxis.GENERATIONAL_CONTINUITY: 0.0,
            SubstrateAxis.EMBODIED_REPETITION: 0.1,
            SubstrateAxis.UNCERTAINTY_TOLERANCE: 0.3,
            SubstrateAxis.SLOW_TIME_EXPOSURE: 0.1,
        },
        notes="urban, educated, sedentary, content-rich substrate-poor",
    )


def working_practitioner() -> SubstrateProfile:
    """A person trained by elders, working in the relevant landscape."""
    return SubstrateProfile(
        name="working_practitioner",
        values={
            SubstrateAxis.PHYSICAL_LOAD: 0.85,
            SubstrateAxis.REAL_CONSEQUENCE: 0.85,
            SubstrateAxis.LANDSCAPE_TIME: 0.8,
            SubstrateAxis.MULTI_SKILL_INTEGRATION: 0.85,
            SubstrateAxis.REALITY_TESTING: 0.9,
            SubstrateAxis.SENSORY_CALIBRATION: 0.8,
            SubstrateAxis.MATERIAL_FAMILIARITY: 0.85,
            SubstrateAxis.GENERATIONAL_CONTINUITY: 0.8,
            SubstrateAxis.EMBODIED_REPETITION: 0.85,
            SubstrateAxis.UNCERTAINTY_TOLERANCE: 0.8,
            SubstrateAxis.SLOW_TIME_EXPOSURE: 0.7,
        },
        notes="full developmental loading, multi-generational continuity",
    )


def displaced_descendant() -> SubstrateProfile:
    """Cultural inheritance present, developmental loading absent."""
    return SubstrateProfile(
        name="displaced_descendant",
        values={
            SubstrateAxis.PHYSICAL_LOAD: 0.3,
            SubstrateAxis.REAL_CONSEQUENCE: 0.3,
            SubstrateAxis.LANDSCAPE_TIME: 0.2,
            SubstrateAxis.MULTI_SKILL_INTEGRATION: 0.4,
            SubstrateAxis.REALITY_TESTING: 0.5,
            SubstrateAxis.SENSORY_CALIBRATION: 0.3,
            SubstrateAxis.MATERIAL_FAMILIARITY: 0.3,
            SubstrateAxis.GENERATIONAL_CONTINUITY: 0.4,
            SubstrateAxis.EMBODIED_REPETITION: 0.3,
            SubstrateAxis.UNCERTAINTY_TOLERANCE: 0.4,
            SubstrateAxis.SLOW_TIME_EXPOSURE: 0.3,
        },
        notes=(
            "common modern descendant: stories carried, hands not "
            "loaded. content present, substrate lost."
        ),
    )


# ---------------------------------------------------------------------
# REFERENCE KNOWLEDGE UNITS (illustrative)
# ---------------------------------------------------------------------

def example_brain_tanning_unit() -> KnowledgeUnit:
    return KnowledgeUnit(
        name="brain_tanning_hide",
        kind=UnitKind.TECHNIQUE,
        content=(
            "scrape, soak in brain emulsion, work hide repeatedly until "
            "fibers separate uniformly, smoke to set, finish to softness"
        ),
        substrate_requirement=SubstrateRequirement(
            minimums={
                SubstrateAxis.PHYSICAL_LOAD: 0.6,
                SubstrateAxis.MATERIAL_FAMILIARITY: 0.7,
                SubstrateAxis.SENSORY_CALIBRATION: 0.6,
                SubstrateAxis.EMBODIED_REPETITION: 0.6,
                SubstrateAxis.SLOW_TIME_EXPOSURE: 0.5,
                SubstrateAxis.GENERATIONAL_CONTINUITY: 0.5,
                SubstrateAxis.UNCERTAINTY_TOLERANCE: 0.5,
            },
            notes=(
                "the technique reads simple in text. function depends "
                "on hands knowing when fibers have shifted, eyes "
                "knowing when smoke is right, body knowing when to "
                "stop working and let it rest. words don't carry that."
            ),
        ),
        landscape_specificity=0.2,
        notes="unit content portable; functional execution substrate-bound",
    )


def example_landscape_reading_unit() -> KnowledgeUnit:
    return KnowledgeUnit(
        name="cross_river_decision",
        kind=UnitKind.DECISION_HEURISTIC,
        content=(
            "read color, sound, debris pattern, bank cut profile, "
            "and recent precipitation context. cross only when "
            "all five match safe pattern."
        ),
        substrate_requirement=SubstrateRequirement(
            minimums={
                SubstrateAxis.LANDSCAPE_TIME: 0.7,
                SubstrateAxis.SENSORY_CALIBRATION: 0.7,
                SubstrateAxis.REAL_CONSEQUENCE: 0.7,
                SubstrateAxis.UNCERTAINTY_TOLERANCE: 0.7,
                SubstrateAxis.SLOW_TIME_EXPOSURE: 0.6,
            },
            notes=(
                "five-signal pattern is meaningless without years of "
                "watching this kind of river under all conditions. "
                "reading the signals requires tuned senses; weighting "
                "them requires consequence-coupled calibration."
            ),
        ),
        landscape_specificity=0.7,
        notes="heuristic looks like a checklist; functions only as embodied pattern",
    )


def example_fire_geometry_unit() -> KnowledgeUnit:
    return KnowledgeUnit(
        name="fire_geometry_for_cold",
        kind=UnitKind.PRINCIPLE,
        content=(
            "fire shape and reflector geometry shape thermal radiation "
            "field. configure for sustained warmth without fuel waste, "
            "matching shelter geometry."
        ),
        substrate_requirement=SubstrateRequirement(
            minimums={
                SubstrateAxis.PHYSICAL_LOAD: 0.5,
                SubstrateAxis.MATERIAL_FAMILIARITY: 0.6,
                SubstrateAxis.REAL_CONSEQUENCE: 0.6,
                SubstrateAxis.SENSORY_CALIBRATION: 0.6,
                SubstrateAxis.EMBODIED_REPETITION: 0.5,
            },
            notes=(
                "principle is encodable; correct application needs "
                "having been cold enough times to feel small "
                "geometric changes in heat distribution."
            ),
        ),
        landscape_specificity=0.3,
    )


def example_bundle() -> KnowledgeBundle:
    return KnowledgeBundle(
        name="example_traditional_bundle",
        units=[
            example_brain_tanning_unit(),
            example_landscape_reading_unit(),
            example_fire_geometry_unit(),
        ],
        description=(
            "small illustrative bundle showing how the same content "
            "transmits differently to different substrates."
        ),
    )


# ---------------------------------------------------------------------
# SELF-TEST
# ---------------------------------------------------------------------

def _selftest():
    print("=" * 72)
    print("knowledge_transmission_substrate - self-test")
    print("=" * 72)

    bundle = example_bundle()

    profiles = [
        text_only_recipient(),
        displaced_descendant(),
        working_practitioner(),
    ]

    for profile in profiles:
        print(f"\n[transmission to: {profile.name}]")
        result = bundle.audit_transmission(profile)
        print(f"    avg function: {result['average_expected_function']:.2f}")
        print(f"    weakest unit: {result['weakest_unit']} "
              f"({result['weakest_function']:.2f})")
        print(f"    strongest unit: {result['strongest_unit']} "
              f"({result['strongest_function']:.2f})")
        worst = min(result["results"], key=lambda r: r.expected_function)
        print("    detail on weakest:")
        print(f"      {worst.advisory}")
        if worst.failure_modes:
            print("      top failure mode:")
            print(f"        {worst.failure_modes[0]}")

    print("\n" + "=" * 72)
    print("structural property:")
    print("  same CONTENT, three substrates, three different")
    print("  functional outcomes. text-only transmission of")
    print("  substrate-bound knowledge degrades to symbol/heritage.")
    print("=" * 72)


if __name__ == "__main__":
    _selftest()
