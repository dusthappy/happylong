---
name: hy-review
description: "Independent code review: audit the implementation against the plan, ACs, contract, language standards, and security red lines, producing an implementation/review.md verdict (pass/pass-with-notes/block). Triggered by /hy-review."
metadata:
  hy:
    command: hy-review
    kind: lifecycle
    stage: dev
    entry: true
---

# hy-review · Independent code review

> Re-run the checks from a "fault-finding" stance: you may re-verify `/hy-dev`'s self-check conclusion, or independently review any already-implemented iteration. Complementary to the same-session self-check in `/hy-dev` stage 3, this command is an **independent cross-session review**: trigger it in a fresh session without implementation memory, and verify evidence item by item against persisted artifacts only (plan/AC/contract/standards/code changes) — do not re-derive the implementation. **Report problems and suggestions only; do not modify code directly** (when the user explicitly asks for a fix, follow the `/hy-dev` stage-2 baseline).

## Session entry gate (P0)

- In a new session, start with `session show`. If unbound, use `iter list [project]` to show candidates, then enter an Ask-First loop in which the user chooses to **bind an existing iteration** or **create a new iteration**. An independent review must never guess the “latest iteration.”
- When the user selects an existing iteration, run `session set`, verify with `session show`, and resume the original review request. If the user chooses a new iteration, route through `/hy-req` to complete a PRD; resume `/hy-review` only once there is an implementation to review. Invalid or incomplete input keeps the gate closed and repeats the question until cancellation.
- Before the gate completes, do not create or update `implementation/review.md`. Even when the user supplies both project and iteration ID, obtain binding confirmation and persist the binding first.

## Inputs

- The session iteration (or `--project` + `--iteration-id`); `--repo {name}` limits the review to a single repo.
- Review targets: actual code changes in `code_lib` + `plan.md` + `prd.md` + `contract.md`.

## Review dimensions

| Dimension | What to check |
|-----------|---------------|
| Delivery completeness | All plan tasks closed or defer-explained; every AC maps to at least one completed task |
| Scope discipline | Changes only on plan-declared paths; shared repo stays within the backend_app boundary; no drive-by edits |
| Contract consistency | Implemented interfaces/fields/error codes align item by item with contract.md; FE consumption matches BE provision |
| Language standards | Against `shared/standards/{typescript,go,rust}.md` and `coding-standards.md` |
| Security red lines | Hard-coded credentials / SQL concatenation / missing permission checks / sensitive data in logs |
| Error handling | No swallowed exceptions; user-visible errors have fallbacks; Go errors wrapped; TS promises without bare catch |
| Maintainability | Naming/layering follows repo conventions; duplicate code; dead code; leftover debug statements |
| Verification trail | Verification reproducible, evidence genuine (command and output summaries) |

## Outputs

- Generate/update `implementation/review.md` from `.hy/i18n/{lang}/templates/iteration/review.md.tpl`:
  - Verdict **pass** / **pass-with-notes** (with issue list) / **block** (must-fix items listed).
  - Issue grading: `P0 must fix` / `P1 should fix` / `P2 acceptable`, each with location (repo/file/line) and suggestion.
- block or unfixed P0 → back to `/hy-dev` (stage 2) or `/hy-fix`; not counted as pass.

## Checkpoints

- No implementation at all (no code_lib changes, empty plan) → explain and abort.
- "Implementation clearly contradicts the PRD" → mark block and identify whether it is a requirement change (back to `/hy-req` to revise the PRD) or an implementation deviation (back to `/hy-dev`).

## [Next Steps]

- Verdict pass → `/hy-test` to close out with smoke
- block/P0 present → `/hy-fix` (or `/hy-dev` back to stage 2)
- Want another perspective → `/hy-roles` (architect persona)
