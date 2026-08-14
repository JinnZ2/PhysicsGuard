"""
Characterization tests for the vector-similarity gate.

These pin the *measured* boundary of `core/vectorizer.py`, established by the
F-006 investigation (see FALSIFICATION_LOG.md). They are not aspirational —
they encode what the vectorizer actually does, so that a future change to the
similarity threshold or the reference library fails loudly instead of silently
shifting behavior.

The finding they guard: the vector fallback generalizes to *near-verbatim
paraphrase only*. On genuinely novel phrasing it neither fires nor should be
made to fire — every alternative operating point tested also flagged
physics-free control sentences as violations.

Corpus: benchmarks/vector_gate_probe.jsonl
"""

import json
from pathlib import Path

import pytest

from core.premise_parser import parse_premise
from core.vectorizer import REFERENCE_LIBRARY, match_premise

# The gate in core/premise_parser.py: vector fallback applies when
# claim_pattern == "generic" and similarity > VECTOR_FALLBACK_THRESHOLD.
VECTOR_FALLBACK_THRESHOLD = 0.2

PROBE_PATH = Path(__file__).parent.parent / "benchmarks" / "vector_gate_probe.jsonl"


def _load(kind):
    rows = [json.loads(line) for line in PROBE_PATH.read_text().splitlines() if line.strip()]
    return [r for r in rows if r["kind"] == kind]


def test_probe_corpus_loads():
    rows = [json.loads(line) for line in PROBE_PATH.read_text().splitlines() if line.strip()]
    assert len(rows) == 24
    assert len({r["id"] for r in rows}) == len(rows), "probe ids must be unique"
    assert {r["kind"] for r in rows} == {"violation", "valid", "control"}


# -- The load-bearing guard ---------------------------------------------------

@pytest.mark.parametrize("row", _load("control"), ids=lambda r: r["id"])
def test_control_sentences_are_not_flagged(row):
    """
    Physics-free sentences must not reach a violation verdict.

    This is the constraint that makes lowering the similarity threshold unsafe.
    "she walked the dog around the block twice" scores 0.219 against
    `creation_from_nothing` once out-of-vocabulary terms are dropped, and 3 of
    these 4 controls cross the line under every alternative scoring variant
    tested in F-006. If a change to the threshold or the library makes this
    test fail, the change is flagging arbitrary English as a physics violation.
    """
    parsed = parse_premise(row["input"])
    assert not parsed["is_impossibility_claim"], (
        f"Physics-free control sentence flagged as an impossibility claim: {row['input']!r} "
        f"(pattern={parsed['claim_pattern']!r}, sim={parsed['vector_match']['similarity']})"
    )


def test_control_similarity_stays_below_gate():
    """Controls must stay under the fallback threshold, not merely be unflagged."""
    for row in _load("control"):
        sim = match_premise(row["input"]).similarity
        assert sim <= VECTOR_FALLBACK_THRESHOLD, (
            f"Control {row['input']!r} scored {sim:.3f}, at or above the "
            f"{VECTOR_FALLBACK_THRESHOLD} gate — arbitrary text is now matchable."
        )


# -- Documented reach of the vectorizer ---------------------------------------

def test_near_verbatim_paraphrase_still_matches():
    """
    The capability the vectorizer genuinely has: near-verbatim paraphrase.

    Guards the other direction — raising the threshold far enough to break this
    would make the module entirely inert.
    """
    result = match_premise("heat flows from hot to cold naturally")
    assert result.similarity > 0.8
    assert result.best_category == "transfer_claim"
    assert result.best_label == "valid"


def test_novel_phrasing_does_not_reach_the_gate():
    """
    The capability it does NOT have, pinned deliberately.

    These two inputs are real first-law / information violations. Commit
    c477e6b's message claimed the vectorizer catches them; F-006 established it
    never did. They are categorized correctly but score far below the gate, so
    the category is computed and discarded.

    This test asserts the *limitation*. If it fails because scores rose, read
    F-006 before celebrating: the same change also lifts the control sentences.
    """
    for text in ["output appears with no source energy",
                 "results emerge without any data input"]:
        result = match_premise(text)
        assert result.best_label == "violation", "category detection itself works"
        assert result.similarity < VECTOR_FALLBACK_THRESHOLD, (
            f"{text!r} now scores {result.similarity:.3f}, above the gate. "
            "Verify the controls in this file still pass before accepting this."
        )


# -- Library composition ------------------------------------------------------

def test_reference_library_is_violation_weighted():
    """
    41 violation entries vs 20 valid. Recorded because it biases `best_label`
    toward "violation" for out-of-domain text — 3 of the 4 control sentences
    are labeled "violation" purely on this prior.
    """
    from collections import Counter
    counts = Counter(label for _, label, _ in REFERENCE_LIBRARY)
    assert counts["violation"] == 41
    assert counts["valid"] == 20
