# Changelog

本项目的所有显著变更记录在此文件。

格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/)，
版本遵循 [SemVer 2.0.0](https://semver.org/lang/zh-CN/)；判级口径见 [.hy/opensource.md](.hy/opensource.md) 第四节。

> 版本号与底部对比链接在**正式发布（打 tag）时**按 `.hy/opensource.md` 第五节流程回填；
> 首个发布版本之前的全部变更均记于 Unreleased。

## [Unreleased]

### Added

- 2026-11-06：新增双语 `shared/feishu-cli.md`，独立整理 CLI 接入、按来源下载图片、缺图核对与本地验收经验；双语 hy-req 按需引用并沿用迭代 `attach/`，不新增技能体系或运行依赖，不迁入来源工程的账号、组织、任务、项目或图片数据。

- 2026-10-16：新增 `prototype preview {project} [--open]`，返回本地 HTML 入口或通过系统默认浏览器打开文件 URI，不启动服务；`show` 增加 `preview_mode` 与 `entry_uri`，schema 1 旧清单省略模式时兼容为 `file`，入口限制为 `.html`/`.htm`。

- 2026-10-15：项目级 `prototype/` 目录与 `iterations/` 平级；新增 `prototype init|show`，`project new` 自动建原型骨架；元数据记录入口、状态和同项目来源迭代，校验路径与入口，安全补建缺件且不覆盖现有内容；`doctor` 支持原型检查与缺件补建；存量项目完全没有原型目录时仅提醒、不计入问题且不写文件，可按需 `prototype init` 或 `doctor --fix` 初始化，已有目录缺件或清单非法仍报错。

### Changed

- 2026-10-16：双语原型模板、README、AGENTS 与相关 Skill 明确原型须直接打开本地 HTML，不以 Node/npm、服务或构建作为预览前提；规定本地资源兼容、文件页存储退化与导出、HTTP 数据隔离，并要求 `ready` 前实际进行 `file://` 交互验证。

- 2026-10-15：中英文 README、AGENTS 语言源与 hy-project/guide/req/dev/spec 明确产品原型的来源追踪、版本覆盖、模拟服务和验证记录；项目原型与迭代附件各归其位，原型可评审状态不能替代业务 AC 或推进 `prd/dev/smoke`。

### Fixed

- 2026-11-06：将 ZCode 自动生成的 `.zcodeignore` 归入本机层并加入 Git 忽略规则，修复它被误当作发布文件导致 release-check 失败的问题；发布文件白名单和扫描规则保持严格。

## [0.1.2] - 2026-09-24

### Added

- 2026-09-24：软链登记显式化——`link add` 的 `--role` 改为必填，role 枚举新增 `service`（服务层）角色；新增 `--desc`（一句话功能定位）与 `--lang`（显式代码类型，可多次，pending 仓可预声明）参数，显式声明优先于自动探测；`--app` 子项目路由放开到 backend/service 共享仓；`link list` 全景展示 role/shared/apps/langs 与功能定位，doctor 对缺失 desc 输出提醒；双语 Skill（hy-project/guide/spec/dev/req）、AGENTS.md 语言源、profile 模板与中英 README 三模式示例同步更新，存量 6 个项目 12 条仓库登记补齐功能定位


### Changed

- 2026-09-24：中英文一致性清理——CLI 文案表与 `ui()` 调用键双向核对归零（删 10 条失效翻译），`--role` 帮助与 pending 状态提示纳入 i18n 渲染；双语 Skill 源（标题层级/代码块结构）、模板占位符、AGENTS.md 章节与根安装产物扫描全部对齐
- 2026-09-24：会话串线防护——`session show` 新增 `session_scope.fingerprint`（绑定文件哈希前 8 位）供并行会话核验身份；AGENTS.md/Skill 源明确「并行会话必须使用独立会话 ID，执行前先核对 fingerprint，串线即换 ID」；支持 SessionStart hook 的平台经 additionalContext 注入每会话唯一 `hy-<CLAUDE_SESSION_ID>` 身份（本机 .zcode/config.json 已配），修复多会话共用主会话 ID 导致绑定互相覆盖、全部走同一迭代的问题
- 2026-09-09：中英文 README 补充独立/关联项目软链接入、迭代全过程留痕与多会话并行开发说明，并明确共享代码目录及项目配置的并发修改边界
- 2026-09-09：中英文 README 快速上手改为“安装初始化→接入代码项目→AI 对话提需求”三步，说明 PyYAML 的用途、独立 Python 环境、命令执行位置与成功标志；会话及语言协议移至后续配置章节

### Fixed

- 显式迭代 ID 在统一入口做白名单校验（`iter show`/`iter close`/`session set`/`iter new` 共用），阻断 `..`、绝对路径等路径穿越读改工作区外 `_index.yaml`（P0）
- `project new` / `iter new` 的标题与描述经 YAML 双引号标量转义后写入模板，冒号、换行、`#` 等字符不再改变 YAML 结构或使文件无法解析
- `link add` 将参数、目标清单和注册表校验前置于建链副作用；文件操作仍可能失败，由快照与回滚保护链接及登记一致性；Windows 目录软链补传 `target_is_directory`
- `link apply` 修正 pending 计数恒为 0 的问题；`link_status` 新增 `mismatch` 状态，链接指向错误目标时 `link list` 与 `doctor` 如实报告异常
- 损坏 YAML（自引用别名、深嵌套触发递归）统一转为可读 `HyError`，语言偏好文件非对象时 fail closed；文案渲染用的语言查询改为自包含宽容降级，消除报错递归崩溃
- `release-check` 凭据扫描补充 `github_pat_`（GitHub 细粒度 PAT）模式，并断言必需发布文件与 CI 工作流存在，缺件临时副本不再假阴性通过
- 迭代、项目、会话绑定、知识库和软链父目录统一校验实际路径边界，拒绝预置元数据软链与手改 profile 仓库键穿越；共享后端 app 路径拒绝绝对路径和父目录穿越
- 项目创建、迭代创建/绑定、软链增删/补链和语言安装在改写前保存本机快照，同步失败回滚；批量补链先检查整批冲突，同目标既有链接可安全重试。快照保留在忽略的 `.hy/snapshots/`，用于异常中断后的人工恢复，不承诺断电原子性或并发写入隔离
- 所有模板字符串使用 YAML 感知转义，补齐隐式类型项目名、Unicode 换行/控制字符及 emoji 往返；严格区分空文档与非对象假值，拒绝循环引用和损坏编码，修复 `doctor`、`status` 与知识库消费者的损坏配置裸崩
- 知识库新鲜度按实际时间点比较，兼容不同 UTC 偏移及 Python 3.10 对原有无冒号时区格式的解析限制
- 发布清单改用 Git NUL 分隔，中文等特殊文件名不再漏扫；补齐未加引号/JSON/环境变量凭据与私钥标记检测，拒绝无法按 UTF-8 文本检查的发布文件
- 发布检查要求双语必需模板、社区资源、运行时依赖与工作流实际进入发布清单；验证工作流结构及真实 run 字段中的测试/发布检查命令，注释不再冒充验证步骤
- 回归测试由 41 项扩充至 65 项，覆盖路径边界、失败回滚、配置类型、发布检查反例与时间兼容性

## [0.1.1] - 2026-09-04

### Added

- 会话模型升级为“一个代理会话绑定一个迭代”（配置 schema 2）：以 `--session-id` → `HY_SESSION_ID` → `CODEX_THREAD_ID` 解析跨 Agent 稳定身份，选择 `.hy/session/bindings/{hash}.yaml`；仅持久化固定命名空间下的 ID 摘要，并采用原子替换与绑定键完整性校验。无可信 ID 时 fail closed，不再读取共享 `current.yaml`。迭代解析改为显式 `project+id` > 当前会话绑定，不再读写项目级 `active_iteration`，支持多个 Agent 会话并行开发不同 workspace，乃至同项目不同迭代；上下文压缩不影响落盘绑定

- 单文件管理工具 `happlylong.py`（+ Windows `.bat`）：`init [--lang]` / `lang` / `release-check` / `status` / `doctor` / `project new` / `link add|apply|rm` / `iter new|close|list` 等子命令
- 10 个 `hy-*` 代理 Skill：spec / guide / roles / req / dev / fix / review / test / knowledge / project，**中英双语各一套**（`.hy/i18n/{zh,en}/skills/`）
- 指令语言 i18n（CLI 文案 + 模板 + Skill + AGENTS.md 四层同语言）：首次 `init` 按系统 locale 自动探测并固定，`init --lang` 显式选择，`lang` 命令随时切换；语言选择存 gitignored 的 `.hy/session/prefs.yaml`
- 迭代/知识库模板双语：`.hy/i18n/{zh,en}/templates/`，按当前语言加载
- 三阶段迭代状态机（`prd → dev → smoke` + 契约闭合字段），产物平铺 prd/contract/plan/smoke 四个单文件
- 多仓编排：仓库角色（frontend/backend/fullstack/lib）、backend 先行开发序、共享后端 `backend_apps` 子项目路由、pending 软链补链
- 知识体系：`/hy-knowledge` bootstrap 冷启动与 iteration 沉淀，知识库四件套（overview/api/data/changelog）
- 跨项目通用规范 `shared/`：通用编码/Git、TypeScript/Go/Rust 语言规范、安全红线、测试标准
- 脱敏示例项目 `examples/example/`：profile 三挂法示例 + 知识库样例 + 完整示例迭代
- 开源发布规范 `.hy/opensource.md`：三层隔离模型、内容分级与脱敏清单、`release-check` 发布前自检、SemVer 三处同步
- CI：`.github/workflows/ci.yml`（Ubuntu + macOS + Windows × Python 3.10/3.14，最小权限；编译检查 + 全新克隆体验 + 语言往返 + 项目/迭代/软链生命周期 + 单元测试 + release-check）
- 单元测试 `tests/`（unittest）：ID/slug/校验/语言探测、跨 Agent 会话身份与隔离、workspace 绑定不变量、fail-closed、原子写入 + 双语源/frontmatter 解析
- 依赖声明：`requirements.txt`（唯一运行时依赖 PyYAML 6.0.3，固定精确版本并由 Dependabot 维护）
- 社区文件：README、CONTRIBUTING、CODE_OF_CONDUCT、SECURITY 与 Issue/PR 模板均提供中英文内容

### Security

- 项目名/仓库名/迭代 ID 白名单校验（`fullmatch`，防路径穿越与正则尾换行绕过）
- `knowledge init` 校验 profile.yaml 仓库名键，防手工编辑注入
- `lang` 切换前校验 `.agents/skills` 非软链，防预置软链导致整组重写波及链接目标
- 安装产物（`.agents/`、`AGENTS.md`、`CLAUDE.md`）不入库，`release-check` 基于发布层源文件扫描
- active/previous 会话绑定在读写边界强制校验 `project`、`iteration_id` 与规范路径 `workspace/{project}/iterations/{iteration_id}`，拒绝缺字段、跨 workspace 路径或裸 ID 推断
- GitHub Actions 第三方步骤固定到完整 commit SHA，checkout 禁止持久化凭据；`.gitattributes` 统一文本行尾并保留 `.bat` 的 CRLF
- `.github/dependabot.yml` 每月检查 GitHub Actions 与 Python 依赖更新，降低完整 SHA 固定后的维护成本
- Unix 下的 `happlylong.py` 标记为可执行文件，同时继续支持显式 `python3 happlylong.py` 调用

### Changed

- 未绑定会话新增执行入口门禁：`session show` 结构化返回 `active: false`、`entry_gate` 策略与合法动作；`/hy-req`（无显式 title）、`/hy-dev`、`/hy-fix`、`/hy-review`、`/hy-test`、`/hy-knowledge iteration` 及等价自然语言请求会列出候选并 Ask-First 循环选择绑定已有/创建新迭代，成功后恢复原请求；显式 `/hy-req --title` 作为唯一明确的新 PRD 信号，始终创建并绑定新迭代
- `session show` 的 stdout 改为单一 YAML 文档，并在未绑定契约中声明 workspace 根与必填字段；框架源码维护、诊断和开源/发版准备明确豁免业务迭代门禁
- `release-check` 补齐无 Git 环境的发布层枚举，正确解析私有名称的纯文本/列表/映射写法，并增加发布层软链拒绝、双语 Skill 精确清单及 `[Next Steps]` 收尾、README 结构、版本三处同步、Issue 模板 frontmatter、不可变 Action 引用与 Markdown 本地链接检查
- 冒烟命令由 `/hy-run` 更名 `/hy-test`（对齐 make/npm test 惯例；阶段名 smoke 与产物 smoke.md 不变）
- 通用规范目录由 `workspace/_shared/` 迁至根 `shared/`；`workspace/` 整目录为本机层，任何内容不入库
