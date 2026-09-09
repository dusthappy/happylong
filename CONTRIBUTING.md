# 贡献指南 / Contributing Guide

感谢关注 happlylong（hy）。贡献流程保持轻量：小步提交、完成自动检查、不带私人内容。

Thanks for your interest in happlylong (hy). Contributions follow the same lightweight model as the framework: keep changes focused, pass the automated checks, and include no private content.

## 能贡献什么 / What you can contribute

| 范围 / Area | 说明 / Details |
|-------------|----------------|
| 工具 / CLI | 改进 `happlylong.py` 的子命令、健壮性或跨平台行为；涉及 Windows 启动时同步维护 `.bat`。 / Improve commands, robustness, or cross-platform behavior in `happlylong.py`; keep the `.bat` launcher aligned when Windows startup behavior changes. |
| Skill | 改进 `.hy/i18n/{zh,en}/skills/hy-*/` 的流程、提示质量或触发描述。 / Improve workflows, instruction quality, or trigger descriptions under `.hy/i18n/{zh,en}/skills/hy-*/`. |
| 模板 / Templates | 改进 `.hy/i18n/{zh,en}/templates/` 中 `.tpl` 文件的字段或结构。 / Improve fields or structure in `.tpl` files under `.hy/i18n/{zh,en}/templates/`. |
| 通用规范 / Shared standards | 向 `shared/` 补充可跨项目复用的编码、Git、安全、测试或语言规则。 / Add reusable coding, Git, security, testing, or language rules to `shared/`. |
| 文档与示例 / Docs and examples | 同步改进双语 README、FAQ 或 `examples/example/` 教学样例。 / Improve the bilingual READMEs, FAQ, or the fictional `examples/example/` tutorial. |
| 测试 / Tests | 在 `tests/` 中补充基于 `unittest` 的回归测试。 / Add `unittest` regression coverage under `tests/`. |

**不接受**：任何指向真实业务项目的改动、个人数据、凭据或本机绝对路径。业务场景请用虚构名称 `example`、`example_fe`、`example_pc`、`example_be`、`example_rs`、`example_game` 与 `shared_be` 复现。完整边界见 [.hy/opensource.md](.hy/opensource.md)。

**Not accepted**: changes that reference real business projects, personal data, credentials, or machine-specific absolute paths. Reproduce business scenarios with the fictional names `example`, `example_fe`, `example_pc`, `example_be`, `example_rs`, `example_game`, and `shared_be`. See [.hy/opensource.md](.hy/opensource.md) for the complete boundary.

## 上手开发 / Getting started

从 GitHub 仓库的 **Code** 菜单克隆项目，然后运行以下命令。 / Clone the project from GitHub's **Code** menu, then run:

```bash
cd happlylong
python3 -m pip install -r requirements.txt
python3 happlylong.py init
python3 happlylong.py --session-id contributor-check doctor
python3 -m unittest discover -s tests -v
python3 happlylong.py release-check
```

`init` 会幂等检查骨架并按 locale 安装语言包。在支持 `.agents/skills` 的 AI IDE 中打开目录即可使用 `/hy-*`；用 `/hy-spec` 查看元规范。

`init` idempotently checks the skeleton and installs a language pack based on the locale. Open the directory in an AI IDE that supports `.agents/skills` to use `/hy-*`; run `/hy-spec` for the meta-spec.

## 提交约定 / Commit conventions

- 提交信息使用 `type(scope): subject`；type 为 `feat`、`fix`、`refactor`、`doc` 或 `chore`，scope 使用模块名。 / Use `type(scope): subject`; choose `feat`, `fix`, `refactor`, `doc`, or `chore`, with the module as scope.
- 迭代 ID、状态机、schema、目录约定或 Skill 触发名的破坏性变更必须在 PR 中显著说明，并同步 `CHANGELOG.md`。 / Clearly flag breaking changes to iteration IDs, state machines, schemas, directory conventions, or skill trigger names, and update `CHANGELOG.md`.
- 未经仓库维护者明确要求，不在自动化 Agent 流程中自行提交或推送。 / Automated agents must not commit or push unless the maintainer explicitly requests it.

## PR 自检清单 / Pull request checklist

- [ ] `python3 happlylong.py --session-id contributor-check doctor` 通过。 / Passes.
- [ ] `python3 -m unittest discover -s tests -v` 全部通过。 / All tests pass.
- [ ] `python3 happlylong.py release-check` 通过。 / Passes.
- [ ] 未引入真实项目名、个人路径、凭据或未完成占位符。 / No real project names, personal paths, credentials, or unfinished placeholders were introduced.
- [ ] 指令变更同时更新 `.hy/i18n/zh/` 与 `.hy/i18n/en/`，并运行 `python3 happlylong.py lang zh` 或 `lang en` 重装活跃集。 / Instruction changes update both language sources and reinstall the active set with `lang zh` or `lang en`.
- [ ] README 的结构或示例变更同时更新 `README.md` 与 `README.en.md`。 / README structure or examples are updated in both files.
- [ ] 发版变更同步 `.hy/config.yaml` 版本、双语 AGENTS 版本头和 `CHANGELOG.md`。 / Release changes align the config version, both AGENTS version headers, and the changelog.
- [ ] 遵守 P0 红线：无硬编码凭据、无裸异常吞噬、产物路径正确。 / P0 red lines are respected: no hard-coded credentials, swallowed exceptions, or misplaced artifacts.

## Issue 指南 / Issue guide

- 提交前搜索既有 Issue，避免重复。 / Search existing issues before opening a new one.
- Bug 请附操作系统、Python 版本、AI IDE、指令语言、复现步骤及脱敏后的 `doctor` 输出。 / For bugs, include the OS, Python version, AI IDE, command language, reproduction steps, and sanitized `doctor` output.
- 使用仓库模板并补全关键信息；维护者可能要求先补充信息。 / Use the repository templates and provide the requested details; maintainers may ask for missing information first.
- 安全漏洞不要开公开 Issue，请按 [SECURITY.md](SECURITY.md) 私密报告。 / Do not open public issues for vulnerabilities; report them privately as described in [SECURITY.md](SECURITY.md).
