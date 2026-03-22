# PhysicsGuard — Implementation Plan

## Goal

Transform PhysicsGuard from a keyword-matching prototype into a genuinely useful
physics-grounded verification system for AI models, agents, and humans.

## Phase 1: Real Semantic Parsing (premise_parser.py rewrite)

### Problem
Current parser does substring matching against keyword lists. "Power can emerge
spontaneously" passes as CLEAN because "emerge" and "spontaneously" aren't keywords.

### Solution: Pattern-based claim extraction
Instead of keyword lists, use structured claim patterns that capture semantic roles:

```
CLAIM_PATTERNS = [
    # "X can be created/generated/produced from nothing/without Y"
    (r"(\w+) can be (created|generated|produced|made).*(?:from nothing|without)", "creation_from_nothing"),

    # "X produces/generates Y without/with no Z"
    (r"(produce|generate|extract|create)\w*.*(?:without|with no|no)\s+(\w+)", "output_without_cost"),

    # "infinite/unlimited/perpetual X"
    (r"(infinite|unlimited|perpetual|boundless)\s+(\w+)", "infinite_claim"),

    # "X cannot be destroyed/created" (conservation statement)
    (r"(\w+)\s+cannot be (destroyed|created|lost)", "conservation_claim"),

    # "X from Y to Z" (transfer statement)
    (r"(\w+)\s+(?:from|moves from)\s+(\w+)\s+to\s+(\w+)", "transfer_claim"),
]
```

This captures the *structure* of claims, not just keyword presence.

### New parsed output shape:
```python
{
    "raw": str,
    "type": "thermodynamic" | "mass_balance" | "information" | "unknown",
    "claim_pattern": "creation_from_nothing" | "output_without_cost" | ...,
    "subject": str,          # what's being claimed about
    "action": str,           # what's happening
    "cost_mentioned": bool,  # is there an acknowledged cost/input?
    "cost_negated": bool,    # is the cost explicitly denied?
    "magnitude": list[float],
    "is_conservation_statement": bool,  # "X cannot be destroyed" = valid physics
    "is_impossibility_claim": bool,     # "infinite power" = red flag
}
```

## Phase 2: Real Constraint Math (constraint_mapper.py rewrite)

### Problem
Current system sets lhs=rhs always, then uses a boolean `corrupted` flag. The
"physics equations" are decorative.

### Solution: Model actual conservation equations

```python
# First Law: Energy In = Energy Out + Work + Losses
# If claim says "create energy from nothing": input=0, output>0 → violation
def _first_law(parsed):
    if parsed["claim_pattern"] == "creation_from_nothing":
        return {"law": "first_law", "lhs": 0.0, "rhs": 1.0, ...}  # real imbalance
    if parsed["claim_pattern"] == "transfer_claim":
        return {"law": "first_law", "lhs": 1.0, "rhs": 1.0, ...}  # balanced
    if parsed["is_impossibility_claim"]:
        return {"law": "first_law", "lhs": 0.0, "rhs": float('inf'), ...}

# Second Law: Entropy of isolated system never decreases
# If claim says "extract X without entropy cost": entropy_delta < 0 → violation
def _second_law(parsed):
    if parsed["claim_pattern"] == "output_without_cost":
        return {"law": "second_law", "entropy_delta": -1.0, ...}  # entropy decrease = violation
    if parsed["cost_mentioned"] and not parsed["cost_negated"]:
        return {"law": "second_law", "entropy_delta": 0.0, ...}   # balanced
```

The key change: **lhs and rhs actually differ when claims are physically impossible**.
The conservation_checker then does real math, not boolean passthrough.

## Phase 3: Domain Modules

### 3a: Information Conservation (new: domains/information.py)

Claims about information also follow conservation-like laws:
- Information cannot be created from nothing (no free lunch)
- Lossy processes are irreversible (entropy)
- Signal cannot exceed channel capacity (Shannon)

Useful for AI: detecting claims like "this model learns without data" or
"lossless compression below entropy limit".

### 3b: Wire up existing domains

- `domains/thermodynamic.py` — Implement with real thermodynamic constraint checks
- `domains/mass_balance.py` — Resource flow accounting with input/output tracking
- `domains/organizational.py` — Already implemented, needs integration with main pipeline

## Phase 4: Structured Output for AI Consumption

### Problem
Current output is a flat dict with string reasons. Not machine-actionable.

### Solution: Rich structured verdicts

```python
@dataclass
class Verdict:
    premise: str
    status: str                    # CLEAN | SUSPECT | CORRUPTED
    score: float                   # 0.0-1.0
    violations: list[Violation]    # specific laws violated
    suggestion: str                # how to fix the premise
    confidence: float              # how confident the system is
    applicable_laws: list[str]     # which physical laws were checked

@dataclass
class Violation:
    law: str                       # e.g. "first_law_thermodynamics"
    description: str               # human-readable
    expected: str                  # what physics requires
    claimed: str                   # what the premise claims
    severity: float                # 0.0-1.0
```

### JSON API mode
```bash
python main.py --json "Energy can be created from nothing"
```
Returns structured JSON for programmatic consumption by other AI systems.

## Phase 5: Batch & Integration Modes

### Batch checking
```bash
python main.py --batch premises.txt
python main.py --batch --json premises.txt  # JSON lines output
```

### Python API for AI integration
```python
from physicsguard import check, check_batch

result = check("Energy can be created from nothing")
results = check_batch(["claim1", "claim2", "claim3"])
```

### Stdin pipe mode for agent chains
```bash
echo "claim1\nclaim2" | python main.py --pipe
```

## Implementation Order

1. Rewrite premise_parser.py with pattern-based extraction
2. Rewrite constraint_mapper.py with real conservation math
3. Update flag_engine.py with structured Verdict/Violation dataclasses
4. Add --json output mode to main.py
5. Add domains/information.py
6. Implement domains/thermodynamic.py and domains/mass_balance.py
7. Wire conditional_verdict.py and contrapositive_tester.py into main pipeline
8. Add batch/pipe modes
9. Expand test suite with adversarial/edge cases
10. Update CLAUDE.md
