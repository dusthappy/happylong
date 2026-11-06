---
name: hy-project
description: "workspace project and codebase symlink management: project new / link add three modes (single repo, FE+BE dual repos, shared backend + subprojects) / prototype directory / pending linking / doctor check. Triggered by /hy-project when onboarding a project, managing prototype directories, or when symlinks misbehave."
metadata:
  hy:
    command: hy-project
    kind: workspace
    entry: false
---

# hy-project · Projects and symlinks

> All mechanical operations go through `happlylong.py`; this skill owns the judgment and demonstration of how to register. The tool anchors the framework root to the script's location and can run from any cwd (use the script's absolute path when outside the root). Real codebases are never moved into the framework — only absolute-path symlinks.

## Registration model

Each symlink is registered into `workspace/{project}/profile.yaml → repos`:

```yaml
repos:
  example_fe:                    # repo name = symlink name under code_lib/
    role: frontend               # frontend | backend | service | fullstack | lib (--role is mandatory at registration)
    desc: owns demo web pages and interactions # one-line functional role (recommended; doctor warns when missing)
    target: /abs/path/example_fe # absolute path
    langs: [typescript, vue]     # code languages: explicit --lang wins, else auto-detected, hand-editable
  shared_be:
    role: backend
    shared: true                 # cross-project shared repo (mounted by both example and example_game)
    target: /abs/path/shared_be
    backend_apps:                # business submodules inside the shared repo (coding route scope; backend/service repos)
      example:
        title: example backend submodule
        paths: [api/example, internal/biz/example, internal/service/example,
                internal/data/example, sql/example]
      example_game:
        title: example_game backend submodule (reserved)
        paths: [api/example_game, internal/biz/example_game, internal/service/example_game, internal/data/example_game, sql/example_game]
```

Rules:
- **registration declares responsibility**: `--role` is mandatory — state whether each repo is frontend, backend, service layer, fullstack, or lib; pair each repo with `--desc` (one-line functional role) and `--lang` (code languages); doctor warns on missing desc.
- **role decides dev order**: backend/service repos first, the rest in declaration order (`/hy-dev` chains on this rule).
- **shared repos must declare backend_apps**: coding is confined to paths — crossing the boundary is a scope checkpoint (Ask-First).
- **pending**: register first when the target dir doesn't exist yet, link later; no dangling symlinks (`--lang` may declare code languages upfront).

## Three onboarding modes (copy and change the paths)

### Mode A · Single repo (example_rs style)

```bash
python3 happlylong.py project new demo --title "Demo"
python3 happlylong.py link add demo demo /abs/demo --role fullstack --desc "single fullstack repo: pages and API in one"
```

### Mode B · FE + BE dual repos (example style)

```bash
python3 happlylong.py project new demo --title "Demo"
python3 happlylong.py link add demo demo /abs/demo_fe --role frontend --lang typescript --desc "demo web frontend (Vue)"
python3 happlylong.py link add demo demo_be /abs/demo_be --role backend --lang go --desc "demo business backend"
# multiple frontends (example_fe style): keep adding role=frontend links (declaration order = dev order)
```

### Mode C · Shared backend + subproject (example / example_game style)

```bash
python3 happlylong.py project new demo --title "Demo"
python3 happlylong.py link add demo demo /abs/demo_fe --role frontend --lang typescript --desc "demo web frontend (Vue)"
python3 happlylong.py link add demo shared_be /abs/shared_be --role backend --lang go --shared \
  --app demo=api/demo,internal/biz/demo,internal/service/demo,internal/data/demo,sql/demo \
  --desc "shared business backend, coding routed per subproject" \
  --note "follows shared_be layering conventions; adjust the profile if the subproject paths differ once created"
```

> Pure service-layer repos (gateway/BFF/middleware) use `--role service`; when shared, they likewise route subprojects via `--app`.

> Mounting the same shared repo into multiple projects is **expected behavior** (shared_be sits under both example and example_game); iteration artifacts stay separate per project in their own `iterations/`.

## Pending workflow

```bash
# register (no dangling link even if the target doesn't exist; --lang may declare code languages upfront)
python3 happlylong.py link add demo demo_new /abs/demo_new --role frontend --lang typescript --desc "new admin console" --pending
# one-shot linking once the target exists (doctor also reports pending)
python3 happlylong.py link apply demo
```

## Project-level product prototype

`project new` automatically scaffolds `prototype/_index.yaml` and `prototype/README.md` alongside `iterations/`. Add missing files to existing projects through the tool:

```bash
python3 happlylong.py prototype init demo
python3 happlylong.py prototype show demo
python3 happlylong.py prototype preview demo
python3 happlylong.py prototype preview demo --open
```

- `init` only creates missing scaffold files without overwriting content or generating placeholder business pages; `show` validates and displays metadata and `entry_uri`. `preview` requires an existing entry and returns its local file location; only `--open` opens the file URI in the system default browser. Preview never starts a server, and these commands never change iteration bindings or business stages.
- `_index.yaml` fields are `schema: 1`, `project`, `title`, `entry`, `preview_mode: file`, `status`, `source_iterations`, `created`, and `updated`. Schema 1 manifests without `preview_mode` default to `file`. The entry must be a relative `.html`/`.htm` file within the prototype directory; source iterations must exist in the same project.
- `status` is `planned/draft/ready`; `planned` permits an entry that has not been created, while `draft/ready` require an existing entry. `ready` means the prototype is reviewable only.
- README records source roadmap, PRD, requirements coverage, and page versions, with mocked services, instructions to double-click the HTML file, and verification evidence. Maintain the cross-iteration prototype here only; iteration-specific attachments stay in `attach/` and link to it.
- Prototypes must open directly as local HTML in a browser (`file://`), using relative CSS, classic scripts, media paths, or inline assets. Do not require users to run Node/npm, a server, or a build first. Keep demo data in local classic scripts or HTML; do not depend on fetching local JSON, ES modules, a CDN, or service workers. If the browser restricts storage on file pages, visibly fall back to current-page state and offer export; never automatically migrate data from the old HTTP origin. Before marking a prototype `ready`, open it through `file://` and verify key interactions, assets, and storage fallback. Static metadata checks do not replace runtime verification.
- A prototype cannot replace PRDs/contracts, pass business ACs, or complete business `prd/dev/smoke` stages. Real business implementation still uses `/hy-dev` inside the declared `code_lib/` repositories.

## Inspection

```bash
python3 happlylong.py link list [project]   # status + full role/langs/desc picture
python3 happlylong.py doctor --fix          # full check + auto-fix _index/profile drift
```

Troubleshooting:
- `broken`: target moved/deleted → confirm the new path, then `link rm` and re-`link add` (no force needed).
- `no-link`: registered but the symlink is gone → `link apply {project}` skips non-pending entries; in that case rerun `link add ... --force`.
- `_index/profile drift` → `doctor --fix` syncs automatically.
- Legacy project with no `prototype/` directory at all → `doctor` only warns, without adding a failure or writing files. Opt into scaffolding with `prototype init {project}` or `doctor --fix`.
- Existing `prototype/` missing its manifest or README → `doctor` reports a failure; `prototype init {project}` or `doctor --fix` safely adds missing files. Invalid metadata, symlinks, or escaping paths → fail without overwriting; inspect and correct the declaration, then check again.

## Checkpoints

1. Confirm that you are invoking the intended framework's `happlylong.py`; from another cwd, use the script's absolute path and never infer framework state from the cwd.
2. `link add` targets must be absolute paths; relative paths are always rejected.
3. `--role` must be declared explicitly; complete each repo with `--desc` (functional role) and `--lang` (code languages) — `link list` should read as "which repo does what, on which stack" from the registry alone.
4. After onboarding, fill `profile.yaml → stack.langs/frameworks` by hand (doctor only warns on detection drift).

## Revision history

| Date | Change |
|------|--------|
| 2026-10-16 | Add local HTML preview commands, compatible metadata, direct-open constraints, and file-page verification requirements. |
| 2026-10-15 | Add project-level prototype paths, source traceability, business-delivery boundaries, and legacy-project compatibility. |

## [Next Steps]

- Project mounted, start a requirement → `/hy-req --project {project} --title {title}`
- See the framework map → `/hy-guide`
- Symlink trouble → `python3 happlylong.py doctor --fix`
