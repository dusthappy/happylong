# 冒烟记录: 任务标签

- 迭代: `260828-fe-task-labels`
- 状态: stages.smoke = pass

> 每条 PRD AC 至少一行；fail 项回 /hy-fix 修复后重跑。

| # | 验证项 | AC | 结果 | 证据（命令输出/截图路径/URL） |
|---|--------|----|------|------------------------------|
| 1 | 任务详情添加/移除标签，第 6 个时被拒绝并提示 | AC-001 | pass | curl PUT labels 返回 422；前端提示截图 attach/smoke-1.png |
| 2 | 新建标签选颜色、重名返回 409 且前端有提示 | AC-002 | pass | curl POST 重名 409；UI 截图 attach/smoke-2.png |
| 3 | 列表按标签筛选，刷新后条件保持（?label=） | AC-003 | pass | 浏览器刷新后筛选保留，URL 同步 |
| 4 | 删除标签后自动从全部任务摘除，任务本体保留 | AC-004 | pass | 删除后任务列表完整，详情无该标签 |

## 回归（repos_in_scope 各仓测试套件）

> 整仓跑既有测试套件（go test / cargo test / 仓内 test 脚本），与 AC 验证互为独立闸门；结果计入 smoke 判定，任一 fail 即 stages.smoke=fail。

| 仓库 | 套件命令 | 结果 | 证据 |
|------|----------|------|------|
| example_be | `go build ./... && go test ./...` | pass | 全绿，新增用例 10 项 |
| example_fe | 仓内 `tsc --noEmit` + `lint` 脚本 | pass | 无错误 |

## 结论

pass。4/4 AC 全部验证通过，两仓回归全绿；2026-08-28 由 /hy-test 判定。
