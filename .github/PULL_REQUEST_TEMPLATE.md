<!-- Run the checklist in CONTRIBUTING.md before submitting. / 提交前请完成 CONTRIBUTING.md 自检。 -->

## Summary / 变更说明

What changed? / 做了什么？

## Motivation / 动机

Link an issue or explain the use case. / 关联 Issue 或说明使用场景。

## Change type / 变更类型

- [ ] CLI (`happlylong.py` / `.bat`)
- [ ] Skills (`.hy/i18n/{zh,en}/skills/hy-*`)
- [ ] Templates (`.hy/i18n/{zh,en}/templates/`)
- [ ] Shared standards (`shared/`)
- [ ] Documentation or examples / 文档或示例
- [ ] Breaking change: iteration ID, state machine, schema, directory convention, or skill trigger / 破坏性变更

## Verification / 自检

- [ ] `python3 happlylong.py --session-id pr-check doctor` passes / 通过
- [ ] `python3 -m unittest discover -s tests -v` passes / 通过
- [ ] `python3 happlylong.py release-check` passes / 通过
- [ ] No real project names, personal paths, raw session IDs, credentials, or unfinished placeholders / 无真实项目名、个人路径、原始会话 ID、凭据或未完成占位符
- [ ] Instruction changes update both `.hy/i18n/zh/` and `.hy/i18n/en/` / 指令变更已同步双语源
- [ ] README structure or examples remain aligned in both languages / README 双语结构与示例保持同步
- [ ] Release changes align config, both AGENTS version headers, and `CHANGELOG.md` / 发版变更已同步版本三处

## Additional context / 补充信息

Screenshots, evidence, or trade-offs. / 截图、验证证据或权衡说明。
