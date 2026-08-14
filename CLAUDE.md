# CLAUDE.md — PhysicsGuard

## Project Overview

PhysicsGuard is a physics-grounded logic verification system that detects corrupted or adversarial premises by translating natural language claims into physical constraint equations and checking them against conservation laws. When the math doesn't balance, the premise is flagged.

- **License**: CC0 1.0 Universal (Public Domain)
- **Language**: Python 3.9+ (standard library only — zero external dependencies)
- **Repository**: github.com/JinnZ2/PhysicsGuard

## Repository Structure

```
PhysicsGuard/
├── main.py                        # Entry point — check(), check_batch(), CLI
├── ai_interface.py                # audit() — unified, exception-safe AI entry point
├── core/
│   ├── premise_parser.py          # Pattern-based semantic claim extraction + dismissal layer
│   ├── constraint_mapper.py       # Maps claims → real conservation equations
│   ├── conservation_checker.py    # Validates constraints with actual delta math
│   ├── flag_engine.py             # Severity-weighted scoring, Verdict/Violation dataclasses
│   ├── vectorizer.py              # TF-IDF vectors + cosine similarity reference matching
│   ├── contrapositive_tester.py   # Four-corner semantic validation (standalone)
│   └── conditional_verdict.py     # Scope-conditional verdict layer (standalone)
├── domains/
│   ├── organizational.py          # Org structure constraint checking
│   ├── information.py             # Information conservation (Landauer, Shannon, NFL)
│   └── thermodynamic_accountability.py  # TAF energy accounting (extraction/labor claims)
├── monoculture_detector.py        # Variance-collapse audit across 7 axes
├── trait_waveform_validator.py    # Phase-space anti-bias framework (base module)
├── cognition_state_surface.py     # Add-on: task-specific cognition surfaces
├── environment_expression_surface.py    # Add-on: developmental-loading axes
├── knowledge_transmission_substrate.py  # Companion: content + substrate transmission
├── benchmarks/
│   ├── cases.jsonl                # 26-case seed corpus (not authoritative data)
│   ├── vector_gate_probe.jsonl    # 24-row boundary corpus for the similarity gate
│   └── README.md                  # Schema, framing warning, contribution rules
├── tests/                         # 139 tests total
│   ├── test_premises.py           # Core pipeline tests (53)
│   ├── test_benchmarks.py         # Benchmark corpus regression (45)
│   ├── test_vectorizer.py         # Vector similarity tests (13)
│   ├── test_thermodynamic_accountability.py  # TAF tests (9)
│   ├── test_organizational.py     # Organizational module tests (6)
│   ├── test_information.py        # Information conservation tests (4)
│   └── test_vector_gate.py        # Similarity-gate boundary + controls (9)
├── legacy/                        # Superseded artifacts — do NOT treat as current
│   ├── README.md                  # What is here and what falsified it
│   ├── v1_specification.md        # Original README w/ inline v1 source (was README.md)
│   └── PLAN.md                    # Executed rewrite plan
├── FALSIFICATION_LOG.md           # Claim → run → result → edited claim record
├── .github/workflows/ci.yml       # ruff + pytest on py3.9/3.11/3.12
├── pyproject.toml                 # Project metadata, pytest/ruff/mypy config
├── README.md                      # Current user-facing documentation
├── LICENSE                        # CC0 1.0 Universal
└── .gitignore
```

## Legacy and the falsification record

This repo keeps superseded work rather than deleting it. **Precedence carries** —
a falsified design is the evidence that constrains the next one.

- `FALSIFICATION_LOG.md` — the hypothesize → run → result → falsified → edit loop,
  one entry per turn. Read it before proposing a simplification; several
  obvious-looking approaches are already in there with the evidence that killed
  them. Four of the nine entries falsify claims this project made *about itself*.
  **Before touching `core/vectorizer.py` or its similarity threshold, read
  F-006 through F-009** — the gate has been measured, every alternative operating
  point tested was worse, and the suite alone cannot detect a bad threshold.
- `legacy/` — the artifacts themselves. Never imported, never current.

When superseding something:
1. `git mv` it into `legacy/` (never copy-and-delete — `git log --follow` must work)
2. Add a `FALSIFICATION_LOG.md` entry: claim, run, **verbatim** result, edited claim
3. Add a row to the table in `legacy/README.md`
4. Record unresolved unknowns as `OPEN` rather than omitting them

## Commands

```bash
# Check a single premise
python main.py "Energy can be created from nothing"

# JSON output (for AI consumption)
python main.py --json "Energy can be created from nothing"

# Batch mode (one premise per line)
python main.py --batch premises.txt
python main.py --batch --json premises.txt

# Pipe mode (stdin)
echo "claim1" | python main.py --pipe

# Interactive mode
python main.py

# Run tests
pytest tests/ -v

# Lint
ruff check .
ruff check --fix .
```

## Python API

```python
from main import check, check_batch

result = check("Energy can be created from nothing")
# Returns: {"verdict": "CORRUPTED", "score": 0.67, "flags": [...], ...}

results = check_batch(["claim1", "claim2"])
```

Preferred entry point for AI clients — auto-routes by input shape and never
raises (failures return `mode="error"` instead):

```python
from ai_interface import audit

audit("Energy can be created from nothing")   # str  → premise
audit(["doc 1", "doc 2", "doc 3"])            # list → corpus / monoculture
audit({"domain": "organizational", ...})      # dict → domain module
audit(x, mode="premise")                      # force a mode
```

## Architecture

### Core Pipeline

```
premise (str)
  → parse_premise()     — pattern-based semantic extraction
  → map_to_constraints() — real conservation equations (lhs != rhs when violated)
  → check_conservation() — actual delta math with severity scoring
  → score_and_flag()     — severity-weighted verdict with audit trail
```

### 1. Premise Parser (`core/premise_parser.py`)

Uses regex claim patterns (not keyword matching) to identify claim structures:

| Pattern | Example | Meaning |
|---------|---------|---------|
| `creation_from_nothing` | "Energy created from nothing" | Zero input, nonzero output |
| `infinite_claim` | "Infinite power" | Finite input, infinite output |
| `output_without_cost` | "Extract with no entropy cost" | Output with denied cost |
| `perfect_efficiency` | "100% efficient conversion" | Violates second law |
| `conservation_statement` | "Mass cannot be destroyed" | Valid physics (CLEAN) |
| `transfer_claim` | "Heat flows from hot to cold" | Balanced transfer (CLEAN) |
| `entropy_reversal` | "Entropy decreases without work" | Second law violation |
| `perpetual_motion` | "Perpetual motion machine" | First + second law violation |

Output includes: `claim_pattern`, `is_impossibility_claim`, `is_conservation_statement`, `cost_mentioned`, `cost_negated`, `negated_kw`, `subject`

### 2. Constraint Mapper (`core/constraint_mapper.py`)

Generates real conservation equations where **lhs and rhs actually differ** when physics is violated:

- `creation_from_nothing` → `lhs=0.0, rhs=1.0` (zero input, nonzero output)
- `infinite_claim` → `lhs=1.0, rhs=inf` (finite in, infinite out)
- `transfer_claim` → `lhs=1.0, rhs=1.0` (balanced)
- `conservation_statement` → `lhs=1.0, rhs=1.0` (balanced)

### 3. Conservation Checker (`core/conservation_checker.py`)

Computes actual deltas and severity scores:
- `delta = abs(lhs - rhs)` — real imbalance measurement
- `severity` on 0.0-1.0 scale using sigmoid normalization
- Handles `inf` deltas for infinite claims

### 4. Flag Engine (`core/flag_engine.py`)

Severity-weighted scoring (not simple counting):
- Score = average severity across all constraints
- Structured `Verdict` and `Violation` dataclasses
- Confidence score based on claim pattern specificity + vector similarity
- Full audit trail with fix hints

### 5. Vector Similarity (`core/vectorizer.py`)

TF-IDF vectorizer with cosine similarity against a reference library of ~60 known physics violations and valid claims. Uses word unigrams + bigrams + trigrams for phrase-level matching. Zero external dependencies.

**Role in pipeline**: Integrated into `premise_parser.py` as:
- **Fallback**: When regex patterns return `"generic"` and similarity > 0.2, vector match provides the claim category
- **Impossibility detection**: High similarity to violation references flags claims even without regex match
- **Confidence boost/penalty**: Vector agreement with regex result increases confidence; disagreement decreases it

**Measured reach — read before changing anything here.** The F-006 investigation
(see `FALSIFICATION_LOG.md`, entries F-006 through F-009) established:

- The vectorizer generalizes to **near-verbatim paraphrase only**. On novel
  phrasing, true-positive and false-positive rates at the 0.2 gate are both
  `0.00` — the gate is effectively closed, and that is the safest measured
  setting.
- **No threshold separates the classes.** Violation and valid similarity
  distributions overlap almost entirely on held-out phrasing. Best achievable
  balanced accuracy is 0.75–0.80 against a 0.50 coin flip, and every variant at
  its own optimum flags 3–4 of 4 *physics-free* control sentences as violations.
- Per-category thresholds were tested and are **no better** than the global gate.
- `best_label` is not calibrated: the library is 41 violation vs 20 valid
  entries, so out-of-domain text defaults to "violation".
- OOV terms get a *higher* IDF than any in-vocab term while being unable to match
  anything, so scores are deflated in proportion to phrasing novelty (86–91% of
  query magnitude is dead weight on novel input). This is a real defect;
  correcting it in isolation makes discrimination **worse**, so it is
  deliberately unfixed.

Do not retune the threshold, rebalance the library, or "fix" the OOV weighting
without running `benchmarks/vector_gate_probe.jsonl` — outside of
`tests/test_vector_gate.py`, the suite has only **3 distinct cases** that reach
this gate, all far from the boundary, so it cannot detect a bad threshold
(F-008).

**Reference library categories**: `creation_from_nothing`, `output_without_cost`, `perfect_efficiency`, `entropy_reversal`, `infinite_claim`, `perpetual_motion`, `information_violation`, `conservation_statement`, `transfer_claim`

**API**:
```python
from core.vectorizer import match_premise
result = match_premise("power emerges from the void")
result.best_label       # "violation"
result.best_category    # "creation_from_nothing"
result.similarity       # 0.72
result.violation_score  # 0.65
result.valid_score      # 0.08
```

### Verdict System

| Verdict | Score | Meaning |
|---------|-------|---------|
| `CLEAN` | 0.0 | No violations |
| `SUSPECT` | < 0.3 | Minor/uncertain violation |
| `CORRUPTED` | >= 0.3 | Premise fails physics |

### Output Shape

```python
{
    "verdict": "CORRUPTED",
    "score": 0.67,                    # severity-weighted
    "flags": ["first_law_thermodynamics"],
    "reason": "human-readable summary",
    "violations": [
        {
            "law": "first_law_thermodynamics",
            "description": "...",
            "expected": "input (0.0) = output (1.0)",
            "claimed": "delta = 1.0",
            "severity": 0.67,
            "fix_hint": "Specify the input/source..."
        }
    ],
    "applicable_laws": ["first_law_thermodynamics", "second_law_thermodynamics"],
    "confidence": 0.95,               # how sure we are
    "audit": {                         # full trace
        "claim_pattern": "creation_from_nothing",
        "chain": [...],
        "summary": "..."
    }
}
```

## Domain Modules

### Organizational (`domains/organizational.py`)

Checks `OrgClaim` dataclass against 5 constraints:

| Threshold | Value | Meaning |
|-----------|-------|---------|
| `PHI_RESILIENCE_THRESHOLD` | 0.62 | Minimum resilience score |
| `MAX_ENFORCEMENT_RATIO` | 0.30 | >30% enforcement = parasitic |
| `MIN_ADAPTIVE_SLACK` | 0.15 | <15% slack = brittle |
| `MAX_INTERDEPENDENCY_LOAD` | 0.75 | >75% single-point deps = cascade risk |

### Information (`domains/information.py`)

Checks `InfoClaim` dataclass against 4 laws:
- **Landauer's principle** — erasing information has minimum energy cost
- **No-free-lunch** — learning requires data
- **Data processing inequality** — processing cannot increase information
- **Shannon noise bound** — accuracy bounded by noise level

### Thermodynamic Accountability (`domains/thermodynamic_accountability.py`)

Checks `TAFClaim` dataclass — same shape as `OrgClaim` / `InfoClaim`:
- **Energy balance** — outflow must be accounted for by inflow
- **Friction ratio** — overhead as a fraction of useful work
- **Distance to collapse** — 1.2 / 1.4 / 1.6 × E_in ladder
- **Parasitic debt** — extraction without return flow
- **Narrative cover** — justification mass vs. measured flow

Anchors the `organizational.py` thresholds: enforcement / slack / cascade limits
trace back to TAF friction-ratio and collapse-threshold physics. Also drives the
`energy_extraction_without_return` claim pattern in the core pipeline.

### Extended Modules (standalone, not wired into main pipeline)

- **Contrapositive Tester** (`core/contrapositive_tester.py`) — Four-corner semantic validation
- **Conditional Verdict** (`core/conditional_verdict.py`) — Scope-conditional truth boundaries

## Top-Level Modules

Kept at the repository root because their own docstrings document the root import
path (`from trait_waveform_validator import ...`) as the public API. That path is
stable — do not relocate them without updating the docstrings and any downstream
copies.

- **`ai_interface.py`** — `audit(input, mode="auto")`. Auto-routes by input shape
  (str → premise, list → corpus, dict → domain module), catches all exceptions at
  the boundary, returns one envelope: `mode`, `verdict`, `native_verdict`, `score`,
  `flags`, `summary`, `details`, `error`. Monoculture GREEN/YELLOW/RED is normalized
  into CLEAN/SUSPECT/CORRUPTED with the original kept as `native_verdict`.
- **`monoculture_detector.py`** — grades a corpus GREEN/YELLOW/RED on seven axes
  (lexical entropy, structural diversity, causal/timescale/substrate coverage,
  failure-mode awareness, lineage diversity). All thresholds published and
  overridable. Distinguishes variance collapse from legitimate attractor convergence.
- **`trait_waveform_validator.py`** — phase-space anti-bias framework. Rejects
  scalar group comparisons as a *type* error unless all required axes are
  specified. Plugs in via `PhysicsGuardAdapter`.
- **`cognition_state_surface.py`** — add-on. Task-specific cognition surfaces;
  enforces both axis and task specification.
- **`environment_expression_surface.py`** — add-on. Developmental-loading axes, plus
  `compare_within_vs_across_environment()` as a confounding diagnostic.
- **`knowledge_transmission_substrate.py`** — companion. Models transmission as
  encodable CONTENT + non-encodable developmental SUBSTRATE.

## Code Conventions

- **No external dependencies** — stdlib only (`sys`, `re`, `math`, `json`, `collections`, `dataclasses`, `typing`, `argparse`)
- **snake_case** for all functions and variables
- **Compact single-line if/elif/else** is the project style (E701 ignored in ruff)
- **Pattern-first design** — claim patterns drive constraint generation, not keywords
- **Real math** — lhs and rhs differ when physics is violated; delta measures violation magnitude
- **Structured output** — `Verdict`/`Violation` dataclasses with `.to_dict()` for JSON
- **Backward compatible** — `run = check` alias preserved for old callers

## Tooling

Defined in `pyproject.toml`:
- **pytest**: test discovery in `tests/`, 139 tests
- **ruff**: Python 3.9 target, 120 char lines, E/F/W/I rules (E701 ignored)
- **mypy**: Python 3.9, warns on `Any` returns
- **CI** (`.github/workflows/ci.yml`): ruff + pytest on Python 3.9, 3.11, 3.12

## Testing

```bash
pytest tests/ -v                                  # all 139 tests
pytest tests/test_premises.py -v                  # core pipeline (53)
pytest tests/test_benchmarks.py -v                # benchmark corpus (45)
pytest tests/test_vectorizer.py -v                # vector similarity (13)
pytest tests/test_thermodynamic_accountability.py # TAF (9)
pytest tests/test_organizational.py               # org module (6)
pytest tests/test_information.py                  # info module (4)
```

Test categories:
- **Verdict correctness** — parametrized premises with expected verdicts
- **Claim pattern detection** — verifies regex patterns match correctly
- **Dismissal handling** — denied violations ("you cannot get something from nothing") return CLEAN
- **Real constraint math** — checks that deltas are nonzero for violations, zero for valid claims
- **Output structure** — verifies all required fields present
- **Adversarial cases** — tricky wordings, edge cases, empty input
- **Batch API** — `check_batch()` returns correct results
- **Benchmark regression** — every case in `benchmarks/cases.jsonl` asserted on verdict
  and optional `expected_pattern`

`benchmarks/cases.jsonl` is a **seed corpus, not authoritative training data**.
Known-failure cases must stay visible in it rather than be silenced.
