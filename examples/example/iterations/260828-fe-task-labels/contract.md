# 数据契约: 任务标签

- 迭代: `260828-fe-task-labels`
- 状态: contract = done

## 契约范围

覆盖 example_be ↔ example_fe 的本次新增接口与表结构变更；不涉及外部系统。

## 数据与字段要点

- `labels`：`id`（主键）、`project_id`（索引）、`name`（唯一约束：project_id + name）、`color`（枚举 8 色，存字符串）、`deleted_at`（软删除）
- `task_labels`：`task_id` + `label_id` 联合主键；删除标签时同事务删除关联行

## 接口要点

| 接口 | 方法 | 提供方 | 消费方 | 请求要点 | 响应要点 |
|------|------|--------|--------|----------|----------|
| /api/labels | GET | example_be | example_fe | query: keyword（可选） | 标签数组（id/name/color） |
| /api/labels | POST | example_be | example_fe | body: name, color | 201 + 标签对象；重名返回 409 |
| /api/labels/{id} | PATCH | example_be | example_fe | body: name 或 color | 更新后对象 |
| /api/labels/{id} | DELETE | example_be | example_fe | — | 204；同事务摘除全部关联 |
| /api/tasks/{id}/labels | PUT | example_be | example_fe | body: label_ids（≤5） | 任务对象（内嵌 labels 数组）；超限返回 422 |

- 任务列表/详情响应统一内嵌 `labels: [{id,name,color}]`，前端不再二次请求。

## 跨仓依赖

example_be 先行（接口 + 表结构），example_fe 按 contract.md 开发，联调前以契约字段为准做 mock 分流；无外部系统依赖。
