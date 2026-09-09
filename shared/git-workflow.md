# Git 工作流（git-workflow）

> 个人多项目：轻流程、强纪律。核心红线——**代理不得自动 add/commit/push**。

## 1. 分支

- 日常可直接在主分支工作（个人项目默认）；改动大或多步验证时开短分支：`{type}/{iteration-id}`，如 `feat/260901-feat-share-card`。
- 共享仓（shared_be）涉及子项目的改动建议开分支，避免影响另一子项目的在途工作。
- 分支存活不过三天量级；合完即删。

## 2. 提交

- 格式与类型见 `coding-standards.md §4`：`type(scope): subject`，scope=仓库名。
- 一次提交一件事；迭代产物（workspace 侧）与代码（code_lib 侧）分开提交。
- 多仓迭代：各仓独立提交，commit body 可写迭代 ID 互相引用（`happlylong: 260901-feat-share-card`）。
- 提交前自查：`git status` 无意外文件；生成物/依赖目录未混入；敏感文件未提交。

## 3. 推送与远端

- 推送前确认目标远端与分支（多项目机器上容易推错仓）；推送是用户动作或用户明确要求后执行。
- shared_be 的 `git-recursive-push.sh` 等脚本：理解其行为再使用，不确定就问。

## 4. 迭代收尾

1. `/hy-test` 全 pass（smoke.md 留痕，含各仓测试套件回归）。
2. 用户审阅 diff、自行提交/推送。
3. `/hy-knowledge iteration` 把本次变动沉淀进知识库（changelog + api/data 增量）。
4. `python3 happlylong.py iter close` 关闭迭代（status: done）。
5. 本次是从其他在途迭代切来（紧急 fix 等）→ `python3 happlylong.py session back` 切回原迭代。
6. 需要留档的教训/约定已随第 3 步进 knowledge；仓内 README 级别的重大变化单独提 PR。

## 5. 事故处置

- 提交了敏感信息：立即告知用户 → 轮换凭据 → 按用户指示清理历史（rewrite 前备份）。
- 推错分支/仓库：不自行 force 操作，报告并给方案。
