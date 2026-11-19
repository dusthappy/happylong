---
name: hy-dashboard
description: "刷新 happlylong 全局项目看板：在单份本地 HTML 中查看所有已登记项目、前后端仓库、全部迭代及各阶段状态。适用于 /hy-dashboard 或查看、刷新项目总览。"
metadata:
  hy:
    command: hy-dashboard
    kind: workspace
    entry: false
---

# hy-dashboard · 全局项目看板

执行 `python3 happlylong.py dashboard`。若当前目录不在框架根，使用该工作台下 `happlylong.py` 的绝对路径。用户要求直接打开时加 `--open`。

工具从项目注册表、仓库登记和迭代元数据生成快照。首次创建 `workspace/dashboard.html`，以后刷新同一文件。只用工具生成，避免手写 HTML 或创建副本。HTML 可直接离线打开，生成和查看均无需服务或业务迭代绑定。

成功时提供工具返回的本地 HTML 路径。若工具报告读取或写入问题，说明相关位置和原因。

## 修订历史

| 日期 | 变更 |
|------|------|
| 2026-11-18 | 新增全局项目看板技能。 |

## [Next Steps]

- 数据变更后刷新 → `/hy-dashboard`
- 在终端刷新并打开 → `python3 happlylong.py dashboard --open`
