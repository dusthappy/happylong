# Smoke record: $title

- Iteration: `$id`
- Status: stages.smoke = pending (update this line after the /hy-test verdict; all-pass → pass, any fail → fail)

> At least one row per PRD AC; fail items loop back to /hy-fix and rerun.

| # | Verification item | AC | Result | Evidence (command output / screenshot path / URL) |
|---|-------------------|----|--------|---------------------------------------------------|
| 1 |  |  |  |  |

## Regression (existing test suites per repos_in_scope repo)

> Run each repo's existing suite (go test / cargo test / in-repo test scripts) as a gate independent of the ACs; results count toward the smoke verdict — any fail means stages.smoke=fail.

| Repo | Suite command | Result | Evidence |
|------|---------------|--------|----------|
|  |  |  |  |

## Verdict

(pass / fail and why)
