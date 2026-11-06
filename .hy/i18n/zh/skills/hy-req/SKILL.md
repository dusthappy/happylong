---
name: hy-req
description: "开迭代+PRD 一体入口：显式 --title 始终新建迭代并绑定；无 title 时先按当前会话路由，未绑定则 Ask-First 循环选择绑定已有或创建新迭代，再闭合单文件 PRD（正文+AC+仓库面+契约）。触发 /hy-req --project X --title T 或直接 /hy-req 贴需求。"
metadata:
  hy:
    command: hy-req
    kind: lifecycle
    stage: entry
    entry: true
---

# hy-req · 开迭代 + 单文件 PRD（一体）

> 链路入口：一次交互完成「迭代目录创建 + 会话绑定 + PRD 闭合（正文/AC/仓库面/契约三分支）」，让 `/hy-dev` 拿到就能开工。契约时机**前移到本阶段**，dev 阶段 0 只兜底。

## 触发与输入模式

```
/hy-req [--project {project}] [--title {标题}] [--type feat|fix|refactor|doc|chore] [--slug {slug}]
……尾部自由文本 = 需求正文（照此理解，可整理不可改意）
```

| 模式 | 输入形态 | 路由 |
|------|----------|------|
| A 显式新 PRD | 带 `--title` | 标题原样使用；跳过“绑定/创建”二选一，始终创建并绑定一个新迭代 |
| B 无标题、已绑定 | 有无尾部正文均可 | `prd` 未完成则继续当前 PRD；已完成则 Ask-First 选择修订当前或新开迭代 |
| C 无标题、未绑定 | 有无尾部正文均可 | 先列出候选，Ask-First 循环选择绑定已有或创建新迭代；保留尾部正文，成功后恢复本请求 |

- 模式 A 的 `--project` 缺省从当前绑定补全；新会话无绑定且未给项目时只追问项目，然后直接新建，不再问绑定还是创建。
- 选择创建但没有 `--title` 时，从尾部内容总结拟题（简洁中文标题 + 英文 slug 建议 + type 推断），把项目/标题/slug/type 与需求缺口合并为一轮确认；空手调用则同时询问需求描述。
- `--type` 缺省 `feat`；无显式标题时可按内容推断并在创建确认时一并给出。
- `--slug` 用于显式指定英文短语；纯中文标题自动回退时间片 slug（如 `t0930`）。

## 执行步骤

### ① 检查点

- 先确认当前 Agent 会话具备稳定身份：优先使用会话启动环境中的 `HY_SESSION_ID`（Codex 可自动使用 `CODEX_THREAD_ID`），或在每次工具调用的子命令前传同一个 `--session-id`。ID 必须在整个长会话及上下文压缩前后保持不变；不可用时停止并提示配置，禁止自行生成临时 ID。
- 运行 `python3 happlylong.py session show` 解析当前代理会话的独立绑定，按其状态路由（禁止直接读旧文件 `current.yaml`）：
  - **带 `--title`（最高优先级）** → 这是明确的新 PRD 信号。解析项目后直接走②新建并绑定，不出现“绑定已有/创建新迭代”二选一；即使会话已绑定也新开，旧绑定由工具保存到 `previous`。同日同 slug 冲突时让用户给新的 `--slug`（可附推荐后缀）或取消，禁止改成复用已有迭代。
  - **无 `--title` 且未绑定** → 运行 `python3 happlylong.py iter list [project]` 展示有效候选，Ask-First 询问“绑定已有迭代 / 创建新迭代”（可结合原始意图推荐，但禁止代选）。选择绑定时只补齐 project/iteration ID，执行 `session set` 并用 `session show` 验证，再重新进入本路由并恢复原始 `/hy-req`；选择创建时保留尾部正文，补齐项目并确认拟定的 title/slug/type，然后走②。项目或迭代无效、输入仍不足时不落任何产物，重新列候选并继续问；用户取消才结束。
  - **无 `--title` 且已绑定、`stages.prd ≠ done`** → 本命令转为填充该迭代 PRD，不新建目录；缺需求正文时只问正文及真正缺失的信息。
  - **无 `--title` 且已绑定、`stages.prd = done`** → 卡点：需求有变走**修订**（新增 AC + 修订历史，不回收已用 AC 编号）还是**新开迭代**？选择新开后按尾部内容拟题并确认，再走②。
- 项目确定后运行 `python3 happlylong.py doctor`，确认目标项目软链健康（broken 时先修，避免后续落码踩空）。
- 读 `workspace/{project}/profile.yaml → repos`，作为仓库面判定素材。

### ② 建迭代（仅新开时，纯脚本一步完成）

```bash
python3 happlylong.py iter new {project} --title "{title}" --type {type}
```

产物（模板来自 `.hy/i18n/{lang}/templates/iteration/`）：

```
workspace/{project}/iterations/{YYMMDD}-{type}-{slug}/
├── _index.yaml      ← 三阶段状态机（stages: prd/dev/smoke）+ contract 字段
├── prd.md  contract.md  plan.md  smoke.md
├── implementation/  （fix-*.md、review.md）
└── attach/          （原型图、外部契约等附件）
```

当前代理会话自动绑定为该迭代，状态原子写入 `.hy/session/bindings/{hash}.yaml`。缺少可信会话 ID 时工具在创建目录前 fail closed，不产生半成品，也不回退 `current.yaml`。

### ③ 需求澄清（轻量）

- 用户指定飞书资料或要求保存其中图片时，按需读取框架根下的 `shared/feishu-cli.md`：只处理已授权资源，按来源选择 CLI 下载方式，缺图时核对授权页面；完成绑定后再存当前迭代 `attach/`，验证实际图片并以相对路径引用。不引入其他工程的账号配置、业务数据或任务体系。
- 信息齐全直接写；缺口采用 `/hy-roles` PM 四支柱（完整性/一致性/清晰性/可行性）**只问缺的**，一次打包问完（Ask-First）。
- 模式 B/C 的拟题确认与本步澄清**合并为一轮**，避免多轮往返。
- 会话图片/附件（原型图、截图、外部契约片段）→ 存 `attach/` 并在 PRD 登记。

### ④ 仓库面判定 → repos_in_scope

按 PRD 内容自行判定并**直接执行，不问用户**（判定依据写入 PRD「范围」节）：

| 内容特征 | 判定 |
|----------|------|
| 纯接口/表/后台逻辑 | backend 仓（共享仓时指明 backend_app 名） |
| 网关/BFF/中间层逻辑 | service 仓（共享仓时指明 backend_app 名） |
| 纯页面/交互/UI | frontend 仓（多前端仓时按平台特征细分：mobile uni-app / pc react / cocos） |
| 两者皆涉 | 双仓，backend/service 在前（dev 自动串联服务端→前端） |
| 单仓项目（example_rs） | 该仓 |

回写 `_index.yaml → repos_in_scope`（backend/service 在前的顺序）。仅当 PRD 信息完全无法支撑判断时才停下问（卡点）。

### ⑤ 契约三分支

判定「本次需求是否产生跨仓数据交互（新接口/新表/字段变更/缓存键）」：

1. **有外部契约**（用户给定）→ 校验其完整性后整理落盘 `contract.md`，`_index.yaml → contract: done`（同步 contract.md 头部状态行），PRD 标注「契约来源：外部」。
2. **无外部契约但有数据影响** → 依据 PRD 生成 `contract.md`（范围/数据与字段要点/接口要点/跨仓依赖四节），`contract: done`。字段拿不准的条目标 `待联调确认` 并列入 dev 阶段 0 兜底清单。
3. **无数据影响** → `contract: skipped`，`contract_note` 写明判定理由，`contract.md` 保留空模板即可。

走向模糊（看不出是否有数据影响）→ 卡点询问。

### ⑥ 写入 prd.md

按模板填充并保持结构：修订历史 / 背景与目标 / **验收标准（AC-001…可勾选，2~8 条，每条可冒烟验证）** / 范围（包含/不包含 + 仓库面判定依据）/ 功能需求（按仓分节）/ 非功能需求（无则删节）。最后回写 `_index.yaml → stages.prd: done`、`updated`，并同步 `prd.md` 头部状态行。

### ⑦ 验证

`python3 happlylong.py session show` 确认绑定；`iter show` 确认 `prd`/`contract` 状态与实际一致。

## 质量自检（提交前）

```
□ AC 全部可验证、有编号、无「尽量/更快」类模糊词
□ repos_in_scope 与 PRD 内容一致且已回写 _index
□ 契约分支结论与 _index → contract 字段一致
□ 原型/附件已存 attach/ 并登记
□ 无占位符残留；修订历史已更新
```

## 卡点（Ask-First）

- 未绑定且无显式 `--title` 时的“绑定已有 / 创建新迭代”入口选择；无效或不完整输入须循环询问；
- 选择创建但无显式标题时的拟题确认（项目/title/slug/type 与需求缺口一次打包）；
- 显式新建发生迭代 ID 冲突时的新 slug / 取消选择；
- 需求关键信息缺失（③ 无法自答）；
- 契约走向模糊（三分支无法判定）；
- 需求明显超出一个迭代体量（建议拆分，交用户裁定）；
- `prd` 已 done 时的修订/新开抉择。

## 边界

- 不碰 `code_lib/`（无 PRD 禁改码）。
- 显式 `--title` 不得解释为“续用已有”；同日同 slug 已存在时保持新建语义，改用新的 slug 或取消。
- 未绑定门禁完成前不创建目录、不写迭代产物；用户选择绑定后必须验证绑定再恢复原始请求。
- 建迭代（②）是纯脚本步骤，PRD 内容生成（③~⑥）才是 LLM 步骤，两者不得颠倒（先有目录再落内容）。

## 修订历史

| 日期 | 变更 |
|------|------|
| 2026-11-06 | 增加按需加载飞书 CLI/图片下载指南，沿用迭代附件落点并隔离账号与业务数据。 |

## [Next Steps]

- 进入开发 → `/hy-dev`（状态机自动从契约兜底/计划开始）
- 继续打磨需求或契约 → `/hy-roles`（PM/架构师人格）或直接细化 `contract.md`
- 看当前状态 → `python3 happlylong.py status`
