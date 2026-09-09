# 冒烟记录: $title

- 迭代: `$id`
- 状态: stages.smoke = pending（/hy-test 判定后同步更新本行；全 pass 置 pass，任一 fail 置 fail）

> 每条 PRD AC 至少一行；fail 项回 /hy-fix 修复后重跑。

| # | 验证项 | AC | 结果 | 证据（命令输出/截图路径/URL） |
|---|--------|----|------|------------------------------|
| 1 |  |  |  |  |

## 回归（repos_in_scope 各仓测试套件）

> 整仓跑既有测试套件（go test / cargo test / 仓内 test 脚本），与 AC 验证互为独立闸门；结果计入 smoke 判定，任一 fail 即 stages.smoke=fail。

| 仓库 | 套件命令 | 结果 | 证据 |
|------|----------|------|------|
|  |  |  |  |  |

## 结论

（pass / fail 及原因）
