# Rust 规范

> 覆盖：example_rs（cargo workspace，edition 2024，工具链 1.98.0，rustfmt + clippy 已配）。

## 1. 工程组织

- workspace 内新功能优先放进语义明确的既有 crate；新建 crate 需满足「被 ≥2 处复用或边界清晰」（避免碎片化）。
- crate 命名 kebab-case；bin 放 `apps/`、库放 `crates/`（跟随 example_rs 既有结构）。
- 模块文件 snake_case；`mod.rs` 与 `文件名/` 目录风格跟随所在 crate 现状，不混用。
- 公共 API 必须有文档注释（`///`），说明用途、参数与 panic 条件（若会 panic）。

## 2. 格式化与静态检查（提交前基线）

```bash
cargo fmt --check     # 无 diff；只格式化本任务触碰的文件
cargo clippy          # 改动 crate 无 warning（工作区整体历史 warning 不要求本次清零）
cargo test            # 改动 crate 相关测试通过
```

- 不为消 clippy 警告引入 `#[allow]`，除非注释写明理由。

## 3. 错误处理

- 库 crate：`thiserror` 定义错误枚举，错误变体表达语义（`NotFound`/`InvalidInput`…）。
- 应用/bin：`anyhow`（或仓内既有等价物）传播上下文，`.context("加载配置失败")` 补充语义。
- **生产路径禁止 `unwrap()/expect()`**：初始化期「不可能失败」的可用 `expect("原因")` 并注释；请求/命令路径一律 `?` 传播或 match 处理。
- 不用 `Result<(), ()>` 这类无信息错误。

## 4. 所有权与性能

- 优先借用，需要所有权/生命周期纠缠复杂时才 `clone`；热路径 clone 需注释说明取舍。
- `String` vs `&str`、`Vec` vs slice 参数：入参取 `&str`/`&[T]`，产出才拥有。
- 迭代器链优先于手写循环；`collect` 前想清楚是否必要分配。
- async（若 crate 使用 tokio）：禁止未 await 的 future；`.await` 点注意取消安全；阻塞调用放 `spawn_blocking`。

## 5. 安全与边界

- 禁止 `unsafe`，除非：第三方接口要求 + 注释写明不变量 + 用户知情；新增 unsafe 是 Ask-First 卡点。
- 依赖新增/升版：确认活跃维护、license 兼容；锁文件（Cargo.lock，bin 型 workspace 保留）一并提交。
- FFI/序列化边界的数据先校验再使用（不信任外部输入的反序列化结果直接 unwrap）。

## 6. 测试

- 单元测试与被测代码同文件 `#[cfg(test)]`；跨模块集成测试放 crate 的 `tests/`。
- 断言给上下文：`assert_eq!(got, want, "分享卡片宽度计算错误: got={got}")`。
- 边界必测：空集合、0/负数、超长输入、UTF-8 多字节。

## 7. 常见坑（本项目特别提醒）

- edition 2024：嵌套 `impl`、`gen`/`unsafe extern` 等新语法注意 MSRV；不要为老编译器写兼容代码。
- workspace 依赖版本统一在根 `Cargo.toml [workspace.dependencies]` 声明，crate 内 `{ workspace = true }` 引用，禁止各自锁不同版本。
- `rust-toolchain.toml` 已锁 1.98.0 + clippy/rustfmt 组件：不改动该文件除非任务就是升工具链。
