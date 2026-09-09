---
name: hy-knowledge
description: "项目知识库注入与迭代沉淀：bootstrap 模式从代码直接生成初始知识（零迭代冷启动），iteration 模式提取已完成迭代的功能变动追加沉淀；驱动 happlylong.py knowledge 子命令。触发 /hy-knowledge。"
metadata:
  hy:
    command: hy-knowledge
    kind: knowledge
    entry: true
---

# hy-knowledge · 知识库

> 把「代码与迭代里的稳定事实」沉淀成项目历史：后来者（含未来的 Agent 会话）读知识库即可快速建立上下文，不必每次重新分析全仓。两个模式共用一套产物结构，无参调用时自动路由。

## 知识库结构

```
workspace/{project}/knowledge/
├── _index.yaml            ← 清单（CLI 维护）：每仓 files/updated/source
└── {repo}/
    ├── overview.md        ← 必有：定位/技术栈/目录地图/启动与验证/约定要点/仓间关系
    ├── api.md             ← 有 HTTP 后端才建：接口按模块分组的清单
    ├── data.md            ← 有持久化才建：schema/表清单与定义位置
    └── changelog.md       ← 迭代流水（iteration 模式追加，新的在上）
```

**写入原则**：只写稳定事实（结构、约定、清单、关系），不抄实现细节、不复述代码；来源必须标注 `bootstrap`（代码注入）或 `iteration`（迭代沉淀）；结论要能被代码验证，发现文档与代码矛盾时以代码为准并修正知识（矛盾无法裁定 → 卡点问用户）。

**共享仓知识归属**：同一共享仓（如 shared_be）挂在多个项目下时，**完整知识只放「主消费项目」**（子模块已实际存在的项目，如 example）；其余项目（如 example_game）只放一份轻引用 overview（说明共享关系 + 本项目视角的子模块规划 + 指向主消费侧完整知识路径），不建 api/data/changelog 副本，避免双份漂移。iteration 沉淀同样只写主消费侧（changelog 注明影响的子项目）。

## 模式路由（无参调用时）

```
/hy-knowledge
  ├─ knowledge/_index.yaml 不存在，或某登记仓缺 overview.md ─→ bootstrap（优先补齐）
  ├─ 会话迭代 status=done 或 smoke=pass，且 changelog 无该迭代 ─→ iteration
  └─ 都不需要 ─→ 展示 knowledge status 汇报（新鲜度/缺口）
```

显式指定：`/hy-knowledge bootstrap [--project X] [--repo Y]`、`/hy-knowledge iteration [--iteration-id {id}]`。

**会话门禁**：`bootstrap` 与只展示 `knowledge status` 不要求迭代绑定。只有即将进入 `iteration` 模式时先执行 `session show`；若未绑定，先 `iter list [project]`，Ask-First 循环选择绑定已有或创建新迭代。绑定后以 `session show` 验证再恢复沉淀；选择创建则转 `/hy-req`，并等该迭代满足 smoke=pass/已关闭前置后再恢复。无效或不完整输入保持门禁、不写知识文件并继续询问，取消才结束。即使显式传 `--iteration-id`，未绑定会话也先确认并落绑定。

## bootstrap · 从代码注入（零迭代冷启动）

适用：新接入项目、或知识库落后太多想整体重建认知。

1. **准备**：`python3 happlylong.py knowledge init --project {project}`（已初始化则跳过；逐仓刷新加 `--force` 只重建清单不动 md）。
2. **逐仓分析**（可并行），证据来源按优先级：仓内 AGENTS.md/CLAUDE.md/README → 目录结构与 manifests（package.json/go.mod/Cargo.toml/pages.json 等）→ 关键入口代码。共享仓（shared_be）按 `backend_apps` 子项目分组分析。
3. **产出**：
   - `overview.md`（必有）：按模板五节填实；「约定要点」从邻近代码归纳（命名/分层/错误处理/请求封装），这是给未来开发的最有价值输入。
   - `api.md`：后端仓扫路由注册（Go 看 api/ 与 internal/server）得到**模块级**接口清单（路由/方法/说明/鉴权）；不追求逐参数穷举，模块级可用即可。
   - `data.md`：扫 ent schema / sql/ / schemas/ 得表清单与定义位置；共享仓按子项目分小节。
   - 前端仓只产 overview.md。
4. **登记**：每仓写完即 `python3 happlylong.py knowledge register --project {project} --repo {repo} --source bootstrap --file overview.md [--file api.md --file data.md]`。
5. **汇报**：每仓一段摘要 + doctor 验证知识库覆盖。

**规模纪律**：单仓 bootstrap 产物 overview ≤80 行、api/data 各 ≤120 行；信息密度优先于穷举——清单太长就收敛到模块级并注明「详细见代码位置」。

## iteration · 迭代变动沉淀

适用：迭代 smoke=pass（或已 close）后，把这次「做了什么、改了什么、学到什么」沉淀进知识库。`/hy-test` 全 pass 与 `git-workflow` 收尾步骤都会指向这里。

1. **定位迭代**：只使用已通过入口门禁并验证的会话绑定；`--iteration-id` 用于指明要确认绑定的目标，不绕过门禁。读 `_index.yaml`（repos_in_scope/stages）+ `prd.md`（AC）+ `contract.md`（接口/表变更）+ `plan.md`（任务与证据）。
2. **逐仓追加**（只动 repos_in_scope 内的仓）：
   - `changelog.md` 顶部加一节：迭代 ID + 日期 + 功能一句话 + 变更要点（新接口/新表/页面变更，引用 contract 对应小节）+ 教训（有则写）。
   - `contract.md` 里的新接口/新表 → 同步追加到 `api.md` / `data.md` 对应模块小节（保持清单是最新的）。
   - 若迭代改变了仓库结构/约定（新增分层、换请求封装等）→ 刷新 `overview.md` 对应小节并更新其「更新」日期。
3. **登记**：`knowledge register --source iteration --file changelog.md [--file api.md --file data.md --file overview.md]`。
4. **汇报**：沉淀了哪些仓哪些文件，知识新鲜度（`knowledge status`）。

**纪律**：changelog 只记增量不重写历史；AC 未全 pass 的迭代不沉淀（先修完）；跨仓各自追加各自的 changelog，不混写。

## 卡点（Ask-First）

- 代码与既有知识矛盾且无法裁定（可能代码错了）；
- 共享仓发现无子项目归属的公共层变更要写入知识；
- bootstrap 时仓库体量异常（如 shared_be 全量接口逐条穷举会失控）→ 收敛粒度前先确认。

## 检查点

- bootstrap/iteration 产物均无占位符残留；每个文件「来源/更新」行已填。
- register 过的文件真实存在；`doctor` 的 [5] 知识库段无缺 overview 的警告。
- 未迭代过的仓 changelog.md 可以不存在（不要建空壳）。

## [Next Steps]

- bootstrap 完成 → `/hy-req` 开第一个需求（hy-dev 会把 overview 当上下文）
- 迭代收尾 → `/hy-test` 全 pass 后执行 `/hy-knowledge iteration`
- 看覆盖与新鲜度 → `python3 happlylong.py knowledge status`
