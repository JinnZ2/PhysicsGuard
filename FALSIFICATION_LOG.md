# Falsification Log

The record of what PhysicsGuard claimed, what happened when it was run, and what
the claim became afterward.

This file exists because **precedence carries**. A claim that was falsified is not
noise to be deleted — it is the evidence that constrains the next claim. Without
the record, the same falsified hypothesis gets re-proposed, re-implemented, and
re-falsified by whoever comes next (human or model). Deleting a superseded design
destroys the only proof that the design does not work.

## The loop

```
hypothesize  →  run  →  result  →  falsified?  →  edit the claim
                                       │              ↓
                                       │        search for unknowns
                                       │              ↓
                                       └──────────  rerun
```

Every entry below is one turn of that loop.

## How to add an entry

When something is superseded, do not silently overwrite it. Record:

| Field | Meaning |
|-------|---------|
| **Claim** | What was asserted, in the form it was asserted |
| **Run** | The concrete input that tested it — reproducible, copy-pasteable |
| **Result** | What actually came out. Verbatim, not paraphrased |
| **Status** | `FALSIFIED` / `HOLDS` / `OPEN` / `RESOLVED` (investigated; outcome recorded, no change shipped) |
| **Edited claim** | What replaced it, or `—` if nothing yet |
| **Where it went** | Commit, and `legacy/` path if the artifact was preserved |

Rules:

1. **Do not delete a falsified claim.** Mark it and keep it.
2. **Do not soften a result.** If it returned CLEAN when the commit message said
   CORRUPTED, write CLEAN.
3. **`OPEN` is a valid status.** An unknown you have not resolved is more useful
   recorded than tidied away.
4. **Re-run old entries when the pipeline changes.** A `HOLDS` can become a
   `FALSIFIED` later. That is the point.
5. **A negative result is a result.** If you investigate and every candidate fix
   measures worse than doing nothing, that is worth more than a plausible change.
   Record it and ship nothing — see F-007.

## Provenance of these entries

Every historical result below was **re-run against a checkout of the commit in
question**, not copied from a commit message. Method:

```bash
git worktree add -d /tmp/probe <commit>
cd /tmp/probe && python -c "from main import check; print(check('...'))"
```

This matters: **F-006 exists only because a commit message was checked against
the code it described and did not survive.** Commit messages are claims. Treat
them as claims.

---

## F-001 — Keyword matching detects physics violations

- **Claim** (initial commit, `legacy/v1_specification.md`): substring matching
  against `ENERGY_KEYWORDS` / `MASS_KEYWORDS` / `FLOW_KEYWORDS` is sufficient to
  identify corrupted premises.
- **Run**: `check("Power can emerge spontaneously")` at `b3f06e6`
- **Result**: `CLEAN`, score `0.00`. Neither "emerge" nor "spontaneously" was in
  any keyword list, so no constraint fired. (Control: "Energy can be created from
  nothing" → `CORRUPTED 0.50` at the same commit — the system worked only for
  premises using its own vocabulary.)
- **Status**: **FALSIFIED**
- **Edited claim**: claim *structure* is the detectable signal, not vocabulary.
  Replaced keyword lists with regex claim patterns capturing semantic roles
  (`creation_from_nothing`, `output_without_cost`, `infinite_claim`, …).
- **Where it went**: falsification documented in `legacy/PLAN.md` § Phase 1;
  fix in `92cefb1`; v1 parser preserved in `legacy/v1_specification.md`.
- **Re-run today**: `CORRUPTED 0.67`, pattern `creation_from_nothing`. Fix holds.

## F-002 — Constraint equations were decorative

- **Claim** (v1 `constraint_mapper.py`): the pipeline "checks whether the math
  closes."
- **Run**: inspect `_first_law()` in `legacy/v1_specification.md`.
- **Result**: `lhs = mag * direction_factor` and `rhs = mag * direction_factor` —
  **identical by construction**. `delta = abs(lhs - rhs)` was therefore always
  `0.0`. Every verdict was actually decided by a separate boolean
  `"corrupted": "create" in keywords`. The conservation math was ornamental; the
  keyword check was doing all the work.
- **Status**: **FALSIFIED** — the system did not do the thing it described.
- **Edited claim**: `lhs` and `rhs` must genuinely differ when physics is
  violated. `creation_from_nothing → lhs=0.0, rhs=1.0`;
  `infinite_claim → lhs=1.0, rhs=inf`. `delta` now measures violation magnitude.
- **Where it went**: `92cefb1`.

## F-003 — Violation count is a good severity score

- **Claim** (v1 `flag_engine.py`): `score = len(failed) / len(total)`, with
  `SUSPECT < 0.5`, `CORRUPTED >= 0.5`.
- **Run**: `check("Energy can be created from nothing")` at `b3f06e6` — a premise
  generating two constraints where one fails.
- **Result**: score exactly `0.50`, regardless of whether the failure was a
  rounding imbalance or a claim of infinite free energy. The score carried no magnitude
  information — it was a ratio of how many equations were emitted.
- **Status**: **FALSIFIED**
- **Edited claim**: score = mean *severity* across constraints, severity computed
  from real deltas via sigmoid normalization. Thresholds retuned to
  `SUSPECT < 0.3`, `CORRUPTED >= 0.3` because severity-weighted scores distribute
  differently than count ratios.
- **Where it went**: `92cefb1`. Note the threshold change: v1 docs saying 0.5 are
  superseded, and the v1 numbers survive in `legacy/v1_specification.md`.

## F-004 — Regex patterns cover rephrasings

- **Claim** (post-`92cefb1`): eight structural regex patterns catch violations
  regardless of wording.
- **Run**: `check("output appears with no source energy")`
- **Result**: `CLEAN`, pattern `generic`. The claim structure was present but the
  surface form matched no regex.
- **Status**: **FALSIFIED**
- **Edited claim**: add a TF-IDF + cosine-similarity fallback over a ~60-entry
  reference library of known violations and valid claims, consulted when regex
  returns `generic`.
- **Where it went**: `c477e6b`, `core/vectorizer.py`.
- **Caveat**: the fix was incomplete for this exact input. See **F-006**.

## F-005 — Matching a violation pattern means the premise asserts it

- **Claim** (post-`c477e6b`): if a premise matches `creation_from_nothing`, the
  premise is corrupted.
- **Run**: `check("You cannot get something from nothing")` and
  `check("It is impossible to build a perpetual motion machine")` at `c477e6b`
- **Result**: both `CORRUPTED 0.67` — matched as `creation_from_nothing` and
  `perpetual_motion` respectively. Both are **correct statements of conservation
  law**. The parser could not distinguish asserting a violation from denying one,
  so textbook physics was flagged as adversarial — a false positive on precisely
  the claims the tool should rate highest.
- **Status**: **FALSIFIED**
- **Edited claim**: a dismissal-detection layer runs *before* pattern
  classification. Seven regex patterns (`cannot`/`never`/`impossible`/
  `no such thing`) reclassify a matched violation as `conservation_statement`,
  and the `is_dismissal` flag also suppresses the vector fallback so the
  similarity path cannot re-flag it.
- **Where it went**: `bbde35f`. 13 regression tests added.
- **Re-run today**: both `CLEAN`. Fix holds.

## F-006 — The vectorizer catches the rephrasings F-004 identified

- **Claim** (`c477e6b` commit message, verbatim): "This catches rephrased
  violations that regex patterns miss: `output appears with no source energy` →
  violation (`output_without_cost`); `results emerge without any data input` →
  violation (`information_violation`)."
- **Run**: those two inputs, against `c477e6b` itself (checked out in a
  detached worktree) and against `HEAD`.
- **Result**:

  | Input | Vector category | Similarity | Verdict |
  |-------|-----------------|-----------:|---------|
  | `output appears with no source energy` | `output_without_cost` | 0.142 | **CLEAN** |
  | `results emerge without any data input` | `information_violation` | 0.163 | **CLEAN** |
  | `heat flows from hot to cold naturally` | `transfer_claim` | 0.892 | CLEAN ✓ |

  The vectorizer **categorized** both correctly but scored them at 0.14–0.16,
  below the `similarity > 0.2` fallback gate in `core/premise_parser.py`. The
  category was computed and then discarded. The verdict never changed.

  The third example in that commit message was accurate. The first two were not —
  and were **never** accurate, including at the commit that asserted them. This
  is not a later regression; the claim was untested when written.
- **Status**: **FALSIFIED** (claim), **RESOLVED** (gap — investigated, no fix
  shipped, see F-007/F-008/F-009)
- **Edited claim**: the vectorizer raises recall on *near-verbatim paraphrases*
  of reference entries only. On genuinely novel phrasing it does not fire at all,
  and **should not be made to** — every operating point that fires on novel
  violations also fires on arbitrary English. F-004 is therefore not
  meaningfully addressed by the vectorizer, and cannot be by tuning it.
- **The three unknowns, resolved**: all three were searched (n=20 held-out probe
  set + 4 physics-free controls, now committed as
  `benchmarks/vector_gate_probe.jsonl`). Every variant was tuned to its *own*
  best operating point before comparison:

  | Variant | Best balanced accuracy | TP | FP | Controls flagged |
  |---------|----------------------:|---:|---:|-----------------:|
  | Current (global gate) | 0.75 @ 0.03 | 10/10 | 5/10 | **3/4** |
  | Drop-OOV terms | 0.70 @ 0.02 | 10/10 | 6/10 | **3/4** |
  | Violation-minus-valid margin | 0.70 @ 0.05 | 4/10 | 0/10 | 1/4 |
  | Margin + drop-OOV | 0.80 @ 0.02 | 10/10 | 4/10 | **4/4** |
  | Per-category thresholds (U3) | 0.75 @ 0.12 | 10/10 | 5/10 | **3/4** |

  Coin flip is 0.50. The best-scoring variant flags **all four** control
  sentences. `"she walked the dog around the block twice"` scores 0.219 against
  `creation_from_nothing`; `"the recipe calls for two cups of flour"` scores
  0.201 against `information_violation`.

  1. **Is 0.2 the right gate?** No threshold is right. The violation and valid
     distributions overlap almost completely on novel phrasing
     (violations mean 0.082, valid mean 0.066 under current scoring). At the
     shipped 0.2 gate, novel-phrasing TPR **and** FPR are both `0.00` — the gate
     is effectively closed, which is the safest available setting. Every
     direction tested trades that safety for noise.
  2. **Threshold or library?** Neither, exactly — see **F-007**. The root cause
     is a scoring defect, not sparsity. But correcting it does not help.
  3. **Per-category thresholds?** 0.75 balanced accuracy, identical to the global
     gate, still 3/4 controls flagged. **FALSIFIED.**
- **Where it went**: no behavior change. `benchmarks/vector_gate_probe.jsonl` and
  `tests/test_vector_gate.py` commit the experiment so it is re-runnable and so a
  future threshold change fails loudly against the controls.

## F-007 — Out-of-vocabulary terms are weighted, and it is a real defect

- **Claim** (mine, while investigating F-006): the low scores in F-006 are caused
  by out-of-vocabulary n-grams inflating the query vector's magnitude. Removing
  them will fix detection.
- **Run**: decomposed query-vector magnitude by vocabulary membership; then
  re-scored the whole probe set with OOV terms dropped.
- **Result** — the mechanism is real and worse than expected:
  - `TfIdfVectorizer.vectorize()` assigns unknown terms
    `idf = log(N + 1) = 4.127`, which is **higher than the maximum in-vocabulary
    IDF (4.111)**. Novel terms receive the greatest weight in the space.
  - An OOV term overlaps **zero** reference vectors by construction (verified:
    the 587 terms across all reference vectors are a subset of the fitted vocab).
    It contributes nothing to any dot product but is added to `mag_a`, which
    *divides* every similarity.
  - Consequence: cosine similarity is deflated in proportion to how unusual the
    phrasing is. For `"output appears with no source energy"`, **86.6%** of the
    query vector's magnitude is dead weight; for
    `"results emerge without any data input"`, **91.3%**. Library-verbatim
    strings carry 0%.
  - So the score is substantially measuring *vocabulary overlap with a 60-entry
    library*, not semantic match — exactly the failure mode F-001 replaced
    keyword lists to escape.
- **Status**: defect **CONFIRMED**; the proposed fix **FALSIFIED**.
- **Why it was not shipped**: dropping OOV terms raises the F-006 cases 2.0× and
  2.5× — past the gate, as predicted. It raises the valid claims by the same
  mechanism. Balanced accuracy goes **down** (0.75 → 0.70) and control
  sentences stay flagged 3/4. It is a monotone rescaling, not a discrimination
  improvement. Applying it while leaving the gate at 0.2 would move
  novel-phrasing FPR from `0.00` to `0.50`.
- **Edited claim**: this is a genuine implementation defect that miscalibrates
  the score, and it is *also* not the reason the vectorizer fails. Both are true.
  Fixing it is only worth doing as part of replacing the scoring approach, not on
  its own.
- **Where it went**: recorded, not fixed. Shipping a change that is provably
  correct in isolation but measurably worse in effect is how a system rots.

## F-008 — "Run the suite before retuning" was a sufficient safety check

- **Claim** (mine, F-006 as originally written): "Do not tune it without running
  both [the 130-test suite and the 26-case benchmark corpus]."
- **Run**: instrumented the parser's routing and counted how many labeled cases
  in the entire repo actually reach the vector gate — i.e. have
  `claim_pattern == "generic"` and are not dismissals.
- **Result**: **4 of 41** labeled premise cases reach the gate, and only **3 are
  distinct**:

  | Similarity | Expected | Input |
  |-----------:|----------|-------|
  | 0.512 | CLEAN | Energy is conserved in all physical processes |
  | 0.574 | CLEAN | Heat flows from hot objects to cold objects |
  | 0.345 | CORRUPTED | This machine needs no input energy |

  All three sit far above the 0.2 gate. **Nothing in the test suite lies near the
  decision boundary.** The threshold could be set anywhere in `0.0 – 0.345` and
  all 130 tests would still pass. Two of the 41 cases are also verbatim reference
  library entries, so they score 1.000 by construction.
- **Status**: **FALSIFIED.** Running the suite is necessary but nowhere near
  sufficient; passing tests would have given false confidence in a bad threshold.
- **Edited claim**: a threshold change must be evaluated against a corpus built
  *for* the boundary, with physics-free controls included. That corpus now exists
  at `benchmarks/vector_gate_probe.jsonl` and is enforced by
  `tests/test_vector_gate.py`.
- **Note**: this entry falsifies a prescription written in this very file one
  commit earlier. That is the loop working, not a lapse — the prescription was
  plausible, untested, and wrong.

## F-009 — The reference library is balanced across labels

- **Claim**: implicit in the vectorizer's design — `best_label` compares
  similarity to violation vs valid references, which assumes comparable coverage.
- **Run**: counted `REFERENCE_LIBRARY` entries by label; scored four physics-free
  control sentences.
- **Result**: **41 violation entries vs 20 valid** — roughly 2:1. Three of four
  control sentences (`"she walked the dog around the block twice"`,
  `"please submit the quarterly report by friday"`,
  `"the recipe calls for two cups of flour"`) are labeled `violation`, on nothing
  but this prior. `best_label` defaults to "violation" for out-of-domain text.
- **Status**: **FALSIFIED**
- **Edited claim**: `best_label` is not a calibrated classifier. It is only
  meaningful when `similarity` is high enough that a specific reference actually
  matched. Below that, it reports the library's composition.
- **Where it went**: pinned by `test_reference_library_is_violation_weighted` so
  the ratio cannot drift silently. Rebalancing was **not** attempted — it would
  be a new hypothesis needing its own run.

---

## Claims that still hold

Re-run at each pipeline change. Currently passing.

| Claim | Run | Result |
|-------|-----|--------|
| Structural patterns beat keywords | `Power can emerge spontaneously` | `CORRUPTED 0.67` |
| Explicit violations are caught | `Energy can be created from nothing` | `CORRUPTED 0.67`, conf 0.99 |
| Dismissals are not violations | `It is impossible to build a perpetual motion machine` | `CLEAN`, conf 0.90 |
| Valid transfers stay clean | `Heat flows from hot to cold` | `CLEAN`, `transfer_claim` |
| Extraction accounting works | `The company extracts value from workers without returning compensation` | `CORRUPTED 0.67` |
| Near-paraphrase recall | `heat flows from hot to cold naturally` | sim 0.892 |

Reproduce all of the above:

```bash
python main.py "Power can emerge spontaneously"
pytest tests/ -q          # 139 tests
```

---

## Designs proposed but never built

Recorded so they are not re-proposed as new ideas.

| Proposed | Where | Status |
|----------|-------|--------|
| `domains/thermodynamic.py` | v1 architecture sketch | Never built. Coverage absorbed by `core/` first-law and second-law checks plus `domains/thermodynamic_accountability.py`. |
| `domains/mass_balance.py` | v1 architecture sketch | Never built. `mass_balance` survives only as a `type` label from `_detect_type()`. |
| `domains/geometric.py` | v1 architecture sketch | Never built. No spatial constraint checking exists. Genuinely open if wanted. |

The domains that *were* built — `organizational`, `information`,
`thermodynamic_accountability` — were not in the original plan. The plan's
domain axis (by physical quantity) was replaced in practice by a different axis
(by claim domain). That substitution was never explicitly decided; it emerged.
Recorded here so it can be revisited deliberately.
