---
name: hy-review
description: "独立复检/Code Review：对照 plan/AC/契约与各语言规范、安全红线审查实现，产出 implementation/review.md 结论（pass/pass-with-notes/block）。触发 /hy-review。"
metadata:
  hy:
    command: hy-review
    kind: lifecycle
    stage: dev
    entry: true
---

# hy-review · 独立复检

> 站在「挑毛病」立场重跑一遍检查：可复核 `/hy-dev` 的自检结论，也可对任意已实现迭代单独审查。与 `/hy-dev` 阶段 3 的同会话自检（热眼）互补，本命令定位**跨会话冷眼复查**：建议在新会话触发、不携带实现过程记忆，只以落盘产物（plan/AC/契约/规范/代码变更）为据**逐条核验证据**，不重新推理实现。**只报问题与建议，不直接改码**（用户明确要求顺手修时按 `/hy-dev` 阶段2 基线执行）。

## 会话入口门禁（P0）

- 新会话先 `session show`。未绑定则 `iter list [project]` 展示候选，Ask-First 循环选择**绑定已有迭代**或**创建新迭代**；冷眼复检也不得按“最近迭代”猜测。
- 绑定已有后执行 `session set` 并用 `session show` 验证，再恢复原始审查请求。选择创建则转 `/hy-req` 闭合 PRD，并在有可审实现后才恢复 `/hy-review`；无效/不完整输入继续询问，取消才结束。
- 门禁完成前不创建或更新 `implementation/review.md`；若用户显式同时给出 project/iteration ID，也必须先获得绑定确认并落绑定。

## 输入

- 会话迭代（或 `--project` + `--iteration-id` 指定）；可 `--repo {name}` 只查单仓。
- 审查对象：`code_lib` 中的实际代码变更 + `plan.md` + `prd.md` + `contract.md`。

## 审查维度

| 维度 | 检查什么 |
|------|----------|
| 交付完整 | plan 任务全闭合/有 defer 说明；每条 AC 至少映射一个已完成任务 |
| 范围纪律 | 变更仅在 plan 声明路径；共享仓未越 backend_app 边界；无顺手私改 |
| 契约一致 | 实现的接口/字段/错误码与 contract.md 逐项对齐；FE 消费与 BE 提供一致 |
| 语言规范 | 对照 `shared/standards/{typescript,go,rust}.md` 与 `coding-standards.md` |
| 安全红线 | 凭据硬编码 / SQL 拼接 / 权限校验缺失 / 敏感信息入日志 |
| 错误处理 | 无吞异常；用户可见错误有兜底；Go error 有 wrap、TS promise 无裸 catch |
| 可维护性 | 命名/分层是否跟随仓库惯例；重复代码；死代码；遗留调试语句 |
| 验证留痕 | 验证方式可复现、证据真实（命令与输出摘要） |

## 产出

- 从 `.hy/i18n/{lang}/templates/iteration/review.md.tpl` 生成/更新 `implementation/review.md`：
  - 结论 **pass** / **pass-with-notes**（附问题清单）/ **block**（列必须修复项）。
  - 问题分级：`P0 必须修` / `P1 建议修` / `P2 可接受`，各附定位（仓/文件/行）与建议。
- block 或 P0 未修 → 回 `/hy-dev`（阶段 2）或 `/hy-fix`，不视为通过。

## 检查点

- 迭代无任何实现（code_lib 无变更、plan 空）→ 说明后中止。
- 发现「实现与 PRD 明显不符」→ 列为 block 并指出是需求变更（回 `/hy-req` 修订 PRD）还是实现偏差（回 `/hy-dev`）。

## [Next Steps]

- 结论 pass → `/hy-test` 冒烟收尾
- 有 block/P0 → `/hy-fix`（或 `/hy-dev` 回阶段 2）
- 想看另一个视角 → `/hy-roles`（架构师人格）
