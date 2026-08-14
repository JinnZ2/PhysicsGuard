# legacy/

Superseded artifacts, kept deliberately.

Nothing here is live code. Nothing here is imported by the pipeline. It is kept
because **precedence carries**: a design that was tried and falsified is
evidence, and evidence that gets deleted stops constraining future work.

The failure mode this folder prevents: someone (human or model) reads the current
codebase, notices an apparently simpler approach, implements it, and rediscovers
by hand that it does not work — because the record that it was already tried and
already failed was tidied away.

## What is here

| File | What it was | Why it is here |
|------|-------------|----------------|
| `v1_specification.md` | The original README — a 972-line document that carried the entire v1 implementation inline as pasted source, plus the v1 user-facing README nested inside it | Every module was extracted out of this file into real files (`b3f06e6`), then rewritten (`92cefb1`). It is now a snapshot of the pre-rewrite system, not documentation. |
| `PLAN.md` | The rewrite plan that drove `92cefb1` | Fully executed. Its "Problem" sections describe behavior that no longer exists — reading it as current documentation would be actively misleading. |

## What these artifacts still prove

`v1_specification.md` is the primary evidence for three falsified claims. Read it
alongside `../FALSIFICATION_LOG.md`:

- **F-001** — the v1 keyword lists (`ENERGY_KEYWORDS`, `MASS_KEYWORDS`,
  `FLOW_KEYWORDS`) and why vocabulary matching missed structurally-identical
  claims.
- **F-002** — the v1 `_first_law()`, where `lhs` and `rhs` are assigned the same
  expression, proving the conservation math could never detect anything and the
  keyword boolean was making every decision.
- **F-003** — the v1 `score_and_flag()` count ratio, and the original
  `SUSPECT < 0.5` / `CORRUPTED >= 0.5` thresholds, superseded by `0.3`.

`PLAN.md` records the falsifying example for F-001
(`"Power can emerge spontaneously"` → CLEAN) in its own words, at the time, before
the fix existed.

## Reading rules

1. **Do not treat anything here as current.** Verdict thresholds, module lists,
   architecture diagrams, and API shapes in these files are all out of date. The
   current system is described in `../README.md` and `../CLAUDE.md`.
2. **Do not restore code from here.** If something looks worth reviving, check
   `../FALSIFICATION_LOG.md` first — it probably explains what killed it.
3. **Do not delete these files.** Superseding an artifact means moving it here and
   logging why, not removing it.

## Adding to this folder

When something is superseded:

1. `git mv` it here — do not copy-and-delete, so `git log --follow` keeps working.
2. Add an entry to `../FALSIFICATION_LOG.md`: the claim, the run, the verbatim
   result, the edited claim.
3. Add a row to the table above saying what it was and what falsified it.

Full history for anything here:

```bash
git log --follow -- legacy/v1_specification.md
```
