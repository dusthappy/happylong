<div align="center">

# happlylong

**AI 代理驱动的个人多项目产研工作台** —— 一套轻链路管理多个独立项目的 `需求 → PRD → 开发 → 冒烟`，代码库通过软链挂载，不动原仓库结构。

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
![Platform](https://img.shields.io/badge/Platform-macOS%20%7C%20Linux%20%7C%20Windows-lightgrey.svg)

简体中文 | [English](README.en.md)

</div>

---

## 这是什么

happlylong（缩写 **hy**）把「带 PRD 门槛的产研流程」做成一套 AI 代理 Skill + 单文件工具，跑在你已有的编辑器/终端里：

- **多个项目，统一管理**：既支持彼此独立的项目，也支持共享后端或公共代码库的关联项目。通过软链将代码库接入 `workspace/{project}/code_lib/`，无需搬动代码或改变原仓库结构；
- **按迭代推进，全过程可追溯**：每次需求作为独立迭代，持续记录需求文档（PRD）、接口契约、开发计划与实现记录、测试结果，统一保存在 `workspace/{project}/iterations/{id}/`，方便回顾、接续和复检；
- **不同会话，并行开发**：每个 AI 会话明确绑定一个项目的一次迭代，不同会话可分别推进不同项目或同一项目的不同迭代，绑定信息和迭代产物各自归属明确。未绑定的新会话会先询问绑定已有迭代还是创建新迭代；
- **无 PRD 禁改码**：所有业务仓库改动必须先过 `/hy-req` 闭合 PRD 与验收标准（AC），AI 代理才能动代码；
- **多仓自动串联**：前后端分离、共享后端多项目挂载，`/hy-dev` 按角色自动排序与路由。

> 会话与迭代隔离不等于代码副本隔离：软链仍指向真实代码目录。多个会话涉及同一代码库时，需协调修改范围，避免同时改写同一文件；同一项目的配置变更应串行执行。

## 设计理念

| 原则 | 含义 |
|------|------|
| **单轨轻链路** | 一条链路 `req → dev → test`，req 阶段即闭合 PRD 与契约；不设多框架多档位 |
| **零平台镜像** | 只维护 `AGENTS.md`（跨平台开放标准）与 `.hy/i18n/` 双语语言源（`.agents/skills/` 为安装产物），不做 .cursor/.claude 等镜像目录与同步机制 |
| **工具即真相** | 一个单文件 CLI `happlylong.py` 管骨架/软链/迭代/会话/体检/语言，状态全部落 YAML，无隐藏数据库 |
| **三阶段状态机** | 迭代只有 `prd → dev → smoke` 三个阶段 + 契约闭合字段，产物平铺四个单文件 |

## 快速上手

准备好 **Git、Python 3.10 或更新版本，以及支持本项目技能的 AI 编辑器**。下面的终端命令在本机执行，`/hy-*` 指令在 AI 对话框中发送，两者不要混用。

### 1. 下载并初始化（只做一次）

在终端执行；已经克隆过的，直接进入包含 `happlylong.py` 的目录：

```bash
git clone https://github.com/dusthappy/happylong.git
cd happylong
```

创建独立 Python 环境，避免影响其他项目。按系统选择一组命令：

**macOS / Linux**

```bash
python3 -m venv .venv
source .venv/bin/activate
```

**Windows PowerShell**

```powershell
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
```

接着在同一终端执行：

```bash
python -m pip install -r requirements.txt
python happlylong.py init --lang zh
python happlylong.py --session-id setup-check doctor
```

看到“体检通过，无问题”即安装成功。`requirements.txt` 只安装 **PyYAML**，用于读写项目配置和迭代状态；`init` 会生成 AI 所需的规则和技能文件，无需手工创建。

> 后续打开新终端时需重新激活 `.venv`；AI 调用工具也应使用此环境的 Python。若 PowerShell 阻止激活，可将后续命令中的 `python` 换成 `.\.venv\Scripts\python.exe`，无需更改执行策略。

### 2. 接入一个代码项目

仍在框架目录的终端执行。`example` 是本机项目名；将 `/abs/path/your-project` 换成你**实际存在的代码目录绝对路径**（Windows 如 `D:/code/your-project`）：

```bash
python happlylong.py project new example --title "我的项目"
python happlylong.py link add example example "/abs/path/your-project" --role fullstack
```

这里只建立链接，不搬动或复制代码；后续 AI 开发会修改原代码目录。还没有代码目录？先创建一个空目录再接入。Windows 建立目录链接可能需要开启开发者模式或管理员权限。

### 3. 在 AI 对话中开始需求

用 AI 编辑器打开 **框架目录 `happylong`**，让它加载规则与技能。Claude Code 的技能接入见 FAQ；非自动提供会话身份的 Agent，先按下一节设置 `HY_SESSION_ID`。

在对话框发送（不是终端）：

```text
/hy-req --project example --title "添加一个新功能"
我希望实现：在这里描述具体功能、使用场景和预期效果。
```

按 AI 的提问确认需求，PRD 完成后发送 `/hy-dev` 开发；开发完成后发送 `/hy-test` 验证。**逐步执行，不要一次把三条指令全部发出。**

已有代码的项目，可在提需求前发送 `/hy-knowledge bootstrap --project example`，让 AI 先梳理代码；验收通过后可用 `/hy-knowledge iteration` 更新知识库。

## 会话与语言（按需配置）

快速上手已显式安装中文。改用英文执行 `python happlylong.py lang en`；切回中文执行 `python happlylong.py lang zh`。不指定语言的首次 `init` 会按系统语言自动选择。切换会同时更新 CLI 文案、模板和 AI 规则；生成的 `.agents/skills/`、`AGENTS.md`、`CLAUDE.md` 只留在本机。

> 显式 `/hy-req --title` 是“新 PRD”信号：无论当前是否已绑定，都直接创建并绑定新迭代。未带 `--title` 时先按当前会话路由；若未绑定，则询问绑定已有还是创建新迭代。

**跨 Agent 会话协议**：优先使用命令前的 `--session-id`，其次使用 `HY_SESSION_ID`，Codex 还可自动适配 `CODEX_THREAD_ID`。每个会话的绑定分别原子写入 `.hy/session/bindings/{hash}.yaml`；只保存带固定命名空间的 SHA-256 摘要，不落原始 ID。每条 active/previous 绑定都显式保存 `project`、`iteration_id`、`iteration_path`，且路径必须严格等于 `workspace/{project}/iterations/{iteration_id}`；读写时都会校验，不能用裸迭代 ID、最近记录或 cwd 猜 workspace。其他 Agent 应在**会话启动环境**中注入稳定且唯一的 `HY_SESSION_ID`：

```bash
export HY_SESSION_ID="claude:project-a:conversation-001"  # 每个会话唯一，整个长会话保持不变
python3 happlylong.py session show
# 无法设置环境变量时，每次都在子命令前传同一个值：
python3 happlylong.py --session-id "claude:project-a:conversation-001" session show
```

PowerShell 等价写法为 `$env:HY_SESSION_ID = "claude:project-a:conversation-001"`。

上下文压缩不会改变落盘绑定；只要该 ID 在压缩、进程续跑或 Agent 交接后保持不变，就会稳定解析到同一迭代。跨 Agent 交接同一逻辑会话时，双方显式使用同一个 `HY_SESSION_ID`，且同一时刻只保留一个写入者；真正并行的会话必须使用不同 ID。若没有可信 ID，绑定相关命令会 **fail closed** 并拒绝执行，不再回退共享的 `current.yaml`，从而避免静默串线。

**未绑定会话入口门禁**：新会话第一次收到会推进需求、开发、修复、复检、冒烟或 iteration 沉淀的 `/hy-*` 或自然语言请求时，先检查绑定。`session show` 的整个 stdout 是单份 YAML 文档；未绑定时以 `active: false` + `entry_gate` 返回机器可判定的门禁契约，并声明 workspace 根与必填绑定字段。代理据此列出有效迭代并循环 Ask-First，让你选择“绑定已有迭代”或“创建新迭代”。输入无效时不会落产物或改代码，而是重新询问；绑定/创建成功后会恢复最初请求。唯一例外是显式 `/hy-req --title`：它明确表示新 PRD，只补齐项目后直接创建。纯问答、框架导航/规范/职责评审、项目或软链接入、诊断、框架源码维护与开源/发版准备，以及 `/hy-knowledge bootstrap` 不受业务迭代门禁影响。

## Skill 一览（全部 hy- 前缀）

| 命令 | 说明 |
|------|------|
| `/hy-spec` | 元规范：P0/P1 约束 + 执行生命周期 + 输出质量分级 |
| `/hy-guide` | 框架地图与链路导航、按场景速查 |
| `/hy-roles` | PM/架构师/开发者三视角评审（只评审不落盘） |
| `/hy-req` | 开迭代 + PRD 一体入口（单文件 PRD + AC + 仓库面判定 + 契约三分支） |
| `/hy-dev` | 四阶段开发状态机（契约兜底→计划→实现→自检）+ 多仓自动串联 |
| `/hy-fix` | 系统化缺陷修复（fix-*.md 留痕） |
| `/hy-review` | 独立复检/Code Review（review.md 结论） |
| `/hy-test` | 冒烟执行（AC↔结果↔证据四列表，fail 回流 /hy-fix） |
| `/hy-knowledge` | 知识库 bootstrap 冷启动 + 迭代变动沉淀 |
| `/hy-project` | 项目登记、软链三模式、pending 补链、doctor 体检 |

## shared：跨项目通用规范

`shared/` 是框架随附的跨项目通用规范（通用编码/Git、TypeScript/Go/Rust 语言规范、安全红线、测试标准），由 `.hy/config.yaml → paths.shared_rules` 指向，`doctor` 会校验其完整性。

## workspace：业务项目位（本机私有，永不入库）

`workspace/` 是你的个人业务区，**整个目录被 `.gitignore` 排除，不进入公开仓库**——项目注册表与各项目的 profile/知识库/迭代产物只存在于本机；虚构教学示例在根目录 [examples/example/](examples/example/)。

首次使用先登记一个项目（真实项目目录在本机，与公开仓库隔离）：

```bash
python3 happlylong.py project new myapp --title "我的应用"
# 单仓（--role 必填：frontend/backend/service/fullstack/lib；建议配 --desc 与 --lang）
python3 happlylong.py link add myapp myapp /abs/path/myapp --role fullstack --desc "单仓全栈"
# 前后端双仓
python3 happlylong.py link add myapp myapp_fe /abs/path/myapp_fe --role frontend --lang typescript --desc "Web 前端"
python3 happlylong.py link add myapp myapp_be /abs/path/myapp_be --role backend --lang go --desc "业务后端"
# 共享后端 + 子项目（多项目挂同一后端仓，按 backend_apps 子模块路由；服务层仓用 --role service）
python3 happlylong.py link add myapp shared_be /abs/path/shared_be --role backend --lang go --shared \
  --app myapp=api/myapp,internal/biz/myapp,internal/service/myapp,internal/data/myapp,sql/myapp \
  --desc "共享业务后端，按子项目路由落码"
# 目标目录还没建好：先登记后补链（--lang 可预先声明代码类型）
python3 happlylong.py link add myapp myapp_new /abs/path/myapp_new --role frontend --lang typescript --desc "新增管理端" --pending
python3 happlylong.py link apply myapp          # 目录就绪后一键补链
```

完整说明见 `/hy-project` Skill 与 [examples/example/](examples/example/) 示例。

## 目录速查

```
happlylong.py|.bat    管理工具（本 README 的所有命令）
AGENTS.md / CLAUDE.md  代理规范与 Claude Code 接入口（init/lang 生成的本机安装产物，不入库）
.agents/skills/       hy-* 技能集（当前语言的安装产物，不入库）
.hy/config.yaml       约定值；.hy/session/bindings/ 每会话迭代绑定 + 语言偏好（本机）
.hy/i18n/{zh,en}/     语言源（skills/ + AGENTS.md + templates/，lang 命令安装）
.hy/opensource.md     开源发布规范（三层隔离/发布流程/release-check）
shared/               跨项目通用规范（编码/安全/测试/Git + TS/Go/Rust）
examples/example/     脱敏示例项目
.github/              Issue/PR 模板、CI 与 Dependabot 配置
workspace/            业务项目位（本机私有，整目录不入库）：_index.yaml + {project}/（profile + code_lib/ 软链 + knowledge/ + iterations/）
```

## FAQ

- **为什么没有 .cursor/.claude 镜像目录？** `AGENTS.md` 是跨平台开放标准（`init` 自动生成根 `CLAUDE.md`，内容为 `@AGENTS.md` 引用，Claude Code 直接识别）；ZCode/Codex 直接读 `.agents/`，框架不维护任何同步机制。
- **Claude Code 怎么用 `/hy-*` 技能？** 仓库不维护平台镜像；需要技能时自建一次软链：`mkdir -p .claude && ln -s ../.agents/skills .claude/skills`（从仓库根执行；Claude Code 项目技能路径是 `.claude/skills/`）。
- **仓库里为什么没有 workspace/？** `workspace/` 是本机业务区（真实项目、注册表、迭代产物），**整目录不入库**；框架层通用规范在根目录 `shared/`，虚构示例在 `examples/`。
- **改了共享后端仓，怎么避免影响其他项目？** 共享仓按 `backend_apps.{name}.paths` 路由到子项目目录，`hy-dev` 自动路由；跨子项目的改动属于 scope 卡点，会停下确认。
- **迭代何时关闭？** `/hy-test` 全 pass 后由你提交业务代码，再执行 `python3 happlylong.py iter close`（要求 smoke=pass）。
- **多个 AI 会话会不会串到同一迭代？** Codex 自动按 `CODEX_THREAD_ID` 隔离；其他 Agent 必须为每个会话设置稳定且唯一的 `HY_SESSION_ID`（或始终传同一个 `--session-id`）。没有可信 ID 时会直接报错，不会共享 `current.yaml`。`session show/set/back/clear`、`iter new` 和依赖绑定的 `iter show/close` 都只作用于当前会话；显式同时传 `--project` 与 `--iteration-id` 的 show/close 可绕过会话补全。
- **新会话没有绑定就直接说“继续开发”会怎样？** 代理先展示可用迭代并询问绑定已有还是创建新的，直到选择有效目标或取消；不会自动选择“最近迭代”。若输入的是 `/hy-req --title "..."`，则明确视为新 PRD 并直接创建新迭代。
- **旧版 `.hy/session/current.yaml` 怎么迁移？** 它不会被自动读取。先为当前 Agent 配置稳定 ID，再根据旧文件中的 `project` 与 `iteration_id` 执行 `python3 happlylong.py session set {project} {iteration_id}`；旧文件仅保留作人工核对。
- **如何保证发布内容不泄露隐私？** 见 [.hy/opensource.md](.hy/opensource.md)：三层隔离模型 + 发布前扫描清单（真实项目名模式源在本机私有文件，不入库）。

## 贡献

欢迎 Issue 与 PR。贡献前请读 [CONTRIBUTING.md](CONTRIBUTING.md)：贡献范围限于框架层（工具/Skill/模板/通用规范/文档/示例），不接受任何真实业务项目内容；参与社区请遵循[行为准则](CODE_OF_CONDUCT.md)，安全漏洞请走 [SECURITY.md](SECURITY.md) 的私密通告流程（勿开公开 Issue）。版本历史见 [CHANGELOG.md](CHANGELOG.md)（当前版本 0.1.2）。

## 许可证

[MIT](LICENSE) © The happlylong Authors
