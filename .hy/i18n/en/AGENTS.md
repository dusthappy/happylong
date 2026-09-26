---
description: happlylong (hy) global agent spec for a personal multi-project product-dev workbench
alwaysApply: true
---

# happlylong Agent Behavior Spec

> **Version**: 0.1.2 | **Updated**: 2026-09-24
> happlylong (**hy** for short) is a product-dev workbench serving multiple personal projects under `workspace/`.
> Design tenets: **single lightweight track, zero platform mirroring, the CLI is the source of truth**.

---

## 1. Core model (understand this before the constraints)

```
happlylong/                     ← framework root (directory containing this file)
├── happlylong.py / .bat        ← the only tool: skeleton / symlinks / iterations / session / doctor / language
├── CLAUDE.md                   ← Claude Code entry (@AGENTS.md reference, install artifact)
├── .agents/skills/hy-*/        ← installed skills (active language set, install artifact)
├── .hy/                        ← config, session, templates, language sources
│   ├── config.yaml             ← conventions (ID format / stages / roles / quality bar)
│   ├── session/                ← local session state (the whole directory is untracked)
│   │   ├── bindings/{hash}.yaml ← one iteration binding per agent session
│   │   ├── current.yaml        ← legacy only (manual migration; never read automatically)
│   │   └── prefs.yaml          ← command-language preference
│   └── i18n/{zh,en}/           ← language sources (skills/ + AGENTS.md + templates/)
├── shared/                     ← cross-project standards (general/TS/Go/Rust/security/testing/Git, published)
└── workspace/                  ← local business area (personal content; the whole directory is never committed)
    ├── _index.yaml             ← project registry
    └── {project}/              ← business project slot
        ├── profile.yaml        ← repo registry (role/shared/backend_apps/desc/langs/pending)
        ├── code_lib/{repo} →   ← symlinks to real codebases (where changes land)
        ├── knowledge/{repo}/   ← knowledge base (overview/api/data/changelog, maintained by /hy-knowledge)
        └── iterations/{id}/    ← iteration artifacts (prd/contract/plan/smoke/implementation/attach)
```

**Iteration ID**: `{YYMMDD}-{type}-{slug}`, type ∈ feat|fix|refactor|doc|chore.
**Three-stage state machine** (SSOT at iteration `_index.yaml → stages`): `prd → dev → smoke`; contract closure is a separate `_index.yaml → contract` field (closed within `/hy-req`, dev stage-0 as fallback).
**Repo dev order**: backend/service-role repos first, the rest in profile declaration order; a shared backend/service-layer repo (e.g. shared_be) is routed to subproject directories via `backend_apps.{name}.paths`.

## 2. Skill system (all hy- prefixed)

| Capability | Trigger | Description |
|------------|---------|-------------|
| Meta-spec | `/hy-spec` | P0/P1 constraints + execution lifecycle + output quality (a must-know for every session) |
| Navigation | `/hy-guide` | framework map and pipeline navigation |
| Role chain | `/hy-roles` | PM/architect/developer personas combined (clarify/gate/protect), review only, no writes |
| Project/symlinks | `/hy-project` | new project registration, three symlink modes, pending linking |
| Iteration+PRD | `/hy-req --project X --title T` | explicit `--title` always creates and binds; without it, continue/revise by session state, or prompt to bind existing/create new when unbound |
| Dev | `/hy-dev` | four-stage state machine (contract fallback → plan → implement → self-check) + automatic multi-repo chaining |
| Fix | `/hy-fix` | systematic defect fixing (fix-*.md trail) |
| Recheck | `/hy-review` | independent recheck / code review (review.md verdict) |
| Smoke | `/hy-test` | smoke.md (AC↔result↔evidence), fail flows back to /hy-fix |
| Knowledge | `/hy-knowledge` | code injection (bootstrap cold start) + iteration change distillation (iteration) |

**Cross-agent session isolation**: each agent session binds to exactly one iteration, and that binding must explicitly belong to exactly one `workspace/{project}`. Both active and previous records require `project`, `iteration_id`, and `iteration_path`; the path must be exactly `workspace/{project}/iterations/{iteration_id}`. The tool validates this invariant at both read and write boundaries and fails closed, so a workspace must never be inferred from a bare iteration ID, recency, or cwd. Identity precedence is a leading `--session-id` → `HY_SESSION_ID` → `CODEX_THREAD_ID` (the Codex adapter). Every entry point maps the same raw ID to the same namespaced SHA-256 digest; the raw ID is never persisted. Other agents must inject a stable, unique `HY_SESSION_ID` into the session launch environment and keep it unchanged across context compaction and process resumption. For a cross-agent handoff of one logical session, both sides use the same ID but only one writer may be active at a time; genuinely concurrent sessions require different IDs. Before running hy commands, run `session show` and check `session_scope.fingerprint`: if it matches another parallel session, the line is cross-wired — switch to a distinct ID immediately; any named shared ID (e.g. a mainline ID) belongs to exactly one session at a time and must never be reused by a second session. Platforms with SessionStart hooks (e.g. ZCode) should configure a workspace hook that injects `${CLAUDE_SESSION_ID}` via additionalContext as a per-session-unique `--session-id hy-<CLAUDE_SESSION_ID>`, preventing shared-ID cross-wiring at the supply side. Without a trustworthy ID, binding-dependent commands must fail closed; reading or writing the shared `.hy/session/current.yaml` is forbidden.

**Unbound-session entry gate (execution requests)**: on the first `/hy-*` or natural-language request that would advance requirements, development, fixing, rechecking, smoke testing, or iteration distillation, first run `python3 happlylong.py session show`. Pure Q&A, `/hy-spec`, `/hy-guide`, `/hy-roles`, project/symlink onboarding, framework diagnostics, framework-source maintenance and open-source/release preparation, and `/hy-knowledge bootstrap` do not require a business-iteration binding. When a stable identity exists but the structured result says `active: false` with `entry_gate.policy: ask_first_bind_or_create`:

1. **The sole exception is `/hy-req` with an explicit `--title`**: it is an unambiguous “new PRD” signal. Do not ask whether to bind or create; resolve or confirm `project`, then create and bind a new iteration immediately. Even when another iteration is already bound, open a new one and move the old binding to `previous`.
2. For every other execution request, run `iter list` to show candidates, then Ask-First whether to **bind an existing iteration** or **create a new iteration**. Prefer the host's structured question/choice UI when available; otherwise ask an equivalent explicit question. A recommendation may follow from the original intent, but never select it for the user.
3. Bind existing: ask only for any missing project/iteration ID, run `session set`, verify with `session show`, and resume the original request. Create new: collect project/title/type/requirement body, route through `/hy-req` to complete the PRD, then continue according to the original request and its stage prerequisites.
4. If the selected project/iteration is invalid or information remains incomplete, keep the gate closed, create no iteration artifacts, make no `code_lib/` changes, show valid candidates again, and repeat Ask-First. Stop when the user explicitly cancels.

**Iteration resolution order**: explicit `--project + --iteration-id` > the current session binding. When passed alone, `--project` must match the project already bound to the current session; no project-level shared pointer is used to guess across sessions.

**Command language**: skill sources live in `.hy/i18n/{zh,en}/skills/`; `.agents/skills/` and this file are install artifacts, switched via `python3 happlylong.py lang zh|en` (the first `init` detects the system locale once and pins it). To change instructions, edit the matching language source and re-run the switch command.

## 3. P0 red lines (violation = stop immediately)

**Security**: no hard-coded credentials (passwords/keys/tokens); no SQL string concatenation (parameterize everything); every endpoint must verify permissions; no bare `except` (exceptions must be handled or logged).

**Business**:
- **No PRD, no code changes**: while `stages.prd ≠ done`, changing anything under `code_lib/` is forbidden (P0; even a hotfix requires completing a PRD first or explicit permission).
- **Snapshot before deleting data**: any data/file deletion must first record the pre-deletion state.
- **No automatic git commits**: without an explicit user request, never run `git add/commit/push`; leave working-tree changes for user review.
- **Single artifact path**: iteration artifacts go only to `workspace/{project}/iterations/{id}/`; framework files only to `.agents/` and `.hy/`; no scattering outside the framework.
- **Never guess session identity**: binding-dependent operations must stop when no trustworthy session ID is available. Never infer it from the cwd, process ID, terminal, latest iteration, or a shared `current.yaml`.
- **Every binding names its workspace**: active and previous bindings must carry a valid `project`, and their path must exactly match `workspace/{project}/iterations/{iteration_id}`. Missing fields or a mismatched path stop execution.
- **No execution while unbound**: except for the explicit new-iteration signal `/hy-req --title`, execution requests must pass the Ask-First “bind existing / create new” gate. Do not write iteration artifacts or business code before the user chooses.

## 4. P1 hard constraints

- Always use `pathlib.Path` for paths (tool scripts); never depend on cwd — anchor at the framework root.
- No `except: pass`; no bare `raise` — use custom exceptions.
- No placeholder residue in output (TODO/待补充/TBD/FIXME); document changes must update the revision history.
- Load code standards by language: `shared/standards/{typescript,go,rust}.md` + `coding-standards.md` (general & Git); for security/testing see `security-rules.md` and `testing-standards.md`.
- Cross-platform access: AGENTS.md is the cross-platform open standard (this file, `CLAUDE.md` and `.agents/skills/` are all **local install artifacts** generated by `init`/`lang`; language sources live in `.hy/i18n/{lang}/`); Claude Code reads the root `CLAUDE.md` (an `@AGENTS.md` reference) automatically — to also get the `/hy-*` skills, link them yourself (`mkdir -p .claude && ln -s ../.agents/skills .claude/skills`); the framework maintains no mirror directories.

## 5. Skill execution lifecycle

```
Trigger → identity check (stable session ID) → session gate (if unbound, run the Ask-First bind/create loop; hy-req --title creates directly)
        → context gathering (resolve the binding with happlylong.py session show, then read the iteration _index.yaml + profile.yaml)
        → checkpoint (precondition validation; on failure give clear guidance)
        → execution (advance the state machine; artifacts land in the iteration dir)
        → quality validation (placeholders / completeness / path correctness)
        → finalize (write back stages, output Next Steps)
```

**Ask-First principle**: stop and ask only for "decisions you are unsure about" (question + options + recommendation); routine progress runs automatically and continuously — go as far as a single request allows.

## 6. Quality grades

A (meets all dimensions) | B (P0 met, minor flaws) | C (minimum deliverable) → pass; **D (P0 unmet) → reject and fix**. Minimum delivery line: C (see `.hy/config.yaml`).

## 7. Violation handling

P0 → stop immediately + explanation + fix suggestion; P1 → warn and fix; P2 (suggestions) → note and continue.

---

*happlylong v0.1.2 · single-track lite · zero mirroring · the CLI is the source of truth*
