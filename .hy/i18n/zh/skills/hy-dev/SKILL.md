---
name: hy-dev
description: "一体化开发状态机：契约兜底→计划→实现/修复→自检四阶段自动路由，多仓按 backend→frontend 自动串联，Ask-First 仅卡点暂停；无 PRD 禁改码（P0）。触发 /hy-dev。"
metadata:
  hy:
    command: hy-dev
    kind: lifecycle
    stage: dev
    entry: true
---

# hy-dev · 一体化开发

> 一次请求完成全部：按迭代状态自动路由「契约兜底 → 计划 → 实现 → 自检」，多仓需求 BE 全链 pass 后**自动**切 FE 仓，不等待确认。仅卡点停下。

## 会话入口门禁（P0）

- 先运行 `python3 happlylong.py session show`；稳定身份缺失则 fail closed，禁止猜测或临时生成 ID。
- 若当前会话未绑定，运行 `python3 happlylong.py iter list [project]` 展示有效候选，Ask-First 让用户选择**绑定已有迭代**或**创建新迭代**，可推荐但禁止代选。
- 选择绑定：补齐 project/iteration ID，执行 `session set`，再用 `session show` 验证并恢复原始 `/hy-dev`。选择创建：补齐 project/title/type/需求正文，转 `/hy-req` 创建并闭合 PRD；`stages.prd == done` 后自动恢复本次 `/hy-dev`。
- 输入无效或不完整时保持门禁，重新列出候选并继续询问；用户取消才结束。门禁和 PRD 前置未通过前，不得写 plan/contract/review 或改 `code_lib/`。

## 前置（P0）

- `stages.prd == done`，否则中止并指引 `/hy-req`（**无 PRD 禁改码**）。
- 仓集合 = `_index.yaml → repos_in_scope`；为空时按 PRD 重判并回写（判定规则见 `/hy-req` ④ 仓库面判定）。
- 加载 `workspace/{project}/profile.yaml`：确认各仓 role 与 desc 功能定位、共享仓 `backend_apps`；加载 `shared/` 中与涉及语言对应的规范。
- 涉及仓若已有 `knowledge/{repo}/overview.md`（含 api/data）→ 作为仓库认知上下文加载（约定要点、既有接口与表以知识库+代码为准，知识过期时顺手提出刷新建议）。

- 若项目已有 `prototype/`，读取其 README、来源迭代和适用页面，作为交互参考；版本范围、字段与行为以当前迭代 PRD/契约为准。模拟数据和服务不得直接视为生产实现，原型检查不能代替真实接口、权限和持久化验收。仅制作原型时不进入本开发状态机，也不改变业务 `prd/dev/smoke`；交付可直接打开的本地 HTML，预览不依赖运行服务或构建。

## 状态机（每仓命中第一个未完成阶段）

```
/hy-dev [--repo {name}]
  │
  ├─ 仓集合与顺序：repos_in_scope（backend/service 在前）；--repo 聚焦单仓
  │
  ├─ 对每个仓，依次检查：
  │    contract 字段未 done/skipped 且 PRD 有数据影响 ─→ 阶段0 契约兜底
  │    无 plan.md 或 AC 集合变化                        ─→ 阶段1 计划
  │    plan 存在未闭合任务（或缺陷待修）                 ─→ 阶段2 实现/修复
  │    任务全闭合且无 review 结论                        ─→ 阶段3 自检
  │
  └─ 仓间串联：本仓阶段3 pass → 自动切下一仓（FE 仓消费 contract.md 接口要点），不停不等
```

全链完成后统一汇报：仓集合与顺序 + 各仓 plan/review 结论 + 验证证据摘要。

## 阶段细则

### 阶段 0 · 契约兜底

仅当 `/hy-req` 未闭合契约（`_index.yaml → contract` 仍 pending）且需求有数据影响时执行：按四节结构补写 `contract.md`，回写 `contract: done`（同步 contract.md 头部状态行）；无影响则置 `skipped` 并写 `contract_note`。走向模糊 → 卡点。

### 阶段 1 · 计划（plan.md）

- 从 PRD 的 AC 生成/刷新：**AC 覆盖表**（每条 AC ≥1 任务）+ **任务清单**（T-01…：仓库/路径/要点/验证方式/验证证据）+ 关联契约状态。
- 任务粒度 = 一次可验证的最小改动；共享仓任务的路径必须落在 `backend_apps.{name}.paths` 内。
- AC 冲突、AC 无法映射任务 → 卡点。

### 阶段 2 · 实现/修复

- 按 `/hy-roles` 实现四原则落码：最小改动、跟随仓库惯例、复用优先、验证闭环。
- 落码范围：`workspace/{project}/code_lib/{repo}/`；共享仓只动对应 backend_app 的 paths。
- 每任务完成即勾选 plan 并填「验证证据」（实际执行的命令与结果摘要，没有跑=没有完成）。
- 验证基线（仓库自有 Makefile/AGENTS.md/package.json scripts 优先）：

  | 仓库语言 | 基线 |
  |----------|------|
  | Go（example_be / shared_be） | `go build ./...`；涉及包 `go test ./...`；shared_be 子项目改动另跑表驱动测试 |
  | Rust（example_rs） | `cargo fmt --check` + `cargo clippy` + `cargo test` |
  | TS Web（example_fe / example_pc / example_game） | 仓内 tsc/lint/test 脚本；UI 说明人工验证路径 |
  | Cocos（example_game） | `tsc` + 编辑器运行说明 |

- 同一 AC 有多条实现路径 / 要动的代码超出 PRD 范围（兄弟页面、公共层、其他子项目）→ **卡点**（scope 边界）。

### 阶段 3 · 自检（implementation/review.md）

- 从 `.hy/i18n/{lang}/templates/iteration/review.md.tpl` 生成检查单：任务闭合、AC 覆盖、变更仅在声明路径、契约一致、语言规范、安全红线、占位符、验证留痕。
- 结论 `pass` / `pass-with-notes` / `block`；**block 项回阶段 2 修复**后重出结论。
- 本阶段是**同会话热眼自检**（带着实现记忆查漏）；需要独立视角时用 `/hy-review`——跨会话冷眼复查，只对照落盘产物逐条核验，不重新推理实现。
- 全仓 pass → `stages.dev: done`（有仓 defer 时保持 in_progress 并说明）。

## 卡点（Ask-First，答前禁止推进）

| # | 卡点 | 典型场景 |
|---|------|----------|
| 1 | 未绑定入口 | 绑定已有迭代 vs 创建新迭代；无效输入持续循环 |
| 2 | 契约走向 | 表结构/接口字段不清，无法确定生成契约还是 skipped |
| 3 | 实现方案 | 改公共组件 vs 局部、新增接口 vs 复用 |
| 4 | scope 边界 | 要动共享仓公共层、兄弟子项目、PRD 之外的代码 |
| 5 | AC 缺口/冲突 | AC 互相矛盾或缺少前置条件 |
| 6 | 体量升级 | 需求超出单迭代承载 → 建议拆迭代/补原型（交用户裁定） |
| 7 | 修复根因 | 多候选根因无法唯一确定最小修复点 |

每次只问当前卡点，给「问题+选项+推荐项」。

## 完成判定

- [ ] 各仓 plan 任务全闭合（或显式 defer 并说明）
- [ ] 代码变更仅落在 plan 声明的仓库与路径（共享仓在 backend_app paths 内）
- [ ] 每仓 review.md 有结论且无未处理 block
- [ ] 验证命令实际执行、证据已留痕
- [ ] 卡点均有用户确认记录；无卡点时为纯自动执行

## 修订历史

| 日期 | 变更 |
|------|------|
| 2026-10-16 | 区分本地 HTML 原型预览与业务开发运行流程。 |
| 2026-10-15 | 增加项目级产品原型的路径、来源与业务交付边界。 |

## [Next Steps]

- 冒烟 → `/hy-test`（每仓至少跑一次）
- 测试/线上出问题 → `/hy-fix`（回到阶段 2 修复模式）
- 对质量不放心 → `/hy-review`（独立复检）
