# CLAUDE.md — PhysicsGuard

## Project Overview

PhysicsGuard is a physics-grounded logic verification system that detects corrupted or adversarial premises by translating natural language claims into physical constraint equations and checking them against conservation laws. If the math doesn't close, the premise is flagged.

- **License**: CC0 1.0 Universal (Public Domain)
- **Language**: Python 3.9+ (standard library only — no external dependencies)
- **Repository**: github.com/JinnZ2/PhysicsGuard

## Repository Structure

```
PhysicsGuard/
├── main.py                        # Entry point — run(premise) orchestrates the pipeline
├── core/
│   ├── premise_parser.py          # NLP claim extraction: type, direction, magnitude, keywords
│   ├── constraint_mapper.py       # Maps parsed claims → physical constraint equations
│   ├── conservation_checker.py    # Validates constraints against conservation laws
│   ├── flag_engine.py             # Contradiction scoring, audit trails, verdicts
│   ├── contrapositive_tester.py   # Four-corner semantic validation
│   └── conditional_verdict.py     # Scope-conditional verdict layer (v1.1)
├── domains/
│   └── organizational.py          # Org structure constraint checking (v2)
├── tests/
│   ├── test_premises.py           # Core pipeline tests (parametrized)
│   └── test_organizational.py     # Organizational module tests
├── pyproject.toml                 # Project metadata, pytest/ruff/mypy config
├── README.md                      # Full specification and design document
├── LICENSE                        # CC0 1.0 Universal
└── .gitignore
```

## Commands

```bash
# Run a single premise check
python main.py "Energy can be created from nothing"

# Interactive mode
python main.py

# Run tests
pytest tests/ -v

# Lint
ruff check .

# Auto-fix lint issues
ruff check --fix .
```

## Architecture

### Core Pipeline (4 stages)

```
premise (str) → parse_premise() → map_to_constraints() → check_conservation() → score_and_flag() → verdict (dict)
```

1. **Premise Parser** (`core/premise_parser.py`) — Extracts claim type (`thermodynamic`/`mass_balance`/`unknown`), direction, magnitude, negation count, keywords, and negated keywords using stem matching
2. **Constraint Mapper** (`core/constraint_mapper.py`) — Translates parsed claims into constraint dicts with `{law, lhs, rhs, tolerance, corrupted}`. Handles First Law, Second Law (with negation-aware entropy detection), mass conservation, and generic balance
3. **Conservation Checker** (`core/conservation_checker.py`) — Validates each constraint: `passed = (delta <= tolerance) and not corrupted`
4. **Flag Engine** (`core/flag_engine.py`) — Scores: `failed_count / total`. Produces verdict with full audit trail and fix hints

### Verdict System

| Verdict     | Score    | Meaning                |
|-------------|----------|------------------------|
| `CLEAN`     | 0.0      | No violations          |
| `SUSPECT`   | < 0.5    | Partial contradiction  |
| `CORRUPTED` | >= 0.5   | Premise fails physics  |

### Extended Modules

- **Contrapositive Tester** (`core/contrapositive_tester.py`) — Tests claim, negation, opposite, and opposite-negation (four corners) to surface scope boundaries
- **Conditional Verdict v1.1** (`core/conditional_verdict.py`) — Scope-conditional truth boundaries using `ScopeCondition` dataclasses. Predefined scope libraries: `hierarchy_works`, `distributed_works`, `patriarchy_works`, `nomadic_egalitarian_works`
- **Organizational Module v2** (`domains/organizational.py`) — Checks `OrgClaim` dataclass against 5 constraints: resilience, enforcement cost, adaptive slack, cascade risk, justification validity

### Key Data Shapes

**Constraint dict** (internal):
```python
{"law": str, "lhs": float, "rhs": float, "tolerance": float, "corrupted": bool}
```

**Verdict dict** (returned by `run()`):
```python
{"verdict": str, "score": float, "flags": list[str], "reason": str, "details": list, "audit": dict|None}
```

**OrgConstraintResult** (dataclass, returned by `check_organization()`):
```python
OrgConstraintResult(claim, resilience_score, enforcement_waste, cascade_risk, verdict, flags, audit)
```

## Code Conventions

- **No external dependencies** — stdlib only (`sys`, `re`, `dataclasses`, `typing`)
- **snake_case** for all functions and variables
- **Compact single-line if/elif/else** is the project style (E701 ignored in ruff config)
- **Dict returns** for core pipeline; **`@dataclass`** for domain modules
- **Threshold constants** at module level with descriptive names (e.g., `PHI_RESILIENCE_THRESHOLD = 0.62`)
- **Stem matching** for keyword extraction — `"created"` matches keyword `"create"`, `"extracting"` matches `"extract"`
- **Negation-aware** keyword tracking — `negated_kw` field in parsed claims detects words like "no", "without" preceding keywords within 3-word window

## Tooling Configuration

Defined in `pyproject.toml`:
- **pytest**: test discovery in `tests/`
- **ruff**: Python 3.9 target, 120 char line length, E/F/W/I rules (E701 ignored)
- **mypy**: Python 3.9, warns on `Any` returns

## Organizational Module Thresholds

| Constant                    | Value | Meaning                                         |
|-----------------------------|-------|-------------------------------------------------|
| `PHI_RESILIENCE_THRESHOLD`  | 0.62  | Minimum resilience score (from Urban Resilience) |
| `MAX_ENFORCEMENT_RATIO`     | 0.30  | >30% resources on enforcement = parasitic        |
| `MIN_ADAPTIVE_SLACK`        | 0.15  | <15% slack = brittle                             |
| `MAX_INTERDEPENDENCY_LOAD`  | 0.75  | >75% single-point deps = cascade risk            |

## Known Design Decisions

- The README contains the original specification with inline code. The actual `.py` files are the canonical source of truth
- Keyword matching uses stem prefix comparison (not regex or NLP), keeping it dependency-free but imprecise on edge cases
- The `negated_kw` feature uses a 3-word lookahead window from negation words — covers common patterns like "no entropy cost" and "without any heat loss"
- Domain modules (`domains/`) are separate from core — new physics domains can be added without touching the core pipeline
