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
├── core/
│   ├── premise_parser.py          # Pattern-based semantic claim extraction
│   ├── constraint_mapper.py       # Maps claims → real conservation equations
│   ├── conservation_checker.py    # Validates constraints with actual delta math
│   ├── flag_engine.py             # Severity-weighted scoring, Verdict/Violation dataclasses
│   ├── contrapositive_tester.py   # Four-corner semantic validation
│   └── conditional_verdict.py     # Scope-conditional verdict layer (v1.1)
├── domains/
│   ├── organizational.py          # Org structure constraint checking (v2)
│   └── information.py             # Information conservation (Landauer, Shannon, NFL)
├── tests/
│   ├── test_premises.py           # Core pipeline tests (42 cases)
│   ├── test_organizational.py     # Organizational module tests
│   └── test_information.py        # Information conservation tests
├── pyproject.toml                 # Project metadata, pytest/ruff/mypy config
├── README.md                      # Original specification document
├── PLAN.md                        # Architecture evolution plan
├── LICENSE                        # CC0 1.0 Universal
└── .gitignore
```

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
- Confidence score based on claim pattern specificity
- Full audit trail with fix hints

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

### Extended Modules (standalone, not wired into main pipeline)

- **Contrapositive Tester** (`core/contrapositive_tester.py`) — Four-corner semantic validation
- **Conditional Verdict** (`core/conditional_verdict.py`) — Scope-conditional truth boundaries

## Code Conventions

- **No external dependencies** — stdlib only (`sys`, `re`, `math`, `json`, `dataclasses`, `typing`, `argparse`)
- **snake_case** for all functions and variables
- **Compact single-line if/elif/else** is the project style (E701 ignored in ruff)
- **Pattern-first design** — claim patterns drive constraint generation, not keywords
- **Real math** — lhs and rhs differ when physics is violated; delta measures violation magnitude
- **Structured output** — `Verdict`/`Violation` dataclasses with `.to_dict()` for JSON
- **Backward compatible** — `run = check` alias preserved for old callers

## Tooling

Defined in `pyproject.toml`:
- **pytest**: test discovery in `tests/`, 42 tests
- **ruff**: Python 3.9 target, 120 char lines, E/F/W/I rules (E701 ignored)
- **mypy**: Python 3.9, warns on `Any` returns

## Testing

```bash
pytest tests/ -v          # all 42 tests
pytest tests/test_premises.py -v      # core pipeline (30 tests)
pytest tests/test_organizational.py   # org module (6 tests)
pytest tests/test_information.py      # info module (4 tests)
```

Test categories:
- **Verdict correctness** — parametrized premises with expected verdicts
- **Claim pattern detection** — verifies regex patterns match correctly
- **Real constraint math** — checks that deltas are nonzero for violations, zero for valid claims
- **Output structure** — verifies all required fields present
- **Adversarial cases** — tricky wordings, edge cases, empty input
- **Batch API** — `check_batch()` returns correct results
