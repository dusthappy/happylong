---
name: hy-test
description: "Smoke execution: expand the PRD ACs into a checklist and verify item by item, producing smoke.md with its four-column table (item↔AC↔result↔evidence); fail loops back to /hy-fix, all-pass sets stages.smoke=pass. Triggered by /hy-test."
metadata:
  hy:
    command: hy-test
    kind: lifecycle
    stage: smoke
    entry: true
---

# hy-test · Smoke test

> Pipeline closure: prove that "what was built actually satisfies the ACs". Real operations are the truth — no paper deductions.

## Session entry gate (P0)

- Start with `session show`. If unbound, use `iter list [project]` to show candidates, then enter an Ask-First loop in which the user chooses to **bind an existing iteration** or **create a new iteration**. Never silently test the most recently completed iteration.
- Bind existing: run `session set`, verify with `session show`, and resume the original `/hy-test`. Create new: route through `/hy-req` to complete the PRD, then satisfy the `/hy-dev` prerequisite; resume this smoke request only when the iteration is testable.
- Invalid or incomplete input keeps the gate closed and repeats the question until cancellation. Before the gate completes, do not create or update `smoke.md` or change `stages.smoke`.

## Inputs

- The session iteration; the AC list from `prd.md` (including ACs revised after `/hy-req`) + `contract.md`.
- Optional argument: `--scope all|failed` (default all; after a smoke loop-back you may run failed + regression only).

## Flow

```
① Expand the checklist  at least one verification item per AC; group by repo when multiple repos are involved;
                        add interface cross-checks for contract changes; plus a regression section: run each
                        repos_in_scope repo's existing test suite once (a gate independent of the ACs)
② Execute item by item  automate what can be automated (commands/scripts/HTTP/browser automation — UI ACs prefer
                        real browser automation to minimize manual items); what truly cannot be automated gets
                        clear manual steps for the user to perform
③ Record                smoke.md four columns: # / item / AC / result(pass|fail|skip) / evidence; one regression row per repo
④ Verdict               any fail or failing regression suite → stages.smoke=fail; all pass (or well-justified skips)
                        with regression all-pass → pass; update the status line at the top of smoke.md accordingly
```

- **Evidence** must be traceable: commands and key output, URLs, screenshot paths (stored in `attach/`). Every `skip` needs a reason (e.g. external service temporarily unavailable); an unjustified skip counts as fail.
- Use each repo's existing conventions for the environment (dev server / Makefile / docker compose / test accounts); unsure how to start a service → read the repo README/Makefile first, still unclear → checkpoint and ask.

## Verdict and loop-back

| Result | Action |
|--------|--------|
| All pass | `stages.smoke: pass` (both AC and regression gates green); prompt the user to review and commit the code themselves (**no automatic git operations**), then `python3 happlylong.py iter close`; after committing, `/hy-knowledge iteration` is suggested to distill the change |
| Any fail | `stages.smoke: fail` (AC item or regression suite); organize fails into a defect list → `/hy-fix`, then rerun (`--scope failed` + regression) |
| Blocked | Environment won't start / dependency missing → record the blocker and stop here (checkpoint); never pretend it ran |

## Checkpoints

- `stages.dev ≠ done` → return to `/hy-dev` to finish first (or confirm a defer and continue).
- An AC turns out missing/wrong at smoke time → that's an AC gap checkpoint: back to `/hy-req` to revise (new AC numbers); never silently change an old AC's meaning.

## [Next Steps]

- All pass → after the user commits, `python3 happlylong.py iter close` (requires smoke=pass; if this session switched from another in-flight iteration, `session back` first after close), then `/hy-knowledge iteration` to distill
- Fails present → `/hy-fix` (paste the fail list) → `/hy-test --scope failed`
- Want a quality verdict on record → `/hy-review`
