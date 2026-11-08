"""Install lifecycle: remembered selections, narrowing guard, list, doctor, uninstall and OpenCode agents.

Everything runs against the real library and a throwaway home; no real home is touched.
"""
import contextlib
import importlib.util
import io
import json
import pathlib
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.dont_write_bytecode = True
ROOT = pathlib.Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("lifecycle_installer", ROOT / "tools/install.py")
installer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(installer)


def agent(tools, extra=""):
    return f"---\nname: sample-agent\ndescription: Sample role.\ntools: {tools}\n{extra}---\n\nYou are a sample.\n"


class OpenCodeAgentTests(unittest.TestCase):
    def test_read_only_role_denies_edit_and_shell(self):
        text = installer.md_to_opencode_agent(agent("Read, Grep, Glob, Bash", "permissionMode: plan\n"))
        self.assertIn("mode: subagent\n", text)
        for action in ("edit", "bash", "webfetch", "websearch"):
            self.assertIn(f"  {action}: deny\n", text)
        self.assertNotIn("tools:", text)

    def test_editing_role_keeps_edit_and_shell(self):
        text = installer.md_to_opencode_agent(agent("Read, Grep, Glob, Bash, Edit, Write"))
        self.assertNotIn("edit: deny", text)
        self.assertNotIn("bash: deny", text)
        self.assertIn("  webfetch: deny\n", text)

    def test_target_points_at_opencode_folders(self):
        cfg = installer.TARGETS["opencode"]
        self.assertEqual(cfg["skills"], installer.HOME / ".config/opencode/skills")
        self.assertEqual(cfg["agents"], installer.HOME / ".config/opencode/agents")


class LifecycleTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.home = pathlib.Path(self.tmp.name).resolve()
        targets = {
            name: {**cfg,
                   "skills": self.home / cfg["skills"].relative_to(installer.HOME),
                   "agents": self.home / cfg["agents"].relative_to(installer.HOME),
                   **({"legacy_roots": tuple(self.home / root.relative_to(installer.HOME)
                                             for root in cfg["legacy_roots"])}
                      if "legacy_roots" in cfg else {})}
            for name, cfg in installer.TARGETS.items()
        }
        self.patches = [patch.object(installer, "HOME", self.home),
                        patch.object(installer, "MANIFEST_ROOT", self.home / ".skillry/manifests"),
                        patch.object(installer, "TARGETS", targets)]
        for item in self.patches:
            item.start()
        self.claude_skills = self.home / ".claude/skills"
        self.claude_agents = self.home / ".claude/agents"

    def tearDown(self):
        for item in self.patches:
            item.stop()
        self.tmp.cleanup()

    def run_main(self, *argv):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = installer.main(list(argv))
        return code, out.getvalue()

    def selections(self):
        return json.loads((self.home / ".skillry/manifests/selection.json").read_text())["targets"]

    def test_selection_is_remembered_and_a_second_install_changes_nothing(self):
        self.run_main("--apply", "--targets", "claude", "--departments", "security")
        installed = sorted(p.name for p in self.claude_skills.iterdir())
        self.assertTrue(installed)
        self.assertTrue(all(name in {"security-and-secrets-review", "ai-security-review",
                                     "dependency-supply-chain-review"} for name in installed), installed)
        self.assertEqual(self.selections()["claude"]["departments"], ["security"])
        code, out = self.run_main("--apply", "--targets", "claude")
        self.assertEqual(code, 0)
        self.assertIn("write:0 remove:0", out)

    def test_narrowing_needs_allow_removal(self):
        self.run_main("--apply", "--targets", "claude", "--departments", "security", "core-operations")
        with self.assertRaises(installer.SafetyError):
            self.run_main("--apply", "--targets", "claude", "--departments", "security")
        self.assertTrue((self.claude_skills / "repo-diagnostics").is_dir())
        self.run_main("--apply", "--targets", "claude", "--departments", "security", "--allow-removal")
        self.assertFalse((self.claude_skills / "repo-diagnostics").exists())

    def test_departments_and_skills_together_install_both(self):
        self.run_main("--apply", "--targets", "claude", "--departments", "core-operations",
                      "--skills", "security-and-secrets-review")
        skills = {p.name for p in self.claude_skills.iterdir()}
        self.assertIn("security-and-secrets-review", skills)
        self.assertIn("repo-diagnostics", skills)
        self.assertNotIn("ai-security-review", skills)
        agents = sorted(p.stem for p in self.claude_agents.iterdir())
        self.assertEqual(agents, ["agent-governance-officer", "chief-architect",
                                  "system-orchestrator", "workflow-dispatcher"])

    def test_naming_skills_replaces_the_remembered_departments(self):
        self.run_main("--apply", "--targets", "claude", "--departments", "security")
        self.run_main("--apply", "--targets", "claude", "--skills", "repo-diagnostics", "--allow-removal")
        selection = self.selections()["claude"]
        self.assertIsNone(selection["departments"])
        self.assertEqual(selection["skills"], ["repo-diagnostics"])
        self.assertEqual(sorted(p.name for p in self.claude_skills.iterdir()), ["repo-diagnostics"])

    def test_community_choice_is_inferred_for_installs_made_before_selections_existed(self):
        self.run_main("--apply", "--targets", "claude", "--community")
        (self.home / ".skillry/manifests/selection.json").unlink()
        code, out = self.run_main("--targets", "claude")
        self.assertIn("selection: community", out)
        self.assertIn("remove:0", out)

    def test_doctor_reports_a_locally_changed_file(self):
        self.run_main("--apply", "--targets", "claude", "--departments", "security")
        code, _ = self.run_main("--doctor")
        self.assertEqual(code, 0)
        changed = next(self.claude_skills.glob("*/SKILL.md"))
        changed.write_text(changed.read_text() + "\nlocal note\n")
        code, out = self.run_main("--doctor")
        self.assertEqual(code, 1)
        self.assertIn("1 changed locally", out)

    def test_uninstall_removes_unchanged_files_and_keeps_local_changes(self):
        self.run_main("--apply", "--targets", "claude", "--departments", "security")
        changed = next(self.claude_skills.glob("*/SKILL.md"))
        changed.write_text("my own notes\n")
        code, out = self.run_main("--uninstall", "--targets", "claude")
        self.assertIn("WOULD REMOVE", out)
        self.assertTrue((self.home / ".skillry/manifests/claude.json").exists())
        self.run_main("--uninstall", "--targets", "claude", "--apply")
        self.assertTrue(changed.exists())
        remaining = [p for p in self.claude_skills.rglob("*") if p.is_file()]
        self.assertEqual(remaining, [changed])
        self.assertFalse(self.claude_agents.exists() and any(self.claude_agents.iterdir()))
        self.assertFalse((self.home / ".skillry/manifests/claude.json").exists())
        self.assertNotIn("claude", self.selections())

    def test_list_shows_departments_and_installed_targets(self):
        self.run_main("--apply", "--targets", "opencode", "--skills", "repo-diagnostics", "--no-agents")
        code, out = self.run_main("--list", "--json")
        data = json.loads(out)
        self.assertIn("security", data["departments"])
        self.assertEqual(data["installed"]["opencode"]["selection"]["skills"], ["repo-diagnostics"])
        self.assertTrue((self.home / ".config/opencode/skills/repo-diagnostics/SKILL.md").is_file())
        self.assertFalse((self.home / ".config/opencode/agents").exists())

    def test_unknown_names_are_refused(self):
        with self.assertRaises(installer.SafetyError):
            self.run_main("--targets", "claude", "--departments", "no-such-department")
        with self.assertRaises(installer.SafetyError):
            self.run_main("--targets", "claude", "--skills", "no-such-skill")


if __name__ == "__main__":
    unittest.main()
