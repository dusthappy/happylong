# 开发计划: 任务标签

- 迭代: `260828-fe-task-labels`
- 生成方式: /hy-dev 阶段1 自动生成，AC 变更后重刷

## 关联

- PRD: `prd.md`
- 契约: `contract.md`（状态以 `_index.yaml → contract` 为准）

## AC 覆盖表

| AC | 任务 | 仓库 | 状态 |
|----|------|------|------|
| AC-001 | T-02, T-04 | example_be / example_fe | [x] |
| AC-002 | T-01, T-04 | example_be / example_fe | [x] |
| AC-003 | T-05 | example_fe | [x] |
| AC-004 | T-03, T-04 | example_be / example_fe | [x] |

## 任务清单

> 每个任务写明：改动仓库与路径、要点、验证方式。完成勾选并在「验证证据」留痕。

- [x] T-01: 标签表与 CRUD 接口
  - 仓库/路径: example_be · sql/labels、internal/data/labels、internal/service/labels、api/labels
  - 要点: labels/task_labels 两表迁移；name 项目内唯一校验（重名 409）；软删除 + 事务清理关联
  - 验证方式: go test ./internal/service/labels/...（表驱动用例：唯一性/软删/关联清理）
  - 验证证据: `go test ./...` 全绿；用例 6 项
- [x] T-02: 任务打标接口与任务响应内嵌标签
  - 仓库/路径: example_be · internal/service/tasks、api/tasks
  - 要点: PUT /api/tasks/{id}/labels 校验上限 5（422）；列表/详情内嵌 labels
  - 验证方式: go test 任务服务包 + curl 冒烟
  - 验证证据: 用例 4 项全绿
- [x] T-03: 删除标签联动摘除
  - 仓库/路径: example_be · internal/service/labels
  - 要点: DELETE 事务内删除 task_labels 关联行；返回 204
  - 验证方式: 表驱动用例（删标签后任务本体保留）
  - 验证证据: `go test ./internal/service/labels/...` 全绿
- [x] T-04: 标签选择器与标签管理页
  - 仓库/路径: example_fe · src/components/LabelPicker、src/views/Labels
  - 要点: 选择器搜索+新建一步完成（重名提示）；管理页重命名/删除二次确认并提示影响任务数
  - 验证方式: 仓内 tsc + lint；人工验证路径见 smoke
  - 验证证据: tsc/lint 通过；smoke #1/#2/#4
- [x] T-05: 列表按标签筛选 + URL 持久化
  - 仓库/路径: example_fe · src/views/TaskList、src/router
  - 要点: 筛选栏单标签过滤；`?label=` 与路由 query 双向同步，刷新保持
  - 验证方式: tsc/lint + 人工刷新验证
  - 验证证据: smoke #3

## 仓库串联顺序

example_be（T-01 → T-02 → T-03）→ example_fe（T-04、T-05），契约字段以 contract.md 为准。
