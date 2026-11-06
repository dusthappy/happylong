#!/usr/bin/env python3
"""happlylong CLI — 个人多项目产研工作台管理工具。

设计理念：
  1. 单文件工具：路径 SSOT / 软链管理 / 迭代创建 / 会话绑定全部集中于此，不拆 lib。
  2. 软链一等公民：code_lib 软链 + repo 角色 + 共享后端子项目（backend_apps）+ pending 延迟建链。
  3. 状态机极简：迭代只有 prd / dev / smoke 三个阶段键 + contract 独立字段，产物平铺在迭代目录。
  4. 零 cwd 依赖：一切以本文件所在目录为框架根，可在任意目录调用。

用法：
  python3 happlylong.py [--session-id ID] <command> [args]
  常用：init [--lang zh|en] / lang [zh|en] / status / doctor / project new /
        link add|rm|apply|list / prototype init|show|preview /
        iter new|list|show|close / session show|set|back|clear
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import uuid
import webbrowser
from collections.abc import Mapping
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from string import Template
from typing import Any

def _force_utf8_console() -> None:
    """Windows 控制台默认 GBK；把 stdio 重绑为 UTF-8，中文输出才不乱码。"""
    if sys.platform != "win32":
        return
    import io
    for name in ("stdout", "stderr"):
        raw = getattr(sys, name)
        if raw is not None and hasattr(raw, "buffer"):
            setattr(sys, name, io.TextIOWrapper(raw.buffer, encoding="utf-8", line_buffering=True))


_force_utf8_console()

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None  # 所有 yaml 相关子命令会在入口给出明确报错

ROOT = Path(__file__).resolve().parent
WORKSPACE_ROOT = ROOT / "workspace"
SHARED_DIR = ROOT / "shared"
HY_DIR = ROOT / ".hy"
SESSION_DIR = HY_DIR / "session"
SESSION_BINDINGS_DIR = SESSION_DIR / "bindings"
SESSION_ID_ENV_VARS = ("HY_SESSION_ID", "CODEX_THREAD_ID")
SESSION_ID_MAX_LENGTH = 512
SESSION_BINDING_SCHEMA = 3
SESSION_HASH_NAMESPACE = b"happlylong.session.v1\0"
UNBOUND_SESSION_POLICY = "ask_first_bind_or_create"
UNBOUND_SESSION_ACTIONS = ("bind_existing", "create_new")
EXPLICIT_NEW_ITERATION_SIGNAL = "hy-req --title"
SESSION_WORKSPACE_ROOT = "workspace"
SESSION_REQUIRED_ACTIVE_FIELDS = ("project", "iteration_id", "iteration_path")
SESSION_ID_OVERRIDE: str | None = None


def template_root() -> Path:
    """模板按当前指令语言加载：.hy/i18n/{lang}/templates/。"""
    return I18N_DIR / resolve_language() / "templates"
WORKSPACE_INDEX = WORKSPACE_ROOT / "_index.yaml"
I18N_DIR = HY_DIR / "i18n"
PREFS_FILE = SESSION_DIR / "prefs.yaml"
LANGUAGES = ("zh", "en")

ITER_TYPES = ("feat", "fix", "refactor", "doc", "chore")
REPO_ROLES = ("frontend", "backend", "service", "fullstack", "lib")
STAGES = ("prd", "dev", "smoke")  # contract 为 _index.yaml 独立字段（/hy-req 内闭合）
PROTOTYPE_STATUSES = ("planned", "draft", "ready")

ITER_ID_PATTERN = re.compile(r"^(\d{6})-(feat|fix|refactor|doc|chore)-([a-z0-9]+(?:-[a-z0-9]+)*)")
ITER_ID_FORMAT_HINT = "YYMMDD-{feat|fix|refactor|doc|chore}-slug"
REPO_NAME_PATTERN = re.compile(r"^[A-Za-z][A-Za-z0-9_-]*")
PROJECT_NAME_PATTERN = re.compile(r"[A-Za-z][A-Za-z0-9_-]{0,63}")

SLUG_STOPWORDS = {
    "the", "a", "an", "of", "for", "to", "and", "or", "in", "on", "with",
    "add", "new", "update", "support", "page", "feature",
}


class HyError(RuntimeError):
    """happlylong 工具统一业务异常，携带用户可读的处理建议。"""


class MissingSessionIdentityError(HyError):
    """当前进程没有可证明稳定的 Agent 会话身份。"""



# ---------------------------------------------------------------- CLI 文案 i18n
# 中文模板为键、英文为值；{} 为位置占位符，顺序与调用点一致。未收录的模板回退中文。

UI_EN: dict[str, str] = {
    "拒绝不安全的框架路径: {}": "unsafe framework path rejected: {}",
    "配置必须是 YAML 对象: {}": "configuration must be a YAML object: {}",
    "配置字段无效: {} ({})": "invalid configuration field: {} ({})",
    "操作失败，恢复记录见 {}: {}": "operation failed; recovery snapshot: {}: {}",
    "回滚失败，必须从快照恢复 {}: {}": "rollback failed; restore from snapshot {}: {}",
    "文件操作失败: {}": "file operation failed: {}",
    "发布资源无效或未纳入发布清单: {}": "release resource invalid or absent from publish inventory: {}",
    "YAML 不允许循环引用": "cyclic YAML aliases are not allowed",
    "\n[1] 骨架": "\n[1] Skeleton",
    "\n[2] 项目与软链": "\n[2] Projects & symlinks",
    "\n[3] 会话": "\n[3] Session",
    "\n[4] 共享规范": "\n[4] Shared standards",
    "\n[5] 知识库（覆盖情况，缺项仅提醒不计入问题）": "\n[5] Knowledge base (coverage; missing items are hints, not failures)",
    "\n[6] 产品原型": "\n[6] Product prototypes",
    "\n项目:": "\nProjects:",
    "\n会话:": "\nSession:",
    "\n最近迭代:": "\nRecent iterations:",
    "发布层自检（隐私 + 双语源 + 版本 + GitHub 配置）": "publish-layer self-check (privacy, bilingual sources, versions, and GitHub configuration)",
    "共 {} 项发布层问题": "{} publish-layer problem(s)",
    "发布层自检通过（{} 个文件）": "publish-layer self-check passed ({} files)",
    "发布层禁止软链: {}": "symlinks are forbidden in the publish layer: {}",
    "检测到真实项目名: {}": "private project name found in publish-layer file: {}",
    "本机路径泄露: {}": "machine-specific path found: {}",
    "疑似凭据/个人邮箱: {}": "possible credential or personal email found: {}",
    "仓库所有者占位符未替换: {}": "repository-owner placeholder has not been replaced: {}",
    "占位符残留: {}": "unfinished placeholder found: {}",
    "{} Skill 清单不完整: missing={} extra={}": "{} skill inventory mismatch: missing={} extra={}",
    "缺少语言源: {}": "missing language source: {}",
    "frontmatter 文件数量错误: {}（应为 {}）": "wrong frontmatter file count: {} (expected {})",
    "指令源结构校验失败: {}": "instruction-source structure validation failed: {}",
    "双语模板不一致: zh={} en={}": "bilingual template inventory mismatch: zh={} en={}",
    "双语 README 标题层级结构不一致": "bilingual README heading structures do not match",
    ".hy/config.yaml version 不是 SemVer X.Y.Z": ".hy/config.yaml version is not SemVer X.Y.Z",
    "版本不一致: {} != {}": "version mismatch: {} != {}",
    "CHANGELOG.md 缺少版本段: {}": "CHANGELOG.md is missing version section: {}",
    "Issue 模板 frontmatter 无效: {}": "invalid issue-template frontmatter: {}",
    "Dependabot 配置缺少生态: {}": "Dependabot configuration is missing ecosystem(s): {}",
    "Dependabot 配置无效: {}": "invalid Dependabot configuration: {}",
    "requirements.txt 存在未固定版本的依赖: {}": "requirements.txt contains an unpinned dependency: {}",
    "GitHub Action 未固定完整 commit SHA: {} {}@{}": "GitHub Action is not pinned to a full commit SHA: {} {}@{}",
    "Markdown 本地链接不存在: {} -> {}": "broken local Markdown link: {} -> {}",
    "  （无活跃迭代）": "  (no active iteration)",
    "  （未登记仓库）": "  (no repos registered)",
    "  知识库未初始化（/hy-knowledge bootstrap 或 knowledge init）": "  knowledge base not initialized (/hy-knowledge bootstrap or knowledge init)",
    "当前会话已绑定 {} / {}，不能只用 --project 切到 {}；请先 session set，或同时指定 --iteration-id": "the current session is bound to {} / {}; --project alone cannot switch to {}; run session set first, or also pass --iteration-id",
    "初始化/自检框架骨架（幂等）": "initialize/self-check the framework skeleton (idempotent)",
    "（未登记仓库）": "(no repos registered)",
    "profile.yaml 含非法仓库名: {}（字母开头，仅 A-Za-z0-9_-；请修正 profile 后重试）": "invalid repo name in profile.yaml: {} (letter first, A-Za-z0-9_- only; fix the profile and retry)",
    "{}/{}: 链接状态 {}（target={}）": "{}/{}: link status {} (target={})",
    "happlylong 个人多项目产研工作台": "happlylong personal multi-project product-dev workbench",
    "happlylong 骨架自检完成": "happlylong skeleton self-check complete",
    "目录结构完整，无需修复": "directory structure intact, nothing to fix",
    "创建 {}": "created {}",
    "语言包: {}（.agents/skills + AGENTS.md）": "language pack: {} (.agents/skills + AGENTS.md)",
    "语言包: {}（.agents/skills + AGENTS.md，源 .hy/i18n/{}/）": "language pack: {} (.agents/skills + AGENTS.md; source: .hy/i18n/{}/)",
    "pyyaml 未安装（yaml 相关命令不可用）": "pyyaml not installed (yaml-dependent commands unavailable)",
    "缺少依赖 pyyaml，请先执行: pip3 install pyyaml": "missing dependency pyyaml; run: pip3 install pyyaml",
    "未检测到 pyyaml，yaml 相关子命令不可用: pip3 install pyyaml": "pyyaml not detected; yaml-dependent subcommands unavailable: pip3 install pyyaml",
    "YAML 解析失败 {}: {}": "YAML parse error {}: {}",
    "JSON 解析失败 {}: {}": "JSON parse error {}: {}",
    "缺少目录 {}": "missing directory {}",
    "缺少模板 {}": "missing template {}",
    "缺少共享规范 shared/{}": "missing shared standard shared/{}",
    "安装指令语言包 zh|en（默认按 config: auto=系统 locale 探测）": "install command language zh|en (default per config: auto=detect system locale)",
    "语言仅支持 {}": "supported languages: {}",
    "语言包不完整（缺 AGENTS.md 或 skills/）: {}": "language pack incomplete (missing AGENTS.md or skills/): {}",
    "当前语言: {} ｜ 已安装: {} ｜ 偏好: {}": "current language: {} | installed: {} | prefs: {}",
    "切换: python3 happlylong.py lang zh|en": "switch: python3 happlylong.py lang zh|en",
    "指令语言已切换为 {}（.agents/skills + AGENTS.md 已重写）": "command language switched to {} (.agents/skills + AGENTS.md rewritten)",
    "源文件在 .hy/i18n/{}/，修改请改源后重跑本命令同步": "sources live in .hy/i18n/{}/ — edit the source, then rerun this command to sync",
    "省略则查看当前状态": "omit to show current status",
    "查看/切换指令语言（zh|en）": "show/switch the command language (zh|en)",
    ".agents/skills 本身是软链，拒绝整组重写（防误删链接目标），请人工排查: {}": ".agents/skills is itself a symlink; refusing group rewrite (protecting the link target), inspect manually: {}",
    "创建 workspace/{name} 项目": "create workspace/{name} project",
    "项目管理": "project management",
    "项目目录已存在: workspace/{}": "project directory already exists: workspace/{}",
    "项目已创建: workspace/{}": "project created: workspace/{}",
    "结构: profile.yaml / code_lib/ / iterations/ / prototype/": "layout: profile.yaml / code_lib/ / iterations/ / prototype/",
    "产品原型管理": "product prototype management",
    "初始化项目产品原型目录（幂等，不覆盖已有文件）": "initialize the project prototype directory (idempotent; preserve existing files)",
    "查看原型路径、入口与状态": "show the prototype path, entry, and status",
    "查看可直接打开的本地 HTML 原型入口": "show the directly openable local HTML prototype entry",
    "用默认浏览器打开本地 HTML（不启动服务）": "open the local HTML in the default browser (no server)",
    "原型入口必须是原型目录内的 .html 或 .htm 文件: {}": "prototype entry must be an .html or .htm file inside the prototype directory: {}",
    "原型入口尚未创建，无法预览: {}": "prototype entry has not been created and cannot be previewed: {}",
    "浏览器未接受打开请求，请手动打开: {}": "the browser did not accept the open request; open manually: {}",
    "调用浏览器失败: {}；请手动打开: {}": "could not launch a browser: {}; open manually: {}",
    "原型骨架已就绪: workspace/{}/prototype/（新增 {} 个文件）": "prototype scaffold ready: workspace/{}/prototype/ ({} files added)",
    "原型骨架缺失: {}；运行 prototype init {}": "prototype scaffold missing: {}; run prototype init {}",
    "{}: 原型目录尚未初始化（旧项目可选）；运行 prototype init {} 按需启用": "{}: prototype directory not initialized (optional for existing projects); run prototype init {} when needed",
    "原型入口文件缺失: {}（draft/ready 必须有入口文件）": "prototype entry file missing: {} (draft/ready require an entry file)",
    "原型状态不改变迭代 prd/dev/smoke 状态": "prototype status does not change iteration prd/dev/smoke stages",
    "结构: _index.yaml + 每仓一目录（overview/api/data/changelog 按需）": "layout: _index.yaml + one dir per repo (overview/api/data/changelog as needed)",
    "非法项目名: {}（字母开头，仅 A-Za-z0-9_-，长度 ≤64，禁止路径分隔符与 ..）": "invalid project name: {} (letter first, A-Za-z0-9_- only, ≤64 chars; path separators and .. forbidden)",
    "项目不存在: workspace/{}。已注册: {}": "project not found: workspace/{}. registered: {}",
    "缺少项目档案: workspace/{}/profile.yaml，请先 happlylong.py project new {}": "missing project profile: workspace/{}/profile.yaml; run happlylong.py project new {} first",
    "{}: 缺 profile.yaml": "{}: missing profile.yaml",
    "workspace/_index.yaml 缺少项目 {}，请先 project new": "workspace/_index.yaml lacks project {}; run project new first",
    "{}: 未注册进 workspace/_index.yaml": "{}: not registered in workspace/_index.yaml",
    "{}: 已补注册 _index": "{}: registered into _index",
    "{}: _index.repos 已同步": "{}: _index.repos in sync",
    "{}: _index.repos 与 profile 不一致": "{}: _index.repos out of sync with profile",
    "代码库软链管理": "codebase symlink management",
    "登记仓库并建软链": "register a repo and create its symlink",
    "仓库名（code_lib 下的软链名）": "repo name (symlink name under code_lib)",
    "目标仓库绝对路径": "absolute path to the target repo",
    "标记为跨项目共享仓": "mark as a cross-project shared repo",
    "显式声明代码类型（可多次），如 --lang go；未给则自动探测": "declare code language explicitly (repeatable), e.g. --lang go; auto-detected when omitted",
    "一句话功能定位（该仓负责前端/后端/服务层什么职责）": "one-line functional description (what this repo owns: frontend/backend/service-layer duty)",
    "backend/service 共享仓子项目（可多次），如 --app example=api/example,internal/biz/example": "backend/service shared-repo subproject (repeatable), e.g. --app example=api/example,internal/biz/example",
    "备注（如预留子模块说明）": "note (e.g. reserved-submodule remarks)",
    "--app 仅用于 backend/service 角色仓库（共享仓子项目）": "--app applies only to backend/service-role repos (shared-repo subprojects)",
    "代码类型: {}": "code languages: {}",
    "功能定位: {}": "functional role: {}",
    "{}/{}: 缺少 desc 功能定位（link add --force --desc 补录，或直接改 profile）": "{}/{}: missing desc (functional role); backfill via link add --force --desc, or edit profile directly",
    "仅登记不建链（目标就绪后 link apply）": "register only, no symlink yet (link apply once the target exists)",
    "覆盖已登记的仓库条目": "overwrite the registered repo entry",
    "非法仓库名: {}（字母开头，允许 A-Za-z0-9_-）": "invalid repo name: {} (letter first, A-Za-z0-9_- allowed)",
    "仓库已登记: {}（重定向请加 --force）": "repo already registered: {} (add --force to redirect)",
    "--app 格式应为 NAME=path1,path2，收到: {}": "--app format should be NAME=path1,path2, got: {}",
    "--app 非法: {}": "invalid --app: {}",
    "目标必须为绝对路径: {}": "target must be an absolute path: {}",
    "目标不存在，自动按 pending 登记: {}": "target missing; registering as pending automatically: {}",
    "code_lib/{} 是实体目录而非软链，拒绝覆盖，请人工处理": "code_lib/{} is a real directory, not a symlink; refusing to overwrite, resolve manually",
    "已登记 repo {} [{}]{}": "registered repo {} [{}]{}",
    "移除软链与登记": "remove a symlink and its registration",
    "仓库未登记: {}": "repo not registered: {}",
    "code_lib/{} 不是软链而是实体目录，拒绝删除，请人工处理": "code_lib/{} is a real directory, not a symlink; refusing to delete, resolve manually",
    "已从 profile 与 _index 移除 {}": "removed {} from profile and _index",
    "补建 pending 软链": "materialize pending symlinks",
    "{}: 目标仍不存在 {}，保持 pending": "{}: target still missing {}, kept pending",
    "补链 {} 个，仍 pending {} 个": "linked {} repos, {} still pending",
    "列出软链健康状态": "list symlink health",
    "仓库未登记于 profile: {}": "repo not registered in profile: {}",
    "{}: 链接状态 {}（target={}）": "{}: link status {} (target={})",
    "全部链接健康": "all links healthy",
    "{} 个仓库链接异常，可运行 doctor 诊断": "{} repo links unhealthy; run doctor to diagnose",
    "迭代管理": "iteration management",
    "创建迭代并绑定会话": "create an iteration and bind the session",
    "需求标题（同时用于生成 slug）": "requirement title (also generates the slug)",
    "覆盖自动 slug": "override the auto slug",
    "覆盖完整迭代 ID": "override the full iteration ID",
    "非法迭代 ID: {}（格式 {}）": "invalid iteration ID: {} (format {})",
    "语言偏好文件格式错误（应为 YAML 对象）: {}": "invalid language prefs format (expected a YAML object): {}",
    "缺少发布文件: {}": "missing release file: {}",
    "缺少 CI 工作流: .github/workflows/": "missing CI workflow: .github/workflows/",
    "迭代已存在: {}（新建请用 --slug 换名；续用须经用户明确选择后 session set）": "iteration already exists: {} (use --slug for a new iteration; reuse requires the user's explicit choice followed by session set)",
    "产物: _index.yaml / prd.md / contract.md / plan.md / smoke.md / implementation/ / attach/": "artifacts: _index.yaml / prd.md / contract.md / plan.md / smoke.md / implementation/ / attach/",
    "迭代已创建并绑定会话: workspace/{}/iterations/{}": "iteration created and session bound: workspace/{}/iterations/{}",
    "下一步: /hy-req 填充需求（空手调用即可续填当前迭代，或 happlylong.py session set 切换其他迭代）": "next: fill the requirement via /hy-req (bare invocation continues this iteration, or happlylong.py session set to switch)",
    "下一步: happlylong.py link add 挂载代码仓库": "next: mount code repos via happlylong.py link add",
    "列出迭代": "list iterations",
    "查看迭代状态": "show iteration status",
    "关闭迭代（smoke=pass 才允许）": "close an iteration (requires smoke=pass)",
    "smoke 阶段为 {}，仅 smoke=pass 可 close（强制请加 --force）": "smoke stage is {}; only smoke=pass can close (add --force to override)",
    "迭代已关闭: workspace/{}/iterations/{}": "iteration closed: workspace/{}/iterations/{}",
    "未指定迭代且会话未绑定，请用 --project/--iteration-id 或先绑定会话": "no iteration specified and session unbound; use --project/--iteration-id or bind a session first",
    "迭代不存在: workspace/{}/iterations/{}": "iteration not found: workspace/{}/iterations/{}",
    "（尚无迭代）": "(no iterations yet)",
    "会话管理": "session management",
    "查看当前会话": "show the current session",
    "绑定会话到已有迭代": "bind the session to an existing iteration",
    "切回上一绑定的迭代": "switch back to the previous binding",
    "清空会话": "clear the session",
    "会话已绑定: {} / {}": "session bound: {} / {}",
    "已切回上一绑定: {} / {}": "switched back to previous binding: {} / {}",
    "无上一绑定可返回（previous 为空）": "no previous binding to return to (previous is empty)",
    "上一绑定的迭代不存在: {}": "previous-bound iteration not found: {}",
    "会话已清空": "session cleared",
    "会话作用域: {} ｜ 绑定文件: {}": "session scope: {} | binding file: {}",
    "无法确定稳定会话 ID。请在 Agent 启动环境设置 HY_SESSION_ID，或在子命令前加 --session-id；为避免并行串线，已拒绝回退 current.yaml": "cannot determine a stable session ID. Set HY_SESSION_ID in the agent launch environment, or add --session-id before the subcommand; refusing to fall back to current.yaml to prevent sessions from being cross-wired",
    "会话 ID 不能为空": "session ID must not be empty",
    "会话 ID 过长（最大 {} 个字符）": "session ID is too long (maximum {} characters)",
    "会话 ID 含控制字符，已拒绝": "session ID contains control characters and was rejected",
    "会话绑定文件身份校验失败: {}": "session binding identity check failed: {}",
    "会话绑定 schema 不受支持: {}（当前要求 {}）": "unsupported session binding schema: {} (current schema: {})",
    "会话绑定文件格式错误（应为 YAML 对象）: {}": "invalid session binding format (expected a YAML object): {}",
    "会话绑定 active 必须是布尔值: {}": "session binding active must be a boolean: {}",
    "会话绑定 {} 必须是 YAML 对象": "session binding {} must be a YAML object",
    "会话绑定 {} 缺少必填字段: {}": "session binding {} is missing required field(s): {}",
    "会话绑定 {} 的迭代 ID 非法: {}": "session binding {} has an invalid iteration ID: {}",
    "会话绑定 {} 的路径不属于指定 workspace 项目: {}（应为 {}）": "session binding {} path does not belong to the selected workspace project: {} (expected {})",
    "未配置稳定会话身份（绑定相关命令将拒绝执行）": "stable session identity is not configured (binding-dependent commands will be rejected)",
    "稳定且唯一的跨 Agent 会话 ID（须放在子命令前；优先于 HY_SESSION_ID）": "stable, unique cross-agent session ID (place before the subcommand; takes precedence over HY_SESSION_ID)",
    "写入会话绑定失败 {}: {}": "failed to write session binding {}: {}",
    "临时会话文件清理失败: {}（{}）": "failed to clean up temporary session file: {} ({})",
    "当前会话未绑定。执行型请求前必须 Ask-First: 选择绑定已有迭代（先 iter list，再 session set）或创建新迭代（/hy-req --title）；禁止自动选择": "the current session is unbound. Before an execution request, Ask-First whether to bind an existing iteration (iter list, then session set) or create a new one (/hy-req --title); never choose automatically",
    "无活跃会话": "no active session",
    "活跃迭代: {} / {}": "active iteration: {} / {}",
    "会话指向不存在的迭代: {} / {}": "session points to a missing iteration: {} / {}",
    "当前会话指向已关闭迭代: happlylong.py session back 返回上一绑定，或 iter list 另选": "session points to a closed iteration; happlylong.py session back returns to the previous binding, or iter list to pick another",
    "框架体检": "framework health check",
    "自动修复可修项": "auto-fix what can be fixed",
    "体检通过，无问题": "health check passed, no problems",
    "共 {} 个问题（加 --fix 自动修复可修项）": "{} problem(s) in total (add --fix to auto-fix)",
    "共 {} 个问题（已尽量自动修复，其余请人工处理）": "{} problem(s) in total (automatic repairs attempted; resolve the remainder manually)",
    "无": "none",
    "（代码有新提交，知识待刷新）": "(new code commits detected; refresh the knowledge base)",
    "项目知识库管理": "project knowledge management",
    "初始化知识库结构与清单": "initialize knowledge structure and registry",
    "重建清单（不动已生成的 md）": "rebuild the registry (generated md untouched)",
    "知识库已存在（重建加 --force，会清空清单但不动已生成的 md）: {}": "knowledge base already exists (add --force to rebuild the registry, md untouched): {}",
    "知识库未初始化: workspace/{}/knowledge/_index.yaml，请先 happlylong.py knowledge init --project {}": "knowledge base not initialized: workspace/{}/knowledge/_index.yaml; run happlylong.py knowledge init --project {} first",
    "知识库已初始化: workspace/{}/knowledge/": "knowledge base initialized: workspace/{}/knowledge/",
    "登记/刷新某仓知识文件条目": "register/refresh knowledge entries for a repo",
    "文件名，可多次（overview.md 等）": "file name, repeatable (overview.md etc.)",
    "source 仅允许 bootstrap | iteration": "source must be bootstrap | iteration",
    "已登记 {}: files={} source={}": "registered {}: files={} source={}",
    "知识库覆盖与新鲜度": "knowledge coverage and freshness",
    "（未登记仓库）": "(no repos registered)",
    "{}/{}: 缺 overview.md（/hy-knowledge bootstrap 注入）": "{}/{}: missing overview.md (inject via /hy-knowledge bootstrap)",
    "{}/{}: 语言探测 {} 与登记 {} 不同（人工确认后可改 profile）": "{}/{}: detected language {} differs from registered {} (edit profile after confirming)",
    "注入内容: /hy-knowledge bootstrap": "to inject: /hy-knowledge bootstrap",
    "总览: 项目/会话/最近迭代": "overview: projects/session/recent iterations",
    "已安装 Skill: {} 个 -> {}": "installed skills: {} -> {}",
    "已中断": "interrupted",
    "（pending，目标就绪后 link apply 补链）": "(pending; run link apply once the target is ready)",
    "frontend/backend/service/fullstack/lib（必须显式声明）": "frontend/backend/service/fullstack/lib (explicit declaration required)",
}


def ui(template: str, *args: Any) -> str:
    """CLI 文案按当前指令语言渲染：英文表命中则翻译，否则回退中文原文。"""
    if resolve_language() == "en":
        template = UI_EN.get(template, template)
    return template.format(*args) if args else template


# ---------------------------------------------------------------- 基础工具

def need_yaml() -> None:
    if yaml is None:
        raise HyError(ui("缺少依赖 pyyaml，请先执行: pip3 install pyyaml"))


def read_yaml_file(path: Path, default: Any = None) -> Any:
    if path.absolute().is_relative_to(ROOT.absolute()):
        checked_path(path)
    if not path.exists():
        return default
    need_yaml()
    try:
        with path.open("r", encoding="utf-8") as fh:
            data = yaml.safe_load(fh)
        validate_yaml_tree(data)
        return default if data is None else data
    except (OSError, UnicodeError, yaml.YAMLError, RecursionError) as exc:
        raise HyError(ui('YAML 解析失败 {}: {}', path, exc)) from exc


def write_yaml_file(path: Path, data: Any) -> None:
    write_yaml_file_atomic(path, data)


def validate_yaml_tree(data: Any) -> None:
    """Reject cycles, while visiting shared acyclic aliases only once."""
    seen: set[int] = set()
    active: set[int] = set()
    def visit(value: Any) -> None:
        if not isinstance(value, (dict, list)):
            return
        identity = id(value)
        if identity in active:
            raise HyError(ui("YAML 不允许循环引用"))
        if identity in seen:
            return
        active.add(identity)
        for child in (value.values() if isinstance(value, dict) else value):
            visit(child)
        active.remove(identity)
        seen.add(identity)
    visit(data)


def yaml_object(data: Any, source: Any) -> dict[str, Any]:
    if not isinstance(data, dict):
        raise HyError(ui("配置必须是 YAML 对象: {}", source))
    return data


def checked_path(path: Path, *, link_leaf: bool = False) -> Path:
    """Framework metadata never follows links; only a code_lib leaf may do so."""
    try:
        parts = path.absolute().relative_to(ROOT.absolute()).parts
        if ".." in parts:
            raise ValueError("parent traversal")
        current = ROOT
        for part in (parts[:-1] if link_leaf else parts):
            current = current / part
            if current.is_symlink() or getattr(current, "is_junction", lambda: False)():
                raise ValueError("linked metadata")
        parent = path.parent if link_leaf else path
        parent.resolve().relative_to(ROOT.resolve())
    except (ValueError, OSError, RuntimeError) as exc:
        raise HyError(ui("拒绝不安全的框架路径: {}", path)) from exc
    return path


@contextmanager
def mutation_transaction(paths: list[Path]):
    """Snapshot before mutation; roll back synchronous failures across links and files.

    This is not a crash-proof multi-file database transaction. The durable snapshot
    also provides manual recovery after a process or machine interruption.
    """
    snapshot = checked_path(HY_DIR / "snapshots" / ("operation-" + uuid.uuid4().hex))
    snapshot.mkdir(parents=True, mode=0o700)
    records: list[dict[str, Any]] = []
    for number, path in enumerate(dict.fromkeys(paths)):
        checked_path(path, link_leaf=True)
        record: dict[str, Any] = {"path": path.relative_to(ROOT).as_posix(), "kind": "missing"}
        if path.is_symlink():
            record.update(kind="symlink", target=os.readlink(path), directory=path.is_dir() or not path.exists())
        elif path.is_dir():
            backup = snapshot / f"{number}.directory"
            shutil.copytree(path, backup, symlinks=True)
            record.update(kind="directory", backup=backup.name)
        elif path.exists():
            if not path.is_file():
                raise HyError(ui("拒绝不安全的框架路径: {}", path))
            backup = snapshot / f"{number}.bin"
            shutil.copyfile(path, backup)
            backup.chmod(0o600)
            record.update(kind="file", backup=backup.name)
        records.append(record)
    write_yaml_file_atomic(snapshot / "manifest.yaml", {"paths": records})
    try:
        yield
    except (OSError, ValueError, HyError, KeyboardInterrupt) as exc:
        errors = []
        for record in reversed(records):
            path = ROOT / record["path"]
            try:
                checked_path(path, link_leaf=True)
                if path.is_symlink():
                    path.unlink()
                if record["kind"] == "missing":
                    if path.is_dir():
                        shutil.rmtree(path)
                    elif path.exists():
                        path.unlink()
                elif record["kind"] == "symlink":
                    if path.exists():
                        raise OSError(f"unexpected non-link at {path}")
                    path.symlink_to(record["target"], target_is_directory=record["directory"])
                elif record["kind"] == "directory":
                    if path.is_dir():
                        shutil.rmtree(path)
                    elif path.exists():
                        path.unlink()
                    shutil.copytree(snapshot / record["backup"], path, symlinks=True)
                else:
                    recovery = path.with_name(f".{path.name}.{uuid.uuid4().hex}.restore")
                    shutil.copyfile(snapshot / record["backup"], recovery)
                    recovery.replace(path)
            except (OSError, HyError) as recovery_error:
                errors.append(str(recovery_error))
        if errors:
            raise HyError(ui("回滚失败，必须从快照恢复 {}: {}", snapshot, "; ".join(errors))) from exc
        if isinstance(exc, KeyboardInterrupt):
            raise KeyboardInterrupt() from exc
        raise HyError(ui("操作失败，恢复记录见 {}: {}", snapshot, exc)) from exc


def write_yaml_file_atomic(path: Path, data: Any) -> None:
    """同目录临时文件落盘后原子替换，避免进程中断留下半份会话绑定。"""
    need_yaml()
    if path.absolute().is_relative_to(ROOT.absolute()):
        checked_path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
    try:
        with temp_path.open("x", encoding="utf-8") as fh:
            yaml.safe_dump(data, fh, allow_unicode=True, sort_keys=False, default_flow_style=False)
            fh.flush()
            os.fsync(fh.fileno())
        temp_path.replace(path)
    except (OSError, UnicodeError, yaml.YAMLError) as exc:
        raise HyError(ui("写入会话绑定失败 {}: {}", path, exc)) from exc
    finally:
        if temp_path.exists():
            try:
                temp_path.unlink()
            except OSError as exc:
                warn(ui("临时会话文件清理失败: {}（{}）", temp_path, exc))


def local_timestamp() -> str:
    return datetime.now().astimezone().strftime("%Y-%m-%dT%H:%M:%S%z")


def validate_session_id(raw_session_id: str) -> str:
    """校验并规范化跨 Agent 会话 ID；原值只参与哈希，绝不落盘。"""
    if any(ord(char) < 32 or ord(char) == 127 for char in raw_session_id):
        raise HyError(ui("会话 ID 含控制字符，已拒绝"))
    normalized = raw_session_id.strip()
    if not normalized:
        raise HyError(ui("会话 ID 不能为空"))
    if len(normalized) > SESSION_ID_MAX_LENGTH:
        raise HyError(ui("会话 ID 过长（最大 {} 个字符）", SESSION_ID_MAX_LENGTH))
    return normalized


def canonical_iteration_path(project: str, iteration_id: str) -> str:
    """Return the only valid publish-independent path for a workspace iteration."""
    return (Path(SESSION_WORKSPACE_ROOT) / project / "iterations" / iteration_id).as_posix()


def validate_session_binding(data: Mapping[str, Any]) -> None:
    """Fail closed when an active/previous binding is not scoped to one workspace project."""
    active = data.get("active", False)
    if not isinstance(active, bool):
        raise HyError(ui("会话绑定 active 必须是布尔值: {}", active))

    records: list[tuple[str, Any]] = []
    if active:
        records.append(("active", data))
    if data.get("previous") is not None:
        records.append(("previous", data["previous"]))

    for label, record in records:
        if not isinstance(record, Mapping):
            raise HyError(ui("会话绑定 {} 必须是 YAML 对象", label))
        missing = [
            field for field in SESSION_REQUIRED_ACTIVE_FIELDS
            if not isinstance(record.get(field), str) or not str(record[field]).strip()
        ]
        if missing:
            raise HyError(ui("会话绑定 {} 缺少必填字段: {}", label, ", ".join(missing)))

        project = str(record["project"])
        iteration_id = str(record["iteration_id"])
        iteration_path = str(record["iteration_path"])
        validate_project_name(project)
        if not ITER_ID_PATTERN.fullmatch(iteration_id):
            raise HyError(ui("会话绑定 {} 的迭代 ID 非法: {}", label, iteration_id))
        expected = canonical_iteration_path(project, iteration_id)
        if iteration_path != expected:
            raise HyError(ui(
                "会话绑定 {} 的路径不属于指定 workspace 项目: {}（应为 {}）",
                label,
                iteration_path,
                expected,
            ))
        checked_path(ROOT / expected)


def resolve_session_scope(environ: Mapping[str, str] | None = None) -> tuple[Path, str, str]:
    """定位当前 Agent 会话的绑定文件；缺少稳定身份时 fail closed。"""
    source_env = os.environ if environ is None else environ
    source = "--session-id"
    raw_session_id = SESSION_ID_OVERRIDE
    if raw_session_id is None:
        for env_name in SESSION_ID_ENV_VARS:
            candidate = source_env.get(env_name)
            if candidate is not None and candidate.strip():
                source = env_name
                raw_session_id = candidate
                break
    if raw_session_id is None:
        raise MissingSessionIdentityError(ui(
            "无法确定稳定会话 ID。请在 Agent 启动环境设置 HY_SESSION_ID，或在子命令前加 --session-id；为避免并行串线，已拒绝回退 current.yaml"
        ))
    normalized = validate_session_id(raw_session_id)
    session_key = hashlib.sha256(SESSION_HASH_NAMESPACE + normalized.encode("utf-8")).hexdigest()
    return SESSION_BINDINGS_DIR / f"{session_key}.yaml", source, session_key


def current_session_path() -> Path:
    return resolve_session_scope()[0]


def read_current_session() -> dict[str, Any]:
    session_path, _source, session_key = resolve_session_scope()
    if not session_path.exists():
        return {}
    data = read_yaml_file(session_path, default=None)
    if not isinstance(data, dict):
        raise HyError(ui("会话绑定文件格式错误（应为 YAML 对象）: {}", session_path))
    stored_schema = data.get("schema")
    if stored_schema != SESSION_BINDING_SCHEMA:
        raise HyError(ui(
            "会话绑定 schema 不受支持: {}（当前要求 {}）",
            stored_schema,
            SESSION_BINDING_SCHEMA,
        ))
    stored_key = data.get("session_key")
    if stored_key != session_key:
        raise HyError(ui("会话绑定文件身份校验失败: {}", session_path))
    validate_session_binding(data)
    return data


def write_current_session(data: dict[str, Any]) -> None:
    session_path, source, session_key = resolve_session_scope()
    payload: dict[str, Any] = {
        "schema": SESSION_BINDING_SCHEMA,
        "session_source": source,
        "session_key": session_key,
    }
    payload.update({
        key: value for key, value in data.items()
        if key not in {"schema", "session_source", "session_key"}
    })
    validate_session_binding(payload)
    write_yaml_file_atomic(session_path, payload)


def session_scope_label() -> tuple[str, str]:
    session_path, source, _session_key = resolve_session_scope()
    return source, session_path.relative_to(ROOT).as_posix()


# ---------------------------------------------------------------- 语言（i18n）

def detect_language() -> str:
    """按系统 locale 探测指令语言；C/POSIX/纯编码等无语言信息的值跳过，全无信息回退英文。"""
    for var in ("LC_ALL", "LC_CTYPE", "LANG", "LANGUAGE"):
        val = (os.environ.get(var) or "").strip()
        if not val:
            continue
        lang = val.lower().split(".")[0].split("@")[0]  # 去编码与修饰符：zh_cn.utf-8 -> zh_cn
        if lang in ("", "c", "posix"):
            continue
        return "zh" if lang.startswith("zh") else "en"
    return "en"


def load_lang_prefs() -> dict[str, Any]:
    """本机语言偏好（gitignored）：首次 init 探测一次并固定，之后 lang 命令维护。"""
    if yaml is None:
        return {}
    prefs = read_yaml_file(PREFS_FILE, default={})
    if not isinstance(prefs, dict):
        raise HyError(ui("语言偏好文件格式错误（应为 YAML 对象）: {}", PREFS_FILE))
    for key in ("language", "installed_language"):
        if key in prefs and prefs[key] not in LANGUAGES:
            raise HyError(ui("配置字段无效: {} ({})", PREFS_FILE, key))
    return prefs


def resolve_language() -> str:
    """渲染文案用语言查询：偏好不可读时降级系统 locale。

    自包含宽容读取、绝不抛错——报错文案本身要经 ui() 依赖本函数，
    若复用 load_lang_prefs 的严格路径会在「格式化 YAML 报错 → 再读偏好」上无限递归。
    """
    lang = ""
    if yaml is not None:
        try:
            with PREFS_FILE.open("r", encoding="utf-8") as fh:
                data = yaml.safe_load(fh)
            if isinstance(data, dict) and isinstance(data.get("language"), str):
                lang = data["language"]
        except (OSError, UnicodeError, yaml.YAMLError, RecursionError):
            lang = ""
    return lang if lang in LANGUAGES else detect_language()


def get_installed_language() -> str:
    return str(load_lang_prefs().get("installed_language") or "")


def save_lang_prefs(language: str, installed: str) -> None:
    write_yaml_file(PREFS_FILE, {"language": language, "installed_language": installed})


def install_language(lang: str) -> None:
    """把 .hy/i18n/{lang} 的 skills/ 与 AGENTS.md 安装为活跃集（整组重写）。"""
    src = I18N_DIR / lang
    if not (src / "AGENTS.md").is_file() or not (src / "skills").is_dir():
        raise HyError(ui('语言包不完整（缺 AGENTS.md 或 skills/）: {}', src.relative_to(ROOT)))
    skills_src = src / "skills"
    skills_dst = ROOT / ".agents" / "skills"
    # Preflight every destination before deleting or rewriting any installed file.
    for path in (skills_dst, ROOT / "AGENTS.md", ROOT / "CLAUDE.md"):
        checked_path(path)
    if skills_dst.is_dir():
        for child in skills_dst.iterdir():
            if child.name.startswith("hy-"):
                checked_path(child)
    if skills_dst.is_symlink():
        raise HyError(ui('.agents/skills 本身是软链，拒绝整组重写（防误删链接目标），请人工排查: {}', skills_dst))
    with mutation_transaction([skills_dst, ROOT / "AGENTS.md", ROOT / "CLAUDE.md"]):
        skills_dst.mkdir(parents=True, exist_ok=True)
        for child in skills_dst.iterdir():
            if child.is_dir() and child.name.startswith("hy-"):
                shutil.rmtree(child)
        for child in sorted(skills_src.iterdir()):
            if child.is_dir() and child.name.startswith("hy-"):
                shutil.copytree(child, skills_dst / child.name)
        shutil.copyfile(src / "AGENTS.md", ROOT / "AGENTS.md")
        (ROOT / "CLAUDE.md").write_text("@AGENTS.md\n", encoding="utf-8")


def info(msg: str) -> None:
    print(f"  [ok] {msg}")


def warn(msg: str) -> None:
    print(f"  [!] {msg}")


def fail(msg: str) -> None:
    print(f"  [x] {msg}", file=sys.stderr)


def title_to_slug(title: str, max_len: int = 24) -> str:
    """标题 → 迭代 ID slug。取英文实词；无英文词时回退时间片（如 t0930）。"""
    tokens: list[str] = []
    for raw in re.split(r"[^A-Za-z0-9]+", title):
        low = raw.lower()
        if low and low not in SLUG_STOPWORDS and not low.isdigit():
            tokens.append(low)
    slug = "-".join(tokens)[:max_len].strip("-")
    if not slug:
        slug = f"t{datetime.now().strftime('%H%M')}"
    return slug


def compose_iter_id(iter_type: str, title: str, slug: str | None = None) -> str:
    date_tag = datetime.now().strftime("%y%m%d")
    return f"{date_tag}-{iter_type}-{slug or title_to_slug(title)}"


def validate_iteration_id(iter_id: str) -> str:
    """迭代 ID 白名单校验：阻断路径穿越（`/`、`\\`、`..`）与绝对路径拼接。"""
    if not isinstance(iter_id, str) or not ITER_ID_PATTERN.fullmatch(iter_id):
        raise HyError(ui("非法迭代 ID: {}（格式 {}）", iter_id, ITER_ID_FORMAT_HINT))
    return iter_id


def validate_project_name(name: str) -> None:
    """项目名白名单校验：字母开头，仅 A-Za-z0-9_-，≤64 字符。

    防路径穿越（`/`、`\\`、`..`、绝对路径拼接替换基底）与保留名（`_` 前缀为
    `_index.yaml` 等框架文件预留）。fullmatch 避免正则 `$` 的尾随换行绕过。
    """
    if not isinstance(name, str) or not PROJECT_NAME_PATTERN.fullmatch(name):
        raise HyError(ui('非法项目名: {}（字母开头，仅 A-Za-z0-9_-，长度 ≤64，禁止路径分隔符与 ..）', name))


def project_dir(project: str) -> Path:
    validate_project_name(project)
    path = checked_path(WORKSPACE_ROOT / project)
    if not path.is_dir():
        known = [p.name for p in WORKSPACE_ROOT.iterdir() if p.is_dir() and not p.name.startswith("_")] \
            if WORKSPACE_ROOT.is_dir() else []
        raise HyError(ui('项目不存在: workspace/{}。已注册: {}', project, ', '.join(known) or '（无）'))
    return path


def profile_path(project: str) -> Path:
    return checked_path(project_dir(project) / "profile.yaml")


def read_profile(project: str) -> dict[str, Any]:
    data = yaml_object(read_yaml_file(profile_path(project), default={}), profile_path(project))
    if not data:
        raise HyError(ui('缺少项目档案: workspace/{}/profile.yaml，请先 happlylong.py project new {}', project, project))
    if data.get("project") != project:
        raise HyError(ui("配置字段无效: {} ({})", profile_path(project), "project"))
    repos = yaml_object(data.setdefault("repos", {}), "profile.repos")
    for name, entry in repos.items():
        if not isinstance(name, str) or not REPO_NAME_PATTERN.fullmatch(name):
            raise HyError(ui('profile.yaml 含非法仓库名: {}（字母开头，仅 A-Za-z0-9_-；请修正 profile 后重试）', name))
        yaml_object(entry, f"repos.{name}")
        target = entry.get("target")
        if not isinstance(target, str) or not target or not Path(target).is_absolute():
            raise HyError(ui("配置字段无效: {} ({})", profile_path(project), f"{name}.target"))
        if entry.get("role") not in REPO_ROLES:
            raise HyError(ui("配置字段无效: {} ({})", profile_path(project), f"{name}.role"))
        for key in ("pending", "shared"):
            if key in entry and not isinstance(entry[key], bool):
                raise HyError(ui("配置字段无效: {} ({})", profile_path(project), f"{name}.{key}"))
        if "langs" in entry and (not isinstance(entry["langs"], list)
                                  or any(not isinstance(v, str) or not v.strip() for v in entry["langs"])):
            raise HyError(ui("配置字段无效: {} ({})", profile_path(project), f"{name}.langs"))
        if "desc" in entry and (not isinstance(entry["desc"], str) or not entry["desc"].strip()):
            raise HyError(ui("配置字段无效: {} ({})", profile_path(project), f"{name}.desc"))
        if "backend_apps" in entry:
            apps = yaml_object(entry["backend_apps"], f"{name}.backend_apps")
            if entry["role"] not in ("backend", "service"):
                raise HyError(ui("--app 仅用于 backend/service 角色仓库（共享仓子项目）"))
            for app, settings in apps.items():
                settings = yaml_object(settings, f"{name}.{app}")
                validate_app_paths(app, settings.get("paths"))
    return data


def read_workspace_registry() -> dict[str, Any]:
    data = yaml_object(read_yaml_file(checked_path(WORKSPACE_INDEX), default={}), WORKSPACE_INDEX)
    for project, entry in yaml_object(data.get("projects", {}), "workspace.projects").items():
        validate_project_name(project)
        yaml_object(entry, project)
        if not isinstance(entry.get("repos", []), list):
            raise HyError(ui("配置字段无效: {} ({})", WORKSPACE_INDEX, f"{project}.repos"))
    return data


def save_workspace_index(data: dict[str, Any]) -> None:
    data["updated"] = datetime.now().strftime("%Y-%m-%d")
    write_yaml_file(WORKSPACE_INDEX, data)


def index_register_project(project: str, title: str) -> None:
    data = read_workspace_registry()
    data.setdefault("schema", 1)
    data.setdefault("defaults", {"min_quality_grade": "C"})
    projects = data.setdefault("projects", {})
    projects[project] = {"title": title, "repos": []}
    save_workspace_index(data)


def index_sync_project(project: str, repos: list[str]) -> None:
    data = read_workspace_registry()
    entry = data.get("projects", {}).get(project)
    if entry is None:
        raise HyError(ui('workspace/_index.yaml 缺少项目 {}，请先 project new', project))
    entry["repos"] = list(repos)
    save_workspace_index(data)


def detect_langs(target: Path) -> list[str]:
    """按仓库清单文件探测语言，仅作登记与体检参考，可被人工覆盖。"""
    langs: list[str] = []
    if (target / "Cargo.toml").exists():
        langs.append("rust")
    if (target / "go.mod").exists():
        langs.append("go")
    pkg = target / "package.json"
    if pkg.exists():
        meta = yaml_object(json_load(pkg), pkg)
        deps = {**yaml_object(meta.get("dependencies", {}), f"{pkg}: dependencies"),
                **yaml_object(meta.get("devDependencies", {}), f"{pkg}: devDependencies")}
        if any(k in deps for k in ("vue", "@dcloudio/uni-app", "@dcloudio/vite-plugin-uni")):
            langs.extend(["typescript", "vue"])
        elif any(k in deps for k in ("react", "next")):
            langs.extend(["typescript", "react"])
        elif (target / "assets").is_dir() and (target / "settings").is_dir():
            langs.extend(["typescript", "cocos"])
        else:
            langs.append("typescript" if (target / "tsconfig.json").exists() else "javascript")
    if not langs and (target / "tsconfig.json").exists():
        langs.append("typescript")
    return list(dict.fromkeys(langs))


def json_load(path: Path) -> Any:
    try:
        with path.open("r", encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, ValueError) as exc:
        raise HyError(ui('JSON 解析失败 {}: {}', path, exc)) from exc


def fill_template(name: str, mapping: dict[str, Any]) -> str:
    tpl_path = template_root() / name
    if not tpl_path.exists():
        raise HyError(ui('缺少模板 {}', tpl_path))
    return Template(tpl_path.read_text(encoding="utf-8")).safe_substitute(mapping)


def yaml_scalar(value: Any) -> str:
    """Use YAML escaping, including NEL/control characters and supplementary Unicode."""
    need_yaml()
    return yaml.safe_dump(str(value), allow_unicode=True, default_style='"', width=1000000).strip()


# ---------------------------------------------------------------- init

def cmd_init(args: argparse.Namespace) -> int:
    """初始化/自检框架骨架，幂等。"""
    created: list[str] = []
    for sub in (
        WORKSPACE_ROOT,
        SHARED_DIR / "standards",
        SESSION_DIR,
        SESSION_BINDINGS_DIR,
        template_root() / "iteration",
        template_root() / "project",
        template_root() / "knowledge",
        template_root() / "prototype",
    ):
        if not sub.exists():
            sub.mkdir(parents=True, exist_ok=True)
            created.append(str(sub.relative_to(ROOT)))

    try:
        session_path = current_session_path()
    except MissingSessionIdentityError:
        session_path = None
        warn(ui("未配置稳定会话身份（绑定相关命令将拒绝执行）"))
    if session_path is not None and not session_path.exists():
        write_current_session({
            "active": False,
            "project": None,
            "iteration_id": None,
            "iteration_path": None,
            "title": None,
            "last_command": "init",
            "last_command_at": local_timestamp(),
        })
        created.append(session_path.relative_to(ROOT).as_posix())

    if not WORKSPACE_INDEX.exists():
        write_yaml_file(WORKSPACE_INDEX, {
            "schema": 1,
            "defaults": {"min_quality_grade": "C"},
            "projects": {},
            "shared_rules": [
                "coding-standards.md",
                "standards/typescript.md",
                "standards/go.md",
                "standards/rust.md",
                "security-rules.md",
                "testing-standards.md",
                "git-workflow.md",
            ],
        })
        created.append("workspace/_index.yaml")

    # 语言包：--lang 显式指定则强制安装；否则按本机偏好（无则 locale 探测一次并固定）
    if getattr(args, "lang", None):
        if args.lang not in LANGUAGES:
            raise HyError(ui('语言仅支持 {}', ' | '.join(LANGUAGES)))
        install_language(args.lang)
        save_lang_prefs(args.lang, args.lang)
        created.append(ui("语言包: {}（.agents/skills + AGENTS.md）", args.lang))
    else:
        desired = resolve_language()
        if desired != get_installed_language():
            install_language(desired)
            save_lang_prefs(desired, desired)
            created.append(ui(
                "语言包: {}（.agents/skills + AGENTS.md，源 .hy/i18n/{}/）",
                desired,
                desired,
            ))

    skills = sorted(p.name for p in (ROOT / ".agents" / "skills").iterdir()
                    if p.is_dir() and p.name.startswith("hy-")) if (ROOT / ".agents" / "skills").is_dir() else []

    print(ui("happlylong 骨架自检完成"))
    if created:
        for item in created:
            info(ui('创建 {}', item))
    else:
        info(ui("目录结构完整，无需修复"))
    info(ui('已安装 Skill: {} 个 -> {}', len(skills), ', '.join(skills) if skills else '（无）'))
    if yaml is None:
        warn(ui("未检测到 pyyaml，yaml 相关子命令不可用: pip3 install pyyaml"))
    return 0


def cmd_lang(args: argparse.Namespace) -> int:
    """查看/切换指令语言（zh|en）。切换会按语言源整组重写活跃集。"""
    desired, installed = resolve_language(), get_installed_language()
    if not args.lang:
        info(ui('当前语言: {} ｜ 已安装: {} ｜ 偏好: {}', desired, installed or '（未安装）', PREFS_FILE.relative_to(ROOT)))
        info(ui('切换: python3 happlylong.py lang zh|en'))
        return 0
    if args.lang not in LANGUAGES:
        raise HyError(ui('语言仅支持 {}', ' | '.join(LANGUAGES)))
    install_language(args.lang)
    save_lang_prefs(args.lang, args.lang)
    info(ui('指令语言已切换为 {}（.agents/skills + AGENTS.md 已重写）', args.lang))
    warn(ui('源文件在 .hy/i18n/{}/，修改请改源后重跑本命令同步', args.lang))
    return 0

def cmd_project_new(args: argparse.Namespace) -> int:
    validate_project_name(args.name)
    pdir = checked_path(WORKSPACE_ROOT / args.name)
    if pdir.exists():
        raise HyError(ui('项目目录已存在: workspace/{}', args.name))
    read_workspace_registry()
    profile = fill_template("project/profile.yaml.tpl", {
        "project": yaml_scalar(args.name),
        "title": yaml_scalar(args.title or args.name),
        "description": yaml_scalar(args.description or ""),
        "created": local_timestamp(),
    })
    with mutation_transaction([pdir, WORKSPACE_INDEX]):
        (pdir / "code_lib").mkdir(parents=True)
        (pdir / "iterations").mkdir()
        (pdir / "profile.yaml").write_text(profile, encoding="utf-8")
        index_register_project(args.name, args.title or args.name)
        ensure_prototype_scaffold(args.name, args.title or args.name)
    print(ui('项目已创建: workspace/{}', args.name))
    info(ui("结构: profile.yaml / code_lib/ / iterations/ / prototype/"))
    info(ui("下一步: happlylong.py link add 挂载代码仓库"))
    return 0


# ---------------------------------------------------------------- prototype

def prototype_dir(project: str) -> Path:
    """Project-wide prototypes live outside iteration truth and production repos."""
    return checked_path(project_dir(project) / "prototype")


def prototype_entry_path(project: str, entry: Any) -> Path:
    if not isinstance(entry, str) or not entry or "\\" in entry or ":" in entry \
            or any(ord(char) < 32 or ord(char) == 127 for char in entry) \
            or any(part in ("", ".", "..") for part in entry.split("/")):
        raise HyError(ui("配置字段无效: {} ({})", prototype_dir(project) / "_index.yaml", "entry"))
    if Path(entry).suffix.lower() not in (".html", ".htm"):
        raise HyError(ui("原型入口必须是原型目录内的 .html 或 .htm 文件: {}", entry))
    path = checked_path(prototype_dir(project) / entry)
    if path.exists() and not path.is_file():
        raise HyError(ui("配置字段无效: {} ({})", path, "entry must be a file"))
    return path


def read_prototype(project: str) -> dict[str, Any]:
    path = checked_path(prototype_dir(project) / "_index.yaml")
    if not path.is_file():
        raise HyError(ui("原型骨架缺失: {}；运行 prototype init {}", path, project))
    data = yaml_object(read_yaml_file(path), path)
    for key, valid in (
        ("schema", type(data.get("schema")) is int and data["schema"] == 1),
        ("project", data.get("project") == project),
        ("title", isinstance(data.get("title"), str) and bool(data["title"].strip())),
        ("status", data.get("status") in PROTOTYPE_STATUSES),
        ("preview_mode", data.get("preview_mode", "file") == "file"),
    ):
        if not valid:
            raise HyError(ui("配置字段无效: {} ({})", path, key))
    for key in ("created", "updated"):
        if not isinstance(data.get(key), str) or not data[key].strip():
            raise HyError(ui("配置字段无效: {} ({})", path, key))
        timestamp_instant(data[key], source=path, field=key)
    sources = data.get("source_iterations")
    if not isinstance(sources, list):
        raise HyError(ui("配置字段无效: {} ({})", path, "source_iterations"))
    seen = set()
    for source in sources:
        if not isinstance(source, str) or not ITER_ID_PATTERN.fullmatch(source) or source in seen:
            raise HyError(ui("配置字段无效: {} ({})", path, "source_iterations"))
        seen.add(source)
        source_path = iteration_dir(project, source)
        meta = read_iteration_meta(source_path) if source_path.is_dir() else None
        if not meta or meta.get("id") != source or meta.get("project") != project:
            raise HyError(ui("配置字段无效: {} ({})", path, f"source_iterations: {source}"))
    entry = prototype_entry_path(project, data.get("entry"))
    if data["status"] != "planned" and not entry.is_file():
        raise HyError(ui("原型入口文件缺失: {}（draft/ready 必须有入口文件）", entry))
    # Schema 1 manifests created before local previews remain readable without a rewrite.
    data["preview_mode"] = "file"
    return data


def prototype_missing_files(project: str) -> list[Path]:
    directory = prototype_dir(project)
    if directory.exists() and not directory.is_dir():
        raise HyError(ui("配置字段无效: {} ({})", directory, "directory"))
    paths = [checked_path(directory / name) for name in ("_index.yaml", "README.md")]
    for path in paths:
        if path.exists() and not path.is_file():
            raise HyError(ui("配置字段无效: {} ({})", path, "file"))
    if paths[0].exists():
        read_prototype(project)  # A malformed existing manifest is never silently replaced.
    else:
        prototype_entry_path(project, "index.html")
    return [path for path in paths if not path.exists()]


def ensure_prototype_scaffold(project: str, title: str) -> int:
    missing = prototype_missing_files(project)
    mapping = {
        "project": yaml_scalar(project), "title": yaml_scalar(title),
        "project_name": project, "created": yaml_scalar(local_timestamp()),
    }
    contents = {path: fill_template(f"prototype/{path.name}.tpl", mapping) for path in missing}
    if contents:
        directory = prototype_dir(project)
        with mutation_transaction(list(contents) if directory.exists() else [directory]):
            directory.mkdir(parents=True, exist_ok=True)
            for path, content in contents.items():
                with path.open("x", encoding="utf-8") as handle:
                    handle.write(content)
    return len(contents)


def require_registered_prototype_project(project: str) -> dict[str, Any]:
    profile = read_profile(project)
    if project not in read_workspace_registry().get("projects", {}):
        raise HyError(ui("workspace/_index.yaml 缺少项目 {}，请先 project new", project))
    return profile


def cmd_prototype_init(args: argparse.Namespace) -> int:
    profile = require_registered_prototype_project(args.project)
    added = ensure_prototype_scaffold(args.project, profile.get("title") or args.project)
    info(ui("原型骨架已就绪: workspace/{}/prototype/（新增 {} 个文件）", args.project, added))
    info(ui("原型状态不改变迭代 prd/dev/smoke 状态"))
    return 0


def prototype_preview_info(project: str) -> dict[str, Any]:
    require_registered_prototype_project(project)
    data = read_prototype(project)
    entry = prototype_entry_path(project, data["entry"])
    return {
        **data, "path": str(prototype_dir(project)),
        "entry_path": str(entry), "entry_uri": entry.as_uri(), "entry_exists": entry.is_file(),
    }


def cmd_prototype_show(args: argparse.Namespace) -> int:
    print(yaml.safe_dump(prototype_preview_info(args.project), allow_unicode=True, sort_keys=False).rstrip())
    return 0


def cmd_prototype_preview(args: argparse.Namespace) -> int:
    data = prototype_preview_info(args.project)
    if not data["entry_exists"]:
        raise HyError(ui("原型入口尚未创建，无法预览: {}", data["entry_path"]))
    data["open_requested"] = args.open
    # Browser acceptance is not proof that rendering or interactions work.
    data["browser_accepted"] = False
    if args.open:
        try:
            accepted = webbrowser.open(data["entry_uri"], new=2)
        except (webbrowser.Error, OSError) as exc:
            raise HyError(ui("调用浏览器失败: {}；请手动打开: {}", exc, data["entry_uri"])) from exc
        if not accepted:
            raise HyError(ui("浏览器未接受打开请求，请手动打开: {}", data["entry_uri"]))
        data["browser_accepted"] = True
    print(yaml.safe_dump(data, allow_unicode=True, sort_keys=False).rstrip())
    return 0


# ---------------------------------------------------------------- link

def validate_app_paths(name: Any, paths: Any) -> None:
    if not isinstance(name, str) or not REPO_NAME_PATTERN.fullmatch(name) \
            or not isinstance(paths, list) or not paths:
        raise HyError(ui('--app 非法: {}', name))
    for value in paths:
        if not isinstance(value, str) or not value.strip() or value.startswith(("/", "\\")) \
                or ":" in value or ".." in value.replace("\\", "/").split("/"):
            raise HyError(ui('--app 非法: {}', name))


def repo_link_path(project: str, name: str) -> Path:
    if not isinstance(name, str) or not REPO_NAME_PATTERN.fullmatch(name):
        raise HyError(ui('非法仓库名: {}（字母开头，允许 A-Za-z0-9_-）', name))
    return checked_path(project_dir(project) / "code_lib" / name, link_leaf=True)


def prepare_repo_registry(project: str, repos: list[str]) -> dict[str, Any]:
    registry = read_workspace_registry()
    entry = registry.get("projects", {}).get(project)
    if entry is None:
        raise HyError(ui('workspace/_index.yaml 缺少项目 {}，请先 project new', project))
    entry["repos"] = repos
    registry["updated"] = datetime.now().strftime("%Y-%m-%d")
    return registry


def parse_app_spec(specs: list[str] | None) -> dict[str, dict[str, Any]]:
    """解析 --app NAME=path1,path2 表达式为 backend_apps 结构。"""
    apps: dict[str, dict[str, Any]] = {}
    for spec in specs or []:
        if "=" not in spec:
            raise HyError(ui('--app 格式应为 NAME=path1,path2，收到: {}', spec))
        name, _, paths_str = spec.partition("=")
        name = name.strip()
        paths = [p.strip() for p in paths_str.split(",") if p.strip()]
        validate_app_paths(name, paths)
        if name in apps:
            raise HyError(ui('--app 非法: {}', spec))
        apps[name] = {"title": name, "paths": paths}
    return apps


def cmd_link_add(args: argparse.Namespace) -> int:
    profile = read_profile(args.project)
    repos: dict[str, Any] = profile.setdefault("repos", {})
    if args.repo in repos and not args.force:
        raise HyError(ui('仓库已登记: {}（重定向请加 --force）', args.repo))
    if not REPO_NAME_PATTERN.fullmatch(args.repo):
        raise HyError(ui('非法仓库名: {}（字母开头，允许 A-Za-z0-9_-）', args.repo))
    # 所有可失败的校验先于建链副作用，避免校验失败留下未登记的孤儿软链
    apps = parse_app_spec(args.app)
    if apps and args.role not in ("backend", "service"):
        raise HyError(ui("--app 仅用于 backend/service 角色仓库（共享仓子项目）"))
    declared_langs = list(dict.fromkeys(v.strip().lower() for v in args.lang if v.strip()))

    target = Path(args.target).expanduser()
    target = Path(os.path.normpath(target))
    if not target.is_absolute():
        raise HyError(ui('目标必须为绝对路径: {}', target))
    if target.exists() and not target.is_dir():
        raise HyError(ui("配置字段无效: {} ({})", target, "repo directory"))
    pending = args.pending or not target.exists()
    if pending and not args.pending and not target.exists():
        warn(ui('目标不存在，自动按 pending 登记: {}', target))

    link_path = repo_link_path(args.project, args.repo)
    link_dir = link_path.parent
    if link_path.exists() and not link_path.is_symlink():
        raise HyError(ui('code_lib/{} 是实体目录而非软链，拒绝覆盖，请人工处理', args.repo))
    entry: dict[str, Any] = {
        "role": args.role,
        "target": str(target),
    }
    if pending:
        entry["pending"] = True
    if args.shared:
        entry["shared"] = True
    # 代码类型：显式 --lang 优先，未声明且目标就绪时回退自动探测
    entry["langs"] = declared_langs or (detect_langs(target) if target.exists() else [])
    if apps:
        entry["backend_apps"] = apps
    if args.desc:
        entry["desc"] = args.desc
    if args.note:
        entry["note"] = args.note
    repos[args.repo] = entry
    profile["updated"] = local_timestamp()
    registry = prepare_repo_registry(args.project, list(repos))
    with mutation_transaction([link_path, profile_path(args.project), WORKSPACE_INDEX]):
        link_dir.mkdir(parents=True, exist_ok=True)
        if link_path.is_symlink():
            link_path.unlink()
        if not pending:
            link_path.symlink_to(target, target_is_directory=True)
        write_yaml_file(profile_path(args.project), profile)
        write_yaml_file(WORKSPACE_INDEX, registry)
    state = ui("（pending，目标就绪后 link apply 补链）") if pending else ""
    info(ui('已登记 repo {} [{}]{}', args.repo, args.role, state))
    if entry["langs"]:
        info(ui('代码类型: {}', ", ".join(entry["langs"])))
    if args.app:
        info(f"backend_apps: {', '.join(apps)}")
    if args.desc:
        info(ui('功能定位: {}', args.desc))
    return 0


def cmd_link_rm(args: argparse.Namespace) -> int:
    profile = read_profile(args.project)
    repos = profile.get("repos", {})
    if args.repo not in repos:
        raise HyError(ui('仓库未登记: {}', args.repo))
    link_path = repo_link_path(args.project, args.repo)
    if link_path.exists() and not link_path.is_symlink():
        raise HyError(ui('code_lib/{} 不是软链而是实体目录，拒绝删除，请人工处理', args.repo))
    del repos[args.repo]
    profile["updated"] = local_timestamp()
    registry = prepare_repo_registry(args.project, list(repos))
    with mutation_transaction([link_path, profile_path(args.project), WORKSPACE_INDEX]):
        if link_path.is_symlink():
            link_path.unlink()
        write_yaml_file(profile_path(args.project), profile)
        write_yaml_file(WORKSPACE_INDEX, registry)
    info(ui('已从 profile 与 _index 移除 {}', args.repo))
    return 0


def cmd_link_apply(args: argparse.Namespace) -> int:
    profile = read_profile(args.project)
    repos = profile.get("repos", {})
    applied = skipped = 0
    ready: list[tuple[Path, Path]] = []
    for name, entry in repos.items():
        if not entry.get("pending"):
            continue
        target = Path(entry["target"])
        link_path = repo_link_path(args.project, name)
        if not target.exists():
            warn(ui('{}: 目标仍不存在 {}，保持 pending', name, target))
            skipped += 1
            continue
        if not target.is_dir():
            raise HyError(ui("配置字段无效: {} ({})", target, "repo directory"))
        if link_path.is_symlink():
            if link_status(args.project, name, entry) != "ok":
                raise HyError(ui('{}: 链接状态 {}（target={}）', name, "mismatch", target))
        elif link_path.exists():
            raise HyError(ui('code_lib/{} 是实体目录而非软链，拒绝覆盖，请人工处理', name))
        entry.pop("pending", None)
        if not entry.get("langs"):
            entry["langs"] = detect_langs(target)
        ready.append((link_path, target))
        applied += 1
    if ready:
        profile["updated"] = local_timestamp()
        with mutation_transaction([path for path, _ in ready] + [profile_path(args.project)]):
            for path, target in ready:
                path.parent.mkdir(parents=True, exist_ok=True)
                if not path.is_symlink():
                    path.symlink_to(target, target_is_directory=True)
            write_yaml_file(profile_path(args.project), profile)
    print(ui('补链 {} 个，仍 pending {} 个', applied, skipped))
    return 0


def link_status(project: str, name: str, entry: dict[str, Any]) -> str:
    link_path = repo_link_path(project, name)
    if entry.get("pending") and not link_path.is_symlink() and not link_path.exists():
        return "pending"
    if not link_path.is_symlink():
        return "no-link"
    if not link_path.exists():
        return "broken"
    try:
        actual = link_path.resolve()
        expected = Path(str(entry.get("target", ""))).resolve()
    except (OSError, RuntimeError):
        return "mismatch"
    return "ok" if actual == expected else "mismatch"


def cmd_link_list(args: argparse.Namespace) -> int:
    projects = [args.project] if args.project else [
        p.name for p in WORKSPACE_ROOT.iterdir()
        if p.is_dir() and not p.name.startswith("_") and (p / "profile.yaml").exists()
    ]
    total_bad = 0
    for project in sorted(projects):
        profile = read_profile(project)
        repos = profile.get("repos", {})
        print(f"\n[{project}] {profile.get('title', '')}")
        if not repos:
            warn(ui("  （未登记仓库）"))
        for name, entry in repos.items():
            state = link_status(project, name, entry)
            marker = {"ok": "ok", "pending": "pending", "broken": "BROKEN",
                      "no-link": "NO-LINK", "mismatch": "MISMATCH"}[state]
            extra = []
            if entry.get("role"):
                extra.append(entry["role"])
            if entry.get("shared"):
                extra.append("shared")
            if entry.get("backend_apps"):
                extra.append("apps=" + ",".join(entry["backend_apps"]))
            if entry.get("langs"):
                extra.append("langs=" + ",".join(entry["langs"]))
            print(f"  {name:<14} [{marker:<7}] {' '.join(extra)}")
            print(f"  {'':<14} -> {entry.get('target', '?')}")
            if entry.get("desc"):
                print(f"  {'':<14} # {entry['desc']}")
            if state in ("broken", "no-link", "mismatch"):
                total_bad += 1
    print()
    if total_bad:
        warn(ui('{} 个仓库链接异常，可运行 doctor 诊断', total_bad))
    else:
        info(ui("全部链接健康"))
    return 0


# ---------------------------------------------------------------- iter

def iteration_dir(project: str, iteration_id: str) -> Path:
    validate_iteration_id(iteration_id)
    return checked_path(project_dir(project) / "iterations" / iteration_id)


def read_iteration_meta(directory: Path) -> dict[str, Any] | None:
    path = checked_path(directory / "_index.yaml")
    meta = read_yaml_file(path)
    if meta is None:
        return None
    yaml_object(meta, path)
    yaml_object(meta.get("stages", {}), f"{path}: stages")
    if "id" in meta and meta["id"] != directory.name:
        raise HyError(ui("配置字段无效: {} ({})", path, "id"))
    if "project" in meta and meta["project"] != directory.parent.parent.name:
        raise HyError(ui("配置字段无效: {} ({})", path, "project"))
    return meta


def cmd_iter_new(args: argparse.Namespace) -> int:
    # 先验证绑定身份与现有绑定文件，再创建任何迭代产物，避免失败后留下半成品。
    read_current_session()
    iter_id = args.iteration_id or compose_iter_id(args.type, args.title, args.slug)
    validate_iteration_id(iter_id)
    iter_dir = iteration_dir(args.project, iter_id)
    if iter_dir.exists():
        raise HyError(ui('迭代已存在: {}（新建请用 --slug 换名；续用须经用户明确选择后 session set）', iter_dir))

    mapping = {
        "id": iter_id,
        "title": args.title,
        "type": iter_id.split("-", 2)[1],
        "project": args.project,
        "created": local_timestamp(),
    }
    rendered = {"_index.yaml": fill_template("iteration/_index.yaml.tpl", {
        **mapping, "title": yaml_scalar(args.title), "project": yaml_scalar(args.project),
    })}
    for tpl_name, out_name in (
        ("iteration/prd.md.tpl", "prd.md"),
        ("iteration/contract.md.tpl", "contract.md"),
        ("iteration/plan.md.tpl", "plan.md"),
        ("iteration/smoke.md.tpl", "smoke.md"),
    ):
        rendered[out_name] = fill_template(tpl_name, mapping)
    with mutation_transaction([iter_dir, current_session_path()]):
        (iter_dir / "implementation").mkdir(parents=True)
        (iter_dir / "attach").mkdir()
        for name, content in rendered.items():
            (iter_dir / name).write_text(content, encoding="utf-8")
        bind_session(args.project, iter_id, iter_dir, args.title, "iter new")
    print(ui('迭代已创建并绑定会话: workspace/{}/iterations/{}', args.project, iter_id))
    info(ui('产物: _index.yaml / prd.md / contract.md / plan.md / smoke.md / implementation/ / attach/'))
    info(ui("下一步: /hy-req 填充需求（空手调用即可续填当前迭代，或 happlylong.py session set 切换其他迭代）"))
    return 0


def iter_summary(iter_dir: Path) -> dict[str, Any] | None:
    meta = read_iteration_meta(iter_dir)
    if not meta:
        return None
    stages = meta.get("stages", {})
    stage_text = " ".join(f"{k}={v}" for k, v in stages.items())
    return {
        "id": iter_dir.name,
        "project": iter_dir.parent.parent.name,
        "title": meta.get("title", ""),
        "status": meta.get("status", "?"),
        "stages": stage_text,
    }


def cmd_iter_list(args: argparse.Namespace) -> int:
    projects = [args.project] if args.project else [
        p.name for p in (WORKSPACE_ROOT.iterdir() if WORKSPACE_ROOT.is_dir() else [])
        if p.is_dir() and not p.name.startswith("_")
    ]
    found = 0
    for project in sorted(projects):
        it_root = checked_path(project_dir(project) / "iterations")
        if not it_root.is_dir():
            continue
        for iter_dir in sorted(it_root.iterdir(), reverse=True):
            if not iter_dir.is_dir() or not ITER_ID_PATTERN.fullmatch(iter_dir.name):
                continue
            summary = iter_summary(iter_dir)
            if summary is None:
                continue
            found += 1
            print(f"{summary['project']:<10} {summary['id']:<30} [{summary['status']:<7}] {summary['stages']}")
            print(f"{'':<10} {summary['title']}")
    if not found:
        print(ui("（尚无迭代）"))
    return 0


def cmd_iter_show(args: argparse.Namespace) -> int:
    session = {} if args.project and args.iteration_id else read_current_session()
    project, iter_id = resolve_iteration(args, session)
    meta = read_iteration_meta(iteration_dir(project, iter_id))
    if meta is None:
        raise HyError(ui('迭代不存在: workspace/{}/iterations/{}', project, iter_id))
    print(yaml.safe_dump(meta, allow_unicode=True, sort_keys=False))
    return 0


def cmd_iter_close(args: argparse.Namespace) -> int:
    session = {} if args.project and args.iteration_id else read_current_session()
    project, iter_id = resolve_iteration(args, session)
    directory = iteration_dir(project, iter_id)
    meta_path = checked_path(directory / "_index.yaml")
    meta = read_iteration_meta(directory)
    if meta is None:
        raise HyError(ui('迭代不存在: workspace/{}/iterations/{}', project, iter_id))
    smoke = (meta.get("stages") or {}).get("smoke")
    if smoke != "pass" and not args.force:
        raise HyError(ui('smoke 阶段为 {}，仅 smoke=pass 可 close（强制请加 --force）', smoke))
    meta["status"] = "done"
    meta["updated"] = local_timestamp()
    write_yaml_file(meta_path, meta)
    info(ui('迭代已关闭: workspace/{}/iterations/{}', project, iter_id))
    if session.get("active") and session.get("project") == project and session.get("iteration_id") == iter_id:
        info(ui("当前会话指向已关闭迭代: happlylong.py session back 返回上一绑定，或 iter list 另选"))
    return 0


# ---------------------------------------------------------------- session

def resolve_iteration(args: argparse.Namespace, session: dict[str, Any]) -> tuple[str, str]:
    """迭代解析顺序：显式 project+id > 当前代理会话绑定；禁止跨会话猜测。"""
    explicit_project = getattr(args, "project", None)
    explicit_iter_id = getattr(args, "iteration_id", None)
    if explicit_iter_id:
        validate_iteration_id(explicit_iter_id)
        project = explicit_project or session.get("project")
        if not project:
            raise HyError(ui("未指定迭代且会话未绑定，请用 --project/--iteration-id 或先绑定会话"))
        return project, explicit_iter_id

    if not session.get("active") or not session.get("project") or not session.get("iteration_id"):
        raise HyError(ui("未指定迭代且会话未绑定，请用 --project/--iteration-id 或先绑定会话"))

    bound_project = str(session["project"])
    bound_iter_id = str(session["iteration_id"])
    if explicit_project and explicit_project != bound_project:
        raise HyError(ui(
            "当前会话已绑定 {} / {}，不能只用 --project 切到 {}；请先 session set，或同时指定 --iteration-id",
            bound_project,
            bound_iter_id,
            explicit_project,
        ))
    return bound_project, bound_iter_id


def bind_session(project: str, iter_id: str, iter_dir: Path, title: str, command: str) -> None:
    """写入会话绑定；覆盖在途绑定时把它存入 previous，供 session back 切回。"""
    current = read_current_session()
    data: dict[str, Any] = {
        "active": True,
        "project": project,
        "iteration_id": iter_id,
        "iteration_path": iter_dir.relative_to(ROOT).as_posix(),
        "title": title,
        "last_command": command,
        "last_command_at": local_timestamp(),
    }
    current_binding = (current.get("project"), current.get("iteration_id"))
    next_binding = (project, iter_id)
    if current.get("active") and all(current_binding) and current_binding != next_binding:
        data["previous"] = {
            "project": current.get("project"),
            "iteration_id": current.get("iteration_id"),
            "iteration_path": current.get("iteration_path"),
            "title": current.get("title") or "",
        }
    elif current_binding == next_binding and current.get("previous"):
        data["previous"] = current["previous"]
    write_current_session(data)


def cmd_session_show(_args: argparse.Namespace) -> int:
    need_yaml()
    data = read_current_session()
    source, session_file = session_scope_label()
    result = dict(data)
    result["session_scope"] = {
        "source": source,
        "binding_file": session_file,
        "fingerprint": Path(session_file).stem[:8],
    }
    if not data.get("active"):
        result["active"] = False
        result["entry_gate"] = {
            "policy": UNBOUND_SESSION_POLICY,
            "actions": list(UNBOUND_SESSION_ACTIONS),
            "explicit_new_iteration_signal": EXPLICIT_NEW_ITERATION_SIGNAL,
            "workspace_root": SESSION_WORKSPACE_ROOT,
            "required_binding_fields": list(SESSION_REQUIRED_ACTIVE_FIELDS),
        }
        result["message"] = ui(
            "当前会话未绑定。执行型请求前必须 Ask-First: 选择绑定已有迭代（先 iter list，再 session set）或创建新迭代（/hy-req --title）；禁止自动选择"
        )
    print(yaml.safe_dump(result, allow_unicode=True, sort_keys=False))
    return 0


def cmd_session_set(args: argparse.Namespace) -> int:
    validate_iteration_id(args.iteration_id)
    iter_dir = iteration_dir(args.project, args.iteration_id)
    meta = read_iteration_meta(iter_dir)
    if meta is None:
        raise HyError(ui('迭代不存在: workspace/{}/iterations/{}', args.project, args.iteration_id))
    bind_session(args.project, args.iteration_id, iter_dir, meta.get("title", ""), "session set")
    info(ui('会话已绑定: {} / {}', args.project, args.iteration_id))
    return 0


def cmd_session_back(_args: argparse.Namespace) -> int:
    current = read_current_session()
    prev = current.get("previous") or {}
    if not prev.get("project") or not prev.get("iteration_id"):
        raise HyError(ui("无上一绑定可返回（previous 为空）"))
    iter_dir = iteration_dir(prev["project"], prev["iteration_id"])
    if read_iteration_meta(iter_dir) is None:
        raise HyError(ui('上一绑定的迭代不存在: {}', iter_dir))
    bind_session(prev["project"], prev["iteration_id"], iter_dir, prev.get("title") or "", "session back")
    info(ui('已切回上一绑定: {} / {}', prev['project'], prev['iteration_id']))
    return 0


def cmd_session_clear(args: argparse.Namespace) -> int:
    write_current_session({
        "active": False, "project": None, "iteration_id": None,
        "iteration_path": None, "title": None,
        "last_command": "session clear", "last_command_at": local_timestamp(),
    })
    info(ui("会话已清空"))
    return 0


# ---------------------------------------------------------------- knowledge

def knowledge_dir(project: str) -> Path:
    return checked_path(project_dir(project) / "knowledge")


def knowledge_index(project: str, *, allow_missing: bool = False) -> dict[str, Any]:
    path = checked_path(knowledge_dir(project) / "_index.yaml")
    data = read_yaml_file(path)
    if data is None:
        if allow_missing:
            return {}
        raise HyError(ui('知识库未初始化: workspace/{}/knowledge/_index.yaml，请先 happlylong.py knowledge init --project {}', project, project))
    data = yaml_object(data, path)
    if "project" in data and data["project"] != project:
        raise HyError(ui("配置字段无效: {} ({})", path, "project"))
    for name, entry in yaml_object(data.setdefault("repos", {}), path).items():
        if not isinstance(name, str) or not REPO_NAME_PATTERN.fullmatch(name):
            raise HyError(ui("配置字段无效: {} ({})", path, "repo name"))
        yaml_object(entry, path)
        files = entry.setdefault("files", [])
        if not isinstance(files, list) or any(not isinstance(value, str) for value in files):
            raise HyError(ui("配置字段无效: {} ({})", path, "files"))
    return data


def repo_last_commit(target: Path) -> str | None:
    """仓库最后一次提交时间（ISO），非 git 仓或失败返回 None。"""
    try:
        proc = subprocess.run(
            ["git", "-C", str(target), "log", "-1", "--format=%cI"],
            capture_output=True, text=True, timeout=15, check=False,
        )
        if proc.returncode == 0 and proc.stdout.strip():
            return proc.stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return None
    return None


def cmd_knowledge_init(args: argparse.Namespace) -> int:
    profile = read_profile(args.project)
    idx_path = checked_path(knowledge_dir(args.project) / "_index.yaml")
    if idx_path.exists() and not args.force:
        raise HyError(ui('知识库已存在（重建加 --force，会清空清单但不动已生成的 md）: {}', idx_path))
    kdir = knowledge_dir(args.project)
    kdir.mkdir(parents=True, exist_ok=True)
    for repo in profile.get("repos", {}):
        if not REPO_NAME_PATTERN.fullmatch(repo):
            raise HyError(ui('profile.yaml 含非法仓库名: {}（字母开头，仅 A-Za-z0-9_-；请修正 profile 后重试）', repo))
        checked_path(kdir / repo).mkdir(exist_ok=True)
    write_yaml_file(idx_path, {
        "schema": 1,
        "project": args.project,
        "updated": local_timestamp(),
        "repos": {name: {"files": [], "updated": None, "source": None}
                  for name in profile.get("repos", {})},
    })
    print(ui('知识库已初始化: workspace/{}/knowledge/', args.project))
    info(ui('结构: _index.yaml + 每仓一目录（overview/api/data/changelog 按需）'))
    info(ui("注入内容: /hy-knowledge bootstrap"))
    return 0


def cmd_knowledge_register(args: argparse.Namespace) -> int:
    profile = read_profile(args.project)
    repos = profile.get("repos", {})
    if args.repo not in repos:
        raise HyError(ui('仓库未登记于 profile: {}', args.repo))
    if args.source not in ("bootstrap", "iteration"):
        raise HyError(ui("source 仅允许 bootstrap | iteration"))
    idx = knowledge_index(args.project)
    entry = idx.setdefault("repos", {}).setdefault(args.repo, {"files": [], "updated": None, "source": None})
    for name in args.file:
        if name not in entry["files"]:
            entry["files"].append(name)
    entry["source"] = args.source
    entry["updated"] = local_timestamp()
    idx["updated"] = local_timestamp()
    write_yaml_file(knowledge_dir(args.project) / "_index.yaml", idx)
    info(ui('已登记 {}: files={} source={}', args.repo, entry['files'], args.source))
    return 0


def cmd_knowledge_status(args: argparse.Namespace) -> int:
    projects = [args.project] if args.project else [
        p.name for p in WORKSPACE_ROOT.iterdir()
        if p.is_dir() and not p.name.startswith("_") and (p / "profile.yaml").exists()
    ]
    for project in sorted(projects):
        profile = read_profile(project)
        print(f"\n[{project}]")
        idx = knowledge_index(project, allow_missing=True)
        entries = idx.get("repos", {})
        if not idx:
            warn(ui("  知识库未初始化（/hy-knowledge bootstrap 或 knowledge init）"))
        for name, meta in profile.get("repos", {}).items():
            entry = entries.get(name) or {}
            files = entry.get("files") or []
            updated = entry.get("updated")
            state = "ok" if files else "missing"
            last = repo_last_commit(Path(meta.get("target", "")))
            stale = ""
            if updated and last and timestamp_instant(last) > timestamp_instant(updated):
                stale = ui("（代码有新提交，知识待刷新）")
                state = "stale"
            print(f"  {name:<14} [{state:<7}] files={files or ui('无')} updated={updated or '-'} {stale}".rstrip())
    print()
    return 0


# ---------------------------------------------------------------- doctor / status

def timestamp_instant(value: Any, *, source: Any = "knowledge", field: str = "timestamp") -> datetime:
    try:
        # Python 3.10 requires a colon in offsets; existing metadata uses %z.
        normalized = re.sub(r"([+-]\d{2})(\d{2})$", r"\1:\2", str(value).replace("Z", "+00:00"))
        return datetime.fromisoformat(normalized).astimezone()
    except (ValueError, OverflowError) as exc:
        raise HyError(ui("配置字段无效: {} ({})", source, field)) from exc


def run_doctor(fix: bool = False) -> tuple[int, list[str]]:
    problems: list[str] = []
    print("== happlylong doctor ==")

    print(ui("\n[1] 骨架"))
    for must in (
        WORKSPACE_ROOT,
        SESSION_DIR,
        SESSION_BINDINGS_DIR,
        template_root() / "iteration",
        ROOT / ".agents" / "skills",
    ):
        if must.is_dir():
            info(f"{must.relative_to(ROOT)}")
        else:
            problems.append(f"缺少目录 {must.relative_to(ROOT)}")
            fail(ui('缺少目录 {}', must.relative_to(ROOT)))
    if yaml is None:
        problems.append("缺少 pyyaml 依赖")
        fail(ui("pyyaml 未安装（yaml 相关命令不可用）"))

    print(ui("\n[2] 项目与软链"))
    projects = [p for p in WORKSPACE_ROOT.iterdir()
                if p.is_dir() and not p.name.startswith("_")] if WORKSPACE_ROOT.is_dir() else []
    index = read_workspace_registry()
    registered = set((index.get("projects") or {}).keys())
    valid_profiles = {}
    for pdir in sorted(projects, key=lambda x: x.name):
        if not (pdir / "profile.yaml").exists():
            problems.append(f"{pdir.name}: 缺 profile.yaml")
            fail(ui('{}: 缺 profile.yaml', pdir.name))
            continue
        try:
            profile = read_profile(pdir.name)
            valid_profiles[pdir.name] = profile
        except HyError as exc:
            problems.append(str(exc))
            fail(str(exc))
            continue
        repos = profile.get("repos", {})
        if pdir.name not in registered:
            problems.append(f"{pdir.name}: 未注册进 workspace/_index.yaml")
            if fix:
                index_register_project(pdir.name, profile.get("title", pdir.name))
                info(ui('{}: 已补注册 _index', pdir.name))
            else:
                fail(ui('{}: 未注册进 workspace/_index.yaml', pdir.name))
        idx_repos = set(((index.get("projects") or {}).get(pdir.name) or {}).get("repos", []) or [])
        if idx_repos != set(repos):
            problems.append(f"{pdir.name}: _index.repos 与 profile 不一致 {sorted(idx_repos)} vs {sorted(repos)}")
            if fix:
                index_sync_project(pdir.name, list(repos))
                info(ui('{}: _index.repos 已同步', pdir.name))
            else:
                fail(ui('{}: _index.repos 与 profile 不一致', pdir.name))
        for name, entry in repos.items():
            try:
                state = link_status(pdir.name, name, entry)
            except HyError as exc:
                problems.append(str(exc))
                fail(str(exc))
                continue
            target = Path(entry.get("target", ""))
            if state == "ok":
                extra = f" apps={','.join(entry.get('backend_apps', {}))}" if entry.get("backend_apps") else ""
                info(f"{pdir.name}/{name} [{entry.get('role')}] -> {target}{extra}")
                try:
                    detected = detect_langs(target)
                except HyError as exc:
                    problems.append(str(exc))
                    fail(str(exc))
                    continue
                if detected and entry.get("langs") and sorted(detected) != sorted(entry.get("langs", [])):
                    warn(ui('{}/{}: 语言探测 {} 与登记 {} 不同（人工确认后可改 profile）', pdir.name, name, detected, entry.get("langs")))
                if not entry.get("desc"):
                    warn(ui('{}/{}: 缺少 desc 功能定位（link add --force --desc 补录，或直接改 profile）', pdir.name, name))
            else:
                problems.append(f"{pdir.name}/{name}: 链接状态 {state}")
                fail(ui('{}/{}: 链接状态 {}（target={}）', pdir.name, name, state, target))

    print(ui("\n[3] 会话"))
    try:
        source, session_file = session_scope_label()
        info(ui("会话作用域: {} ｜ 绑定文件: {}", source, session_file))
        session = read_current_session()
    except HyError as exc:
        session = {}
        problems.append(str(exc))
        fail(str(exc))
    else:
        if session.get("active"):
            p = session.get("project")
            ip = session.get("iteration_path")
            real = ROOT / ip if ip else None
            if not p or not real or not real.is_dir():
                problems.append(f"会话指向不存在的迭代: {p} / {ip}")
                fail(ui('会话指向不存在的迭代: {} / {}', p, ip))
            else:
                info(ui('活跃迭代: {} / {}', p, session.get('iteration_id')))
        else:
            info(ui("无活跃会话"))

    print(ui("\n[4] 共享规范"))
    for rule in (index.get("shared_rules") or [
        "coding-standards.md", "standards/typescript.md", "standards/go.md", "standards/rust.md",
        "security-rules.md", "testing-standards.md", "git-workflow.md",
    ]):
        rule_path = SHARED_DIR / rule
        if rule_path.exists():
            info(rule)
        else:
            problems.append(f"缺少共享规范 {rule}")
            fail(ui('缺少共享规范 shared/{}', rule))

    print(ui("\n[5] 知识库（覆盖情况，缺项仅提醒不计入问题）"))
    for pdir in sorted(projects, key=lambda x: x.name):
        if pdir.name not in valid_profiles:
            continue
        profile = valid_profiles[pdir.name]
        try:
            kidx = knowledge_index(pdir.name, allow_missing=True)
        except HyError as exc:
            problems.append(str(exc))
            fail(str(exc))
            continue
        entries = kidx.get("repos", {}) if kidx else {}
        for name in profile.get("repos", {}):
            files = (entries.get(name) or {}).get("files") or []
            if "overview.md" in files:
                info(f"{pdir.name}/{name}: {', '.join(files)}")
            else:
                warn(ui('{}/{}: 缺 overview.md（/hy-knowledge bootstrap 注入）', pdir.name, name))

    print(ui("\n[6] 产品原型"))
    for project, profile in sorted(valid_profiles.items()):
        try:
            if not prototype_dir(project).exists() and not fix:
                warn(ui("{}: 原型目录尚未初始化（旧项目可选）；运行 prototype init {} 按需启用", project, project))
                continue
            missing = prototype_missing_files(project)
            if missing and fix:
                added = ensure_prototype_scaffold(project, profile.get("title") or project)
                info(ui("原型骨架已就绪: workspace/{}/prototype/（新增 {} 个文件）", project, added))
            elif missing:
                raise HyError(ui("原型骨架缺失: {}；运行 prototype init {}", ", ".join(str(p) for p in missing), project))
            data = read_prototype(project)
            info(f"{project}/prototype [{data['status']}] entry={data['entry']}")
        except HyError as exc:
            problems.append(str(exc))
            fail(str(exc))

    return len(problems), problems


def cmd_doctor(args: argparse.Namespace) -> int:
    count, _ = run_doctor(fix=args.fix)
    print()
    if count:
        message = (
            ui("共 {} 个问题（加 --fix 自动修复可修项）", count)
            if not args.fix
            else ui("共 {} 个问题（已尽量自动修复，其余请人工处理）", count)
        )
        fail(message)
        return 1
    info(ui("体检通过，无问题"))
    return 0


# ---------------------------------------------------------------- release-check

# 占位符扫描的合法提及处（规则定义文件自身包含待扫词，属预期）
PLACEHOLDER_LEGIT = ("opensource.md", "config.yaml", "CONTRIBUTING.md", "AGENTS.md",
                     "hy-spec/SKILL.md", "review.md.tpl", "PULL_REQUEST_TEMPLATE.md")
# 本机路径检测模式运行时拼接，避免扫描器源码自身命中字面量
HOME_PATH_MARK = "/Us" + "ers/"
WIN_HOME_MARK = "C:" + "\\" + "Users" + "\\"
PLACEHOLDER_MARK = "TO" + "DO|\u5f85\u8865\u5145|TB" + "D|FIX" + "ME|XX" + "X"
OWNER_PLACEHOLDER_MARK = "<" + "user>"
EXPECTED_SKILL_NAMES = frozenset({
    "hy-dev", "hy-fix", "hy-guide", "hy-knowledge", "hy-project",
    "hy-req", "hy-review", "hy-roles", "hy-spec", "hy-test",
})
RELEASE_FALLBACK_DIRS = ("shared", "examples", "tests", ".github", ".hy/i18n")
RELEASE_ROOT_FILES = (
    "happlylong.py", "happlylong.bat", "README.md", "README.en.md", "CONTRIBUTING.md",
    "CODE_OF_CONDUCT.md", "SECURITY.md", "CHANGELOG.md", "LICENSE", "requirements.txt",
    ".gitignore", ".gitattributes", ".hy/config.yaml", ".hy/opensource.md",
)
# 凭据扫描模式：ghp_/gho_/ghu_/ghs_/ghr_ 经典 PAT + github_pat_ 细粒度 PAT 前缀
CREDENTIAL_PATTERNS = (
    re.compile(r"\b(?:[A-Za-z0-9]+[_-])*(?:api[_-]?key|password|secret|token)['\"]?\s*[:=]\s*"
               r"(?:['\"][^'\"\n]{8,}['\"]|[A-Za-z0-9_./+@!%-]{8,}(?![A-Za-z0-9_./+@!%-]|\s*\())", re.I),
    re.compile(r"\bgh[pousr]_[A-Za-z0-9]{20,}\b"),
    re.compile(r"\bgithub_pat_[A-Za-z0-9_]{20,}\b"),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    re.compile(r"\bsk-[A-Za-z0-9]{20,}\b"),
    re.compile(r"@[A-Za-z0-9.-]*(?:gmail|qq|163)\.com\b", re.I),
    re.compile("-----BEGIN " + r"(?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
)
REQUIRED_TEMPLATES = (
    "project/profile.yaml.tpl",
    "prototype/_index.yaml.tpl",
    "prototype/README.md.tpl",
    *(f"iteration/{name}.tpl" for name in (
        "_index.yaml", "prd.md", "contract.md", "plan.md", "smoke.md", "fix.md", "review.md")),
    *(f"knowledge/{name}.md.tpl" for name in ("overview", "api", "data", "changelog")),
)


def release_missing_files(root: Path | None = None, inventory: set[Path] | None = None) -> list[str]:
    """必需发布文件与 CI 工作流缺失清单；防止临时副本缺件时自检假阴性。"""
    problems: list[str] = []
    root = ROOT if root is None else root
    required = list(RELEASE_ROOT_FILES) + [
        "tests/test_framework.py", ".github/dependabot.yml", ".github/PULL_REQUEST_TEMPLATE.md",
        ".github/ISSUE_TEMPLATE/config.yml", ".github/ISSUE_TEMPLATE/bug_report.md",
        ".github/ISSUE_TEMPLATE/feature_request.md",
        *(f"shared/{name}.md" for name in ("coding-standards", "testing-standards", "security-rules",
                                           "git-workflow", "standards/typescript", "standards/go", "standards/rust")),
    ]
    for lang in LANGUAGES:
        required += [f".hy/i18n/{lang}/AGENTS.md"]
        required += [f".hy/i18n/{lang}/templates/{name}" for name in REQUIRED_TEMPLATES]
        required += [f".hy/i18n/{lang}/skills/{name}/SKILL.md" for name in sorted(EXPECTED_SKILL_NAMES)]
    for name in required:
        path = root / name
        if not path.is_file() or path.is_symlink():
            problems.append(ui("缺少发布文件: {}", name))
        elif inventory is not None and path not in inventory:
            problems.append(ui("发布资源无效或未纳入发布清单: {}", name))
    workflows = [p for p in (root / ".github/workflows").glob("*")
                 if p.suffix in (".yml", ".yaml") and p.is_file() and not p.is_symlink()
                 and (inventory is None or p in inventory)]
    if not workflows:
        problems.append(ui("缺少 CI 工作流: .github/workflows/"))
    return problems


def validate_workflow(path: Path, commands: list[str] | None = None) -> list[str]:
    """Check workflow structure and immutable references; execution still needs CI."""
    problems = []
    relative = path.relative_to(ROOT)
    try:
        workflow: dict[Any, Any] = yaml_object(read_yaml_file(path), path)
        events = workflow.get("on", workflow.get(True))  # PyYAML's YAML 1.1 boolean key
        event_names = {events} if isinstance(events, str) else set(events or [])
        jobs = yaml_object(workflow.get("jobs"), path)
        if not event_names or not jobs:
            raise HyError("workflow needs triggers and jobs")
        for job in jobs.values():
            yaml_object(job, path)
            if "uses" not in job:
                steps = job.get("steps")
                if not job.get("runs-on") or not isinstance(steps, list) or not steps:
                    raise HyError("job needs runs-on and steps")
                for step in steps:
                    yaml_object(step, path)
                    if not isinstance(step.get("run", step.get("uses")), str):
                        raise HyError("step needs run or uses")
                    if commands is not None and isinstance(step.get("run"), str) \
                            and step.get("if") is not False and job.get("if") is not False:
                        commands.append(step["run"])
        def check_refs(value: Any) -> None:
            if isinstance(value, dict):
                if "uses" in value:
                    ref = value["uses"]
                    if not isinstance(ref, str) or (not ref.startswith("./")
                            and not re.fullmatch(r"[^@\s]+@[0-9a-f]{40}", ref)):
                        problems.append(ui("发布资源无效或未纳入发布清单: {}", f"{relative}: uses"))
                for child in value.values():
                    check_refs(child)
            elif isinstance(value, list):
                for child in value:
                    check_refs(child)
        check_refs(workflow)
    except (HyError, TypeError, ValueError) as exc:
        problems.append(ui("发布资源无效或未纳入发布清单: {}", f"{relative}: {exc}"))
    return problems


def markdown_heading_levels(text: str) -> list[int]:
    """Extract ATX heading levels while ignoring fenced code examples."""
    levels: list[int] = []
    fence: str | None = None
    for line in text.splitlines():
        stripped = line.lstrip()
        marker = stripped[:3]
        if marker in {"```", "~~~"}:
            if fence is None:
                fence = marker
            elif fence == marker:
                fence = None
            continue
        if fence is not None:
            continue
        match = re.match(r"^(#{1,6})\s+", line)
        if match:
            levels.append(len(match.group(1)))
    return levels


def frontmatter_data(path: Path) -> dict[str, Any]:
    """Parse one Markdown YAML frontmatter block and reject missing delimiters/objects."""
    need_yaml()
    lines = path.read_text(encoding="utf-8").splitlines()
    if not lines or lines[0] != "---":
        raise HyError(f"missing opening frontmatter delimiter: {path}")
    try:
        end = lines.index("---", 1)
        data = yaml.safe_load("\n".join(lines[1:end]))
    except (ValueError, yaml.YAMLError) as exc:
        raise HyError(f"invalid frontmatter: {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise HyError(f"frontmatter must be a YAML object: {path}")
    return data


def private_name_patterns(path: Path) -> list[str]:
    """Load literal private names from plain, list-like, or documented mapping lines."""
    if not path.exists():
        return []
    patterns: list[str] = []
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("- "):
            line = line[2:].strip()
        line = re.split(r"\s+#", line, maxsplit=1)[0].strip()
        for separator in ("→", "->"):
            if separator in line:
                line = line.split(separator, 1)[0].strip()
                break
        mapping = re.match(r"^(.+?)\s*:\s+.+$", line)
        if mapping:
            line = mapping.group(1).strip()
        line = line.strip("'\"")
        if line and line not in patterns:
            patterns.append(line)
    return patterns


def publish_layer_files() -> list[Path]:
    """发布层文件清单：优先 git 视角（含未提交的 untracked、排除 ignored），无 git 时按目录枚举。"""
    try:
        proc = subprocess.run(["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"],
                              capture_output=True, timeout=15, check=False, cwd=ROOT)
        if proc.returncode == 0:
            return sorted({ROOT / os.fsdecode(name) for name in proc.stdout.split(b"\0") if name})
        if (ROOT / ".git").exists():
            raise HyError("git publish inventory failed")
    except (OSError, subprocess.SubprocessError) as exc:
        if (ROOT / ".git").exists() and shutil.which("git"):
            raise HyError("git publish inventory unavailable") from exc
    files: list[Path] = []
    for sub in RELEASE_FALLBACK_DIRS:
        base = ROOT / sub
        if base.is_symlink():
            files.append(base)
        elif base.is_dir():
            for directory, directories, names in os.walk(base, followlinks=False):
                parent = Path(directory)
                for name in list(directories):
                    path = parent / name
                    if path.is_symlink():
                        files.append(path)
                    if path.is_symlink() or name in {"__pycache__", ".pytest_cache", ".git"}:
                        directories.remove(name)
                files.extend(parent / name for name in names if not name.endswith((".pyc", ".pyo")))
    for name in RELEASE_ROOT_FILES:
        q = ROOT / name
        if q.is_file() or q.is_symlink():
            files.append(q)
    return sorted(set(files))


def cmd_release_check(_args: argparse.Namespace) -> int:
    """发布层自检：隐私、双语源、版本、社区模板与 CI 供应链约束。"""
    problems: list[str] = []
    publish_entries = publish_layer_files()
    for entry in publish_entries:
        if entry.is_symlink():
            problems.append(ui("发布层禁止软链: {}", entry.relative_to(ROOT)))
    allowed_entries = []
    for entry in publish_entries:
        relative = entry.relative_to(ROOT).as_posix()
        if relative not in RELEASE_ROOT_FILES and not any(relative.startswith(name + "/") for name in RELEASE_FALLBACK_DIRS):
            problems.append(ui("发布资源无效或未纳入发布清单: {}", relative))
            continue
        try:
            checked_path(entry)
        except HyError:
            problems.append(ui("发布资源无效或未纳入发布清单: {}", relative))
            continue
        allowed_entries.append(entry)
    files = [f for f in allowed_entries if f.is_file() and not f.is_symlink()]
    texts = {}
    for file in files:
        try:
            content = file.read_text(encoding="utf-8")
            if "\0" in content:
                raise ValueError("NUL bytes in publish text")
            texts[file] = content
        except (UnicodeError, ValueError):
            problems.append(ui("发布资源无效或未纳入发布清单: {}", f"{file.relative_to(ROOT)}: UTF-8 text required"))

    # 1) 真实项目名（模式源为本机私有文件，跳过空行与注释行）
    names_path = HY_DIR / "private-names.yaml"
    patterns = private_name_patterns(names_path)
    # 2) 本机路径 / 3) 凭据与个人邮箱
    credential_patterns = CREDENTIAL_PATTERNS
    for f, text in texts.items():
        rel = f.relative_to(ROOT).as_posix()
        if any(re.search(re.escape(pattern), text, re.I) for pattern in patterns):
            problems.append(ui("检测到真实项目名: {}", rel))
        if rel == ".hy/opensource.md":
            pass  # 规范文档自身含路径示例与扫描说明，合法提及
        elif HOME_PATH_MARK in text or WIN_HOME_MARK in text:
            problems.append(ui("本机路径泄露: {}", rel))
        if any(pattern.search(text) for pattern in credential_patterns):
            problems.append(ui("疑似凭据/个人邮箱: {}", rel))
        if rel != ".hy/opensource.md" and OWNER_PLACEHOLDER_MARK in text:
            problems.append(ui("仓库所有者占位符未替换: {}", rel))
    # 4) 占位符（排除合法提及处）
    for f, text in texts.items():
        rel = f.relative_to(ROOT).as_posix()
        if any(rel.endswith(leg) for leg in PLACEHOLDER_LEGIT):
            continue
        if re.search(PLACEHOLDER_MARK, text):
            problems.append(ui("占位符残留: {}", rel))
    # 5) frontmatter：双语 skills + AGENTS 源须完整、同名且共 22 份
    fm_targets: list[Path] = []
    for lang in LANGUAGES:
        skill_root = I18N_DIR / lang / "skills"
        actual = {path.parent.name for path in skill_root.glob("*/SKILL.md")}
        if actual != EXPECTED_SKILL_NAMES:
            problems.append(ui(
                "{} Skill 清单不完整: missing={} extra={}",
                lang,
                sorted(EXPECTED_SKILL_NAMES - actual),
                sorted(actual - EXPECTED_SKILL_NAMES),
            ))
        fm_targets.extend(sorted(skill_root.glob("*/SKILL.md")))
        agents_source = I18N_DIR / lang / "AGENTS.md"
        if agents_source.is_file():
            fm_targets.append(agents_source)
        else:
            problems.append(ui("缺少语言源: {}", agents_source.relative_to(ROOT)))
    expected_frontmatter_count = len(LANGUAGES) * (len(EXPECTED_SKILL_NAMES) + 1)
    if len(fm_targets) != expected_frontmatter_count:
        problems.append(ui(
            "frontmatter 文件数量错误: {}（应为 {}）",
            len(fm_targets),
            expected_frontmatter_count,
        ))
    for f in fm_targets:
        try:
            data = frontmatter_data(f)
            if not str(data.get("description") or "").strip():
                raise HyError("description is required")
            if f.name == "SKILL.md":
                if not str(data.get("name") or "").strip():
                    raise HyError("name is required for skills")
                skill_text = f.read_text(encoding="utf-8")
                next_steps = list(re.finditer(r"^## \[Next Steps\]\s*$", skill_text, re.M))
                if len(next_steps) != 1:
                    raise HyError("skills require exactly one [Next Steps] section")
                if re.search(r"^##\s+", skill_text[next_steps[0].end():], re.M):
                    raise HyError("[Next Steps] must be the final level-two section")
                bullet_count = sum(
                    1 for line in skill_text[next_steps[0].end():].splitlines()
                    if line.startswith("- ")
                )
                if not 1 <= bullet_count <= 3:
                    raise HyError("[Next Steps] requires one to three items")
        except HyError:
            problems.append(ui("指令源结构校验失败: {}", f.relative_to(ROOT)))
    # 6) 双语模板结构一致
    zh_t = sorted(q.relative_to(I18N_DIR / "zh" / "templates").as_posix()
                  for q in (I18N_DIR / "zh" / "templates").rglob("*.tpl"))
    en_t = sorted(q.relative_to(I18N_DIR / "en" / "templates").as_posix()
                  for q in (I18N_DIR / "en" / "templates").rglob("*.tpl"))
    if zh_t != en_t:
        problems.append(ui("双语模板不一致: zh={} en={}", zh_t, en_t))

    # 7) README 结构与版本三处同步
    readme_zh = texts.get(ROOT / "README.md", "")
    readme_en = texts.get(ROOT / "README.en.md", "")
    if markdown_heading_levels(readme_zh) != markdown_heading_levels(readme_en):
        problems.append(ui("双语 README 标题层级结构不一致"))
    config = read_yaml_file(HY_DIR / "config.yaml", default={}) or {}
    version = str(config.get("version") or "") if isinstance(config, dict) else ""
    if not re.fullmatch(r"\d+\.\d+\.\d+", version):
        problems.append(ui(".hy/config.yaml version 不是 SemVer X.Y.Z"))
    else:
        for lang in LANGUAGES:
            agents_source = I18N_DIR / lang / "AGENTS.md"
            agents_text = agents_source.read_text(encoding="utf-8") if agents_source.is_file() else ""
            match = re.search(r">\s+\*\*(?:版本|Version)\*\*:\s*(\d+\.\d+\.\d+)", agents_text)
            if not match or match.group(1) != version:
                problems.append(ui("版本不一致: {} != {}", agents_source.relative_to(ROOT), version))
        changelog = texts.get(ROOT / "CHANGELOG.md", "")
        if not re.search(rf"^## \[{re.escape(version)}\](?:\s|$)", changelog, re.M):
            problems.append(ui("CHANGELOG.md 缺少版本段: {}", version))

    # 8) GitHub 社区模板 frontmatter 与 Actions 不可变引用
    for issue_template in sorted((ROOT / ".github" / "ISSUE_TEMPLATE").glob("*.md")):
        try:
            data = frontmatter_data(issue_template)
            if not str(data.get("name") or "").strip() or not str(data.get("about") or "").strip():
                raise HyError("name/about are required")
        except HyError:
            problems.append(ui("Issue 模板 frontmatter 无效: {}", issue_template.relative_to(ROOT)))
    dependabot_path = ROOT / ".github" / "dependabot.yml"
    dependabot = read_yaml_file(dependabot_path, default={}) or {}
    if not isinstance(dependabot, dict) or dependabot.get("version") != 2 \
            or not isinstance(dependabot.get("updates"), list):
        problems.append(ui("Dependabot 配置无效: {}", dependabot_path.relative_to(ROOT)))
    else:
        ecosystems = {
            update.get("package-ecosystem")
            for update in dependabot["updates"]
            if isinstance(update, dict)
        }
        missing_ecosystems = {"github-actions", "pip"} - ecosystems
        if missing_ecosystems:
            problems.append(ui("Dependabot 配置缺少生态: {}", sorted(missing_ecosystems)))
    requirements_path = ROOT / "requirements.txt"
    if requirements_path.is_file():
        dependencies = set()
        for requirement in requirements_path.read_text(encoding="utf-8").splitlines():
            requirement = requirement.strip()
            if requirement and not requirement.startswith("#"):
                dependencies.add(requirement.split("==", 1)[0].lower())
            if requirement and not requirement.startswith("#") \
                    and not re.fullmatch(r"[A-Za-z0-9_.-]+==[^\s;]+", requirement):
                problems.append(ui("requirements.txt 存在未固定版本的依赖: {}", requirement))
        if "pyyaml" not in dependencies:
            problems.append(ui("发布资源无效或未纳入发布清单: {}", "requirements.txt: PyYAML"))
    action_ref = re.compile(r"^\s*-?\s*uses:\s*([^@\s]+)@([^\s#]+)", re.M)
    for workflow in sorted((ROOT / ".github" / "workflows").glob("*.y*ml")):
        workflow_text = workflow.read_text(encoding="utf-8")
        for action, ref in action_ref.findall(workflow_text):
            if not action.startswith("./") and not re.fullmatch(r"[0-9a-f]{40}", ref):
                problems.append(ui(
                    "GitHub Action 未固定完整 commit SHA: {} {}@{}",
                    workflow.relative_to(ROOT),
                    action,
                    ref,
                ))

    # 9) 发布层 Markdown 的本地相对链接必须存在（外部 URL 与页内锚点不联网检查）
    markdown_link = re.compile(r"!?\[[^\]]*\]\(([^)]+)\)")
    for markdown, markdown_text in texts.items():
        if markdown.suffix.lower() != ".md":
            continue
        for raw_target in markdown_link.findall(markdown_text):
            target = raw_target.strip()
            if target.startswith("<") and ">" in target:
                target = target[1:target.index(">")]
            else:
                target = target.split()[0] if target.split() else ""
            if not target or target.startswith(("#", "http://", "https://", "mailto:")):
                continue
            local_target = target.split("#", 1)[0].split("?", 1)[0]
            if local_target and not (markdown.parent / local_target).exists():
                problems.append(ui(
                    "Markdown 本地链接不存在: {} -> {}",
                    markdown.relative_to(ROOT),
                    local_target,
                ))

    # 10) 必需发布文件与 CI 工作流（临时副本缺件必须报错而非通过）
    problems.extend(release_missing_files(ROOT, set(files)))
    workflows = [path for path in files if path.parent == ROOT / ".github/workflows"
                 and path.suffix in (".yml", ".yaml")]
    commands: list[str] = []
    for path in workflows:
        problems.extend(validate_workflow(path, commands))
    ci_text = "\n".join(commands)
    if not re.search(r"^[ \t]*python\S*\s+-m\s+unittest\s+discover", ci_text, re.M) \
            or not re.search(r"^[ \t]*python\S*\s+happlylong\.py\s+release-check", ci_text, re.M):
        problems.append(ui("发布资源无效或未纳入发布清单: {}", ".github/workflows/: unit tests / release-check"))

    if problems:
        for q in problems:
            fail(q)
        fail(ui("共 {} 项发布层问题", len(problems)))
        return 1
    info(ui("发布层自检通过（{} 个文件）", len(files)))
    return 0


def cmd_status(_args: argparse.Namespace) -> int:
    index = read_workspace_registry()
    print("== happlylong status ==")
    print(ui("\n项目:"))
    for name, entry in sorted((index.get("projects") or {}).items()):
        profile = read_profile(name)
        repos = profile.get("repos", {})
        roles = " ".join(f"{n}[{e.get('role')}]" for n, e in repos.items()) or ui("（未登记仓库）")
        print(f"  {name:<10} {entry.get('title', ''):<12} {roles}")
    print(ui("\n会话:"))
    try:
        source, session_file = session_scope_label()
        session = read_current_session()
    except MissingSessionIdentityError:
        print(f"  {ui('未配置稳定会话身份（绑定相关命令将拒绝执行）')}")
    else:
        print(f"  {ui('会话作用域: {} ｜ 绑定文件: {}', source, session_file)}")
        if session.get("active"):
            print(f"  {session.get('project')} / {session.get('iteration_id')} — {session.get('title')}")
        else:
            print(ui("  （无活跃迭代）"))
    print(ui("\n最近迭代:"))
    _ = cmd_iter_list(argparse.Namespace(project=None))
    return 0


# ---------------------------------------------------------------- 入口

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="happlylong", description=ui("happlylong 个人多项目产研工作台"))
    parser.add_argument(
        "--session-id",
        default=None,
        help=ui("稳定且唯一的跨 Agent 会话 ID（须放在子命令前；优先于 HY_SESSION_ID）"),
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_init = sub.add_parser("init", help=ui("初始化/自检框架骨架（幂等）"))
    p_init.add_argument("--lang", default=None, help=ui("安装指令语言包 zh|en（默认按 config: auto=系统 locale 探测）"))
    p_init.set_defaults(func=cmd_init)

    sub.add_parser("release-check", help=ui("发布层自检（隐私 + 双语源 + 版本 + GitHub 配置）")).set_defaults(func=cmd_release_check)

    p_lang = sub.add_parser("lang", help=ui("查看/切换指令语言（zh|en）"))
    p_lang.add_argument("lang", nargs="?", default=None, help=ui("省略则查看当前状态"))
    p_lang.set_defaults(func=cmd_lang)

    p_proj = sub.add_parser("project", help=ui("项目管理"))
    proj_sub = p_proj.add_subparsers(dest="action", required=True)
    p_new = proj_sub.add_parser("new", help=ui("创建 workspace/{name} 项目"))
    p_new.add_argument("name")
    p_new.add_argument("--title", default="")
    p_new.add_argument("--description", default="")
    p_new.set_defaults(func=cmd_project_new)

    p_proto = sub.add_parser("prototype", help=ui("产品原型管理"))
    proto_sub = p_proto.add_subparsers(dest="action", required=True)
    p_pinit = proto_sub.add_parser("init", help=ui("初始化项目产品原型目录（幂等，不覆盖已有文件）"))
    p_pinit.add_argument("project")
    p_pinit.set_defaults(func=cmd_prototype_init)
    p_pshow = proto_sub.add_parser("show", help=ui("查看原型路径、入口与状态"))
    p_pshow.add_argument("project")
    p_pshow.set_defaults(func=cmd_prototype_show)
    p_ppreview = proto_sub.add_parser("preview", help=ui("查看可直接打开的本地 HTML 原型入口"))
    p_ppreview.add_argument("project")
    p_ppreview.add_argument("--open", action="store_true", help=ui("用默认浏览器打开本地 HTML（不启动服务）"))
    p_ppreview.set_defaults(func=cmd_prototype_preview)

    p_link = sub.add_parser("link", help=ui("代码库软链管理"))
    link_sub = p_link.add_subparsers(dest="action", required=True)
    p_add = link_sub.add_parser("add", help=ui("登记仓库并建软链"))
    p_add.add_argument("project")
    p_add.add_argument("repo", help=ui("仓库名（code_lib 下的软链名）"))
    p_add.add_argument("target", help=ui("目标仓库绝对路径"))
    p_add.add_argument("--role", choices=REPO_ROLES, required=True,
                       help=ui("frontend/backend/service/fullstack/lib（必须显式声明）"))
    p_add.add_argument("--lang", action="append", default=[], metavar="LANG",
                       help=ui("显式声明代码类型（可多次），如 --lang go；未给则自动探测"))
    p_add.add_argument("--desc", default="", help=ui("一句话功能定位（该仓负责前端/后端/服务层什么职责）"))
    p_add.add_argument("--shared", action="store_true", help=ui("标记为跨项目共享仓"))
    p_add.add_argument("--app", action="append", default=[], metavar="NAME=PATH,PATH",
                       help=ui("backend/service 共享仓子项目（可多次），如 --app example=api/example,internal/biz/example"))
    p_add.add_argument("--note", default="", help=ui("备注（如预留子模块说明）"))
    p_add.add_argument("--pending", action="store_true", help=ui("仅登记不建链（目标就绪后 link apply）"))
    p_add.add_argument("--force", action="store_true", help=ui("覆盖已登记的仓库条目"))
    p_add.set_defaults(func=cmd_link_add)
    p_rm = link_sub.add_parser("rm", help=ui("移除软链与登记"))
    p_rm.add_argument("project")
    p_rm.add_argument("repo")
    p_rm.set_defaults(func=cmd_link_rm)
    p_apply = link_sub.add_parser("apply", help=ui("补建 pending 软链"))
    p_apply.add_argument("project")
    p_apply.set_defaults(func=cmd_link_apply)
    p_list = link_sub.add_parser("list", help=ui("列出软链健康状态"))
    p_list.add_argument("project", nargs="?", default=None)
    p_list.set_defaults(func=cmd_link_list)

    p_iter = sub.add_parser("iter", help=ui("迭代管理"))
    iter_sub = p_iter.add_subparsers(dest="action", required=True)
    p_inew = iter_sub.add_parser("new", help=ui("创建迭代并绑定会话"))
    p_inew.add_argument("project")
    p_inew.add_argument("--title", required=True, help=ui("需求标题（同时用于生成 slug）"))
    p_inew.add_argument("--type", choices=ITER_TYPES, default="feat")
    p_inew.add_argument("--slug", default=None, help=ui("覆盖自动 slug"))
    p_inew.add_argument("--iteration-id", default=None, help=ui("覆盖完整迭代 ID"))
    p_inew.set_defaults(func=cmd_iter_new)
    p_ilist = iter_sub.add_parser("list", help=ui("列出迭代"))
    p_ilist.add_argument("project", nargs="?", default=None)
    p_ilist.set_defaults(func=cmd_iter_list)
    p_isum = iter_sub.add_parser("show", help=ui("查看迭代状态"))
    p_isum.add_argument("--project", default=None)
    p_isum.add_argument("--iteration-id", dest="iteration_id", default=None)
    p_isum.set_defaults(func=cmd_iter_show)
    p_iclose = iter_sub.add_parser("close", help=ui("关闭迭代（smoke=pass 才允许）"))
    p_iclose.add_argument("--project", default=None)
    p_iclose.add_argument("--iteration-id", dest="iteration_id", default=None)
    p_iclose.add_argument("--force", action="store_true")
    p_iclose.set_defaults(func=cmd_iter_close)

    p_sess = sub.add_parser("session", help=ui("会话管理"))
    sess_sub = p_sess.add_subparsers(dest="action", required=True)
    sess_sub.add_parser("show", help=ui("查看当前会话")).set_defaults(func=cmd_session_show)
    p_sset = sess_sub.add_parser("set", help=ui("绑定会话到已有迭代"))
    p_sset.add_argument("project")
    p_sset.add_argument("iteration_id")
    p_sset.set_defaults(func=cmd_session_set)
    sess_sub.add_parser("back", help=ui("切回上一绑定的迭代")).set_defaults(func=cmd_session_back)
    sess_sub.add_parser("clear", help=ui("清空会话")).set_defaults(func=cmd_session_clear)

    p_doc = sub.add_parser("doctor", help=ui("框架体检"))
    p_doc.add_argument("--fix", action="store_true", help=ui("自动修复可修项"))
    p_doc.set_defaults(func=cmd_doctor)

    p_kn = sub.add_parser("knowledge", help=ui("项目知识库管理"))
    kn_sub = p_kn.add_subparsers(dest="action", required=True)
    p_kinit = kn_sub.add_parser("init", help=ui("初始化知识库结构与清单"))
    p_kinit.add_argument("--project", required=True)
    p_kinit.add_argument("--force", action="store_true", help=ui("重建清单（不动已生成的 md）"))
    p_kinit.set_defaults(func=cmd_knowledge_init)
    p_kreg = kn_sub.add_parser("register", help=ui("登记/刷新某仓知识文件条目"))
    p_kreg.add_argument("--project", required=True)
    p_kreg.add_argument("--repo", required=True)
    p_kreg.add_argument("--source", required=True, choices=["bootstrap", "iteration"])
    p_kreg.add_argument("--file", action="append", default=[], help=ui("文件名，可多次（overview.md 等）"))
    p_kreg.set_defaults(func=cmd_knowledge_register)
    p_kstat = kn_sub.add_parser("status", help=ui("知识库覆盖与新鲜度"))
    p_kstat.add_argument("--project", default=None)
    p_kstat.set_defaults(func=cmd_knowledge_status)

    sub.add_parser("status", help=ui("总览: 项目/会话/最近迭代")).set_defaults(func=cmd_status)
    return parser


def main(argv: list[str] | None = None) -> int:
    global SESSION_ID_OVERRIDE
    parser = build_parser()
    args = parser.parse_args(argv)
    previous_override = SESSION_ID_OVERRIDE
    SESSION_ID_OVERRIDE = args.session_id
    try:
        if args.session_id is not None:
            validate_session_id(args.session_id)
        return int(args.func(args) or 0)
    except HyError as exc:
        fail(str(exc))
        return 2
    except (OSError, UnicodeError) as exc:
        fail(ui("文件操作失败: {}", exc))
        return 1
    except KeyboardInterrupt:
        fail(ui("已中断"))
        return 130
    finally:
        SESSION_ID_OVERRIDE = previous_override


if __name__ == "__main__":
    sys.exit(main())
