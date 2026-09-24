---
name: hy-spec
description: "happlylong 元规范（三合一）：P0/P1 约束速查 + Skill 执行生命周期 + 输出质量分级。所有 hy-* Skill 执行前应知；触发 /hy-spec 或「hy 约束/规范/质量标准」。"
metadata:
  hy:
    command: hy-spec
    kind: meta
    entry: false
---

# hy-spec · 元规范

> 定位：把「约束索引 + 执行规范 + 输出质量」合为一份，全框架唯一元规范（AGENTS.md 为其门面速查）。

## 1. 约束层级

| 层级 | 含义 | 违规处理 |
|------|------|----------|
| **P0 红线** | 安全/业务底线 | 立即中止，说明原因，给修正建议 |
| **P1 硬约束** | 编码/流程/输出规范 | 警告并修正，否则拒绝输出 |
| **P2 建议** | 最佳实践 | 提示后继续 |

### P0 红线

- 禁止硬编码凭据（密码/API Key/Token 一律 env 或本地 secret 文件，且不入库）。
- 禁止 SQL 拼接，一律参数化查询。
- 每个新增端点必须校验权限，无匿名例外。
- 禁止裸 `except`（Python）/ 空 `catch`（TS）/ 忽略 `error`（Go）——必须处理或留日志。
- **无 PRD 禁改码**：迭代 `stages.prd ≠ done` 时禁止改动任何 `code_lib/` 文件（P0）。线上热修也须先补一份最小 PRD 或获得用户明确许可。
- **未绑定禁执行**：需求、开发、修复、复检、冒烟、iteration 沉淀等执行型请求进入时必须先解析当前会话；若稳定身份存在但未绑定，除显式 `/hy-req --title` 直接新建外，必须 Ask-First 让用户选择“绑定已有迭代 / 创建新迭代”，答复前禁止写迭代产物或业务代码。
- **绑定必须指明 workspace**：active/previous 绑定都必须含 `project`、`iteration_id`、`iteration_path`，路径严格等于 `workspace/{project}/iterations/{iteration_id}`；禁止按裸迭代 ID、最近记录或 cwd 猜测项目。
- 删除数据/文件前先记录删除前快照（表名/条件/行数或文件内容摘要）。
- 未经用户明确要求禁止 `git add/commit/push`。
- 迭代产物只落 `workspace/{project}/iterations/{id}/`；框架文件只落 `.agents/`、`.hy/`。

### P1 硬约束

- 工具脚本一律 `pathlib.Path`、绝对路径锚定框架根，禁止依赖 cwd。
- 会话上下文必须先通过 `python3 happlylong.py session show` 解析；非 Codex Agent 须在启动环境提供稳定且唯一的 `HY_SESSION_ID`（或始终传同一个前置 `--session-id`），上下文压缩前后保持不变。缺少可信身份时 fail closed，禁止读取或假定 `.hy/session/current.yaml`。
- 禁止 `except: pass`；禁止裸 `raise`，用自定义异常（工具内为 `HyError`）。
- 输出不得残留占位符：`TODO` / `待补充` / `TBD` / `FIXME` / `XXX`。
- 文档类产物变更必须更新修订历史表。
- 按语言加载规范：改哪类代码就加载 `shared/standards/` 对应文件 + `coding-standards.md`；涉安全/测试再加载 `security-rules.md` / `testing-standards.md`。
- 仓库角色与开发顺序：backend/service 先、其余按 `profile.yaml → repos` 声明序；登记必须显式 `--role` 并补 `--desc`/`--lang`；共享仓（shared_be）改动必须落在 `backend_apps.{name}.paths` 内，越界即 scope 卡点。

## 2. Skill 执行生命周期（五步）

```
① 触发识别     判断是否为执行型请求，并识别显式 /hy-req --title 新建信号
② 身份与门禁   happlylong.py session show；未绑定则 Ask-First 绑定/新建并循环到成功或取消
③ 上下文收集   迭代 _index.yaml → 项目 profile.yaml → 需要的 shared/ 规范
④ 检查点       前置条件校验（如 hy-dev 要求 stages.prd=done）；不满足给明确指引而非猜
⑤ 执行与验证   按 Skill 状态机推进并回写 stages；完整性核对 → 输出汇报 + [Next Steps]
```

每个 hy-* Skill 的输出必须以 **[Next Steps]** 结尾：给 1-3 条分场景可复制的下一步命令。

## 3. Ask-First 原则（全局）

**只有卡点才停，无卡点全程自动。**

- 卡点 = 拿不准、有多种合理路径、影响超出当前迭代的决策。遇到卡点：停下给出「问题 + 选项 + 推荐项及理由」，用户答复前禁止推进、禁止擅自选默认值。
- 未绑定会话是强制入口卡点：先 `iter list` 展示有效候选，再问“绑定已有 / 创建新迭代”（有结构化提问/选择 UI 时优先使用）；选择绑定后补齐 project/iteration ID，执行 `session set` 并用 `session show` 复核；选择创建后补齐 project/title/type/需求正文，转 `/hy-req` 闭合 PRD。输入无效或不完整就重新展示候选并继续问，用户取消才结束。
- 显式 `/hy-req --title` 是唯一绕过上述二选一的信号：标题原样使用，补齐 project 后新建并绑定；即使已有绑定也新开，禁止改成复用既有迭代。
- 纯问答、`/hy-spec`、`/hy-guide`、`/hy-roles`、项目/软链接入、框架诊断、框架源码维护与开源/发版准备，以及 `/hy-knowledge bootstrap` 不触发业务迭代门禁；自然语言是否触发以“是否会推进迭代产物或业务代码”为准。
- 非卡点（状态机路由、计划生成、逐任务实现、自检执行）一律连续自动，一次请求能走多远走多远。

## 4. 输出质量分级

| 级别 | 定义 | 处理 |
|------|------|------|
| A | 全维度达标 | 通过 |
| B | P0 达标，有小瑕疵 | 通过 + 优化建议 |
| C | 最低可交付 | 通过 + 改进建议 |
| D | P0 未达标 | **拒绝输出并修正** |

输出前必检：

```
□ 无占位符残留（TODO/待补充/TBD/FIXME/XXX）
□ 章节完整（对照模板）
□ 修订历史已更新（文档类）
□ 路径准确（产物在迭代目录、代码在声明的仓库内）
□ 依据语言规范做了合规自查（代码类）
□ 无凭据硬编码、有错误处理（代码类）
```

## 5. 违规处理流程

```
检测违规 → 定级（P0/P1/P2）
  P0 → 中止当前动作，向用户说明并给修正方案
  P1 → 警告 + 立即修正后继续；无法修正则拒绝该产物
  P2 → 提示一句，继续执行
```

## [Next Steps]

- 看框架全貌与链路 → `/hy-guide`
- 开新需求 → `/hy-req --project {project} --title {title}`
- 登记/软链新项目 → `/hy-project`
