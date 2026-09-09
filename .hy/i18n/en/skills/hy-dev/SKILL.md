---
name: hy-dev
description: "Integrated development state machine: contract fallback → plan → implement/fix → self-check, four stages auto-routed, multi-repo chained backend→frontend automatically, Ask-First pauses only at checkpoints; no PRD means no code changes (P0). Triggered by /hy-dev."
metadata:
  hy:
    command: hy-dev
    kind: lifecycle
    stage: dev
    entry: true
---

# hy-dev · Integrated development

> One request does it all: auto-route through "contract fallback → plan → implement → self-check" by iteration state; for multi-repo requirements, once a BE repo's full chain passes, **automatically** switch to the FE repo without waiting for confirmation. Stop only at checkpoints.

## Session entry gate (P0)

- First run `python3 happlylong.py session show`. Without a stable identity, fail closed; never guess or generate a temporary ID.
- If the current session is unbound, run `python3 happlylong.py iter list [project]` to show valid candidates, then Ask-First whether to **bind an existing iteration** or **create a new iteration**. A recommendation is allowed; choosing for the user is not.
- Bind existing: collect the project/iteration ID, run `session set`, verify with `session show`, and resume the original `/hy-dev`. Create new: collect project/title/type/requirement body and route through `/hy-req` to create the iteration and complete its PRD; once `stages.prd == done`, automatically resume this `/hy-dev`.
- Invalid or incomplete input keeps the gate closed: list candidates and ask again until the user succeeds or cancels. Before both the gate and the PRD prerequisite pass, do not write plan/contract/review artifacts or change `code_lib/`.

## Preconditions (P0)

- `stages.prd == done`, otherwise abort and point to `/hy-req` (**no PRD, no code changes**).
- Repo set = `_index.yaml → repos_in_scope`; if empty, re-judge from the PRD and write back (rules in `/hy-req` step ④ in-scope repo decision).
- Load `workspace/{project}/profile.yaml`: confirm each repo's role and shared-repo `backend_apps`; load the `shared/` standards matching the languages involved.
- If an involved repo already has `knowledge/{repo}/overview.md` (with api/data) → load it as repo-understanding context (conventions and existing interfaces/tables follow knowledge + code; if knowledge is stale, suggest a refresh in passing).

## State machine (per repo, first unfinished stage wins)

```
/hy-dev [--repo {name}]
  │
  ├─ repo set and order: repos_in_scope (backend first); --repo focuses one repo
  │
  ├─ for each repo, check in order:
  │    contract field not done/skipped and the PRD has data impact ─→ stage 0 contract fallback
  │    no plan.md or the AC set changed                             ─→ stage 1 plan
  │    plan has open tasks (or defects to fix)                       ─→ stage 2 implement/fix
  │    all tasks closed and no review verdict                        ─→ stage 3 self-check
  │
  └─ cross-repo chaining: this repo's stage 3 pass → auto-switch to the next repo
     (FE repos consume contract.md interface highlights); no stopping, no waiting
```

When the full chain finishes, report once: repo set and order + each repo's plan/review verdict + verification evidence summary.

## Stage details

### Stage 0 · Contract fallback

Only when `/hy-req` didn't complete the contract (`_index.yaml → contract` still pending) and the requirement has data impact: write `contract.md` per the four-section structure, write back `contract: done` (sync the status line at the top of contract.md); no impact → set `skipped` and write `contract_note`. Ambiguous direction → checkpoint.

### Stage 1 · Plan (plan.md)

- Generate/refresh from the PRD's ACs: the **AC coverage table** (≥1 task per AC) + the **task list** (T-01…: repo/paths/highlights/verification method/verification evidence) + the linked contract status.
- Task granularity = the smallest verifiable change; shared-repo task paths must fall inside `backend_apps.{name}.paths`.
- AC conflicts, or an AC that cannot map to a task → checkpoint.

### Stage 2 · Implement/fix

- Write code per `/hy-roles`' four implementation principles: minimal change, follow repo conventions, reuse first, closed-loop verification.
- Coding scope: `workspace/{project}/code_lib/{repo}/`; shared repos — touch only the matching backend_app's paths.
- Tick each plan task on completion and fill "verification evidence" (actually executed commands and result summaries; not run = not done).
- Verification baseline (repo's own Makefile/AGENTS.md/package.json scripts take priority):

  | Repo language | Baseline |
  |---------------|----------|
  | Go (example_be / shared_be) | `go build ./...`; affected packages `go test ./...`; shared_be subproject changes also run table-driven tests |
  | Rust (example_rs) | `cargo fmt --check` + `cargo clippy` + `cargo test` |
  | TS Web (example_fe / example_pc / example_game) | in-repo tsc/lint/test scripts; UI ACs describe manual verification paths |
  | Cocos (example_game) | `tsc` + editor run instructions |

- Multiple viable implementations for one AC / code to touch beyond PRD scope (sibling pages, common layers, other subprojects) → **checkpoint** (scope boundary).

### Stage 3 · Self-check (implementation/review.md)

- Generate the checklist from `.hy/i18n/{lang}/templates/iteration/review.md.tpl`: tasks closed, AC coverage, changes only on declared paths, contract consistency, language standards, security red lines, placeholders, verification trail.
- Verdict `pass` / `pass-with-notes` / `block`; **block items return to stage 2** for fixing, then re-issue the verdict.
- This stage is the **same-session self-check** (reviewing with implementation memory in mind); for an independent perspective use `/hy-review` — a cross-session independent review that verifies item by item against persisted artifacts without re-deriving the implementation.
- All repos pass → `stages.dev: done` (deferred repos keep in_progress with an explanation).

## Checkpoints (Ask-First; no advancing before an answer)

| # | Checkpoint | Typical case |
|---|------------|--------------|
| 1 | Unbound entry | bind existing vs create new; invalid input keeps looping |
| 2 | Contract direction | table/interface fields unclear — can't decide contract vs skipped |
| 3 | Implementation approach | modify a common component vs localize; new interface vs reuse |
| 4 | Scope boundary | need to touch the shared repo's common layer, sibling subprojects, or code outside the PRD |
| 5 | AC gap/conflict | ACs contradict each other or miss preconditions |
| 6 | Scale escalation | requirement exceeds one iteration → suggest splitting / prototyping (user decides) |
| 7 | Fix root cause | multiple candidate causes — the minimal fix point can't be pinned |

One checkpoint at a time, each with "question + options + recommendation".

## Completion criteria

- [ ] Each repo's plan tasks all closed (or explicitly deferred with explanation)
- [ ] Code changes only in plan-declared repos and paths (shared repos within backend_app paths)
- [ ] Each repo's review.md has a verdict with no unhandled blocks
- [ ] Verification commands actually executed, evidence recorded
- [ ] All checkpoints have user confirmations; with no checkpoints it ran fully automatically

## [Next Steps]

- Smoke → `/hy-test` (at least once per repo)
- Tests/production break → `/hy-fix` (back to stage-2 fix mode)
- Unsure about quality → `/hy-review` (independent recheck)
