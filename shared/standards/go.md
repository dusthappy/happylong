# Go 规范

> 覆盖：Go 后端仓（如 example_be）与共享单体 shared_be（Kratos 风格分层 + ent）。

## 1. 项目布局（跟随三仓既有惯例）

```
api/            协议定义（proto/openapi/请求响应结构）
cmd/{app}/      main 入口，只做装配
internal/
  biz/          业务逻辑层（用例编排，不碰 SQL/HTTP 细节）
  service/      接口实现层（参数校验、DTO 转换，薄）
  data/         数据访问层（ent 查询、缓存、外部调用）
  server/       HTTP/gRPC 路由注册与中间件装配
  conf/         配置结构
ent/            ent schema（数据库表定义）
sql/            迁移/种子 SQL（按子项目分子目录，如 sql/example）
pkg/            可被外部引用的通用库（谨慎新增）
```

- 新代码落哪层：用例进 `biz`，接口粘合进 `service`，查库进 `data`；跨层直调禁止（service 不写 ent 查询，data 不做业务判断）。

## 2. 错误处理

- 一律显式处理 error，禁止 `_` 丢弃；上层用 `fmt.Errorf("xxx: %w", err)` 保留错误链。
- 业务错误定义成可判别的错误值/错误码（跟随仓库既有 errors 包），HTTP 层统一转响应。
- panic 仅限「不可能发生」的初始化断言；请求路径禁止 panic 兜底当流程控制。

## 3. ent 与数据库

- 表结构改动：改 ent schema 后生成迁移（跟随仓内 make 目标）；迁移 SQL 落 `sql/{子项目}/`，可回滚的写明回滚方式。
- 查询一律 ent API 或参数化 SQL；**禁止 fmt 拼接 SQL**（P0）。
- 新表命名与索引跟随仓内惯例；shared_be 中新表/缓存键带子项目前缀（`app1_*` / `app2_*`）防冲突。
- 事务：跨表写操作用事务；失败即回滚，不留半状态。

## 4. 并发与资源

- goroutine 必须有退出路径（context 取消/channel 关闭）；禁止裸 `go func` 无追踪。
- 共享状态加锁或用 channel；`sync.Mutex` 保护范围最小化。
- HTTP body/文件句柄/rows 必须关闭（defer Close）。
- context 作为函数第一参数传递，超时/取消随调用链下传。

## 5. API 约定

- 请求参数在 service 层校验（binding tag 或显式校验），非法参数 4xx 带字段说明。
- 响应结构统一仓内既有包装（code/message/data）；错误码不裸写数字散落。
- 分页参数与响应格式跟随仓库既有约定，新接口不发明新格式。
- 每个新端点必须有权限校验（登录态/角色），无匿名例外（P0，见 security-rules.md）。

## 6. shared_be 共享仓附加规则

- 子项目改动限定在 `backend_apps.{name}.paths`（api/、internal/{biz,service,data}/ 对应子目录、sql/ 子目录）；动公共层即 scope 卡点。
- 子项目间不互相 import 对应 biz/service 包；公共能力下沉须先征得同意（Ask-First）。
- 路由前缀按子项目隔离（如 `/example/*`），复用全局中间件不重复注册。

## 7. 验证基线

- `gofmt` 无 diff；`go vet ./...` 干净。
- `go build ./...` 通过；改动包 `go test ./...` 通过（表驱动，见 testing-standards.md）。
- 仓内有 Makefile 的优先用 make 目标（build/test/lint）。
