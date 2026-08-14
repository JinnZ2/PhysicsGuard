# PhysicsGuard

Physics-grounded logic verification. Detects corrupted or adversarial premises by
translating natural language claims into physical constraint equations and
checking them against conservation laws. When the math doesn't balance, the
premise is flagged.

- **License**: CC0 1.0 Universal — public domain
- **Dependencies**: none. Python 3.9+ stdlib only
- **Tests**: 130, all passing

```bash
python main.py "Energy can be created from nothing"
```

```
[PhysicsGuard]
Verdict       : CORRUPTED
Score         : 0.667
Confidence    : 99%
Flags         : ['first_law_thermodynamics']
```

## Why the log matters as much as the code

This project is built by running the loop explicitly:

> hypothesize → run → result → falsified → edit the claim → search for unknowns → rerun

Every superseded design is kept, not deleted. Two artifacts carry that record:

- **[`FALSIFICATION_LOG.md`](FALSIFICATION_LOG.md)** — what was claimed, what
  happened when it ran, what the claim became. Six entries so far, including one
  claim that is **currently open and unresolved** (F-006).
- **[`legacy/`](legacy/)** — the superseded artifacts themselves, moved with
  `git mv` so `git log --follow` still works.

Read the log before proposing a simplification. Several obvious-looking
approaches — keyword matching, count-based scoring — are in there with the
evidence that killed them.

## Install

```bash
git clone https://github.com/JinnZ2/PhysicsGuard
cd PhysicsGuard
```

No install step. No dependencies.

## Usage

### CLI

```bash
python main.py "Energy can be created from nothing"    # single premise
python main.py --json "Infinite power from a magnet"   # JSON for machine use
python main.py --batch premises.txt                    # one premise per line
python main.py --batch --json premises.txt
echo "claim" | python main.py --pipe                   # stdin
python main.py                                         # interactive
```

### Python — core pipeline

```python
from main import check, check_batch

result = check("Energy can be created from nothing")
# {"verdict": "CORRUPTED", "score": 0.67, "flags": [...], "confidence": 0.99, ...}

results = check_batch(["claim one", "claim two"])
```

### Python — unified entry point

`audit()` auto-routes by input shape and never raises; every failure comes back
as a normal result with `mode="error"`.

```python
from ai_interface import audit

audit("Energy can be created from nothing")        # str  → premise
audit(["doc one", "doc two", "doc three"])         # list → corpus / monoculture
audit({"domain": "organizational", ...})           # dict → domain module
audit(x, mode="premise")                           # force a mode
```

Returns the same envelope regardless of route: `mode`, `verdict`,
`native_verdict`, `score`, `flags`, `summary`, `details`, `error`.

## Verdicts

| Verdict | Score | Meaning |
|---------|-------|---------|
| `CLEAN` | 0.0 | No violations |
| `SUSPECT` | < 0.3 | Minor or uncertain violation |
| `CORRUPTED` | >= 0.3 | Premise fails physics |

Score is severity-weighted, not a violation count — see **F-003** in the log for
why the original count ratio was replaced, and why the threshold moved from 0.5.

## Repository layout

```
PhysicsGuard/
├── main.py                     # check(), check_batch(), CLI
├── ai_interface.py             # audit() — unified, exception-safe entry point
│
├── core/                       # the premise pipeline
│   ├── premise_parser.py       # regex claim patterns + dismissal detection
│   ├── constraint_mapper.py    # claims → conservation equations
│   ├── conservation_checker.py # delta math + severity scoring
│   ├── flag_engine.py          # severity-weighted verdicts, audit trail
│   ├── vectorizer.py           # TF-IDF fallback for rephrasings
│   ├── contrapositive_tester.py  # four-corner validation (standalone)
│   └── conditional_verdict.py    # scope-conditional verdicts (standalone)
│
├── domains/                    # structured-claim checkers
│   ├── organizational.py       # org structure constraints
│   ├── information.py          # Landauer, Shannon, no-free-lunch
│   └── thermodynamic_accountability.py  # TAF energy accounting
│
├── monoculture_detector.py     # variance-collapse audit across 7 axes
│
├── trait_waveform_validator.py        # phase-space anti-bias framework
│   ├── cognition_state_surface.py         # add-on: task-specific cognition
│   ├── environment_expression_surface.py  # add-on: developmental loading
│   └── knowledge_transmission_substrate.py # companion: content + substrate
│
├── benchmarks/                 # 26-case regression corpus (cases.jsonl)
├── tests/                      # 130 tests
├── legacy/                     # superseded artifacts — see legacy/README.md
└── FALSIFICATION_LOG.md        # the hypothesize → run → falsify record
```

The four phase-space modules are top-level by design: their own docstrings
document `from trait_waveform_validator import ...` as the public import path,
and that path is stable.

## The pipeline

```
premise (str)
  → parse_premise()      regex claim patterns, dismissal detection, vector fallback
  → map_to_constraints() real equations — lhs != rhs when physics is violated
  → check_conservation() delta = abs(lhs - rhs), sigmoid severity
  → score_and_flag()     severity-weighted verdict + full audit trail
```

Eight claim patterns drive constraint generation: `creation_from_nothing`,
`infinite_claim`, `output_without_cost`, `perfect_efficiency`, `entropy_reversal`,
`perpetual_motion`, `energy_extraction_without_return`, plus the valid-physics
patterns `conservation_statement` and `transfer_claim`.

**Dismissal detection runs first.** "You cannot get something from nothing"
matches `creation_from_nothing` structurally but *denies* the violation — it is
correct physics and returns CLEAN. See **F-005**.

## Testing

```bash
pytest tests/ -v            # 130 tests
ruff check .
```

| File | Tests | Covers |
|------|------:|--------|
| `test_premises.py` | 53 | Core pipeline, patterns, dismissals, adversarial cases |
| `test_benchmarks.py` | 45 | The 26-case corpus in `benchmarks/cases.jsonl` |
| `test_vectorizer.py` | 13 | TF-IDF similarity and fallback |
| `test_thermodynamic_accountability.py` | 9 | TAF energy accounting |
| `test_organizational.py` | 6 | Org constraint thresholds |
| `test_information.py` | 4 | Information conservation laws |

The benchmark corpus is a **seed corpus, not authoritative training data**.
Known-failure cases must stay visible rather than be silenced — see
`benchmarks/README.md`.

## Contributing

The one rule specific to this repo: **when you supersede something, log it.**

1. `git mv` the old artifact into `legacy/`.
2. Add an entry to `FALSIFICATION_LOG.md` — claim, run, verbatim result, edited
   claim. Do not soften the result.
3. If you found an unknown you did not resolve, record it as `OPEN`. An
   unresolved unknown on the record beats a tidy repo.

## License

CC0 1.0 Universal. Public domain. Free to use, fork, extend.
