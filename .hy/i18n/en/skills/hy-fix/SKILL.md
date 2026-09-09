---
name: hy-fix
description: "Systematic defect fixing: reproduce → locate → minimal fix → verify, producing an implementation/fix-{date}.md trail linked to plan task status; also the re-entry point for /hy-test smoke failures. Triggered by /hy-fix."
metadata:
  hy:
    command: hy-fix
    kind: lifecycle
    stage: dev
    entry: true
---

# hy-fix · Defect fixing

> The single entry point for bug fixing (production bugs / test failures / smoke failures alike). The flow is `/hy-dev` stage 2's fix mode plus the trail template.

## Session entry gate (P0)

- Resolve the current session with `session show`. If unbound, run `iter list [project]`, then enter an Ask-First loop in which the user chooses to **bind an existing iteration** or **create a new iteration**. Never equate “this is a new defect” with permission to create on the user's behalf.
- Bind existing: collect the project/iteration ID, run `session set`, verify with `session show`, then resume the original defect report. Create new: preserve the defect report, confirm project/title/slug/type (recommend `fix`), then use explicit `/hy-req --type fix --title "brief defect"` to create the iteration and complete a minimal PRD before resuming this `/hy-fix`.
- Invalid or incomplete input keeps listing candidates and asking until cancellation. Before the gate and PRD pass, write no fix artifact and change no code.

## Inputs

| Source | Description |
|--------|-------------|
| Session | `project` / `iteration_id` from a verified binding; when switching, the displaced in-flight iteration is automatically saved to `previous` |
| Trailing free text | Defect description: symptoms, repro steps, expected vs actual |
| Loop back | `/hy-test` smoke fail items (AC and failure evidence attached) |

## Flow (systematic debugging)

```
① Reproduce   run it as described; confirm the symptom is stable and reproducible; not reproducible → checkpoint (ask for more info, don't fix blind)
② Locate      start from the symptom: read code paths/logs/data → hypothesis → verify the hypothesis with a minimal experiment
③ Root cause  pin down the single minimal fix point; multiple candidate causes → checkpoint (Ask-First), present verification evidence and cost for each
④ Fix         minimal change: fix only the root cause; no drive-by refactoring, no scope growth; repo choice follows /hy-dev stage-2 coding and verification baseline
⑤ Verify      re-run the repro steps to confirm the fix + regression-check adjacent features; leave an evidence trail
```

## Trail (P1)

- Generate `implementation/fix-{YYYY-MM-DD}.md` from `.hy/i18n/{lang}/templates/iteration/fix.md.tpl`: symptoms & repro / root-cause analysis / fix / verification.
- Link with `plan.md`: tick the matching task if it exists; otherwise append a task row (tagged `fix` origin + related AC).
- Smoke loop-back case: do not rewrite fail rows in `smoke.md`; append rerun rows; `stages.smoke` is re-judged by the next `/hy-test`.

## Checkpoints

- Fix touches repos/paths beyond the plan declaration → scope checkpoint.
- Root cause lies in a dependency / third party / the data itself (not code) → stop, explain, hand the decision to the user.
- **No PRD, no code changes applies to fixes too**: fixing a production issue outside an iteration requires at least a minimal fix-type PRD.

## [Next Steps]

- Re-run smoke → `/hy-test` (failed items + regression is enough)
- Quality doubts or requirement changes → `/hy-review`, or revise with `/hy-req` before `/hy-dev`
- Return to the original in-flight iteration → `python3 happlylong.py session back`
