schema: 1
id: $id
title: $title
type: $type
project: $project
status: open          # open | done | abandoned
created: $created
updated: $created
summary: ''

# Repos involved in this requirement (written back after the /hy-req decision; backend first)
repos_in_scope: []

# Three-stage state machine (SSOT, read/written by every skill)
stages:
  prd: pending        # pending | done
  dev: pending        # pending | in_progress | done
  smoke: pending      # pending | pass | fail

# Contract closure state (closed by /hy-req branching; hy-dev stage-0 as fallback)
contract: pending     # pending | done | skipped
contract_note: ''     # rationale (required when skipped)
