# 测试规范（testing-standards）

> 个人项目的务实标准：不追覆盖率数字，追「改动必可验证、回归不靠手抖」。

## 1. 分层与取舍

| 层 | 用途 | 要求 |
|----|------|------|
| 单元测试 | 纯逻辑（计算/解析/状态机/工具函数） | 新增纯逻辑必带；快（无 IO） |
| 集成/接口测试 | DB 访问、HTTP 接口 | 涉及 money/权限/数据迁移的改动必带 |
| E2E/Playwright | 关键用户流程 | 仓库已配（example_fe）则核心流程跑通 |
| 冒烟（/hy-test） | AC 逐条验证 | 每迭代必跑，证据留痕 |

## 2. 通用写法

- 命名表达场景：`TestShareCard_ QRTooSmall_FallsBackToLink`（Go）、`分享卡片-二维码过小-回退链接`（vitest）。
- AAA 结构：Arrange 准备 → Act 执行 → Assert 断言；一个用例一个行为。
- 断言带上下文信息，失败时能直接看出 got/want。
- Mock 只 mock 边界（HTTP/DB/时钟），不 mock 被测逻辑本身。
- 边界必测：空输入、0/负数、超长字符串、并发/重复提交（涉及幂等时）。
- 测试数据用构造器/工厂收敛，不在每个用例里手搓大对象。

## 3. Go（example_be / shared_be）

- 表驱动为主：

```go
func TestCalcRetention(t *testing.T) {
    tests := []struct{ name string; in Input; want int64 }{
        {"空用户集", Input{}, 0},
        // ...
    }
    for _, tt := range tests {
        t.Run(tt.name, func(t *testing.T) { /* got := ...; assert */ })
    }
}
```

- DB 相关测试跟随仓内既有 test 库/事务回滚方案；没有则优先可移植方案（sqlite 内存 或 dockertest，看仓库现状）。
- shared_be 子项目：`internal/server/example_http_test.go` 风格已有先例，新接口测试跟随。

## 4. 前端（vitest / playwright）

- 组件测试：渲染 + 关键交互 + 状态结果，不测实现细节（不断言内部 state）。
- uni-app 项目（example_fe/example）仓内已有 vitest 配置的，工具/逻辑模块必须有测试；页面组件以冒烟为主。
- Playwright（example_fe）：核心流程脚本放 `tests/`，选择器优先稳定属性（data-testid / 角色定位），不依赖样式类名。

## 5. Rust（example_rs）

- 同文件 `#[cfg(test)]` 单元测试 + `tests/` 集成测试；`cargo test` 全绿是提交基线。
- 属性测试（proptest）用于解析/计算类逻辑（仓库已引入时）。

## 6. 冒烟与回归

- `/hy-test` 的 smoke.md 是每迭代的验收证据（AC↔结果↔证据）。
- 修复 bug 必须先有失败用例（或冒烟步骤），修复后复跑 + 回归相邻功能（见 `/hy-fix`）。
