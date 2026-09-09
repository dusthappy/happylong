---
name: hy-fix
description: "系统化缺陷修复：复现→定位→最小修复→验证，产出 implementation/fix-{date}.md 留痕，联动 plan 任务状态；也是 /hy-test 冒烟 fail 的回流入口。触发 /hy-fix。"
metadata:
  hy:
    command: hy-fix
    kind: lifecycle
    stage: dev
    entry: true
---

# hy-fix · 缺陷修复

> 修 bug 的唯一入口（线上 bug / 测试失败 / 冒烟 fail 通用）。流程即 `/hy-dev` 阶段 2 的修复模式 + 留痕模板。

## 会话入口门禁（P0）

- 先用 `session show` 解析当前会话。未绑定时先 `iter list [project]`，Ask-First 循环选择**绑定已有迭代**或**创建新迭代**；不得把“这是新缺陷”自行等同为创建。
- 绑定已有：补齐 project/iteration ID，`session set` 后以 `session show` 验证，再恢复原始缺陷描述。创建新迭代：保留缺陷描述，向用户确认 project/title/slug/type（推荐 `fix`），再以显式 `/hy-req --type fix --title "缺陷简述"` 创建、闭合最小 PRD，随后恢复本次 `/hy-fix`。
- 无效或不完整输入继续列候选并询问，取消才结束；门禁与 PRD 未通过前不写 fix 产物、不改代码。

## 输入

| 来源 | 说明 |
|------|------|
| 会话 | 已验证绑定中的 `project` / `iteration_id`；切换绑定时被切走的在途迭代自动存入 `previous` |
| 尾部自由文本 | 缺陷描述：现象、复现步骤、期望 vs 实际 |
| 回流 | `/hy-test` 冒烟 fail 项（AC 与失败证据随附） |

## 流程（systematic-debugging）

```
① 复现   按描述跑一遍，确认现象稳定可复现；复现不了 → 卡点（要更多信息，不瞎修）
② 定位   从现象出发：读代码路径/日志/数据 → 假设 → 用最小实验验证假设
③ 根因   唯一确定最小修复点；多个候选根因 → 卡点（Ask-First），给出各候选的验证证据与代价
④ 修复   最小改动：只修根因，不顺手重构、不扩大范围；改哪仓遵循 /hy-dev 阶段2 的落码与验证基线
⑤ 验证   重跑复现步骤确认已修 + 回归检查相邻功能；证据留痕
```

## 留痕（P1）

- 从 `.hy/i18n/{lang}/templates/iteration/fix.md.tpl` 生成 `implementation/fix-{YYYY-MM-DD}.md`：现象与复现 / 根因定位 / 修复方案 / 验证。
- 联动 `plan.md`：修复对应任务存在则勾选；不存在则追加任务行（标 `fix` 来源 + 关联 AC）。
- 冒烟回流场景：修复后 `smoke.md` 中 fail 行不改写，新增重跑行；`stages.smoke` 由下次 `/hy-test` 重判。

## 检查点

- 修复动到的仓库/路径超出 plan 声明 → scope 卡点。
- 根因在依赖/第三方/数据本身（非代码）→ 停下说明，交用户决策。
- **无 PRD 禁改码同样适用于修复**：跳迭代修线上问题时至少补一份最小 fix 型 PRD。

## [Next Steps]

- 重跑冒烟 → `/hy-test`（只跑失败项 + 回归项即可）
- 质量存疑或涉及需求变化 → `/hy-review`，或先 `/hy-req` 修订 PRD 再 `/hy-dev`
- 修完回原在途迭代 → `python3 happlylong.py session back`
