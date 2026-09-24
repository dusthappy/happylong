---
name: hy-req
description: "One-stop iteration + PRD entry: explicit --title always creates and binds a new iteration; without a title, route by the current session first, and if unbound enter an Ask-First loop to bind an existing iteration or create a new one, then complete the single-file PRD (body + AC + repository scope + contract). Triggered by /hy-req --project X --title T or /hy-req with a pasted requirement."
metadata:
  hy:
    command: hy-req
    kind: lifecycle
    stage: entry
    entry: true
---

# hy-req · Open iteration + single-file PRD (integrated)

> Pipeline entry: one interaction completes "iteration dir creation + session binding + PRD completion (body/AC/in-scope repos/contract branching)", so `/hy-dev` can start immediately. Contract timing is **moved forward into this stage**; dev stage 0 is only a fallback.

## Trigger and input modes

```
/hy-req [--project {project}] [--title {title}] [--type feat|fix|refactor|doc|chore] [--slug {slug}]
…trailing free text = requirement body (interpret as written; may tidy wording, never change intent)
```

| Mode | Input shape | Routing |
|------|-------------|---------|
| A explicit new PRD | has `--title` | use the title verbatim; skip the bind/create choice and always create and bind a new iteration |
| B no title, bound | with or without trailing text | continue the current PRD when incomplete; when complete, Ask-First whether to revise it or open a new iteration |
| C no title, unbound | with or without trailing text | list candidates, then enter the Ask-First bind/create loop until resolved; preserve trailing text and resume this request |

- In mode A, `--project` defaults from the current binding. In a new unbound session with no project, ask only for the project, then create directly; do not ask bind versus create.
- When create-new is selected without `--title`, propose a title from the trailing content (concise title + English slug + inferred type) and combine project/title/slug/type plus requirement gaps into one confirmation round. A bare invocation also asks for the requirement description.
- `--type` defaults to `feat`; without an explicit title it may be inferred from the content and included in the create confirmation.
- `--slug` sets the English phrase explicitly; a title with no Latin words automatically falls back to a time-based slug (e.g. `t0930`).

## Steps

### ① Checkpoint

- First confirm that the current agent session has a stable identity: prefer `HY_SESSION_ID` in the session launch environment (Codex can use `CODEX_THREAD_ID` automatically), or pass the same leading `--session-id` on every tool invocation. The ID must remain unchanged for the entire long-running session and across context compaction. If none is available, stop and ask for configuration; never invent a temporary ID.
- Run `python3 happlylong.py session show` to resolve the current agent session's isolated binding, then route by its state (never read the legacy `current.yaml` directly):
  - **Has `--title` (highest priority)** → this is an explicit new-PRD signal. Resolve the project, then go directly to step ② to create and bind; do not present the bind-existing/create-new choice. Even if the session is already bound, open a new iteration and let the tool move the old binding to `previous`. On a same-day slug collision, ask for a new `--slug` (a recommended suffix is fine) or cancellation; never reinterpret the request as reuse.
  - **No `--title`, unbound** → run `python3 happlylong.py iter list [project]` to show valid candidates, then Ask-First whether to bind an existing iteration or create a new one. A recommendation may follow from the original intent, but never choose for the user. Bind existing: collect only the missing project/iteration ID, run `session set`, verify with `session show`, re-enter this routing step, and resume the original `/hy-req`. Create new: preserve trailing text, resolve the project, confirm the proposed title/slug/type, then go to step ②. Invalid project/iteration or incomplete input creates no artifacts; show candidates and ask again until success or explicit cancellation.
  - **No `--title`, bound, `stages.prd ≠ done`** → fill that iteration's PRD without creating a directory; when the requirement body is missing, ask only for it and other genuinely missing information.
  - **No `--title`, bound, `stages.prd = done`** → checkpoint: is this a **revision** (new ACs + revision history; used AC numbers never recycled) or a **new iteration**? For a new iteration, propose and confirm a title from the trailing text, then go to step ②.
- Once the project is resolved, run `python3 happlylong.py doctor` to confirm its symlinks are healthy (fix broken ones first so later coding does not target missing paths).
- Read `workspace/{project}/profile.yaml → repos` as input for the in-scope repo decision.

### ② Create iteration (new iterations only, one scripted step)

```bash
python3 happlylong.py iter new {project} --title "{title}" --type {type}
```

Artifacts (templates from `.hy/i18n/{lang}/templates/iteration/`):

```
workspace/{project}/iterations/{YYMMDD}-{type}-{slug}/
├── _index.yaml      ← three-stage state machine (stages: prd/dev/smoke) + contract field
├── prd.md  contract.md  plan.md  smoke.md
├── implementation/  (fix-*.md, review.md)
└── attach/          (prototypes, external contracts, other attachments)
```

The current agent session is bound automatically, and its state is written atomically to `.hy/session/bindings/{hash}.yaml`. Without a trustworthy session ID, the tool fails closed before creating the iteration directory, leaves no partial artifacts, and never falls back to `current.yaml`.

### ③ Requirement clarification (lightweight)

- If the information is complete, write directly; for gaps use `/hy-roles` PM's four pillars (completeness/consistency/clarity/feasibility) — **ask only what's missing**, packaged into one round (Ask-First).
- Fold the title confirmation for modes B and C into the same clarification round to avoid unnecessary back-and-forth.
- Session images/attachments (prototypes, screenshots, external contract fragments) → store in `attach/` and register in the PRD.

### ④ Determine repository scope → repos_in_scope

Decide from the PRD content and **execute directly, without asking the user** (rationale written into the PRD's "scope" section):

| Content signature | Decision |
|--------------------|----------|
| Pure API/tables/backend logic | backend repo (for shared repos, name the backend_app) |
| Gateway/BFF/middleware logic | service repo (for shared repos, name the backend_app) |
| Pure pages/interactions/UI | frontend repo (with multiple FE repos, split by platform: mobile uni-app / pc react / cocos) |
| Both | two repos, backend/service first (dev auto-chains server→frontend) |
| Single-repo project (example_rs) | that repo |

Write back `_index.yaml → repos_in_scope` (backend/service first). Stop and ask only when the PRD gives absolutely no basis for judging (checkpoint).

### ⑤ Contract branching

Decide "does this requirement create cross-repo data interaction (new APIs/new tables/field changes/cache keys)":

1. **External contract provided** → validate completeness, organize into `contract.md`, set `_index.yaml → contract: done` (sync the status line), PRD notes "contract source: external".
2. **No external contract but data impact** → generate `contract.md` from the PRD (scope / data & field highlights / interface highlights / cross-repo dependencies), `contract: done`. Uncertain fields are marked "confirm during integration" and listed for dev stage-0 fallback.
3. **No data impact** → `contract: skipped`, `contract_note` records the rationale, `contract.md` keeps the empty template.

Ambiguous direction (can't tell if there's data impact) → checkpoint and ask.

### ⑥ Write prd.md

Complete the template without changing its structure: revision history / background & goals / **acceptance criteria (AC-001… checkable, 2-8 items, each smoke-verifiable)** / scope (include/exclude + repository-scope rationale) / functional requirements (sectioned by repo) / non-functional requirements (delete if none). Finally write back `_index.yaml → stages.prd: done` and `updated`, and sync the status line at the top of prd.md.

### ⑦ Validate

`python3 happlylong.py session show` to confirm binding; `iter show` to confirm `prd`/`contract` states match reality.

## Quality self-check (before submitting)

```
□ Every AC verifiable, numbered, free of vague words ("as much as possible"/"faster")
□ repos_in_scope matches the PRD content and is written back to _index
□ Contract branch conclusion matches _index → contract
□ Prototypes/attachments stored in attach/ and registered
□ No placeholder residue; revision history updated
```

## Checkpoints (Ask-First)

- On an unbound session without explicit `--title`, the entry choice between bind existing and create new; invalid or incomplete input must loop;
- When create-new was selected without an explicit title, one packaged confirmation for project/title/slug/type and requirement gaps;
- On an explicit-create iteration-ID collision, choose a new slug or cancel;
- Key requirement information missing (③ cannot self-answer);
- Ambiguous contract direction (branch undecidable);
- Requirement clearly exceeds one iteration's capacity (suggest splitting; user decides);
- `prd` already done: revise vs open new.

## Boundaries

- Never touch `code_lib/` (no PRD, no code changes).
- Never interpret explicit `--title` as “continue existing.” On a same-day slug collision, preserve create-new semantics by choosing a new slug or cancelling.
- Before the unbound-session gate completes, create no directory and write no iteration artifacts. After the user selects an existing iteration, verify the binding before resuming the original request.
- Iteration creation (②) is a pure scripted step; PRD content generation (③-⑥) is the LLM step — never reversed (directory first, content second).

## [Next Steps]

- Start development → `/hy-dev` (state machine starts at contract fallback/plan automatically)
- Refine the requirement or contract → `/hy-roles` (PM/architect persona) or edit `contract.md` directly
- Current status → `python3 happlylong.py status`
