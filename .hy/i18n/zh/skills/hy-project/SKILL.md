---
name: hy-project
description: "workspace 项目与代码库软链管理：project new / link add 三模式（单仓、FE+BE 双仓、共享后端+子项目）/ pending 补链 / doctor 体检。新项目接入或软链异常时触发 /hy-project。"
metadata:
  hy:
    command: hy-project
    kind: workspace
    entry: false
---

# hy-project · 项目与软链管理

> 一切机械操作交给 `happlylong.py`；本 Skill 负责「该怎么登记」的判断与示范。工具以脚本所在目录锚定框架根，可从任意 cwd 调用（不在根目录时传脚本绝对路径）。真实代码库永不搬进框架，只做绝对路径软链。

## 登记模型

每条软链登记进 `workspace/{project}/profile.yaml → repos`：

```yaml
repos:
  example_fe:                    # 仓库名 = code_lib/ 下软链名
    role: frontend               # frontend | backend | service | fullstack | lib（登记时必须显式声明）
    desc: 负责示例 Web 端页面与交互 # 一句话功能定位（建议给全；doctor 会对缺失提醒）
    target: /abs/path/example_fe # 绝对路径
    langs: [typescript, vue]     # 代码类型：--lang 显式声明优先，未给则自动探测，可人工修
  shared_be:
    role: backend
    shared: true                 # 跨项目共享仓（example 与 example_game 都挂它）
    target: /abs/path/shared_be
    backend_apps:                # 共享仓内业务子模块（路由落码范围；backend/service 仓可用）
      example:
        title: example 后端子模块
        paths: [api/example, internal/biz/example, internal/service/example,
                internal/data/example, sql/example]
      example_game:
        title: example_game 后端子模块（预留）
        paths: [api/example_game, internal/biz/example_game, internal/service/example_game, internal/data/example_game, sql/example_game]
```

规则：
- **登记即定责**：`--role` 必填，登记时明确该仓是前端、后端、服务层还是全栈/库；每仓建议补 `--desc`（一句话功能定位）与 `--lang`（代码类型），缺 desc 时 doctor 提醒。
- **role 决定开发顺序**：backend/service 仓先，其余按声明序（`/hy-dev` 依赖此规则串联）。
- **shared 仓必须配 backend_apps**：落码范围限定在 paths 内，越界即 scope 卡点（Ask-First）。
- **pending**：目标目录还没建好时先登记后补链，不创建悬空软链（可用 `--lang` 预先声明代码类型）。

## 三种接入模式（照抄改路径即可）

### 模式 A · 单仓（example_rs 型）

```bash
python3 happlylong.py project new demo --title "演示"
python3 happlylong.py link add demo demo /abs/demo --role fullstack --desc "单仓全栈：页面与接口一体"
```

### 模式 B · FE + BE 双仓（example 型）

```bash
python3 happlylong.py project new demo --title "演示"
python3 happlylong.py link add demo demo /abs/demo_fe --role frontend --lang typescript --desc "演示 Web 前端（Vue）"
python3 happlylong.py link add demo demo_be /abs/demo_be --role backend --lang go --desc "演示业务后端"
# example_fe 型多前端：继续 link add 多条 role=frontend（声明序即开发序）
```

### 模式 C · 共享后端 + 子项目（example / example_game 型）

```bash
python3 happlylong.py project new demo --title "演示"
python3 happlylong.py link add demo demo /abs/demo_fe --role frontend --lang typescript --desc "演示 Web 前端（Vue）"
python3 happlylong.py link add demo shared_be /abs/shared_be --role backend --lang go --shared \
  --app demo=api/demo,internal/biz/demo,internal/service/demo,internal/data/demo,sql/demo \
  --desc "共享业务后端，按子项目路由落码" \
  --note "沿 shared_be 分层惯例；子项目路径建好后如不符实际，改 profile 即可"
```

> 纯服务层仓（网关/BFF/中间件等）用 `--role service`，共享时同样配 `--app` 路由子项目。

> 重复挂载同一共享仓到多个项目是**预期行为**（shared_be 同时在 example 与 example_game 下）；迭代产物按项目分开存放于各自 `iterations/`。

## pending 工作流

```bash
# 登记（目标不存在也不建悬空链；--lang 可预先声明代码类型）
python3 happlylong.py link add demo demo_new /abs/demo_new --role frontend --lang typescript --desc "新增管理端" --pending
# 目标就绪后一键补链（doctor 也会提示 pending）
python3 happlylong.py link apply demo
```

## 巡检

```bash
python3 happlylong.py link list [project]   # 状态 + role/langs/desc 全景
python3 happlylong.py doctor --fix          # 全量体检 + 自动修复 _index/profile 不一致
```

异常处置：
- `broken`：target 被移动/删除 → 确认新路径后先 `link rm`，再重新 `link add`（无需 `--force`）。
- `no-link`：登记存在但软链丢失 → `link apply {project}` 会跳过非 pending 项，此时直接重跑 `link add ... --force`。
- `_index 与 profile 不一致` → `doctor --fix` 自动同步。

## 检查点

1. 确认调用的是目标框架的 `happlylong.py`；非框架根 cwd 下使用脚本绝对路径，禁止按 cwd 猜框架状态。
2. `link add` 的 target 必须是绝对路径；相对路径一律拒绝。
3. `--role` 必须显式声明；每仓补齐 `--desc` 功能定位与 `--lang` 代码类型——`link list` 应能仅凭登记读出「哪个仓干什么、什么技术」。
4. 新项目完成后把 `profile.yaml → stack.langs/frameworks` 人工补齐（doctor 只提醒探测差异）。

## [Next Steps]

- 项目挂好后开需求 → `/hy-req --project {project} --title {title}`
- 看框架全貌 → `/hy-guide`
- 软链出问题 → `python3 happlylong.py doctor --fix`
