# $project_name 产品原型

本目录与 `iterations/` 平级，承载跨迭代的页面、交互演示及设计说明。需求、契约和验收结论仍以对应迭代文档为准。

## 使用

- 在本目录创建 `index.html`，或将 `_index.yaml → entry` 指向本目录内的相对 `.html`/`.htm` 文件；`preview_mode` 为 `file`。双击入口即可在浏览器体验，无需运行服务。
- 在 `_index.yaml → source_iterations` 登记本项目的来源迭代 ID；同时在设计说明中记录对应需求。
- 入口创建后将 `status` 改为 `draft`；实际以 `file://` 验证关键交互、资源及存储退化并完成原型评审后可改为 `ready`，更新 `updated`。CLI 静态检查不替代浏览器验证。
- 使用 `python3 happlylong.py prototype show $project_name` 查看目录、入口和状态；`prototype preview $project_name` 返回本地文件入口，加 `--open` 通过系统默认浏览器打开文件 URI，不启动服务。
- 重新执行 `prototype init $project_name` 只补齐缺失的骨架文件，保留已有内容；`doctor --fix` 同样不会改写已存在的清单。

## 本地文件兼容

原型必须可在浏览器直接打开本地 HTML（`file://`），使用相对 CSS、经典脚本、媒体路径或内联资源；不得要求用户先运行 Node/npm、服务或构建。演示数据放在本地经典脚本或 HTML 内，不依赖本地 JSON 的 `fetch`、ES module、CDN 或 service worker。浏览器若限制文件页存储，需显示仅当前页有效的状态并提供导出，不能自动迁移旧 HTTP 来源的数据。标为 `ready` 前须实际以 `file://` 打开并验证关键交互、资源和存储退化，静态元数据检查不能替代运行验证。

## 边界

原型中的示例数据、模拟接口和展示状态必须明确标注。原型完成不推进 `prd/dev/smoke`，不替代真实 API 联调、上线或迭代验收；生产实现仍落在已登记的 `code_lib/` 仓库。入口、清单与目录不可使用软链或指向本目录外。

## 修订历史

| 日期 | 说明 |
|------|------|
| $created | 初始化产品原型目录、本地 HTML 直接预览及文件页验证约定。 |
