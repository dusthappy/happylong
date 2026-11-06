# happlylong 开源发布规范

> **版本**: 1.10 | **日期**: 2026-11-06 | **适用**: 本仓库的一切公开行为（首次发布与后续维护）
> 本规范回答一个问题：**如何让「本机工作台」与「公开仓库」长期安全地共存于同一目录**。

---

## 一、仓库模型：单仓直发 + gitignore 分层

happlylong 不设独立的发布分支或发布目录，本目录同时是本机工作台与 GitHub 仓库内容源。安全依赖于 `.gitignore` 的三层隔离：

| 层 | 内容 | 入库策略 |
|----|------|----------|
| **发布层** | `happlylong.py|.bat`、`.hy/config.yaml`、`.hy/i18n/{zh,en}/`（skills + AGENTS.md + **templates**）、`shared/`、`examples/`、`tests/`、`requirements.txt`、`.gitignore`、`.gitattributes`、根目录社区文件、`.github/`（Issue/PR 模板、CI、Dependabot） | **tracked**，正常提交 |
| **本机层** | `.hy/session/`（`bindings/{hash}.yaml` 每会话迭代绑定、仅供人工迁移的旧 `current.yaml`、语言偏好 `prefs.yaml`）、`.hy/snapshots/`、`.hy/private-names.yaml`、`AGENTS.md`、`CLAUDE.md`、`.agents/`（**均为 `init`/`lang` 生成的安装产物**）、`.claude/`（用户自建技能软链）、`.zcode/`、`.zcodeignore`（ZCode 自动生成的本机配置）、`workspace/`（**整目录**） | **ignored**，仅本机存在；绑定文件只存会话 ID 摘要，运行时绝不自动读取共享 `current.yaml` |
| **外部层** | `code_lib/` 软链指向的真实代码库 | **永不入库**，目标路径只以登记字段存在于本机 `profile.yaml` |

**P0**：任何新增顶层文件/目录必须先在本规范登记归属层，再决定是否加入 `.gitignore`。禁止「先提交后补查」。

**两条定址原则**：
1. `workspace/` 整目录属于本机层，**任何内容不入库**——框架需要的通用内容（`shared/` 规范）与教学示例（`examples/`）一律放框架层根目录，不借用 `workspace/`（该目录是工具的活跃扫描区，放示例会污染 `doctor` 与迭代扫描）。
2. `workspace/{project}/profile.yaml → target` 等登记字段只描述本机绝对路径，属于外部层映射信息，不随发布层流动。

## 二、内容分级与脱敏清单

### 2.1 分级

| 级别 | 判定 | 处理 |
|------|------|------|
| A 直接发布 | 框架工具、Skill、模板、通用规范（`shared/`）、示例内容、社区文档 | 直接 tracked |
| B 审查后发布 | README、示例项目、通用规范中涉及具体技术栈选型的表述 | 按下方硬规则脱敏后发布 |
| C 永不发布 | session、snapshots、private-names、`workspace/` 全部内容、绝对路径、个人沿革、凭据 | ignored / 不落盘于发布层 |

### 2.2 脱敏硬规则（B 级内容逐条过）

1. **绝对路径**：发布层文档中一律写 `/abs/path/...` 或 `../relative` 形式；禁止出现 `/Users/<用户名>/...` 等真实机器路径。
2. **真实项目名 → 示例名映射**：真实业务项目名禁止出现在发布层。发布层示例统一用 `example` 名族（`example` / `example_fe` / `example_pc` / `example_be` / `example_rs` / `example_game`）与共享后端示例名 `shared_be`；表/缓存键前缀示例 `app1_*` / `app2_*`。
   **具体映射表属于本机隐私**，只存 `.hy/private-names.yaml`（gitignored，本机私有）。每行可写一个真实名，也可写 `真实名 → 示例名`、`真实名: 示例名` 或 YAML 列表项；扫描器只提取左侧真实名并按字面量匹配。新接入真实项目时同步登记该文件。
3. **个人沿革**：内部框架沿革（如与前身框架的对比、迭代动机、人物/时间线）不进入发布层；README 只陈述设计理念本身。
4. **凭据与联系方式**：密码/Key/Token 一律不出现（安全红线）；社区文件中不留个人邮箱，对外联系走 GitHub Issue 与 Security Advisory。
5. **知识库与迭代产物**：`examples/example/` 内的 knowledge/iterations 是**纯虚构的教学样例**，禁止为省事直接复制真实项目内容后裁剪。

### 2.3 日常写入纪律

- 在发布层文件中写示例时，**只用** `example` 名族 + `shared_be`；禁止图方便引用真实项目名（那是最常见的泄露源）。
- 新增真实项目：`python3 happlylong.py project new` 落在 `workspace/` 下，自动被 gitignore 整目录排除，无需额外动作；新增**发布层**目录才需要改 `.gitignore` 并回本规范登记。

## 三、发布前检查清单（每次 push 前过一遍）

发布层自检由工具承担，跨平台、可进 CI：

```bash
python3 happlylong.py release-check
```

它基于 **git 视角的实际入库文件**（NUL 分隔，含未提交的 untracked、排除 ignored；无 git 时按发布层目录枚举）执行。当前发布层是 UTF-8 文本集，无法解码或含 NUL 的文件必须先人工处理，不得跳过扫描后放行：

1. 真实项目名泄露扫描（模式源 `.hy/private-names.yaml`，**跳过空行与注释行**——空行在 grep -f 语义下会匹配一切，此为本命令取代裸 grep 的原因之一）；
2. 本机路径泄露扫描（`/Users/`、`C:\Users\`）；
3. 凭据/个人邮箱扫描，覆盖常见带/不带引号的赋值、JSON/环境变量键及私钥标记；
4. 占位符残留扫描（TODO/待补充/TBD/FIXME/XXX，排除规则定义文件自身的合法提及）；
5. 双语 Skill 名单、AGENTS 源与 22 份 frontmatter 的完整性/YAML/必填字段验证，并确保每个 Skill 以 1–3 条 `[Next Steps]` 收尾；
6. 双语必需模板、社区资源与工作流的实际发布清单完整性，以及 README 标题层级结构一致性；
7. `.hy/config.yaml`、双语 AGENTS 版本头与 `CHANGELOG.md` 版本段一致性；
8. 发布层无软链、GitHub Issue 模板 frontmatter、Dependabot 的 Actions/Python 生态配置、PyYAML 依赖存在且依赖精确版本固定，以及工作流第三方 Action 使用完整 commit SHA 的供应链约束；验证工作流触发器、任务、步骤结构与 run 字段里的单元测试/发布检查命令，不将 YAML 注释算作验证步骤。
9. 发布层 Markdown 本地相对链接存在性（外部 URL 与页内锚点不联网检查）。

退出码非 0 即失败；扫描器自身的检测模式采用运行时拼接，不会自命中。**全部通过才允许 push**，任一命中回第二节修正后重跑。CI 已内置该步骤。

**证据边界**：本地通过不代表 GitHub 认证、remote 或远端 CI 已通过；凭据扫描是启发式检查，不是无泄露证明。正式发布仍须人工核对实际提交清单，并确认真实 GitHub Actions 矩阵结果。

**本机恢复记录**：项目/迭代创建、软链增删/补链和语言安装在改写前将状态保存至 `.hy/snapshots/operation-*/`，同步操作失败时尝试回滚并报告快照位置。快照包含本机路径与配置，禁止入库；发生进程强杀、机器中断或回滚失败时，从 `manifest.yaml` 核对目标后人工恢复。该机制不提供跨进程锁或断电原子性；同一项目配置的修改应串行执行。快照不自动清理，维护者确认不再需要恢复后另行清理。

## 四、版本规则

- **SemVer**：`MAJOR.MINOR.PATCH`。判级口径：
  - MAJOR：迭代 ID 格式、三阶段状态机、`_index.yaml`/`profile.yaml` schema、Skill 触发名、目录约定（如 `shared/` 定位）变更等破坏性变化；
  - MINOR：新增 Skill、新增工具子命令、模板/规范的能力性补充；
  - PATCH：缺陷修复、文档勘误、脱敏修正。
- **三处同步**（P1，发版必改）：`.hy/config.yaml → version`、`AGENTS.md` 版本头、`CHANGELOG.md` 新增段落。三者不一致视为发版未完成。
- **Tag**：`v{X.Y.Z}` 打在发版提交上，GitHub Release 正文复用 CHANGELOG 对应段落。

## 五、发布流程

```bash
# 首次发布
git init -b main
git add -A
git status --short        # 人工核对实际入库清单（对照 release-check 结果）
git commit -m "feat: opensource happlylong v0.1.1"
# 使用当前 gh 登录身份创建公开仓库并配置 origin；若仓库已存在，则从 GitHub Code 菜单复制 URL 手工添加 origin。
gh repo create happlylong --public --source=. --remote=origin --push
git tag v0.1.1 && git push origin v0.1.1
```

GitHub 仓库设置基线：Description 一句话定位；Topics 建议 `ai-agents` `workflow` `prd` `developer-productivity` `agents-md` `skills` `chinese`；默认分支 `main`；开启 Issues、Private Vulnerability Reporting、Dependency graph、Dependabot alerts 与 security updates，版本更新由 `.github/dependabot.yml` 每月检查 Actions/Python；关闭 Wiki/Discussions（轻链路原则，需要时再开）。

**日常发布** = 第三节清单全过 → commit → push；发版另走第四节三处同步 + tag。

## 六、双语维护规则

- `README.md`（中文为主）与 `README.en.md`（英文）**结构对齐、同 commit 更新**（P1）；只改其一的 PR 请求补齐另一份。
- **指令双语**：Skill 与 AGENTS.md 的语言源在 `.hy/i18n/{zh,en}/`（各含 `skills/` 与 `AGENTS.md`）；`.agents/skills/` 与根 `AGENTS.md` 是安装产物，由 `happlylong.py lang zh|en` 或首次 `init`（locale 探测）安装，本机选择存 gitignored 的 `.hy/session/prefs.yaml`。
- **同步纪律（P1）**：修改任何指令内容，中文源与英文源同 commit 更新；只改一种语言的 PR 请求补齐另一种。改完任一语言源后重跑 `python3 happlylong.py lang {lang}` 重装该语言活跃集。
- Skill 与模板保持完整双语；README、贡献指南、安全政策、行为准则和 GitHub Issue/PR 模板均提供英文入口。`.hy/opensource.md` 是维护者发布操作规范，保持中文以避免双份流程漂移。

## 七、社区文件维护

| 文件 | 更新时机 |
|------|----------|
| `CONTRIBUTING.md` | 贡献流程、检查清单或可贡献范围变化时 |
| `CODE_OF_CONDUCT.md` / `SECURITY.md` | 仅在联系渠道或政策变化时；不随版本发版 |
| `.github/ISSUE_TEMPLATE/`、`PULL_REQUEST_TEMPLATE.md` | 自检清单项与本规范第三节联动变化时 |
| `CHANGELOG.md` | 每次发版；未发版的多条变更可先记 `Unreleased` 段 |

**贡献内容边界**：接受对发布层（工具/Skill/模板/`shared/` 通用规范/文档/示例）的贡献；**不接受**任何指向真实业务项目或 `workspace/` 的改动——本机层与外部层不在公开协作范围内，PR 中出现一律拒绝并指引改用 `example` 名族复现。

---

*修订历史*
- 1.10（2026-11-06）：将 ZCode 的 `.zcode/` 与自动生成的 `.zcodeignore` 明确归入本机层；通过 Git 忽略规则排除本机配置，发布扫描不增加豁免。
- 1.9（2026-09-09）：发布清单按 Git NUL 分隔解析；补齐实际入库资源、运行时依赖、有效工作流步骤与 UTF-8 文本检查；明确启发式扫描/远端 CI 的证据边界与本机操作快照恢复约束。
- 1.8（2026-09-04）：补齐 GitHub 发布准备：会话 active/previous 绑定强制归属唯一 `workspace/{project}`，`session show` 改为单一 YAML 契约；`release-check` 修正无 Git 枚举与私有名称映射解析，增加软链、双语清单/README/版本/Skill 收尾/社区模板、Dependabot、Action SHA 与本地链接检查；社区文件扩为完整双语。
- 1.7（2026-09-04）：开源首发版本定为 v0.1.1（0.x 起步，独立于本文档修订号）；第五节首发示例命令按此同步。
- 1.6（2026-09-04）：增加未绑定会话的执行入口门禁：Skill 指令或自然语言即将推进迭代时，必须 Ask-First 循环选择绑定已有/创建新迭代；显式 `/hy-req --title` 唯一表示直接新建 PRD；`session show` 返回机器可判定的 `active`/`entry_gate` 契约，规则同步到双语 AGENTS、Skills、README 与 CLI。
- 1.5（2026-09-04）：跨 Agent 会话身份协议改为 `--session-id` → `HY_SESSION_ID` → 已知平台适配器；缺少可信 ID 时 fail closed，停止共享 `current.yaml` 回退；绑定采用原子写入与身份键校验，避免中断损坏和误读。
- 1.4（2026-09-04）：会话状态改为 `.hy/session/bindings/{hash}.yaml` 按代理会话隔离；仅保存会话 ID 摘要，无 ID 环境保留 `current.yaml` 兼容回退。
- 1.3（2026-09-04）：指令语言扩为完整 i18n（CLI 文案 UI_EN 目录 + 双语模板 `.hy/i18n/{lang}/templates/`）；AGENTS/CLAUDE/.agents 转为本机安装产物（untracked，`init`/`lang` 生成）；发布前检查改为 `release-check` 子命令（修扫描器空行/自命中/错误吞掉三缺陷）+ 单元测试 `tests/` + CI（最小权限、unittest、真实软链测试）。
- 1.2（2026-09-03）：新增指令双语机制——语言源 `.hy/i18n/{zh,en}/`（skills + AGENTS.md），`.agents/skills/` 与根 AGENTS.md 转为安装产物；`lang` 子命令与 `init --lang`/locale 探测；本机语言选择存 `.hy/session/prefs.yaml`；双语维护纪律入第六节。
- 1.1（2026-09-03）：`workspace/` 升级为整目录本机层（任何内容不入库）；通用规范从 `workspace/_shared/` 迁至根目录 `shared/`（`SHARED_DIR` 与 `paths.shared_rules` 同步改），示例定址 `examples/`；扫描清单范围同步收紧到发布层。
- 1.0（2026-09-03）：首发版。确立三层仓库模型、内容分级与示例名映射、发布前检查清单、SemVer 三处同步、双语与社区文件维护规则。
