# CLAUDE.md — PhysicsGuard

## Project Overview

PhysicsGuard is a physics-grounded logic verification system that detects corrupted or adversarial premises by translating natural language claims into physical constraint equations and checking them against conservation laws. If the math doesn't close, the premise is flagged.

- **License**: CC0 1.0 Universal (Public Domain)
- **Language**: Python 3 (standard library only — no external dependencies)
- **Status**: Specification/design phase — all module code is currently in `README.md`, not yet extracted into separate files

## Repository Structure

```
PhysicsGuard/
├── README.md              # Full specification with embedded source code for all modules
├── LICENSE                # CC0 1.0 Universal
└── CLAUDE.md              # This file
```

### Planned Module Layout (defined in README.md)

```
core/
├── premise_parser.py        # Extract claims as symbolic logic from natural language
├── constraint_mapper.py     # Translate claims to physical constraint equations
├── conservation_checker.py  # Validate constraints against conservation laws
├── flag_engine.py           # Contradiction scoring, audit trails, verdicts
├── contrapositive_tester.py # Four-corner semantic validation
└── conditional_verdict.py   # Scope-conditional verdict layer (v1.1)
domains/
├── thermodynamic.py         # Energy/heat/entropy checks
├── mass_balance.py          # Resource flow accounting
├── geometric.py             # Spatial constraint verification
└── organizational.py        # Organizational structure constraint checking (v2)
tests/
└── test_premises.py         # Test suite
main.py                      # Single command entry point
```

## Architecture

The processing pipeline follows four stages:

1. **Premise Parser** — Extracts claim type (thermodynamic/mass_balance/unknown), direction, magnitude, negation count, and keywords from natural language input
2. **Constraint Mapper** — Translates parsed claims into physical constraint equations (First Law, Second Law, mass conservation, or generic balance)
3. **Conservation Checker** — Validates each constraint; calculates delta between LHS and RHS; determines pass/fail based on tolerance and corruption flags
4. **Flag Engine** — Scores contradictions (0.0–1.0) and produces verdicts

### Verdict System

| Verdict     | Score       | Meaning                      |
|-------------|-------------|------------------------------|
| `CLEAN`     | 0.0         | No violations detected       |
| `SUSPECT`   | < 0.5       | Partial contradiction        |
| `CORRUPTED` | >= 0.5      | Premise fails physics        |

### Extended Modules

- **Contrapositive Tester** — Tests claim, negation, opposite, and opposite-negation (four corners) to surface scope boundaries
- **Conditional Verdict (v1.1)** — Replaces binary verdicts with scope-conditional truth boundaries using `ScopeCondition` dataclasses and predefined scope libraries (hierarchy, distributed, patriarchy, nomadic egalitarian)
- **Organizational Module (v2)** — Checks organizational structure claims against resilience physics, enforcement energy cost, adaptive capacity, and cascade failure risk using configurable thresholds

## Commands

### Run

```bash
python main.py "Energy can be created from nothing"
```

Or interactive mode:
```bash
python main.py
```

### Test

```bash
python tests/test_premises.py
```

## Key Conventions

- **No external dependencies** — Uses only Python standard library (`sys`, `re`, `dataclasses`, `typing`)
- **Snake_case** throughout for functions and variables
- **4-space indentation**
- **Dict-based return values** for core pipeline functions; `@dataclass` for domain modules (v2)
- **Threshold constants** are defined at module level with descriptive names (e.g., `PHI_RESILIENCE_THRESHOLD = 0.62`)
- Each constraint is a dict with keys: `law`, `lhs`, `rhs`, `tolerance`, `corrupted`
- Each check result includes: `law`, `passed`, `delta`, `corrupted`, `detail`
- Verdicts include audit trails with fix hints

## Test Cases

Expected behavior for the core test suite:

| Premise | Expected Verdict |
|---------|-----------------|
| "Energy can be created from nothing without any heat loss" | CORRUPTED |
| "Extracting resources produces output with no entropy cost" | CORRUPTED |
| "Heat transfer moves energy from hot to cold regions" | CLEAN |
| "Mass cannot be destroyed in a closed system" | CLEAN |
| "You can generate infinite power without consuming anything" | CORRUPTED |

## Development Notes

- The README serves as the canonical specification — all module code is embedded there
- When implementing modules as separate files, extract code directly from README.md sections (each section is prefixed with a comment like `# physicsguard/core/premise_parser.py`)
- The `flag_engine.py` has two versions in the README: a simple v1 and an enhanced version with audit trails — use the enhanced version
- The organizational module uses four constraint thresholds: resilience (0.62 phi), enforcement (30%), adaptive slack (15%), interdependency load (75%)
