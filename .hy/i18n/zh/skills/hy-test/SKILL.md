---
name: hy-test
description: "冒烟执行：把 PRD AC 展开为验证清单逐项执行，产出 smoke.md 四列表（验证项↔AC↔结果↔证据）；fail 回流 /hy-fix，全 pass 置 stages.smoke=pass。触发 /hy-test。"
metadata:
  hy:
    command: hy-test
    kind: lifecycle
    stage: smoke
    entry: true
---

# hy-test · 冒烟

> 链路收口：证明「做出来的东西真的满足 AC」。以真实操作为准，不做纸面推断。

## 会话入口门禁（P0）

- 先运行 `session show`。未绑定时用 `iter list [project]` 展示候选，Ask-First 循环选择**绑定已有迭代**或**创建新迭代**，不得自动拿最近完成的迭代来测。
- 绑定已有：`session set` 后以 `session show` 验证并恢复原始 `/hy-test`。创建新迭代：转 `/hy-req` 闭合 PRD，再按前置完成 `/hy-dev`，达到可测状态后才恢复本次冒烟请求。
- 无效/不完整输入保持门禁并继续询问，取消才结束；门禁完成前不创建或更新 `smoke.md`、不回写 `stages.smoke`。

## 输入

- 会话迭代；`prd.md` 的 AC 清单（含 `/hy-req` 之后的修订 AC）+ `contract.md`。
- 可用参数：`--scope all|failed`（默认 all；冒烟回流后可只跑 failed + 回归）。

## 流程

```
① 展开清单   每条 AC 至少一个验证项；涉及多仓时按仓分组；契约有变更的加接口对验项；
             另加回归区：repos_in_scope 各仓既有测试套件整仓各跑一遍（独立于 AC 的闸门）
② 逐项执行   能自动的自动（命令/脚本/HTTP/浏览器自动化——UI 类 AC 优先用浏览器自动化
             真实操作验证，把人工项压到最少）；确实不能自动的给出明确手工步骤并请用户执行
③ 记录       smoke.md 四列表：# / 验证项 / AC / 结果(pass|fail|skip) / 证据；回归区每仓一行
④ 判定       任一 fail 或回归套件 fail → stages.smoke=fail；全 pass（或有理由充分的 skip）
             且回归全 pass → pass；判定后同步更新 smoke.md 头部状态行
```

- **证据**必须可追溯：命令及关键输出、URL、截图路径（存 `attach/`）。`skip` 必须写理由（如依赖外部服务暂不可用），无理由的 skip 视为 fail。
- 执行环境用各仓既有约定（dev server / Makefile / docker compose / 测试账号），不确定怎么起服务 → 先读仓库 README/Makefile，仍不明 → 卡点问。

## 判定与回流

| 结果 | 动作 |
|------|------|
| 全 pass | `stages.smoke: pass`（AC + 回归双闸门均过）；提示用户审阅并自行提交代码（**不自动 git 操作**），之后可 `python3 happlylong.py iter close`；提交后建议 `/hy-knowledge iteration` 沉淀本次变动 |
| 有 fail | `stages.smoke: fail`（AC 项或回归套件任一）；fail 项整理成缺陷清单 → `/hy-fix` 修复后重跑（`--scope failed` + 回归） |
| 阻塞 | 环境起不来/依赖缺失 → 记录阻塞原因，停在这里（卡点），不假装跑过 |

## 检查点

- `stages.dev ≠ done` → 先回 `/hy-dev` 收尾（或确认 defer 后继续）。
- AC 在冒烟阶段发现遗漏/写错 → 这是 AC 缺口卡点：回 `/hy-req` 修订（新增 AC 编号），不偷偷改旧 AC 语义。

## [Next Steps]

- 全 pass → 用户提交代码后 `python3 happlylong.py iter close`（需 smoke=pass；本次是从其他在途迭代切来的话，close 后 `session back` 回原迭代），再 `/hy-knowledge iteration` 沉淀
- 有 fail → `/hy-fix`（尾部贴 fail 清单）→ 再 `/hy-test --scope failed`
- 想留一份质量结论 → `/hy-review`
