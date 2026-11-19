---
name: hy-dashboard
description: "Refresh the happlylong workspace dashboard to see all registered projects, their frontend and backend repositories, and every iteration with its stage states in one local HTML file. Use for /hy-dashboard or requests to view or refresh the project overview."
metadata:
  hy:
    command: hy-dashboard
    kind: workspace
    entry: false
---

# hy-dashboard · Workspace dashboard

Run `python3 happlylong.py dashboard`. When outside the framework root, use the absolute path to this workspace's `happlylong.py`. Add `--open` when the user asks to open the result.

The tool builds a snapshot from the project registry, repository profiles, and iteration metadata. The first run creates `workspace/dashboard.html`. Later runs refresh the same file. Use the tool to generate the HTML so each run writes to the same path. Generation and offline viewing require neither a server nor an iteration binding.

On success, link to the local HTML path returned by the tool. Report the affected location and reason if the tool encounters a read or write problem.

## Revision history

| Date | Change |
|------|--------|
| 2026-11-18 | Add the workspace dashboard skill. |

## [Next Steps]

- Refresh after data changes → `/hy-dashboard`
- Refresh and open from the terminal → `python3 happlylong.py dashboard --open`
