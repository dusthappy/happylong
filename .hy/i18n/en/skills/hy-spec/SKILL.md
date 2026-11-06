---
name: hy-spec
description: 'happlylong meta-spec (three-in-one): P0/P1 constraint quick reference + skill execution lifecycle + output quality grades. Required knowledge before running any hy-* skill; triggered by /hy-spec or "hy constraints/spec/quality standards".'
metadata:
  hy:
    command: hy-spec
    kind: meta
    entry: false
---

# hy-spec · Meta-spec

> Positioning: merges "constraint index + execution spec + output quality" into the single meta-spec of the whole framework (AGENTS.md is its front-door quick reference).

## 1. Constraint tiers

| Tier | Meaning | Violation handling |
|------|---------|--------------------|
| **P0 red line** | Security/business bottom line | Stop immediately, explain, give a fix suggestion |
| **P1 hard constraint** | Coding/process/output rules | Warn and fix, otherwise reject the output |
| **P2 suggestion** | Best practices | Note it and continue |

### P0 red lines

- No hard-coded credentials (passwords/API keys/tokens go to env or a local secret file, never committed).
- No SQL string concatenation; parameterized queries only.
- Every new endpoint must verify permissions — no anonymous exceptions.
- No bare `except` (Python) / empty `catch` (TS) / ignored `error` (Go) — handle it or log it.
- **No PRD, no code changes**: while an iteration's `stages.prd ≠ done`, changing any file under `code_lib/` is forbidden (P0). Even a production hotfix requires a minimal PRD first or explicit user permission.
- **No execution while unbound**: execution requests that advance requirements, development, fixing, rechecking, smoke testing, or iteration distillation must resolve the current session first. If a stable identity exists but is unbound, Ask-First whether to bind an existing iteration or create a new one; the sole bypass is an explicit `/hy-req --title`, which creates a new iteration. Before the user answers, write neither iteration artifacts nor business code.
- **Every binding names its workspace**: active and previous bindings require `project`, `iteration_id`, and `iteration_path`, and the path must equal `workspace/{project}/iterations/{iteration_id}`. Never infer a project from a bare iteration ID, recency, or cwd.
- Record a pre-deletion snapshot (table/conditions/row count or file content summary) before deleting data/files.
- Never `git add/commit/push` without an explicit user request.
- Iteration artifacts go only to `workspace/{project}/iterations/{id}/`; cross-iteration product prototypes, documentation, assets, and verification go only to sibling `workspace/{project}/prototype/`, never replacing source PRDs/contracts/acceptance records. Framework instruction sources/templates stay in `.hy/`, installed artifacts in root `AGENTS.md`/`CLAUDE.md` and `.agents/`; framework tools, tests, standards, and docs retain their established paths.
- Prototypes disclose demonstrated, planned, and deferred capabilities and mocked services, recording same-project source iterations and coverage. Prototype `ready` means reviewable only; it never changes bindings or business `prd/dev/smoke`, and never passes business ACs.

### P1 hard constraints

- Prototype delivery must support double-clicking local `.html`/`.htm` without a server or build prerequisite; record actual `file://` verification before `ready`. When file-page storage is restricted, visibly fall back to current-page state and offer export, without automatically migrating old HTTP data.
- Tool scripts always use `pathlib.Path`, anchored at the framework root by absolute path; never depend on cwd.
- Resolve session context through `python3 happlylong.py session show`. Non-Codex agents must provide a stable, unique `HY_SESSION_ID` in the launch environment (or consistently pass the same leading `--session-id`) and keep it unchanged across context compaction. Fail closed without a trustworthy identity; never read or assume `.hy/session/current.yaml`.
- No `except: pass`; no bare `raise` — use custom exceptions (`HyError` inside the tool).
- Output must not leave placeholder residue: `TODO` / `待补充` / `TBD` / `FIXME` / `XXX`.
- Document-type artifacts must update the revision history table.
- Load standards by language: whichever code you touch, load the matching file from `shared/standards/` plus `coding-standards.md`; add `security-rules.md` / `testing-standards.md` when security/testing is involved.
- Repo roles and dev order: backend/service first, the rest in `profile.yaml → repos` declaration order; registration requires explicit `--role` plus `--desc`/`--lang`; shared-repo (shared_be) changes must stay inside `backend_apps.{name}.paths` — crossing the boundary is a scope checkpoint.

## 2. Skill execution lifecycle (five steps)

```
① Trigger            classify execution intent and detect the explicit /hy-req --title create-new signal
② Identity + gate    happlylong.py session show (verify the fingerprint isn't cross-wired with another parallel session; switch IDs if it is); if unbound, run the Ask-First bind/create loop until success or cancellation
③ Context gathering  iteration _index.yaml → project profile.yaml → needed shared/ standards
④ Checkpoint         validate prerequisites (e.g. hy-dev requires stages.prd=done); guide clearly instead of guessing
⑤ Execute + validate advance the state machine and write back stages; completeness check → report + [Next Steps]
```

Every hy-* skill's output must end with **[Next Steps]**: 1-3 copyable next-step commands per scenario.

## 3. Ask-First principle (global)

**Stop only at checkpoints; everything else runs automatically end to end.**

- Checkpoint = a decision you are unsure about, with multiple reasonable paths, or whose impact exceeds the current iteration. At a checkpoint: stop and give "question + options + recommendation with reasons"; do not proceed and do not silently pick a default before the user answers.
- An unbound session is a mandatory entry checkpoint: run `iter list` to show valid candidates, then ask whether to bind an existing iteration or create a new one (prefer a structured question/choice UI when available). For binding, collect only the missing project/iteration ID, run `session set`, and verify with `session show`. For creation, collect project/title/type/requirement body and route through `/hy-req` to complete the PRD. Invalid or incomplete input keeps the gate closed: show candidates and ask again until the user succeeds or cancels.
- Explicit `/hy-req --title` is the sole bypass of that choice: use the title as written, resolve the project, then create and bind a new iteration. Even if another iteration is bound, open a new one; never reinterpret this signal as reuse.
- Pure Q&A, `/hy-spec`, `/hy-guide`, `/hy-roles`, project/symlink onboarding, prototype scaffold initialization/inspection, framework diagnostics, framework-source maintenance and open-source/release preparation, and `/hy-knowledge bootstrap` do not trigger the business-iteration gate. For natural language, the deciding question is whether the request would advance iteration artifacts or business code.
- Non-checkpoints (state-machine routing, plan generation, task-by-task implementation, self-check execution) always run continuously and automatically — go as far as a single request allows.

## 4. Output quality grades

| Grade | Definition | Handling |
|-------|------------|----------|
| A | Meets all dimensions | Pass |
| B | P0 met, minor flaws | Pass + optimization suggestions |
| C | Minimum deliverable | Pass + improvement suggestions |
| D | P0 unmet | **Reject the output and fix** |

Pre-output checklist:

```
□ No placeholder residue (TODO/待补充/TBD/FIXME/XXX)
□ Sections complete (against the template)
□ Revision history updated (documents)
□ Paths accurate (iteration artifacts in the iteration dir, project prototype in prototype/, business code inside declared repos)
□ Compliance self-check against language standards (code)
□ No hard-coded credentials; error handling present (code)
```

## 5. Violation handling flow

```
Detect violation → grade it (P0/P1/P2)
  P0 → stop the current action, explain to the user, propose a fix
  P1 → warn + fix immediately then continue; if unfixable, reject the artifact
  P2 → mention it once, continue
```

## Revision history

| Date | Change |
|------|--------|
| 2026-10-16 | Add local HTML direct-preview, file-page verification, and storage-fallback constraints. |
| 2026-10-15 | Add project-level prototype paths, source traceability, and business-delivery boundaries. |

## [Next Steps]

- See the framework map and pipeline → `/hy-guide`
- Start a new requirement → `/hy-req --project {project} --title {title}`
- Register/link a new project → `/hy-project`
