---
name: hy-guide
description: "happlylong 框架导航：目录地图、req→dev→test 链路、按场景速查、术语表。触发 /hy-guide 或「hy 怎么用/框架地图/有哪些命令」。"
metadata:
  hy:
    command: hy-guide
    kind: meta
    entry: false
---

# hy-guide · 框架导航

## 链路总图

```
/hy-project ─┐
             ├─→ /hy-req ─→ /hy-dev ─→ /hy-test ─→ (用户提交) ─→ iter close
（项目/软链）     │            │           ↑      │ fail
                  │            │           └─ /hy-fix ┘
                  │            └─ /hy-review（独立复检）
                  │ 建迭代 + PRD + 契约三分支在 /hy-req 闭合（dev 阶段0 只兜底）
                  └ 职责链三人格可随时召唤：/hy-roles（PM/架构师/开发者）
```

- **状态机 SSOT**：`workspace/{project}/iterations/{id}/_index.yaml → stages`（prd/dev/smoke 三阶段；契约闭合状态另记 `contract` 字段）。
- **会话**：每个代理会话独占一个原子写入的绑定文件 `.hy/session/bindings/{hash}.yaml`，命令缺省时只从当前会话补全。active/previous 都必须显式携带 `project`、`iteration_id` 与规范 `iteration_path`，唯一指向 `workspace/{project}/iterations/{iteration_id}`。身份优先级为前置 `--session-id` → `HY_SESSION_ID` → `CODEX_THREAD_ID`；所有入口对同一 ID 得到同一摘要，原始 ID 不落盘。缺少可信 ID 或 workspace 归属不一致时 fail closed，绝不回退共享 `.hy/session/current.yaml`。
- **未绑定入口**：执行型 `/hy-*` 或自然语言请求先 `session show`；未绑定时 `iter list` 后 Ask-First 循环选择“绑定已有 / 创建新迭代”。仅显式 `/hy-req --title` 代表确定新 PRD，可补齐项目后直接创建。框架源码维护、诊断与开源/发版准备不属于业务迭代，不触发该门禁。

## 命令速查

| 命令 | 一句话 | 关键参数 |
|------|--------|----------|
| `/hy-req` | 开迭代 + 单文件 PRD：显式 `--title` 必定新建；否则按绑定状态续填/修订或询问绑定/创建 | `--project`（缺省取会话）`--title`（新 PRD 强信号）`--type feat\|fix\|refactor\|doc\|chore` |
| `/hy-dev` | 四阶段状态机开发：契约兜底→计划→实现→自检；多仓 BE→FE 自动串联 | 可带 `--repo {name}` 聚焦单仓 |
| `/hy-fix` | 系统化修复：复现→定位→最小修复→验证，`implementation/fix-{date}.md` | 缺陷描述直接写在尾部 |
| `/hy-review` | 独立重检/CR，产出 `implementation/review.md` | 可只查单仓 |
| `/hy-test` | 冒烟：AC→验证清单→`smoke.md` 四列表 | fail 自动引导 `/hy-fix` |
| `/hy-knowledge` | 知识库：bootstrap 从代码注入 / iteration 沉淀迭代变动 | 无参自动路由 |
| `/hy-project` | 新项目/软链三模式/pending 补链 | 驱动 `happlylong.py project\|link` |
| `/hy-spec` | 元规范（约束+生命周期+质量） | — |
| `/hy-roles` | 职责链三人格（PM 澄清/架构把关/实现守护），只评审不落盘 | 按视角召唤，产物落盘走 /hy-req、/hy-dev |

工具侧命令（`python3 happlylong.py [--session-id ID] …`）：`--session-id` 是跨 Agent 显式身份且须放在子命令前；子命令包括 `init [--lang zh|en] / lang [zh|en] / release-check / status / doctor --fix / project new / link add|rm|apply|list / iter new|list|show|close / knowledge init|register|status / session show|set|back|clear`。

## 按场景导航

| 场景 | 动作序列 |
|------|----------|
| 明确新需求 | `/hy-req --project X --title T`（总是创建并绑定新迭代）→ `/hy-dev` → `/hy-test` |
| 新会话直接执行或自然语言提需求 | `session show` → 若未绑定则 `iter list [project]` → Ask-First 绑定已有/创建新迭代（无效输入循环）→ 恢复原始请求 |
| 继续已有迭代 | `/hy-dev`；已绑定则自动路由，未绑定则先走入口二选一 |
| 修线上/测试 bug | `/hy-fix`；未绑定则先选择绑定已有或创建 fix 迭代，修完可 `session back` 回原迭代 |
| 冒烟没过 | `/hy-fix`（修复）→ `/hy-test`（重跑失败项） |
| 怀疑实现质量 | `/hy-review` |
| 换项目/换迭代 | `python3 happlylong.py session set {project} {iteration_id}` 或重开 `/hy-req`；切回上一绑定用 `session back` |
| 多 Agent / 多会话并行 | Codex 自动按 `CODEX_THREAD_ID` 隔离；其他 Agent 在各自会话启动环境设置稳定且唯一的 `HY_SESSION_ID`，压缩前后保持不变，再分别执行 `session set` 或 `/hy-req`；同一逻辑会话串行交接时复用同一 ID，同一 ID 不允许并发写 |
| 新项目接入 | `/hy-project`（三模式：单仓 / FE+BE 双仓 / 共享后端+子项目） |
| 项目接入后建立认知 | `/hy-knowledge bootstrap --project X`（从代码注入 overview/api/data） |
| 迭代完成后沉淀 | `/hy-knowledge iteration`（未绑定先过入口门禁；changelog 流水 + api/data 增量） |
| 目录或软链可疑 | `python3 happlylong.py doctor --fix` |

## 术语表

| 术语 | 含义 |
|------|------|
| project | `workspace/` 下的业务项目位（如 example、example_game 等示例） |
| repo | `code_lib/` 下一条软链对应的真实代码库 |
| role | 仓库角色：frontend / backend / fullstack / lib |
| shared 仓 | 被多个 project 同时挂载的后端仓（如 shared_be） |
| backend_apps | 共享仓内的业务子模块（如 shared_be 的 example：api/example、internal/{biz,service,data}/example、sql/example） |
| pending 仓 | 已登记、目标目录未就绪、软链待补的仓库 |
| iteration | `iterations/{YYMMDD}-{type}-{slug}/`，一次需求的全部产物 |
| knowledge | `workspace/{project}/knowledge/{repo}/`，项目历史认知（overview/api/data/changelog） |
| stages | prd / dev / smoke 三阶段状态；契约闭合另记 `contract` 字段（done/skipped） |
| AC | PRD 验收标准，编号 AC-001…，冒烟一行一 AC |
| 卡点（Ask-First） | 拿不准的决策，或未绑定入口的强制二选一；用户答复前停下，其余全程自动 |

## [Next Steps]

- 新需求 → `/hy-req --project {project} --title {title}`
- 先体检环境 → `python3 happlylong.py --session-id {stable-session-id} doctor`（已有 `HY_SESSION_ID` 或 Codex 自动身份时可省略前置参数）
- 看约束与质量线 → `/hy-spec`
