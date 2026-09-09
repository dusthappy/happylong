# 安全政策 / Security Policy

## 支持范围 / Scope

本政策仅覆盖 happlylong 框架自身：`happlylong.py`、`happlylong.bat`、`.hy/i18n/{zh,en}/`、`shared/`、`examples/` 以及发布自动化。

This policy covers the happlylong framework itself: `happlylong.py`, `happlylong.bat`, `.hy/i18n/{zh,en}/`, `shared/`, `examples/`, and release automation.

本政策不覆盖使用该框架管理的业务项目、`workspace/` 或软链目标，也不覆盖使用者自行接入的 IDE 或 AI 平台。

It does not cover business projects managed by the framework, anything under `workspace/` or a symlink target, or third-party IDE and AI platforms connected by users.

## 支持版本 / Supported versions

| 版本 / Version | 状态 / Status |
|----------------|---------------|
| 最新 0.1.x / Latest 0.1.x | ✅ 支持 / Supported |
| 更早版本 / Earlier versions | ❌ 不支持；请升级 / Unsupported; please upgrade |

## 如何报告 / Reporting a vulnerability

请进入本仓库的 **Security** 标签页并选择 **Report a vulnerability**，使用 GitHub Private Vulnerability Reporting 私密提交。不要公开开 Issue，也不要在报告中附带真实业务数据或凭据。若该入口不可用，请通过维护者 GitHub 资料页列出的私密渠道联系。

Open this repository's **Security** tab and choose **Report a vulnerability** to submit through GitHub Private Vulnerability Reporting. Do not open a public issue, and do not include real business data or credentials. If that entry point is unavailable, use a private contact method listed on the maintainer's GitHub profile.

报告应包含以下脱敏信息： / Include the following sanitized details:

- 受影响的版本与组件； / affected version and component;
- 复现步骤与最小复现； / reproduction steps and a minimal reproducer;
- 预期行为、实际行为与影响； / expected behavior, actual behavior, and impact;
- 已知缓解措施或修复建议（如有）。 / known mitigations or a suggested fix, if any.

## 响应预期 / Response expectations

- 约 7 天内确认收到。 / Acknowledgement within approximately 7 days.
- 约 30 天内给出评估与修复计划。 / Assessment and a remediation plan within approximately 30 days.
- 修复按 SemVer 发布，并在 `CHANGELOG.md` 与 Release 说明中致谢报告者（除非要求匿名）。 / Fixes are released under SemVer, with credit in `CHANGELOG.md` and the release notes unless anonymity is requested.

实际时间取决于影响范围与复现难度；若计划变化，维护者会通过私密通告持续更新。

Timelines depend on impact and reproducibility. If the plan changes, maintainers will provide updates through the private advisory.

## 安全设计基线 / Security baseline

- 凭据只放环境变量或不入库的本地 secret 文件。 / Credentials belong in environment variables or untracked local secret files.
- `workspace/`、会话状态和真实代码软链目标不得进入公开仓库。 / `workspace/`, session state, and real codebase symlink targets must never enter the public repository.
- CLI 对项目名、仓库名与迭代 ID 做白名单校验；会话绑定在读写边界校验身份、workspace 项目和规范路径。 / The CLI allowlists project, repository, and iteration identifiers; session bindings validate identity, workspace project, and canonical path on both reads and writes.
- 发布前运行 `python3 happlylong.py release-check`。 / Run `python3 happlylong.py release-check` before release.

更多发布层边界见 [.hy/opensource.md](.hy/opensource.md)。 / See [.hy/opensource.md](.hy/opensource.md) for the complete publish-layer boundary.
