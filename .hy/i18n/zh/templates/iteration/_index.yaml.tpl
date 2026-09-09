schema: 1
id: $id
title: $title
type: $type
project: $project
status: open          # open | done | abandoned
created: $created
updated: $created
summary: ''

# 本次需求涉及的仓库（由 /hy-req 判定后回写；backend 在前）
repos_in_scope: []

# 三阶段状态机（SSOT，各 Skill 读写）
stages:
  prd: pending        # pending | done
  dev: pending        # pending | in_progress | done
  smoke: pending      # pending | pass | fail

# 契约闭合状态（/hy-req 契约三分支闭合；hy-dev 阶段0 兜底）
contract: pending     # pending | done | skipped
contract_note: ''     # 判定理由（skipped 时必写）
