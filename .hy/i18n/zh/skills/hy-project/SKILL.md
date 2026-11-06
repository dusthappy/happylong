---
name: hy-project
description: "workspace 项目与代码库软链管理：project new / link add 三模式（单仓、FE+BE 双仓、共享后端+子项目）/ prototype 原型目录 / pending 补链 / doctor 体检。新项目接入、原型目录管理或软链异常时触发 /hy-project。"
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

## 项目级产品原型

`project new` 自动建立 `prototype/_index.yaml` 和 `prototype/README.md`，与 `iterations/` 平级；存量项目用工具补齐：

```bash
python3 happlylong.py prototype init demo
python3 happlylong.py prototype show demo
python3 happlylong.py prototype preview demo
python3 happlylong.py prototype preview demo --open
```

- `init` 只补建缺失骨架，不覆盖内容或生成占位业务页面；`show` 校验并展示元数据和 `entry_uri`。`preview` 要求入口已存在，返回本地文件入口；加 `--open` 才通过系统默认浏览器打开文件 URI。预览不启动服务，这些命令均不改变迭代绑定或业务阶段。
- `_index.yaml` 字段为 `schema: 1`、`project`、`title`、`entry`、`preview_mode: file`、`status`、`source_iterations`、`created`、`updated`。schema 1 旧清单缺少 `preview_mode` 时按 `file` 处理；入口必须为原型目录内相对 `.html`/`.htm` 文件，来源迭代必须存在于同一项目。
- `status` 为 `planned/draft/ready`；`planned` 允许入口尚未创建，`draft/ready` 要求入口存在。`ready` 仅表示原型可评审。
- README 登记来源路线图、PRD、需求覆盖表及页面版本，说明模拟服务、双击 HTML 的打开方式和验证证据。跨迭代原型仅在此维护；单迭代附件仍在 `attach/`，通过链接引用原型。
- 原型必须可在浏览器直接打开本地 HTML（`file://`），使用相对 CSS、经典脚本、媒体路径或内联资源；不得要求用户先运行 Node/npm、服务或构建。演示数据放在本地经典脚本或 HTML 内，不依赖本地 JSON 的 `fetch`、ES module、CDN 或 service worker。浏览器若限制文件页存储，需显示仅当前页有效的状态并提供导出，不能自动迁移旧 HTTP 来源的数据。标为 `ready` 前须实际以 `file://` 打开并验证关键交互、资源和存储退化，静态元数据检查不能替代运行验证。
- 原型不能替代 PRD/契约、勾选业务 AC，或将业务 `prd/dev/smoke` 标为完成。真实业务实现仍通过 `/hy-dev` 落在声明的 `code_lib/` 仓库。

## 巡检

```bash
python3 happlylong.py link list [project]   # 状态 + role/langs/desc 全景
python3 happlylong.py doctor --fix          # 全量体检 + 自动修复 _index/profile 不一致
```

异常处置：
- `broken`：target 被移动/删除 → 确认新路径后先 `link rm`，再重新 `link add`（无需 `--force`）。
- `no-link`：登记存在但软链丢失 → `link apply {project}` 会跳过非 pending 项，此时直接重跑 `link add ... --force`。
- `_index 与 profile 不一致` → `doctor --fix` 自动同步。
- 存量项目完全没有 `prototype/` → `doctor` 仅提醒，不计入问题且不写文件；按需用 `prototype init {project}` 或 `doctor --fix` 建立骨架。
- 已有 `prototype/` 缺清单或 README → `doctor` 计入问题，`prototype init {project}` 或 `doctor --fix` 可安全补建；元数据非法、软链或路径越界 → 报错且不覆盖，核对并修正声明后重查。

## 检查点

1. 确认调用的是目标框架的 `happlylong.py`；非框架根 cwd 下使用脚本绝对路径，禁止按 cwd 猜框架状态。
2. `link add` 的 target 必须是绝对路径；相对路径一律拒绝。
3. `--role` 必须显式声明；每仓补齐 `--desc` 功能定位与 `--lang` 代码类型——`link list` 应能仅凭登记读出「哪个仓干什么、什么技术」。
4. 新项目完成后把 `profile.yaml → stack.langs/frameworks` 人工补齐（doctor 只提醒探测差异）。

## 修订历史

| 日期 | 变更 |
|------|------|
| 2026-10-16 | 增加本地 HTML 预览命令、兼容字段、直接打开约束与文件页验收要求。 |
| 2026-10-15 | 增加项目级产品原型的路径、来源、业务交付边界与存量项目兼容规则。 |

## [Next Steps]

- 项目挂好后开需求 → `/hy-req --project {project} --title {title}`
- 看框架全貌 → `/hy-guide`
- 软链出问题 → `python3 happlylong.py doctor --fix`
