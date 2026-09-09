"""happlylong 单元测试（unittest，零额外依赖）。

覆盖：ID/slug 生成、名字白名单校验、跨 Agent 会话身份/隔离/原子写入、
fail-closed 与未绑定入口契约、语言探测矩阵、22 份 frontmatter 解析、双语模板结构一致性。
运行：python3 -m unittest discover -s tests -v
"""
from __future__ import annotations

import argparse
import contextlib
import importlib.util
import io
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

ROOT = pathlib.Path(__file__).resolve().parent.parent
_spec = importlib.util.spec_from_file_location("happlylong", ROOT / "happlylong.py")
hy = importlib.util.module_from_spec(_spec)
sys.modules["happlylong"] = hy
_spec.loader.exec_module(hy)


class TestIdsAndNames(unittest.TestCase):
    def test_title_to_slug_english(self):
        self.assertEqual(hy.title_to_slug("Album Share Card"), "album-share-card")

    def test_title_to_slug_fallback_for_non_latin(self):
        slug = hy.title_to_slug("相册分享卡片")
        self.assertTrue(slug.startswith("t") and slug[1:].isdigit())

    def test_compose_iter_id_shape(self):
        iter_id = hy.compose_iter_id("feat", "Some Title", "my-slug")
        self.assertRegex(iter_id, r"^\d{6}-feat-my-slug$")

    def test_project_name_whitelist(self):
        for bad in ("../pwn", "/tmp/pwn", "a/b", "..", "_x", "pwn\n", "中文名", ".hidden", ""):
            with self.assertRaises(hy.HyError, msg=bad):
                hy.validate_project_name(bad)
        hy.validate_project_name("myapp-01_X")

    def test_repo_and_iter_patterns(self):
        self.assertIsNone(hy.REPO_NAME_PATTERN.fullmatch("evil\n"))
        self.assertIsNone(hy.REPO_NAME_PATTERN.fullmatch("../evil"))
        self.assertIsNone(hy.ITER_ID_PATTERN.fullmatch("260903-feat-x\n"))
        self.assertIsNotNone(hy.ITER_ID_PATTERN.fullmatch("260903-feat-x"))


class TestIterationResolution(unittest.TestCase):
    """resolve_iteration 顺序：显式 project+id > 当前会话绑定。"""

    def test_order(self):
        session = {
            "active": True,
            "project": "projX",
            "iteration_id": "session-iteration",
        }

        class Explicit:
            project = "projY"
            iteration_id = "260901-feat-explicit"
        self.assertEqual(
            hy.resolve_iteration(Explicit(), session),
            ("projY", "260901-feat-explicit"),
        )

        class Current:
            project = None
            iteration_id = None
        self.assertEqual(
            hy.resolve_iteration(Current(), session),
            ("projX", "session-iteration"),
        )

        class SameProject:
            project = "projX"
            iteration_id = None
        self.assertEqual(
            hy.resolve_iteration(SameProject(), session),
            ("projX", "session-iteration"),
        )

        class OtherProject:
            project = "projY"
            iteration_id = None
        with self.assertRaises(hy.HyError):
            hy.resolve_iteration(OtherProject(), session)

        with self.assertRaises(hy.HyError):
            hy.resolve_iteration(Current(), {})


class TestSessionIsolation(unittest.TestCase):
    def setUp(self):
        self.original_override = hy.SESSION_ID_OVERRIDE
        hy.SESSION_ID_OVERRIDE = None

    def tearDown(self):
        hy.SESSION_ID_OVERRIDE = self.original_override

    def test_scope_precedence_portability_and_fail_closed(self):
        hy.SESSION_ID_OVERRIDE = "portable-a"
        cli_path, cli_source, cli_key = hy.resolve_session_scope({
            "HY_SESSION_ID": "env-other",
            "CODEX_THREAD_ID": "codex-other",
        })
        hy.SESSION_ID_OVERRIDE = None
        env_path, env_source, env_key = hy.resolve_session_scope({
            "HY_SESSION_ID": "portable-a",
            "CODEX_THREAD_ID": "codex-other",
        })
        codex_path, codex_source, _ = hy.resolve_session_scope({
            "CODEX_THREAD_ID": "codex-a",
        })
        other_path, _, _ = hy.resolve_session_scope({
            "CODEX_THREAD_ID": "codex-b",
        })

        self.assertEqual(cli_source, "--session-id")
        self.assertEqual(env_source, "HY_SESSION_ID")
        self.assertEqual(codex_source, "CODEX_THREAD_ID")
        self.assertEqual((cli_path, cli_key), (env_path, env_key))
        self.assertNotEqual(env_path, codex_path)
        self.assertNotEqual(codex_path, other_path)
        self.assertNotIn("portable-a", cli_path.name)
        self.assertNotIn("codex-a", codex_path.name)
        with self.assertRaises(hy.MissingSessionIdentityError):
            hy.resolve_session_scope({})
        with self.assertRaises(hy.MissingSessionIdentityError):
            hy.resolve_session_scope({"CODEX_SESSION_ID": "unstable-run-id"})

    def test_session_id_validation(self):
        for bad in ("", "   ", "\nleading", "line\nbreak", "x" * (hy.SESSION_ID_MAX_LENGTH + 1)):
            with self.assertRaises(hy.HyError, msg=repr(bad)):
                hy.validate_session_id(bad)
        self.assertEqual(hy.validate_session_id("  agent:session-1  "), "agent:session-1")

    def test_bindings_do_not_clobber_between_threads(self):
        original_root = hy.ROOT
        original_bindings_dir = hy.SESSION_BINDINGS_DIR
        try:
            with tempfile.TemporaryDirectory() as raw_root:
                test_root = pathlib.Path(raw_root)
                hy.ROOT = test_root
                hy.SESSION_BINDINGS_DIR = test_root / ".hy" / "session" / "bindings"
                iter_id_a = "260904-feat-a"
                iter_id_b = "260904-fix-b"
                iter_a = test_root / "workspace" / "project-a" / "iterations" / iter_id_a
                iter_b = test_root / "workspace" / "project-b" / "iterations" / iter_id_b
                iter_a.mkdir(parents=True)
                iter_b.mkdir(parents=True)

                env_a = {
                    "CODEX_THREAD_ID": "thread-a",
                }
                env_b = {
                    "CODEX_THREAD_ID": "thread-b",
                }
                with mock.patch.dict(os.environ, env_a, clear=True):
                    hy.bind_session("project-a", iter_id_a, iter_a, "A", "test")
                with mock.patch.dict(os.environ, env_b, clear=True):
                    hy.bind_session("project-b", iter_id_b, iter_b, "B", "test")

                with mock.patch.dict(os.environ, env_a, clear=True):
                    self.assertEqual(hy.read_current_session()["project"], "project-a")
                with mock.patch.dict(os.environ, env_b, clear=True):
                    self.assertEqual(hy.read_current_session()["project"], "project-b")

                binding_files = list(hy.SESSION_BINDINGS_DIR.glob("*.yaml"))
                self.assertEqual(len(binding_files), 2)
                self.assertFalse(list(hy.SESSION_BINDINGS_DIR.glob("*.tmp")))
                for binding_file in binding_files:
                    binding = hy.read_yaml_file(binding_file)
                    self.assertEqual(binding["schema"], 3)
                    self.assertEqual(
                        binding["iteration_path"],
                        hy.canonical_iteration_path(binding["project"], binding["iteration_id"]),
                    )
        finally:
            hy.ROOT = original_root
            hy.SESSION_BINDINGS_DIR = original_bindings_dir

    def test_switch_preserves_a_workspace_scoped_previous_binding(self):
        original_root = hy.ROOT
        original_bindings_dir = hy.SESSION_BINDINGS_DIR
        try:
            with tempfile.TemporaryDirectory() as raw_root:
                test_root = pathlib.Path(raw_root)
                hy.ROOT = test_root
                hy.SESSION_BINDINGS_DIR = test_root / ".hy" / "session" / "bindings"
                first_id = "260904-feat-first"
                second_id = "260904-fix-second"
                first = test_root / "workspace" / "project-a" / "iterations" / first_id
                second = test_root / "workspace" / "project-b" / "iterations" / second_id
                first.mkdir(parents=True)
                second.mkdir(parents=True)
                with mock.patch.dict(os.environ, {"HY_SESSION_ID": "switching-session"}, clear=True):
                    hy.bind_session("project-a", first_id, first, "First", "test")
                    hy.bind_session("project-b", second_id, second, "Second", "test")
                    binding = hy.read_current_session()
                self.assertEqual(binding["project"], "project-b")
                self.assertEqual(binding["previous"], {
                    "project": "project-a",
                    "iteration_id": first_id,
                    "iteration_path": hy.canonical_iteration_path("project-a", first_id),
                    "title": "First",
                })
        finally:
            hy.ROOT = original_root
            hy.SESSION_BINDINGS_DIR = original_bindings_dir

    def test_binding_key_integrity_check(self):
        original_bindings_dir = hy.SESSION_BINDINGS_DIR
        try:
            with tempfile.TemporaryDirectory() as raw_root:
                hy.SESSION_BINDINGS_DIR = pathlib.Path(raw_root) / "bindings"
                with mock.patch.dict(os.environ, {"HY_SESSION_ID": "agent-a"}, clear=True):
                    binding_path = hy.current_session_path()
                    hy.write_yaml_file(binding_path, {"schema": 3, "session_key": "wrong"})
                    with self.assertRaises(hy.HyError):
                        hy.read_current_session()
        finally:
            hy.SESSION_BINDINGS_DIR = original_bindings_dir

    def test_binding_schema_fails_closed(self):
        original_bindings_dir = hy.SESSION_BINDINGS_DIR
        try:
            with tempfile.TemporaryDirectory() as raw_root:
                hy.SESSION_BINDINGS_DIR = pathlib.Path(raw_root) / "bindings"
                with mock.patch.dict(os.environ, {"HY_SESSION_ID": "agent-schema"}, clear=True):
                    binding_path, _, session_key = hy.resolve_session_scope()
                    hy.write_yaml_file(binding_path, {
                        "schema": hy.SESSION_BINDING_SCHEMA - 1,
                        "session_key": session_key,
                        "active": False,
                    })
                    with self.assertRaises(hy.HyError):
                        hy.read_current_session()
        finally:
            hy.SESSION_BINDINGS_DIR = original_bindings_dir

    def test_active_and_previous_bindings_require_one_workspace_project(self):
        original_bindings_dir = hy.SESSION_BINDINGS_DIR
        try:
            with tempfile.TemporaryDirectory() as raw_root:
                hy.SESSION_BINDINGS_DIR = pathlib.Path(raw_root) / "bindings"
                env = {"HY_SESSION_ID": "workspace-validation"}
                valid = {
                    "active": True,
                    "project": "project-a",
                    "iteration_id": "260904-feat-a",
                    "iteration_path": "workspace/project-a/iterations/260904-feat-a",
                }
                with mock.patch.dict(os.environ, env, clear=True):
                    with self.assertRaises(hy.HyError):
                        hy.write_current_session({
                            "active": True,
                            "iteration_id": "260904-feat-a",
                            "iteration_path": "workspace/project-a/iterations/260904-feat-a",
                        })
                    with self.assertRaises(hy.HyError):
                        hy.write_current_session({
                            **valid,
                            "iteration_path": "workspace/project-b/iterations/260904-feat-a",
                        })
                    with self.assertRaises(hy.HyError):
                        hy.write_current_session({
                            **valid,
                            "previous": {
                                "project": "project-b",
                                "iteration_id": "260904-fix-b",
                            },
                        })
                    self.assertFalse(hy.current_session_path().exists())
        finally:
            hy.SESSION_BINDINGS_DIR = original_bindings_dir

    def test_iter_new_requires_identity_before_project_mutation(self):
        args = argparse.Namespace(
            project="project-a",
            title="No identity",
            type="feat",
            slug=None,
            iteration_id=None,
        )
        with mock.patch.dict(os.environ, {}, clear=True), mock.patch.object(hy, "project_dir") as project_dir:
            with self.assertRaises(hy.MissingSessionIdentityError):
                hy.cmd_iter_new(args)
            project_dir.assert_not_called()

    def test_cli_override_is_scoped_and_missing_identity_exits_two(self):
        original_bindings_dir = hy.SESSION_BINDINGS_DIR
        try:
            with tempfile.TemporaryDirectory() as raw_root:
                hy.SESSION_BINDINGS_DIR = pathlib.Path(raw_root) / "bindings"
                output = io.StringIO()
                with mock.patch.dict(os.environ, {"HY_SESSION_ID": "environment-id"}, clear=True), \
                        contextlib.redirect_stdout(output), contextlib.redirect_stderr(output):
                    self.assertEqual(hy.main(["--session-id", "portable-id", "session", "clear"]), 0)
                portable_path, _, _ = hy.resolve_session_scope(
                    {"HY_SESSION_ID": "portable-id"}
                )
                environment_path, _, _ = hy.resolve_session_scope(
                    {"HY_SESSION_ID": "environment-id"}
                )
                self.assertTrue(portable_path.exists())
                self.assertFalse(environment_path.exists())
                self.assertIsNone(hy.SESSION_ID_OVERRIDE)

                with mock.patch.dict(os.environ, {}, clear=True), \
                        contextlib.redirect_stdout(output), contextlib.redirect_stderr(output):
                    self.assertEqual(hy.main(["session", "show"]), 2)
        finally:
            hy.SESSION_BINDINGS_DIR = original_bindings_dir

    def test_unbound_session_show_exposes_entry_gate_contract(self):
        original_bindings_dir = hy.SESSION_BINDINGS_DIR
        try:
            with tempfile.TemporaryDirectory() as raw_root:
                hy.SESSION_BINDINGS_DIR = pathlib.Path(raw_root) / "bindings"
                output = io.StringIO()
                with mock.patch.dict(os.environ, {"HY_SESSION_ID": "unbound-agent"}, clear=True), \
                        mock.patch.object(
                            hy,
                            "session_scope_label",
                            return_value=("HY_SESSION_ID", ".hy/session/bindings/test.yaml"),
                        ), contextlib.redirect_stdout(output):
                    self.assertEqual(hy.cmd_session_show(argparse.Namespace()), 0)
                status = hy.yaml.safe_load(output.getvalue())
                self.assertFalse(status["active"])
                self.assertEqual(status["entry_gate"]["policy"], hy.UNBOUND_SESSION_POLICY)
                self.assertEqual(
                    status["entry_gate"]["actions"],
                    list(hy.UNBOUND_SESSION_ACTIONS),
                )
                self.assertEqual(
                    status["entry_gate"]["explicit_new_iteration_signal"],
                    hy.EXPLICIT_NEW_ITERATION_SIGNAL,
                )
                self.assertEqual(status["entry_gate"]["workspace_root"], "workspace")
                self.assertEqual(
                    status["entry_gate"]["required_binding_fields"],
                    list(hy.SESSION_REQUIRED_ACTIVE_FIELDS),
                )
                self.assertEqual(status["session_scope"]["source"], "HY_SESSION_ID")
                self.assertEqual(
                    status["session_scope"]["binding_file"],
                    ".hy/session/bindings/test.yaml",
                )
        finally:
            hy.SESSION_BINDINGS_DIR = original_bindings_dir


class TestLanguageDetection(unittest.TestCase):
    _VARS = ("LC_ALL", "LC_CTYPE", "LANG", "LANGUAGE")

    def _with_env(self, env: dict) -> str:
        backup = {v: os.environ.get(v) for v in self._VARS}
        try:
            for v in self._VARS:
                os.environ.pop(v, None)
            os.environ.update(env)
            return hy.detect_language()
        finally:
            for v, val in backup.items():
                if val is None:
                    os.environ.pop(v, None)
                else:
                    os.environ[v] = val

    def test_matrix(self):
        self.assertEqual(self._with_env({"LC_ALL": "zh_CN.UTF-8"}), "zh")
        self.assertEqual(self._with_env({"LC_ALL": "en_US.UTF-8"}), "en")
        self.assertEqual(self._with_env({"LC_CTYPE": "C.UTF-8", "LANG": "zh_CN.UTF-8"}), "zh")
        self.assertEqual(self._with_env({"LC_CTYPE": "C.UTF-8", "LANG": "C.UTF-8"}), "en")
        self.assertEqual(self._with_env({}), "en")
        self.assertEqual(self._with_env({"LANGUAGE": "zh"}), "zh")

    def test_missing_yaml_error_does_not_recurse(self):
        installed_yaml = hy.yaml
        try:
            hy.yaml = None
            with self.assertRaises(hy.HyError):
                hy.validate_project_name("../invalid")
        finally:
            hy.yaml = installed_yaml


class TestI18nAssets(unittest.TestCase):
    def _frontmatter(self, path: pathlib.Path) -> dict:
        import yaml
        lines = path.read_text(encoding="utf-8").splitlines()
        end = lines.index("---", 1)
        return yaml.safe_load("\n".join(lines[1:end]))

    def test_all_skill_frontmatters_parse(self):
        skills = sorted((ROOT / ".hy" / "i18n").glob("*/skills/*/SKILL.md"))
        self.assertEqual(len(skills), 20)
        for p in skills:
            data = self._frontmatter(p)
            self.assertIsInstance(data, dict, p)
            self.assertIn("name", data, p)
            self.assertIn("description", data, p)
            self.assertTrue(str(data["description"]).strip(), p)

    def test_agents_frontmatters_parse(self):
        for p in sorted((ROOT / ".hy" / "i18n").glob("*/AGENTS.md")):
            data = self._frontmatter(p)
            self.assertIn("description", data, p)

    def test_bilingual_template_parity(self):
        zh = sorted(q.relative_to(ROOT / ".hy/i18n/zh/templates").as_posix()
                    for q in (ROOT / ".hy/i18n/zh/templates").rglob("*.tpl"))
        en = sorted(q.relative_to(ROOT / ".hy/i18n/en/templates").as_posix()
                    for q in (ROOT / ".hy/i18n/en/templates").rglob("*.tpl"))
        self.assertEqual(zh, en)
        self.assertTrue(zh, "模板清单非空")

    def test_ui_en_covers_call_templates(self):
        import ast
        tree = ast.parse((ROOT / "happlylong.py").read_text(encoding="utf-8"))
        called = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "ui":
                if node.args and isinstance(node.args[0], ast.Constant):
                    called.add(node.args[0].value)
        missing = called - set(hy.UI_EN)
        self.assertFalse(missing, f"UI_EN 缺失模板: {sorted(missing)[:5]}")

    def test_session_protocol_config_matches_cli(self):
        import yaml
        config = yaml.safe_load((ROOT / ".hy" / "config.yaml").read_text(encoding="utf-8"))
        session = config["session"]
        self.assertEqual(config["schema"], 2)
        self.assertEqual(session["binding_schema"], hy.SESSION_BINDING_SCHEMA)
        self.assertEqual(session["identity_priority"], ["--session-id", *hy.SESSION_ID_ENV_VARS])
        self.assertEqual(session["portable_identity"], "HY_SESSION_ID")
        self.assertEqual(session["workspace_root"], hy.SESSION_WORKSPACE_ROOT)
        self.assertEqual(
            session["required_active_fields"],
            list(hy.SESSION_REQUIRED_ACTIVE_FIELDS),
        )
        self.assertEqual(
            session["hash_namespace"],
            hy.SESSION_HASH_NAMESPACE.removesuffix(b"\0").decode("ascii"),
        )
        self.assertTrue(session["fail_closed"])
        self.assertTrue(session["atomic_write"])
        self.assertTrue(session["single_writer_per_identity"])
        self.assertEqual(session["unbound_policy"], hy.UNBOUND_SESSION_POLICY)
        self.assertEqual(
            session["explicit_new_iteration_signal"],
            hy.EXPLICIT_NEW_ITERATION_SIGNAL,
        )


class TestReleaseChecks(unittest.TestCase):
    def test_private_name_source_accepts_plain_list_and_mapping_forms(self):
        with tempfile.TemporaryDirectory() as raw_root:
            source = pathlib.Path(raw_root) / "private-names.yaml"
            source.write_text(
                "# local only\nreal-alpha\n- real_beta\nreal-gamma → example\nreal-delta: sample\n",
                encoding="utf-8",
            )
            self.assertEqual(
                hy.private_name_patterns(source),
                ["real-alpha", "real_beta", "real-gamma", "real-delta"],
            )

    def test_no_git_fallback_inventory_contains_sources_not_install_artifacts(self):
        with mock.patch.object(hy.subprocess, "run", side_effect=FileNotFoundError("git unavailable")), \
                mock.patch.object(hy.shutil, "which", return_value=None):
            files = {path.relative_to(ROOT).as_posix() for path in hy.publish_layer_files()}
        for required in (
            ".gitattributes",
            ".hy/config.yaml",
            ".hy/opensource.md",
            ".hy/i18n/en/AGENTS.md",
            "tests/test_framework.py",
        ):
            self.assertIn(required, files)
        self.assertFalse(any(path.startswith(".agents/") for path in files))
        self.assertFalse(any(path.startswith(".hy/templates/") for path in files))

    def test_bilingual_readme_heading_structure_matches(self):
        zh = (ROOT / "README.md").read_text(encoding="utf-8")
        en = (ROOT / "README.en.md").read_text(encoding="utf-8")
        self.assertEqual(hy.markdown_heading_levels(zh), hy.markdown_heading_levels(en))
        self.assertTrue(hy.markdown_heading_levels(zh))

    def test_expected_skill_set_matches_both_languages(self):
        for lang in hy.LANGUAGES:
            actual = {
                path.parent.name
                for path in (ROOT / ".hy" / "i18n" / lang / "skills").glob("*/SKILL.md")
            }
            self.assertEqual(actual, hy.EXPECTED_SKILL_NAMES)


class TestAuditReleaseFixes(unittest.TestCase):
    """2026-09-05 GitHub 上架审计 P0/P1 修复回归。

    覆盖：迭代 ID 路径穿越（P0）、模板 YAML 注入、link add 事务顺序、
    pending 计数、链接诊断假健康、损坏偏好 YAML、凭据扫描与必需发布文件断言。
    """

    SANDBOX_GLOBALS = (
        "ROOT", "WORKSPACE_ROOT", "WORKSPACE_INDEX", "HY_DIR", "I18N_DIR",
        "SESSION_DIR", "SESSION_BINDINGS_DIR", "PREFS_FILE",
    )

    def setUp(self):
        self.original = {name: getattr(hy, name) for name in self.SANDBOX_GLOBALS}
        self.tmp = pathlib.Path(tempfile.mkdtemp(prefix="hy-audit-fix-"))
        hy.ROOT = self.tmp
        hy.WORKSPACE_ROOT = self.tmp / "workspace"
        hy.WORKSPACE_INDEX = self.tmp / "workspace" / "_index.yaml"
        hy.HY_DIR = self.tmp / ".hy"
        hy.I18N_DIR = self.original["I18N_DIR"]  # 只读复用真实双语模板
        hy.SESSION_DIR = self.tmp / ".hy" / "session"
        hy.SESSION_BINDINGS_DIR = self.tmp / ".hy" / "session" / "bindings"
        hy.PREFS_FILE = self.tmp / ".hy" / "session" / "prefs.yaml"

    def tearDown(self):
        for name, value in self.original.items():
            setattr(hy, name, value)
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _run(self, fn, *args):
        out = io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(out):
            rc = fn(*args)
        return rc, out.getvalue()

    def _project(self, name="demo"):
        rc, out = self._run(hy.cmd_project_new, argparse.Namespace(name=name, title="Demo", description=""))
        self.assertEqual(rc, 0, out)

    def test_validate_iteration_id_rejects_traversal(self):
        for bad in ("../victim", "..\\victim", "/tmp/victim", "260901-feat-x/../../victim",
                    "260901-feat-x\n", "bad id", "", "260901-hack-x"):
            with self.assertRaises(hy.HyError, msg=bad):
                hy.validate_iteration_id(bad)
        self.assertEqual(hy.validate_iteration_id("260901-feat-a"), "260901-feat-a")

    def test_iter_show_and_close_refuse_ids_outside_iterations(self):
        self._project()
        victim_text = "schema: 1\nstatus: open\nstages: {smoke: pending}\n"
        victim = self.tmp / "victim" / "_index.yaml"
        victim.parent.mkdir()
        victim.write_text(victim_text, encoding="utf-8")
        traversal = argparse.Namespace(project="demo", iteration_id="../../../victim", force=True)
        with self.assertRaises(hy.HyError):
            self._run(hy.cmd_iter_close, traversal)
        self.assertEqual(victim.read_text(encoding="utf-8"), victim_text)
        with self.assertRaises(hy.HyError):
            self._run(hy.cmd_iter_show, argparse.Namespace(project="demo", iteration_id="../../../victim"))

    def test_session_set_rejects_invalid_iteration_id(self):
        with self.assertRaises(hy.HyError):
            self._run(hy.cmd_session_set, argparse.Namespace(project="demo", iteration_id="../../evil"))

    def test_iter_new_bad_id_fails_clean_without_artifacts(self):
        self._project()
        args = argparse.Namespace(project="demo", title="t", type="feat", slug=None, iteration_id="bad id")
        with mock.patch.dict(os.environ, {"HY_SESSION_ID": "audit-iter-new"}, clear=True):
            with self.assertRaises(hy.HyError):
                self._run(hy.cmd_iter_new, args)
        self.assertFalse((hy.WORKSPACE_ROOT / "demo" / "iterations" / "bad id").exists())

    def test_project_new_title_with_yaml_metacharacters_round_trips(self):
        title = "相册: 分享 #1 \"q\""
        description = "desc: with: colons\nsecond line"
        self._run(hy.cmd_project_new, argparse.Namespace(name="inj", title=title, description=description))
        profile = hy.read_yaml_file(hy.WORKSPACE_ROOT / "inj" / "profile.yaml")
        self.assertEqual(profile["title"], title)
        self.assertEqual(profile["description"], description)
        self.assertEqual(profile["project"], "inj")

    def test_iter_new_index_yaml_survives_special_title(self):
        self._project()
        title = "T: 冒号 #hash"
        with mock.patch.dict(os.environ, {"HY_SESSION_ID": "audit-iter-yaml"}, clear=True):
            rc, out = self._run(hy.cmd_iter_new, argparse.Namespace(
                project="demo", title=title, type="feat", slug=None, iteration_id=None))
            self.assertEqual(rc, 0, out)
        iter_dirs = list((hy.WORKSPACE_ROOT / "demo" / "iterations").iterdir())
        self.assertEqual(len(iter_dirs), 1)
        meta = hy.read_yaml_file(iter_dirs[0] / "_index.yaml")
        self.assertEqual(meta["title"], title)
        self.assertEqual(meta["status"], "open")
        self.assertEqual(meta["stages"]["prd"], "pending")

    def test_link_add_app_validation_precedes_symlink_creation(self):
        self._project()
        target = self.tmp / "realrepo"
        target.mkdir()
        args = argparse.Namespace(project="demo", repo="orphan", target=str(target), role="fullstack",
                                  shared=False, app=["sub=api/sub"], note="", pending=False, force=False)
        with self.assertRaises(hy.HyError):
            self._run(hy.cmd_link_add, args)
        link = hy.WORKSPACE_ROOT / "demo" / "code_lib" / "orphan"
        self.assertFalse(link.is_symlink() or link.exists())
        profile = hy.read_yaml_file(hy.WORKSPACE_ROOT / "demo" / "profile.yaml")
        self.assertEqual(profile.get("repos"), {})
        args.role = "backend"
        rc, out = self._run(hy.cmd_link_add, args)
        self.assertEqual(rc, 0, out)
        self.assertTrue(link.is_symlink())

    def test_link_apply_counts_skipped_pending(self):
        self._project()
        ready = self.tmp / "readyrepo"
        ready.mkdir()
        self._run(hy.cmd_link_add, argparse.Namespace(
            project="demo", repo="ghost", target=str(self.tmp / "not-ready"), role="lib",
            shared=False, app=[], note="", pending=True, force=False))
        self._run(hy.cmd_link_add, argparse.Namespace(
            project="demo", repo="ready", target=str(ready), role="lib",
            shared=False, app=[], note="", pending=True, force=False))
        with mock.patch.object(hy, "resolve_language", return_value="zh"):
            rc, out = self._run(hy.cmd_link_apply, argparse.Namespace(project="demo"))
        self.assertEqual(rc, 0, out)
        self.assertIn("补链 1 个，仍 pending 1 个", out)
        profile = hy.read_yaml_file(hy.WORKSPACE_ROOT / "demo" / "profile.yaml")
        self.assertNotIn("pending", profile["repos"]["ready"])
        self.assertTrue(profile["repos"]["ghost"]["pending"])

    def test_link_status_and_list_flag_wrong_target(self):
        self._project()
        good = self.tmp / "goodrepo"
        good.mkdir()
        other = self.tmp / "otherrepo"
        other.mkdir()
        entry = {"role": "lib", "target": str(good)}
        self._run(hy.cmd_link_add, argparse.Namespace(
            project="demo", repo="moved", target=str(good), role="lib",
            shared=False, app=[], note="", pending=False, force=False))
        link = hy.WORKSPACE_ROOT / "demo" / "code_lib" / "moved"
        self.assertEqual(hy.link_status("demo", "moved", entry), "ok")
        link.unlink()
        link.symlink_to(other)
        self.assertEqual(hy.link_status("demo", "moved", entry), "mismatch")
        with mock.patch.object(hy, "resolve_language", return_value="zh"):
            rc, out = self._run(hy.cmd_link_list, argparse.Namespace(project="demo"))
        self.assertIn("MISMATCH", out)
        self.assertIn("异常", out)
        link.unlink()
        link.symlink_to(self.tmp / "gone")
        self.assertEqual(hy.link_status("demo", "moved", entry), "broken")
        link.unlink()
        link.symlink_to(good)
        self.assertEqual(hy.link_status("demo", "moved", entry), "ok")

    def test_corrupted_prefs_yaml_fails_closed(self):
        hy.PREFS_FILE.parent.mkdir(parents=True, exist_ok=True)
        hy.PREFS_FILE.write_text("&a [*a]\n", encoding="utf-8")  # 自引用 → 非对象
        with self.assertRaises(hy.HyError):
            hy.load_lang_prefs()
        # 渲染用查询降级回系统 locale，且不得递归崩溃（报错文案本身需要语言）
        self.assertIn(hy.resolve_language(), hy.LANGUAGES)
        hy.PREFS_FILE.write_text("a: " + "[" * 20000 + "0" + "]" * 20000 + "\n", encoding="utf-8")
        with self.assertRaises(hy.HyError):
            hy.load_lang_prefs()
        self.assertIn(hy.resolve_language(), hy.LANGUAGES)

    def test_credential_patterns_detect_fine_grained_pat(self):
        # 样本一律拼接构造：发布层扫描 tests/ 源码时不得命中测试自身
        samples = (
            "github_pat_" + "11ABCDEFG0someLongTokenBody_1234567890abcdef",
            "ghp_" + "16C7e42F292c6912E7710c838347AE178B4a",
            "AKIA" + "IOSFODNN7EXAMPLE",
            "sk-" + "a1b2c3d4e5f6a7b8c9d0e1f2g3h4i5",
            "token" + " = 'supersecretvalue123'",
        )
        for sample in samples:
            self.assertTrue(any(p.search(sample) for p in hy.CREDENTIAL_PATTERNS), sample)
        self.assertFalse(any(p.search("no secrets here, just docs") for p in hy.CREDENTIAL_PATTERNS))

    def test_release_missing_files_flags_empty_root_and_passes_real(self):
        self.assertEqual(hy.release_missing_files(self.original["ROOT"]), [])
        problems = hy.release_missing_files(self.tmp / "empty")
        self.assertTrue(any("project/profile.yaml.tpl" in p for p in problems))
        self.assertTrue(any("iteration/_index.yaml.tpl" in p for p in problems))
        self.assertTrue(any("workflows" in p for p in problems))
        self.assertTrue(any("README.md" in p for p in problems))

    def test_release_check_passes_on_real_repo_with_new_checks(self):
        saved = {name: getattr(hy, name) for name in ("ROOT", "HY_DIR", "I18N_DIR")}
        for name in saved:
            setattr(hy, name, self.original[name])
        try:
            rc, out = self._run(hy.cmd_release_check, argparse.Namespace())
            self.assertEqual(rc, 0, out)
        finally:
            for name, value in saved.items():
                setattr(hy, name, value)

    def test_release_check_fails_on_pat_injection_and_missing_ci(self):
        ignore = shutil.ignore_patterns(".git", "workspace", "__pycache__", "session", "snapshots", ".agents")
        with tempfile.TemporaryDirectory() as raw:
            copy_root = pathlib.Path(raw) / "repo"
            shutil.copytree(self.original["ROOT"], copy_root, ignore=ignore)
            saved = {name: getattr(hy, name) for name in ("ROOT", "HY_DIR", "I18N_DIR")}
            hy.ROOT = copy_root
            hy.HY_DIR = copy_root / ".hy"
            hy.I18N_DIR = copy_root / ".hy" / "i18n"
            try:
                readme = copy_root / "README.md"
                readme.write_text(
                    readme.read_text(encoding="utf-8")
                    + "\n" + "github_pat_" + "11AAAAAAA0demoTOKENPLACEHOLDER9999\n",
                    encoding="utf-8",
                )
                rc, out = self._run(hy.cmd_release_check, argparse.Namespace())
                self.assertEqual(rc, 1, out)
                self.assertIn("README.md", out)
                shutil.rmtree(copy_root / ".github" / "workflows")
                rc, out = self._run(hy.cmd_release_check, argparse.Namespace())
                self.assertEqual(rc, 1, out)
                self.assertIn("workflows", out)
            finally:
                for name, value in saved.items():
                    setattr(hy, name, value)

    def _link_args(self, target, repo="repo", **changes):
        values = dict(project="demo", repo=repo, target=str(target), role="lib",
                      shared=False, app=[], note="", pending=False, force=False)
        return argparse.Namespace(**{**values, **changes})

    def _release_copy(self):
        copy_root = self.tmp / "release"
        shutil.copytree(self.original["ROOT"], copy_root, ignore=shutil.ignore_patterns(
            ".git", "workspace", "__pycache__", "session", "snapshots", ".agents"))
        hy.ROOT = copy_root
        hy.HY_DIR = copy_root / ".hy"
        hy.I18N_DIR = hy.HY_DIR / "i18n"
        return copy_root

    def test_iteration_directory_and_metadata_symlinks_cannot_escape(self):
        self._project()
        victim = self.tmp / "victim.yaml"
        original = "status: open\nstages: {smoke: pending}\n"
        victim.write_text(original, encoding="utf-8")
        iteration = hy.WORKSPACE_ROOT / "demo/iterations/260908-fix-safe"
        iteration.mkdir()
        (iteration / "_index.yaml").symlink_to(victim)
        for fn in (hy.cmd_iter_show, hy.cmd_iter_close, hy.cmd_session_set):
            with self.assertRaises(hy.HyError):
                self._run(fn, argparse.Namespace(project="demo", iteration_id=iteration.name, force=True))
        self.assertEqual(victim.read_text(encoding="utf-8"), original)
        alias = iteration.parent / "260908-fix-alias"
        alias.symlink_to(iteration, target_is_directory=True)
        with self.assertRaises(hy.HyError):
            self._run(hy.cmd_iter_close, argparse.Namespace(project="demo", iteration_id=alias.name, force=True))

    def test_iter_list_rejects_project_traversal(self):
        self._project()
        with self.assertRaises(hy.HyError):
            self._run(hy.cmd_iter_list, argparse.Namespace(project="../outside"))

    def test_profile_repo_keys_checked_before_apply_or_remove(self):
        self._project()
        target = self.tmp / "target"
        target.mkdir()
        victim = self.tmp / "outside-link"
        victim.symlink_to(target, target_is_directory=True)
        profile = hy.read_profile("demo")
        profile["repos"]["../../../outside-link"] = {"target": str(target), "role": "lib", "pending": True}
        hy.write_yaml_file(hy.profile_path("demo"), profile)
        for fn, args in ((hy.cmd_link_apply, argparse.Namespace(project="demo")),
                         (hy.cmd_link_rm, argparse.Namespace(project="demo", repo="../../../outside-link"))):
            with self.assertRaises(hy.HyError):
                self._run(fn, args)
        self.assertTrue(victim.is_symlink())

    def test_project_and_code_lib_aliases_rejected(self):
        self._project()
        alias = hy.WORKSPACE_ROOT / "alias"
        alias.symlink_to(hy.WORKSPACE_ROOT / "demo", target_is_directory=True)
        with self.assertRaises(hy.HyError):
            hy.read_profile("alias")
        code = hy.WORKSPACE_ROOT / "demo/code_lib"
        code.rename(code.with_name("code_lib-backup"))
        target = self.tmp / "external"
        target.mkdir()
        code.symlink_to(target, target_is_directory=True)
        with self.assertRaises(hy.HyError):
            self._run(hy.cmd_link_add, self._link_args(target))
        self.assertEqual(list(target.iterdir()), [])

    def test_link_add_invalid_manifest_and_registry_leave_no_changes(self):
        self._project()
        target = self.tmp / "target"
        target.mkdir()
        manifest = target / "package.json"
        for content in ("[1]", '{"dependencies": []}'):
            manifest.write_text(content, encoding="utf-8")
            with self.assertRaises(hy.HyError):
                self._run(hy.cmd_link_add, self._link_args(target))
            self.assertFalse((hy.WORKSPACE_ROOT / "demo/code_lib/repo").exists())
            self.assertEqual(hy.read_profile("demo")["repos"], {})
        manifest.write_text("{}", encoding="utf-8")
        hy.write_yaml_file(hy.WORKSPACE_INDEX, {"projects": {}})
        with self.assertRaises(hy.HyError):
            self._run(hy.cmd_link_add, self._link_args(target))
        self.assertEqual(hy.read_profile("demo")["repos"], {})
        self.assertFalse((hy.WORKSPACE_ROOT / "demo/code_lib/repo").exists())

    def test_link_apply_preflights_conflicts_and_retries_existing_matching_link(self):
        self._project()
        for name in ("first", "second"):
            target = self.tmp / name
            target.mkdir()
            self._run(hy.cmd_link_add, self._link_args(target, repo=name, pending=True))
        code = hy.WORKSPACE_ROOT / "demo/code_lib"
        (code / "second").mkdir()
        with self.assertRaises(hy.HyError):
            self._run(hy.cmd_link_apply, argparse.Namespace(project="demo"))
        self.assertFalse((code / "first").is_symlink())
        (code / "second").rename(code / "second-backup")
        (code / "first").symlink_to(self.tmp / "first", target_is_directory=True)
        self._run(hy.cmd_link_apply, argparse.Namespace(project="demo"))
        self._run(hy.cmd_link_apply, argparse.Namespace(project="demo"))
        self.assertTrue((code / "second").is_symlink())
        self.assertFalse(any(e.get("pending") for e in hy.read_profile("demo")["repos"].values()))

    def test_link_force_write_failure_restores_link_and_registries(self):
        self._project()
        first, second = self.tmp / "first", self.tmp / "second"
        first.mkdir()
        second.mkdir()
        self._run(hy.cmd_link_add, self._link_args(first))
        profile_path = hy.profile_path("demo")
        original_profile = profile_path.read_bytes()
        original_index = hy.WORKSPACE_INDEX.read_bytes()
        writer = hy.write_yaml_file
        def fail_registry(path, data):
            if path == hy.WORKSPACE_INDEX:
                raise OSError("injected write failure")
            return writer(path, data)
        with mock.patch.object(hy, "write_yaml_file", side_effect=fail_registry):
            with self.assertRaises(hy.HyError):
                self._run(hy.cmd_link_add, self._link_args(second, force=True))
        self.assertEqual((hy.WORKSPACE_ROOT / "demo/code_lib/repo").resolve(), first.resolve())
        self.assertEqual(profile_path.read_bytes(), original_profile)
        self.assertEqual(hy.WORKSPACE_INDEX.read_bytes(), original_index)

    def test_prefs_decode_errors_and_falsy_objects_fail_cleanly(self):
        hy.PREFS_FILE.parent.mkdir(parents=True)
        for value in (b"[]", b"false", b"0", b"&a {language: *a}", b"\xff\xfe"):
            hy.PREFS_FILE.write_bytes(value)
            with self.assertRaises(hy.HyError):
                hy.load_lang_prefs()
            self.assertIn(hy.resolve_language(), hy.LANGUAGES)
        rc, _ = self._run(lambda _: hy.main(["lang"]), argparse.Namespace())
        self.assertEqual(rc, 2)

    def test_yaml_string_fields_round_trip_in_both_languages(self):
        for lang in hy.LANGUAGES:
            with mock.patch.object(hy, "resolve_language", return_value=lang):
                for project in (("on", "null", "false") if lang == "zh" else ("yes", "off", "true")):
                    title = 'A: # "quote"\n😀\x85\x81'
                    self._run(hy.cmd_project_new, argparse.Namespace(name=project, title=title, description=title))
                    with mock.patch.dict(os.environ, {"HY_SESSION_ID": "yaml-review"}, clear=True):
                        self._run(hy.cmd_iter_new, argparse.Namespace(project=project, title=title,
                            type="feat", slug=None, iteration_id="260908-feat-sample"))
                    profile = hy.read_profile(project)
                    meta = hy.read_yaml_file(hy.WORKSPACE_ROOT / project / "iterations/260908-feat-sample/_index.yaml")
                    self.assertEqual((profile["project"], meta["project"]), (project, project))
                    self.assertEqual((profile["title"], meta["title"]), (title, title))

    def test_release_git_quoted_filename_is_scanned(self):
        root = self._release_copy()
        subprocess.run(["git", "init", "-q", str(root)], check=True, capture_output=True)
        fixture = root / "tests" / "中文样本.yaml"
        fixture.write_text("github_pat_" + "FAKE_AUDIT_VALUE_" * 3, encoding="utf-8")
        self.assertIn(fixture, hy.publish_layer_files())
        rc, out = self._run(hy.cmd_release_check, argparse.Namespace())
        self.assertEqual(rc, 1, out)
        self.assertIn(fixture.name, out)

    def test_release_detects_unquoted_and_json_credentials(self):
        root = self._release_copy()
        fixture = root / "tests" / "credential-fixture.yaml"
        for value in ("password" + ": audit-fixture-value", '"token"' + ': "audit-fixture-value"',
                      "APP_API_KEY" + "=audit-fixture-value"):
            fixture.write_text(value, encoding="utf-8")
            rc, out = self._run(hy.cmd_release_check, argparse.Namespace())
            self.assertEqual(rc, 1, out)

    def test_release_rejects_empty_ci_and_missing_bilingual_templates(self):
        root = self._release_copy()
        ci = root / ".github/workflows/ci.yml"
        backup = ci.read_bytes()
        ci.write_text("# empty\n", encoding="utf-8")
        rc, out = self._run(hy.cmd_release_check, argparse.Namespace())
        self.assertEqual(rc, 1, out)
        ci.write_bytes(backup)
        for lang in hy.LANGUAGES:
            template = hy.I18N_DIR / lang / "templates/project/profile.yaml.tpl"
            template.rename(self.tmp / (lang + "-profile-snapshot"))
        rc, out = self._run(hy.cmd_release_check, argparse.Namespace())
        self.assertEqual(rc, 1, out)

    def test_release_rejects_required_file_ignored_by_git(self):
        root = self._release_copy()
        subprocess.run(["git", "init", "-q", str(root)], check=True, capture_output=True)
        ignore = root / ".gitignore"
        ignore.write_text(ignore.read_text(encoding="utf-8") + "\n/.github/workflows/\n", encoding="utf-8")
        rc, out = self._run(hy.cmd_release_check, argparse.Namespace())
        self.assertEqual(rc, 1, out)

    def test_language_install_refuses_linked_entry_file_before_rewriting(self):
        root = self._release_copy()
        destination = root / ".agents/skills/hy-old"
        destination.mkdir(parents=True)
        sentinel = destination / "keep.md"
        sentinel.write_text("keep", encoding="utf-8")
        victim = self.tmp / "external.md"
        victim.write_text("untouched", encoding="utf-8")
        if (root / "AGENTS.md").exists():
            (root / "AGENTS.md").rename(self.tmp / "entry-backup")
        (root / "AGENTS.md").symlink_to(victim)
        with self.assertRaises(hy.HyError):
            hy.install_language("en")
        self.assertEqual(victim.read_text(encoding="utf-8"), "untouched")
        self.assertEqual(sentinel.read_text(encoding="utf-8"), "keep")

    def test_doctor_reports_invalid_profile_without_traceback(self):
        self._project()
        hy.write_yaml_file(hy.profile_path("demo"), ["invalid"])
        with mock.patch.object(hy, "template_root", return_value=hy.HY_DIR / "templates"), \
                mock.patch.object(hy, "SHARED_DIR", hy.ROOT / "shared"):
            rc, output = self._run(hy.cmd_doctor, argparse.Namespace(fix=False))
        self.assertEqual(rc, 1, output)
        self.assertIn("profile.yaml", output)

    def test_status_reports_invalid_profile_without_traceback(self):
        self._project()
        hy.write_yaml_file(hy.profile_path("demo"), ["invalid"])
        rc, output = self._run(hy.main, ["status"])
        self.assertEqual(rc, 2, output)
        self.assertIn("profile.yaml", output)

    def test_language_install_restores_files_and_skills_on_copy_failure(self):
        root = self._release_copy()
        sentinel = root / ".agents/skills/hy-old/keep.md"
        sentinel.parent.mkdir(parents=True)
        sentinel.write_text("keep", encoding="utf-8")
        entry = root / "AGENTS.md"
        entry.write_text("previous entry", encoding="utf-8")
        original_copy = shutil.copyfile

        def fail_entry_copy(source, destination, *args, **kwargs):
            if pathlib.Path(source) == hy.I18N_DIR / "en/AGENTS.md":
                raise OSError("injected language copy failure")
            return original_copy(source, destination, *args, **kwargs)

        with mock.patch.object(shutil, "copyfile", side_effect=fail_entry_copy):
            with self.assertRaises(hy.HyError):
                hy.install_language("en")
        self.assertEqual(entry.read_text(encoding="utf-8"), "previous entry")
        self.assertEqual(sentinel.read_text(encoding="utf-8"), "keep")
        self.assertEqual([p.name for p in sentinel.parent.parent.iterdir()], ["hy-old"])

    def test_knowledge_freshness_compares_instants_not_timezone_text(self):
        self._project()
        target = self.tmp / "repo"
        target.mkdir()
        self._run(hy.cmd_link_add, self._link_args(target))
        self._run(hy.cmd_knowledge_init, argparse.Namespace(project="demo", force=False))
        index = hy.knowledge_index("demo")
        index["repos"]["repo"].update(files=["overview.md"], updated="2026-09-08T10:00:00+0800")
        hy.write_yaml_file(hy.knowledge_dir("demo") / "_index.yaml", index)
        with mock.patch.object(hy, "repo_last_commit", return_value="2026-09-08T03:00:00+00:00"):
            _, output = self._run(hy.cmd_knowledge_status, argparse.Namespace(project="demo"))
        self.assertIn("stale", output)

    def test_iteration_creation_rolls_back_when_binding_write_fails(self):
        self._project()
        with mock.patch.dict(os.environ, {"HY_SESSION_ID": "rollback-iteration"}, clear=True), \
                mock.patch.object(hy, "write_current_session", side_effect=OSError("injected failure")):
            with self.assertRaises(hy.HyError):
                self._run(hy.cmd_iter_new, argparse.Namespace(project="demo", title="Rollback",
                    type="feat", slug=None, iteration_id="260908-feat-rollback"))
            self.assertFalse(hy.current_session_path().exists())
        self.assertFalse((hy.WORKSPACE_ROOT / "demo/iterations/260908-feat-rollback").exists())

    def test_backend_app_paths_must_stay_relative_to_repository(self):
        for spec in ("app=../outside", "app=/outside", "app=C:\\outside", "app=..\\outside"):
            with self.assertRaises(hy.HyError):
                hy.parse_app_spec([spec])

    def test_knowledge_consumers_reject_malformed_nested_index(self):
        self._project()
        target = self.tmp / "repo"
        target.mkdir()
        self._run(hy.cmd_link_add, self._link_args(target))
        path = hy.knowledge_dir("demo") / "_index.yaml"
        for repos in (["invalid"], {"repo": []}, {"repo": {"files": "overview.md"}}):
            hy.write_yaml_file(path, {"project": "demo", "repos": repos})
            for argv in (["knowledge", "status", "--project", "demo"],
                         ["knowledge", "register", "--project", "demo", "--repo", "repo",
                          "--source", "bootstrap", "--file", "overview.md"]):
                rc, output = self._run(hy.main, argv)
                self.assertEqual(rc, 2, output)

    def test_release_ci_comments_do_not_count_as_validation_steps(self):
        root = self._release_copy()
        ci = root / ".github/workflows/ci.yml"
        ci.write_text("on: push\njobs:\n  smoke:\n    runs-on: ubuntu-latest\n"
                      "    steps:\n      - run: echo 'no validation'\n"
                      "# python -m unittest discover\n# python happlylong.py release-check\n", encoding="utf-8")
        rc, output = self._run(hy.cmd_release_check, argparse.Namespace())
        self.assertEqual(rc, 1, output)

    def test_release_requires_runtime_dependency(self):
        root = self._release_copy()
        (root / "requirements.txt").write_text("# empty\n", encoding="utf-8")
        rc, output = self._run(hy.cmd_release_check, argparse.Namespace())
        self.assertEqual(rc, 1, output)

    def test_release_rejects_unscannable_encoding(self):
        root = self._release_copy()
        fixture = root / "tests/encoded-fixture.yaml"
        fixture.write_bytes(("github_pat_" + "AUDIT_FIXTURE_" * 3).encode("utf-16"))
        rc, output = self._run(hy.cmd_release_check, argparse.Namespace())
        self.assertEqual(rc, 1, output)


if __name__ == "__main__":
    unittest.main()
