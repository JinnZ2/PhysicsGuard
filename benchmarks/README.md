# PhysicsGuard Benchmarks

A **seed corpus**, not ground truth. Each line of `cases.jsonl` is one
structured test case covering a specific constraint the system is supposed
to enforce. The file exists to:

1. Pin behaviour so refactors that silently change verdicts break `tests/test_benchmarks.py`.
2. Document what the system can and cannot catch, case by case.
3. Give anyone fine-tuning or evaluating a model a small, curated,
   provenance-tagged starting point they can extend.

## Framing warning

This is **not a training dataset in the modern-ML sense**. It is a few
dozen hand-curated cases with known provenance. Treating it as
authoritative labelled data for a general-purpose classifier will
produce a model that overfits to the phrasings here and misses the
underlying physics. Use it as a regression harness and a seed, not as
ground truth at scale.

## Schema

Each line is a single JSON object:

```jsonc
{
  "id":               "unique-string-id",
  "domain":           "premise" | "corpus" |
                      "organizational" | "information" | "thermodynamic",
  "input":            <string | list[str] | dict> ,   // matches the mode
  "expected_verdict": "CLEAN" | "SUSPECT" | "CORRUPTED",
  "expected_pattern": "optional — for premise mode only",
  "provenance":       "where this case comes from / why it is here",
  "notes":            "short human-readable explanation"
}
```

Verdicts use the normalized vocabulary from `ai_interface.audit()`:
`GREEN/YELLOW/RED` from the monoculture detector are normalized to
`CLEAN/SUSPECT/CORRUPTED`.

## Current coverage

| Domain           | Cases |
|------------------|-------|
| premise (physics)     | 11 |
| premise (dismissal)   |  3 |
| premise (extraction)  |  3 |
| organizational        |  2 |
| information           |  2 |
| thermodynamic         |  3 |
| corpus (monoculture)  |  2 |
| **total**             | **26** |

## Adding a case

1. Pick the lowest integer suffix not already used for your domain.
2. Include a `provenance` field that cites the module or reference the
   case exercises (e.g. `"TAF integration — soil depletion"`).
3. Run `pytest tests/test_benchmarks.py -v` and confirm the new case passes.
4. If the case intentionally documents a **known failure** of the system,
   mark it with `"expected_verdict": "SUSPECT"` and a `"notes"` field
   explaining what the system misses. Do not add cases that silently
   fail — they must be visible in the harness.

## Rerunning

```bash
pytest tests/test_benchmarks.py -v
```

Failures mean either the code changed the semantics of a constraint
(intentional — update the case) or a regression (unintentional — fix
the code).
