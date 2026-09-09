# 通用编码规范（coding-standards）

> 适用所有语言；语言细节见 `standards/{typescript,go,rust}.md`。改码前按语言加载对应文件，本文件永远生效。

## 1. 通用原则

| 原则 | 要求 |
|------|------|
| 命名 | 名字表达意图：`fetchPendingOrders` 好于 `getData`；禁止 `temp/tmp/data1` 类无义名（循环索引除外） |
| 函数 | 一个函数做一件事；超过 ~60 行或嵌套超过 3 层考虑拆分 |
| 注释 | 解释「为什么」而非「做了什么」；删注释掉的死代码（git 有历史） |
| 错误处理 | 错误必须被处理或显式上抛，禁止吞掉；面向用户的错误给可行动的提示 |
| 日志 | 关键路径有日志；带上下文（谁/什么/参数摘要）；敏感信息脱敏 |
| 魔法值 | 提取常量并命名；字符串状态值用枚举/联合类型收敛 |
| 重复 | 第二次出现即提取（函数/常量/组件） |

## 2. 修改纪律（个人多项目特有）

- **跟随仓库惯例优先于本规范**：目标仓库已有统一写法（目录、命名、错误风格）时先跟随；只有新代码或仓库无惯例时用本规范。
- 最小改动：与当前任务无关的代码不动、不格式化不相关文件、不顺手重构。
- 各仓库自带的 AGENTS.md / CLAUDE.md / README 约定视作该仓最高规范。
- 跨仓改动（一次迭代动多个 repo）每个仓独立提交，不混合 diff。

## 3. 禁止事项（P0/P1）

- 禁止硬编码凭据/密钥/Token（env 或本地不入库配置）。
- 禁止 SQL 拼接；禁止 `except: pass` / 空 `catch` / 忽略 error。
- 禁止提交超大生成物/二进制（构建产物、node_modules、target/、临时导出）。
- 禁止在共享仓（shared_be）改动无子项目归属的公共层而不声明（scope 卡点）。

## 4. Git 提交规范

- 格式：`type(scope): subject`，scope 用仓库名（如 `shared_be`、`example_be`、`example_rs`、`example_game`）。
- type：`feat / fix / refactor / perf / docs / test / chore / style`。
- subject：祈使句、不加句号、≤50 字符优先；一行说不清就写 body。
- 示例：`feat(shared_be): example 相册分享卡片接口`、`fix(example_fe): 分享卡片二维码尺寸错误`。
- **禁止自动提交**：代理不得执行 `git add/commit/push`，除非用户明确要求。
- 多仓迭代提交顺序与开发顺序一致（backend 先），提交信息可互相引用迭代 ID。

## 5. 工具脚本规范（框架自身 Python 代码）

- 一律 `pathlib.Path`；以框架根锚定绝对路径，禁止依赖 cwd。
- 异常体系：业务异常用 `HyError`（`happlylong.py` 内），禁止裸 `raise` / `except: pass`。
- 输出统一走 `info/warn/fail` 三级；子命令返回 int 退出码（0 成功 / 1 异常 / 2 用法错误）。

## 6. 语言规范索引

| 语言/栈 | 文件 | 覆盖仓库 |
|---------|------|----------|
| TypeScript（React/Next、Vue/uni-app、Cocos） | `standards/typescript.md` | example_fe、example_pc、example、example_game、example_rs（TS 部分） |
| Go | `standards/go.md` | example_be、shared_be |
| Rust | `standards/rust.md` | example_rs |
| 安全 | `security-rules.md` | 全部 |
| 测试 | `testing-standards.md` | 全部 |
| 分支/PR | `git-workflow.md` | 全部 |
