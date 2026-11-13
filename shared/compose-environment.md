# Compose 编排确认与开发依赖复用 / Approve Compose plans and reuse dependencies

## 中文

本地开发、缺陷复现和冒烟使用的数据库、缓存、消息队列等常驻 Docker 依赖，以当前项目后端的 Compose YAML 为编排真源。同一后端及同一用途环境，只维护一个固定入口（主配置和已有的环境覆盖文件），不按任务另写可运行配置。

1. **定位后端，已有就增补。** 依据当前项目 `profile.yaml`、迭代仓库范围及实际依赖归属，定位 `code_lib/` 下消费该依赖的后端仓；全栈仓用其约定的服务端目录。读该后端的 README、Compose 文件和启动脚本，查清已有入口、文件合并顺序、profile 和有效覆盖。已有 Compose 配置时，只在现有入口对应的文件中增补缺少的服务或资源定义，保留已有服务、端口、卷、网络和覆盖顺序；条目冲突时提交单独差异，不能覆盖整份文件或另建同义配置。没有配置时，按后端惯例确定拟建路径（无惯例时用该后端目录的 `compose.yaml`）。不能唯一定位后端或发现配置由其他仓管理时，先确认实际归属和落点，不在前端、框架根、迭代目录或共享仓子目录另起一套。共享后端沿用所有者的入口；修改共享根或越出 `backend_apps` 声明范围时，需另获明确的范围扩展批准。
2. **固定命名。** 核对目标环境、Docker context、Compose 工程名与服务名。沿用已有命名；新环境按「所属项目 + 用途」固定工程名，例如 `example-dev`、`example-test`，通过顶层 `name:` 或仓库入口的固定 `-p` 指定。核对 `COMPOSE_PROJECT_NAME` 等覆盖项；不按会话、迭代、时间戳、工作树或目录名改名。保留已有固定容器名；默认由固定工程名和服务名生成稳定的容器名（如 `example-dev-db-1`），有兼容要求时才指定唯一的 `container_name`。启动和补建沿用同一命名。
3. **先交用户确认，再实施。** 新建、增补、首次启用未确认的配置，或已确认的编排发生变化时，先出示目标后端、具体文件路径和可审 YAML/最小差异，并说明环境、工程及容器名、服务及依赖、镜像、端口、卷、网络、就绪条件、拟执行动作及数据影响。候选放在对话或现有计划中。确认前只做只读核对（如 `config --quiet`、`ps --all`），不写入或改动生效配置，不启动、创建、重建、停止或删除容器，包括通过脚本间接执行。用户须明确批准配置落地及实际要执行的操作；只批准改文件不等于批准启动。批准后仍须遵守仓库改动门禁和路径范围；未批准则记录卡点，不临时起库。
4. **确认范围内按状态处理。** 只在配置版本（含有效覆盖）、目标环境和操作范围仍一致，且有可核验的用户确认记录时跨会话沿用；不因测试重跑或换会话重新确认。记录只需定位配置版本、环境和批准的操作，可放在既有本机计划或验证记录中；不复制配置或保存凭据。核对服务归属、镜像、连接目标和数据卷后，健康则直接复用，停止且配置匹配则 `compose start`；只有确认缺失、卷和归属不变且原批准明确包含补建时，才用同一入口执行 `up -d --no-recreate`，仅指定所需服务并核对连带依赖。启动后验证就绪。已运行但不健康时先看日志和连接配置，不另起替代。镜像、端口、卷、网络、覆盖项等实际编排变化，或要做原范围外的操作时，先展示差异并重新确认。
5. **隔离数据，保留服务。** 不同项目、dev/test 分开核对端口、数据卷和库/缓存命名空间；固定 Compose 项目名不能隔离显式全局名称、外部卷或宿主机端口。持久数据使用仓库约定的命名卷。共享后端使用所属子项目的数据范围；涉及迁移、重置或互相干扰的写测试，先隔离数据或串行协调。任务结束不自动 `stop`、`down`、重启或移除常驻容器；确需更新或清理时另行确认范围，删除数据前先快照。禁止把 `down -v`、`prune` 或 `--force-recreate` 作为常规步骤。

Makefile、测试脚本等入口也要遵守相同门禁，执行前检查实际行为。禁止以临时 `docker run`、`compose run`、随机工程名或换端口绕开配置。遇到同名、端口、卷冲突或配置漂移时先查清；不要接管同名容器，也不要把 `--no-recreate` 保留的旧配置当作新配置已生效。并行启动冲突时先重新检查同一工程；若另一会话已启动正确服务，直接复用。

以下是单个 Compose 文件及 `db` 服务的只读检查示例。实际调用保留仓库约定的 context、文件组合、profile 和环境参数；启动与补建命令只按第 4 条的确认范围和服务状态择一执行：

```bash
docker compose -f "$hy_compose_file" -p "$hy_compose_project" config --quiet
docker compose -f "$hy_compose_file" -p "$hy_compose_project" ps --all db
```

验证记录只保留工程名、服务、动作和就绪证据，不记录完整展开的配置或凭据。仓库已有明确隔离的 CI 或测试夹具可沿用自身生命周期；仅管理它们自己创建的资源，不接管本机常驻依赖，也不作为本地缺服务时的回退。

## English

Use the current project's backend Compose YAML as the source of truth for long-lived local development, reproduction, and smoke-test dependencies. Keep one canonical entry point per backend and environment, using the main configuration and its established overrides. Do not generate a runnable configuration per task.

1. **Locate the backend and extend the existing configuration.** Use the current project's `profile.yaml`, iteration repo scope, and actual dependency ownership to find the consuming backend under `code_lib/`; for a full-stack repo use its established server-side directory. Read its README, Compose files, and startup scripts to resolve the entry point, file order, profiles, and overrides. When configuration exists, add only missing services or resources to the appropriate file in that entry point. Preserve existing services, ports, volumes, networks, and override order. Present conflicts as a separate diff; do not overwrite the whole file or create a duplicate. If none exists, propose the backend's conventional path, defaulting to `compose.yaml` in that backend directory. If ownership or destination is unclear, or another repo owns the stack, resolve it first; do not create a separate stack in the frontend, framework root, iteration, or shared-backend subdirectory. Reuse the shared backend owner's entry point and obtain explicit scope expansion before touching the shared root or paths outside `backend_apps`.
2. **Pin names.** Verify the environment, Docker context, Compose project, and service names. Keep existing names. For new environments, pin an owner-and-purpose project name such as `example-dev` or `example-test` with top-level `name:` or the fixed `-p` in the repo entry point. Check `COMPOSE_PROJECT_NAME` and other overrides. Never derive names from sessions, iterations, timestamps, worktrees, or cwd. Retain existing fixed container names; default to stable generated names such as `example-dev-db-1`, with unique explicit `container_name` only when needed for compatibility. Keep the names across starts and restoration.
3. **Get user approval before implementation.** To create or extend configuration, first use an unapproved one, or change an approved stack, present the target backend, exact file paths, YAML or minimal diff, environment, project and container names, services and dependencies, images, ports, volumes, networks, readiness, actions, and data impact. Draft in chat or the existing plan. Before approval, perform only read-only checks such as `config --quiet` and `ps --all`; do not edit live files or start, create, recreate, stop, or remove containers, even through scripts. Obtain explicit approval for the configuration and the actual operations. Approval to edit a file does not authorize startup. Follow existing repo edit and path gates after approval; if approval is absent, record the blocker without a fallback.
4. **Act by state within approval.** Carry approval across sessions only when the configuration version (including effective overrides), target environment, and operation scope still match a verifiable user approval record. Record the configuration reference, environment, and approved actions in an existing local plan or verification record; do not duplicate the configuration or save credentials. Verify ownership, images, connection target, and volumes. Reuse a healthy service or `compose start` a matching stopped service. Use `up -d --no-recreate` only for a confirmed missing service with unchanged ownership and volumes when the existing approval explicitly covers restoring it. Target only needed services and check transitive dependencies. Verify readiness; investigate unhealthy services instead of starting replacements. Show the diff and renew approval for effective changes to images, ports, volumes, networks or overrides, or actions beyond the approved scope.
5. **Isolate data and preserve services.** Check host ports, volumes, and database/cache namespaces across projects and dev/test; Compose names do not isolate explicit global names, external volumes, or published host ports. Use repo-defined named volumes for persistent data. Use the applicable subproject's data scope on shared stacks. Isolate or serialize migrations, resets, and conflicting writes. Do not stop, restart, remove, or bring down shared services after each task. Scope deliberate updates or cleanup separately and snapshot before deleting data. Never use `down -v`, `prune`, or `--force-recreate` as routine steps.

Apply the same gate to Makefile targets and test scripts. Do not bypass configuration with temporary `docker run`, `compose run`, random project names, or arbitrary ports. Resolve naming, port, volume, or configuration conflicts without taking over unrelated containers. `--no-recreate` keeps existing configuration; it cannot apply new settings. On a concurrent startup conflict, recheck the same stack and reuse it if the other session started the correct service. The commands above only inspect; choose a startup or restore action according to step 4. Preserve repo-specific context, file set, profiles, and environment settings. Record project/service names, actions, and readiness, not expanded configuration or credentials. Existing isolated CI or test fixtures manage their own resources and are not a fallback for missing long-lived local services.

## 参考 / References

- [Docker Compose project names](https://docs.docker.com/compose/how-tos/project-name/)
- [Docker Compose up and recreation behavior](https://docs.docker.com/reference/cli/docker/compose/up/)

## 修订历史 / Revision history

| 日期 / Date | 变更 / Change |
|---|---|
| 2026-11-13 | Compose 落在项目后端，已有入口增补缺项；明确批准后实施，沿用固定命名和实例。 / Keep Compose in the project backend, extend its existing configuration, obtain approval before implementation, and reuse fixed names and instances. |
