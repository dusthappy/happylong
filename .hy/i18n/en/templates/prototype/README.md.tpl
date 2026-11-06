# $project_name product prototype

This directory sits beside `iterations/` and contains cross-iteration screens, interaction demos, and design notes. Requirements, contracts, and acceptance evidence remain in their respective iteration documents.

## Usage

- Create `index.html` here, or set `_index.yaml → entry` to a relative `.html`/`.htm` file within this directory; `preview_mode` is `file`. Double-click the entry to try it in a browser without running a server.
- List source iteration IDs from this project under `_index.yaml → source_iterations`; record requirement links in the design notes as well.
- Set `status` to `draft` once the entry exists. Mark it `ready` only after opening through `file://`, verifying key interactions, assets, and storage fallback, and completing prototype review; update `updated`. CLI static checks do not replace browser verification.
- Run `python3 happlylong.py prototype show $project_name` to view the path, entry, and status. `prototype preview $project_name` returns the local file entry; add `--open` to open its file URI in the system default browser. No server is started.
- Repeating `prototype init $project_name` only adds missing scaffold files and preserves existing content; `doctor --fix` also never rewrites an existing manifest.

## Local-file compatibility

Prototypes must open directly as local HTML in a browser (`file://`), using relative CSS, classic scripts, media paths, or inline assets. Do not require users to run Node/npm, a server, or a build first. Keep demo data in local classic scripts or HTML; do not depend on fetching local JSON, ES modules, a CDN, or service workers. If the browser restricts storage on file pages, visibly fall back to current-page state and offer export; never automatically migrate data from the old HTTP origin. Before marking a prototype `ready`, open it through `file://` and verify key interactions, assets, and storage fallback. Static metadata checks do not replace runtime verification.

## Boundaries

Clearly label example data, simulated APIs, and demonstration states. Completing a prototype does not advance `prd/dev/smoke` or replace real API integration, deployment, or iteration acceptance. Production implementation still belongs in registered `code_lib/` repositories. The directory, manifest, and entry must not be symlinks or point outside this directory.

## Revision history

| Date | Change |
|------|--------|
| $created | Initialize the prototype directory, direct local HTML preview, and file-page verification conventions. |
