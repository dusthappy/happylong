# example_be · 总览（overview）

- 项目: example ｜ 仓库: example_be
- 来源: bootstrap（代码注入）｜ 更新: 2026-08-28

## 定位

示例项目的后端仓（backend）：提供任务/标签 REST API 与数据持久化，供 example_fe 消费。本文件为知识库四件套（overview/api/data/changelog）之一的教学样例，内容纯虚构。

## 技术栈

- Go（1.22+）+ gin（HTTP）+ ent（ORM）+ PostgreSQL
- 测试：标准库 testing，服务层表驱动用例

## 目录地图

```
api/             路由与 DTO（按资源分文件）
internal/biz/    业务用例层
internal/service/ 服务编排（事务边界在此）
internal/data/   ent 数据访问
sql/             迁移与种子 SQL
```

## 启动与验证

- 启动：`go run ./cmd/server`（本地依赖 Postgres，连接串走 env）
- 验证：`go build ./...`；`go test ./...`
- lint：`gofmt` + `go vet`

## 约定要点

- 分层 gin → service → data，跨层禁止反向调用
- 错误一律 `fmt.Errorf("...: %w", err)` 包装后上抛，service 层统一映射 HTTP 状态码
- 新表/字段先写 sql/ 迁移再改 ent schema，保持两者同步

## 与其他仓的关系

- example_fe：消费本仓全部 REST 接口（契约以各迭代 contract.md 为准）
- shared_be：无关；共享后端场景见 profile.yaml 中 shared_be 的 backend_apps 演示
