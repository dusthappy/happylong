---
name: hy-knowledge
description: "Project knowledge-base bootstrap and iteration distillation: bootstrap mode builds initial knowledge directly from source code (zero-iteration cold start), iteration mode extracts feature changes from a completed iteration; drives the happlylong.py knowledge subcommand. Triggered by /hy-knowledge."
metadata:
  hy:
    command: hy-knowledge
    kind: knowledge
    entry: true
---

# hy-knowledge · Knowledge base

> Distill "stable facts from the code and iterations" into project history: newcomers (including future agent sessions) read the knowledge base to build context quickly instead of re-analyzing the whole repo every time. Both modes share one artifact structure; bare invocation auto-routes.

## Knowledge base structure

```
workspace/{project}/knowledge/
├── _index.yaml            ← registry (CLI-maintained): per-repo files/updated/source
└── {repo}/
    ├── overview.md        ← always: positioning/stack/directory map/startup & verification/conventions/repo relations
    ├── api.md             ← only for HTTP backends: interfaces grouped by module
    ├── data.md            ← only with persistence: schema/table list and definition locations
    └── changelog.md       ← iteration log (appended by iteration mode, newest on top)
```

**Writing principles**: record only stable facts (structure, conventions, lists, relations) — no implementation details, no code restatement; always tag the source `bootstrap` (built from source code) or `iteration` (iteration distillation); conclusions must be verifiable against code — when docs contradict code, code wins and the knowledge gets fixed (unresolvable contradiction → checkpoint, ask the user).

**Shared-repo knowledge ownership**: when one shared repo (e.g. shared_be) is mounted by multiple projects, **full knowledge lives only in the "primary consumer project"** (the project whose submodule actually exists, e.g. example); other projects (e.g. example_game) keep only a light-reference overview (explaining the sharing relationship + the subproject plan from this project's perspective + pointing to the full knowledge path on the primary side) — no api/data/changelog copies, avoiding double-drift. iteration distillation also writes only to the primary side (changelog notes affected subprojects).

## Mode routing (bare invocation)

```
/hy-knowledge
  ├─ knowledge/_index.yaml missing, or a registered repo lacks overview.md ─→ bootstrap (fill gaps first)
  ├─ session iteration status=done or smoke=pass, and changelog lacks it ─→ iteration
  └─ neither ─→ show the knowledge status report (freshness / gaps)
```

Explicit: `/hy-knowledge bootstrap [--project X] [--repo Y]`, `/hy-knowledge iteration [--iteration-id {id}]`.

**Session gate**: `bootstrap` and a read-only `knowledge status` report require no iteration binding. Only when entering `iteration` mode, run `session show` first. If unbound, use `iter list [project]`, then enter an Ask-First loop in which the user chooses to bind an existing iteration or create a new one. After binding, verify with `session show` and resume distillation. If the user chooses a new iteration, route through `/hy-req` and resume only after that iteration meets the smoke=pass/closed prerequisite. Invalid or incomplete input keeps the gate closed, writes no knowledge files, and repeats the question until cancellation. Even an explicit `--iteration-id` must be confirmed and persisted as the session binding first.

## bootstrap · Build knowledge from source code (zero-iteration cold start)

Applies to: newly onboarded projects, or a knowledge base so stale you want to rebuild understanding wholesale.

1. **Prepare**: `python3 happlylong.py knowledge init --project {project}` (skip if initialized; `--force` refreshes the registry per repo without touching md files).
2. **Per-repo analysis** (parallelizable), evidence sources by priority: in-repo AGENTS.md/CLAUDE.md/README → directory structure and manifests (package.json/go.mod/Cargo.toml/pages.json etc.) → key entry-point code. Shared repos (shared_be) are analyzed grouped by `backend_apps` subproject.
3. **Outputs**:
   - `overview.md` (always): fill all five template sections; "conventions" is generalized from neighboring code (naming/layering/error handling/request wrappers) — the most valuable input for future development.
   - `api.md`: for backend repos, scan route registration (Go: api/ and internal/server) into a **module-level** interface list (route/method/description/auth); no per-parameter enumeration — module-level usable is enough.
   - `data.md`: scan ent schema / sql/ / schemas/ for the table list and definition locations; shared repos sectioned by subproject.
   - Frontend repos produce overview.md only.
4. **Register**: after each repo, `python3 happlylong.py knowledge register --project {project} --repo {repo} --source bootstrap --file overview.md [--file api.md --file data.md]`.
5. **Report**: one summary paragraph per repo + verify coverage with doctor.

**Scale discipline**: per-repo bootstrap output — overview ≤80 lines, api/data ≤120 lines each; information density over enumeration — if a list gets too long, converge to module level and note "details at code location".

## iteration · Distill iteration changes

Applies to: after an iteration reaches smoke=pass (or is closed), distill "what was done, what changed, what was learned" into the knowledge base. `/hy-test` all-pass and the `git-workflow` closing steps both point here.

1. **Locate the iteration**: use only a session binding that passed the entry gate and was verified; `--iteration-id` identifies the target to confirm and bind, not a gate bypass. Read `_index.yaml` (repos_in_scope/stages) + `prd.md` (ACs) + `contract.md` (interface/table changes) + `plan.md` (tasks and evidence).
2. **Append per repo** (only repos inside repos_in_scope):
   - `changelog.md`: add a section on top — iteration ID + date + one-line feature + change highlights (new interfaces/tables/page changes, referencing the contract section) + lessons learned (if any).
   - New interfaces/tables from `contract.md` → append to the matching module sections in `api.md` / `data.md` (keep lists current).
   - If the iteration changed repo structure/conventions (new layer, new request wrapper, etc.) → refresh the matching `overview.md` section and bump its "updated" date.
3. **Register**: `knowledge register --source iteration --file changelog.md [--file api.md --file data.md --file overview.md]`.
4. **Report**: which repos/files were distilled; knowledge freshness (`knowledge status`).

**Discipline**: changelog records deltas only, never rewrites history; iterations without all ACs passing are not distilled (fix first); each repo appends its own changelog — no cross-repo mixing.

## Checkpoints (Ask-First)

- Code contradicts existing knowledge and cannot be adjudicated (the code might be wrong);
- A shared repo shows common-layer changes with no subproject attribution that would be written into knowledge;
- Abnormal repo size at bootstrap (e.g. exhaustively enumerating all shared_be interfaces would spiral) → confirm convergence granularity first.

## Quality checklist

- No placeholder residue in bootstrap/iteration outputs; every file's "source/updated" line filled.
- Registered files actually exist; `doctor` section [5] knowledge base shows no missing-overview warnings.
- A repo never iterated may have no changelog.md (don't create empty shells).

## [Next Steps]

- Bootstrap done → `/hy-req` to open the first requirement (hy-dev uses overview as context)
- Iteration closing → after `/hy-test` all pass, run `/hy-knowledge iteration`
- See coverage and freshness → `python3 happlylong.py knowledge status`
