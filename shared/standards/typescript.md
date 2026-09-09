# TypeScript 规范（React/Next · Vue/uni-app · Cocos Creator）

> 覆盖：TS 类仓库——Next.js / React SPA（如 example_fe、example_pc）、uni-app Vue3（如 example）、Cocos Creator（如 example_game）、pnpm workspace 的 TS 部分（如 example_rs）。

## 1. TS 通用

- `tsconfig` 保持各仓现状，不擅自放宽（禁止把 `strict` 关掉来消警告）。
- 禁止无脑 `any`：拿不准用 `unknown` + 收窄；第三方无类型时写最小声明文件。
- 类型优先从源头生成/共享（后端 openapi/契约 → 类型），避免手抄两份漂移。
- 联合类型收敛状态：`type Loadable = { state: 'idle' | 'loading' | 'ok' | 'error'; ... }` 优于多个布尔。
- 导出明确的 API：文件要么默认导出组件/页面，要么命名导出工具；不混两种风格。
- 错误处理：async 一律 `try/catch` 或调用方统一兜底；Promise 不裸 `.then` 链尾无 `.catch`。
- 常量枚举值集中定义（如 `src/constants/`），禁止散落字符串字面量比对。

## 2. 命名与文件

| 对象 | 约定 |
|------|------|
| 组件/类（含 Cocos 组件） | PascalCase，文件名与导出同名（`ShareCard.tsx` / `ShareCard.vue`） |
| 变量/函数 | camelCase；组件内事件处理 `onXxx` / `handleXxx` 跟随仓库既有风格 |
| 常量 | SCREAMING_SNAKE_CASE |
| 类型/接口 | PascalCase；接口不加 `I` 前缀 |
| 页面/路由文件 | 跟随框架惯例：Next `app/` 路由小写 kebab、uni-app 页面按 `pages.json` |

## 3. React / Next（example_fe、example_pc）

- 组件函数式 + Hooks；不用 class 组件（改旧代码除外）。
- 副作用集中在组件内可读位置；依赖数组写全，禁注释掉依赖消警告。
- 状态就近：本地 `useState`，跨页提升/全局 store 跟随仓库既有方案，不新引状态库。
- 服务端数据：跟随仓库既有请求层（封装的 fetch/axios），新接口调用走统一入口，不散落裸 fetch。
- Next（example_fe）：区分 Server/Client 组件，'use client' 只加在需要交互的叶子组件；App Router 数据获取优先服务端组件。
- CRA（example_pc）：保持既有 config-overrides 配置，不升级/换构建方案除非任务就是干这个。

## 4. Vue3 / uni-app（example_fe、example）

- 一律组合式 API（`<script setup lang="ts">`）；新页面/组件不用 Options API。
- 页面在 `pages.json` 注册后再写；分包页面放对应分包目录。
- 样式：跟随既有方案（scss 变量/设计令牌）；禁止硬编码与设计令牌等值的色值/字号。
- 平台差异用条件编译（`#ifdef MP-WEIXIN` 等）收敛，禁止运行时 `uni.getSystemInfo` 判平台散落各处。
- 请求走仓库统一 request 封装；loading/toast 用统一封装而非裸 `uni.showLoading` 散写。

## 5. Cocos Creator（example_game）

- 组件类：`@ccclass('ShareCard')` 名称与类名、文件名一致（PascalCase）。
- 场景引用：能在编辑器里拖的用 `@property`，运行时动态查找 `find()/getChildByName` 尽量少用。
- 逻辑与表现分离：玩法数值/状态放纯 TS 模块（可单测），组件只做绑定与驱动。
- 资源加载用 `resources/assetManager` 异步 API，注意释放（`releaseAsset`）防内存泄漏。
- 禁止在组件 `onLoad` 里做重 IO；帧循环（`update`）内禁止每帧分配对象。

## 6. pnpm workspace（example_rs TS 部分）

- 跨包依赖一律 `workspace:*` 协议；禁止跨包相对路径 import（`../../packages/x`）。
- 公共类型/工具放对应 package 并从入口导出，不深路径引用。

## 7. 验证基线

- 类型：`tsc --noEmit`（或仓内 type-check 脚本）零错误。
- Lint：仓内 eslint 配置；改动文件必须过 lint。
- 测试：有 vitest/playwright 配置的仓，改动涉及的用例必跑（见 `testing-standards.md`）。
