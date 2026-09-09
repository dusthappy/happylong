---
name: hy-guide
description: 'happlylong framework navigation: directory map, req→dev→test pipeline, scenario-based quick reference, glossary. Triggered by /hy-guide or "how do I use hy / framework map / what commands exist".'
metadata:
  hy:
    command: hy-guide
    kind: meta
    entry: false
---

# hy-guide · Framework navigation

## Pipeline map

```
/hy-project ─┐
             ├─→ /hy-req ─→ /hy-dev ─→ /hy-test ─→ (user commits) ─→ iter close
(projects/links)  │            │           ↑      │ fail
                  │            │           └─ /hy-fix ┘
                  │            └─ /hy-review (independent recheck)
                  │ iteration creation + PRD + contract branching are completed inside /hy-req (dev stage 0 is only a fallback)
                  └ role-chain personas summonable anytime: /hy-roles (PM/architect/developer)
```

- **State machine SSOT**: `workspace/{project}/iterations/{id}/_index.yaml → stages` (prd/dev/smoke; contract closure recorded in the separate `contract` field).
- **Session**: every agent session owns one atomically written binding file at `.hy/session/bindings/{hash}.yaml`; omitted command arguments are filled only from the current session. Both active and previous records must explicitly carry `project`, `iteration_id`, and the canonical `iteration_path`, uniquely pointing to `workspace/{project}/iterations/{iteration_id}`. Identity precedence is a leading `--session-id` → `HY_SESSION_ID` → `CODEX_THREAD_ID`. Every entry point maps the same ID to the same digest, and the raw ID is never persisted. Without a trustworthy ID or a consistent workspace scope, commands fail closed and never fall back to the shared `.hy/session/current.yaml`.
- **Unbound entry**: an execution-oriented `/hy-*` or natural-language request starts with `session show`; if unbound, run `iter list` and enter an Ask-First loop in which the user chooses either an existing iteration or a new one. Only explicit `/hy-req --title` is a definite new-PRD signal and may create directly after resolving the project. Framework-source maintenance, diagnostics, and open-source/release preparation are not business iterations and do not trigger this gate.

## Command quick reference

| Command | In one line | Key arguments |
|---------|-------------|---------------|
| `/hy-req` | Open iteration + single-file PRD: explicit `--title` always creates new; otherwise continue/revise according to binding state, or ask bind vs create | `--project` (defaults to session) `--title` (strong new-PRD signal) `--type feat\|fix\|refactor\|doc\|chore` |
| `/hy-dev` | Four-stage development flow: contract fallback → plan → implement → self-check; automatic multi-repo BE→FE chaining | optional `--repo {name}` to focus one repo |
| `/hy-fix` | Systematic fixing: reproduce → locate → minimal fix → verify, `implementation/fix-{date}.md` | paste the defect description directly after the command |
| `/hy-review` | Independent code review, producing `implementation/review.md` | may target a single repo |
| `/hy-test` | Smoke: ACs → checklist → `smoke.md` four-column table | fail auto-routes to `/hy-fix` |
| `/hy-knowledge` | Knowledge base: bootstrap builds from source code / iteration distills changes | no args auto-routes |
| `/hy-project` | New project / three symlink modes / pending linking | drives `happlylong.py project\|link` |
| `/hy-spec` | Meta-spec (constraints + lifecycle + quality) | — |
| `/hy-roles` | Role-chain personas (PM clarification / architecture gating / implementation guard), review only | summon per perspective; artifacts land via /hy-req, /hy-dev |

Tool-side commands (`python3 happlylong.py [--session-id ID] …`): `--session-id` is the explicit cross-agent identity and must precede the subcommand. Subcommands are `init [--lang zh|en] / lang [zh|en] / release-check / status / doctor --fix / project new / link add|rm|apply|list / iter new|list|show|close / knowledge init|register|status / session show|set|back|clear`.

## Navigate by scenario

| Scenario | Action sequence |
|----------|-----------------|
| Definite new requirement | `/hy-req --project X --title T` (always creates and binds a new iteration) → `/hy-dev` → `/hy-test` |
| New session receives an execution command or natural-language requirement | `session show` → if unbound, `iter list [project]` → Ask-First loop: bind existing/create new (repeat on invalid input) → resume the original request |
| Continue an existing iteration | `/hy-dev`; a bound session auto-routes, an unbound one first presents the entry choice |
| Fix a production/test bug | `/hy-fix`; if unbound, first choose an existing iteration or create a fix iteration; after the fix, `session back` returns to the original iteration |
| Smoke failed | `/hy-fix` (fix) → `/hy-test` (rerun failed items) |
| Implementation quality doubts | `/hy-review` |
| Switch project/iteration | `python3 happlylong.py session set {project} {iteration_id}` or open a new `/hy-req`; `session back` returns to the previous binding |
| Run multiple agents or sessions concurrently | Codex isolates them automatically through `CODEX_THREAD_ID`. For every other agent, set a stable, unique `HY_SESSION_ID` in each session's launch environment, keep it unchanged across compaction, and then run `session set` or `/hy-req`; reuse an ID only for a serial handoff of the same logical session, never for concurrent writers |
| Onboard a new project | `/hy-project` (three modes: single repo / FE+BE / shared backend + subproject) |
| Build project knowledge after onboarding | `/hy-knowledge bootstrap --project X` (builds overview/api/data from source code) |
| Distill after an iteration | `/hy-knowledge iteration` (pass the entry gate if unbound; changelog entries + api/data deltas) |
| Directory or symlink suspicious | `python3 happlylong.py doctor --fix` |

## Glossary

| Term | Meaning |
|------|---------|
| project | a business project slot under `workspace/` (e.g. the example / example_game samples) |
| repo | a real codebase behind one symlink in `code_lib/` |
| role | repo role: frontend / backend / fullstack / lib |
| shared repo | a backend repo mounted by multiple projects (e.g. shared_be) |
| backend_apps | business submodules inside a shared repo (e.g. shared_be's example: api/example, internal/{biz,service,data}/example, sql/example) |
| pending repo | registered, target dir not ready, symlink to be linked later |
| iteration | `iterations/{YYMMDD}-{type}-{slug}/` — all artifacts of one requirement |
| knowledge | `workspace/{project}/knowledge/{repo}/` — the project's accumulated understanding (overview/api/data/changelog) |
| stages | prd / dev / smoke stage states; contract closure recorded in the separate `contract` field (done/skipped) |
| AC | PRD acceptance criteria, numbered AC-001…; one smoke row per AC |
| Checkpoint (Ask-First) | an uncertain decision, plus the mandatory choice at an unbound entry; stop until the user answers, otherwise run automatically |

## [Next Steps]

- New requirement → `/hy-req --project {project} --title {title}`
- Health-check the environment first → `python3 happlylong.py --session-id {stable-session-id} doctor` (omit the leading option when `HY_SESSION_ID` or Codex's automatic identity is already available)
- See constraints and the quality bar → `/hy-spec`
