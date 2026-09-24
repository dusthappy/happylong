---
description: happlylong(hy) 个人多项目产研工作台全局代理规范
alwaysApply: true
---

# happlylong 代理行为规范

> **版本**: 0.1.2 | **更新**: 2026-09-24
> happlylong（缩写 **hy**）是服务于 `workspace/` 下多个个人项目的产研工作台。
> 设计基调：**单轨轻链路、零平台镜像、工具即真相**。

---

## 一、核心模型（先懂这个再看约束）

```
happlylong/                     ← 框架根（本文件所在目录）
├── happlylong.py / .bat        ← 唯一工具：骨架/软链/迭代/会话/体检/语言
├── CLAUDE.md                   ← Claude Code 接入口（@AGENTS.md 引用，安装产物）
├── .agents/skills/hy-*/        ← 已安装技能（当前语言集，安装产物）
├── .hy/                        ← 配置、会话、模板、语言源
│   ├── config.yaml             ← 约定值（ID 格式/阶段/角色/质量线）
│   ├── session/                ← 本机会话状态（整目录不入库）
│   │   ├── bindings/{hash}.yaml ← 每个代理会话各自的迭代绑定
│   │   ├── current.yaml        ← 旧版遗留（仅人工迁移，运行时不自动读取）
│   │   └── prefs.yaml          ← 指令语言偏好
│   └── i18n/{zh,en}/           ← 语言源（skills/ + AGENTS.md + templates/）
├── shared/                     ← 跨项目通用规范（通用/TS/Go/Rust/安全/测试/Git，随仓库发布）
└── workspace/                  ← 本机业务区（含个人内容，整目录不入库）
    ├── _index.yaml             ← 项目注册表
    └── {project}/              ← 业务项目位
        ├── profile.yaml        ← 仓库登记（role/shared/backend_apps/desc/langs/pending）
        ├── code_lib/{repo} →   ← 真实代码库的软链（改动落码的地方）
        ├── knowledge/{repo}/   ← 知识库（overview/api/data/changelog，/hy-knowledge 维护）
        └── iterations/{id}/    ← 迭代产物（prd/contract/plan/smoke/implementation/attach）
```

**迭代 ID**：`{YYMMDD}-{type}-{slug}`，type ∈ feat|fix|refactor|doc|chore。
**三阶段状态机**（SSOT 在迭代 `_index.yaml → stages`）：`prd → dev → smoke`；契约闭合状态另记 `_index.yaml → contract` 字段（`/hy-req` 内闭合，dev 阶段 0 兜底）。
**仓库开发顺序**：backend/service 角色仓先，其余按 profile 声明序；共享后端/服务层仓（如 shared_be）按 `backend_apps.{name}.paths` 路由到子项目目录。

## 二、Skill 体系（全部 hy- 前缀）

| 能力 | 触发 | 说明 |
|------|------|------|
| 元规范 | `/hy-spec` | P0/P1 约束 + 执行生命周期 + 输出质量（每次对话应知） |
| 导航 | `/hy-guide` | 框架地图与链路导航 |
| 职责链 | `/hy-roles` | PM/架构师/开发者三人格合一（澄清/把关/守护），只评审不落盘 |
| 项目/软链 | `/hy-project` | 新项目登记、软链三模式、pending 补链 |
| 开迭代+PRD | `/hy-req --project X --title T` | 显式 `--title` 必定新建并绑定；无 title 时按会话状态续填/修订，未绑定则 Ask-First 绑定已有或创建新迭代 |
| 开发 | `/hy-dev` | 四阶段状态机（契约兜底→计划→实现→自检）+ 仓间自动串联 |
| 修复 | `/hy-fix` | 系统化缺陷修复（fix-*.md 留痕） |
| 复检 | `/hy-review` | 独立重检/CR（review.md 结论） |
| 冒烟 | `/hy-test` | smoke.md（AC↔结果↔证据），fail 回 /hy-fix |
| 知识库 | `/hy-knowledge` | 代码注入（bootstrap 冷启动）+ 迭代变动沉淀（iteration） |

**跨 Agent 会话隔离**：每个代理会话只绑定一个迭代，并且该绑定必须显式归属唯一的 `workspace/{project}`。active 与 previous 记录都必须包含 `project`、`iteration_id`、`iteration_path`，其中路径只能是 `workspace/{project}/iterations/{iteration_id}`；工具在读写边界 fail closed 校验，禁止只凭迭代 ID、最近记录或 cwd 推断 workspace。身份优先级为命令前置 `--session-id` → `HY_SESSION_ID` → 已知平台适配器 `CODEX_THREAD_ID`；所有入口对同一个原始 ID 计算相同的带命名空间 SHA-256 摘要，原始 ID 不落盘。其他 Agent 必须在会话启动环境注入稳定且唯一的 `HY_SESSION_ID`，并在上下文压缩、进程续跑期间保持不变；跨 Agent 交接同一逻辑会话时双方使用同一 ID，但同一时刻只允许一个写入者，真正并行必须使用不同 ID。没有可信 ID 时绑定相关命令必须 fail closed，禁止读取或写入共享 `.hy/session/current.yaml`。

**未绑定会话入口门禁（执行型请求）**：首次收到会推进需求、开发、修复、复检、冒烟或 iteration 沉淀的 `/hy-*` 或自然语言请求时，先运行 `python3 happlylong.py session show`。纯问答、`/hy-spec`、`/hy-guide`、`/hy-roles`、项目/软链接入、框架诊断、框架源码维护与开源/发版准备，以及 `/hy-knowledge bootstrap` 不要求业务迭代绑定。稳定身份存在但结构化结果为 `active: false`（`entry_gate.policy: ask_first_bind_or_create`）时：

1. **仅 `/hy-req` 显式带 `--title` 例外**：它就是“新 PRD”信号，不询问绑定已有还是新建；补齐/确认 `project` 后立即创建并绑定新迭代。即使当前已有绑定，也必须新开迭代，旧绑定进入 `previous`。
2. 其余执行型请求先运行 `iter list` 展示候选，再 Ask-First 让用户选择 **绑定已有迭代** 或 **创建新迭代**；优先使用宿主提供的结构化提问/选择 UI，无此能力时用等价的明确问题。可基于原始意图标推荐项，但禁止代选。
3. 选择绑定：缺什么只追问 project/iteration ID，执行 `session set` 并用 `session show` 验证后，恢复原始请求。选择新建：补齐 project/title/type/需求正文，转 `/hy-req` 闭合 PRD，再按原始请求和阶段前置继续。
4. 用户给出的项目/迭代无效或信息仍不足时，保持门禁、不产生迭代产物、不改 `code_lib/`，重新展示有效候选并继续 Ask-First；用户明确取消则结束。

**迭代定位顺序**：显式 `--project + --iteration-id` > 当前会话绑定；`--project` 单独出现时只能与当前会话已绑定项目一致，禁止通过项目级共享指针跨会话猜测迭代。

**指令语言**：Skill 源在 `.hy/i18n/{zh,en}/skills/`；`.agents/skills/` 与本文件为安装产物，由 `python3 happlylong.py lang zh|en` 切换（首次 `init` 按系统 locale 探测一次并固定）。修改指令请改对应语言源后重跑切换命令。

## 三、P0 红线（违反即中止）

**安全**：禁止硬编码凭据（密码/Key/Token）；禁止 SQL 拼接（一律参数化）；每个端点必须校验权限；禁止裸 `except`（异常必须处理或留日志）。

**业务**：
- **无 PRD 禁改码**：`stages.prd ≠ done` 时禁止改动 `code_lib/`（P0，bug 热修也须先补 PRD 或征得明确许可）。
- **删数据先快照**：任何删除数据/文件的操作先记录删除前状态。
- **禁止自动 git 提交**：未经用户明确要求，不执行 `git add/commit/push`；工作区改动留给用户审阅。
- **产物路径唯一**：迭代产物只落 `workspace/{project}/iterations/{id}/`，框架文件只落 `.agents/`、`.hy/`；禁止在框架外乱放。
- **会话身份不可猜测**：绑定相关操作缺少可信会话 ID 时必须中止；禁止按 cwd、进程号、终端、最近迭代或共享 `current.yaml` 猜测。
- **绑定必须指明 workspace**：active/previous 绑定均须显式携带合法 `project`，且路径严格匹配 `workspace/{project}/iterations/{iteration_id}`；字段缺失或路径不一致即中止。
- **未绑定禁执行**：除 `/hy-req --title` 明确新建外，执行型请求必须先完成“绑定已有 / 创建新迭代”的 Ask-First 门禁；用户选择前禁止写迭代产物或业务代码。

## 四、P1 硬约束

- 路径一律 `pathlib.Path`（工具脚本）；禁止依赖 cwd，用框架根锚定。
- 禁止 `except: pass`；禁止裸 `raise`，用自定义异常。
- 输出禁止占位符残留（TODO/待补充/TBD/FIXME）；文档变更必须更新修订历史。
- 代码规范按语言加载：`shared/standards/{typescript,go,rust}.md` + `coding-standards.md`（通用与 Git）；安全/测试另见 `security-rules.md`、`testing-standards.md`。
- 跨平台接入：AGENTS.md 即跨平台开放标准（本文件与 `CLAUDE.md`、`.agents/skills/` 均为 `init`/`lang` 生成的**本机安装产物**，语言源在 `.hy/i18n/{lang}/`）；Claude Code 自动读根 `CLAUDE.md`（内容为 `@AGENTS.md` 引用），如需 `/hy-*` 技能可自建 `.claude/skills` 软链（`mkdir -p .claude && ln -s ../.agents/skills .claude/skills`），框架不维护镜像目录。

## 五、Skill 执行生命周期

```
触发 → 身份检查（稳定会话 ID）→ 会话门禁（未绑定则 Ask-First 绑定/新建；hy-req --title 直接新建）
     → 上下文收集（用 happlylong.py session show 解析绑定，再读迭代 _index.yaml + profile.yaml）
     → 检查点（前置条件校验，不满足给明确指引）
     → 执行（状态机推进，产物落迭代目录）
     → 质量验证（占位符/完整性/路径正确）
     → 提交（回写 stages，输出 Next Steps）
```

**Ask-First 原则**：只有「拿不准的决策」才停下来问（给问题+选项+推荐项）；常规推进一律自动连续执行，一次请求能走多远走多远。

## 六、质量分级

A（全维度达标）｜B（P0 达标有小瑕疵）｜C（最低可交付）→ 通过；**D（P0 未达标）→ 拒绝并修正**。最低交付线 C（见 `.hy/config.yaml`）。

## 七、违规处理

P0 → 立即中止 + 说明 + 修正建议；P1 → 警告并修正；P2（建议项）→ 提示后继续。

---

*happlylong v0.1.2 · 单轨 lite · 零镜像 · 工具即真相*
