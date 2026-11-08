"""Antigravity installs into ~/.gemini/config with native agents and moves off the legacy folders."""
import glob
import hashlib
import importlib.util
import json
import pathlib
import tempfile
import unittest
from unittest.mock import patch

ROOT = pathlib.Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("antigravity_installer", ROOT / "tools/install.py")
installer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(installer)

KNOWN = {tool for names in installer.ANTIGRAVITY_TOOLS.values() for tool in names}


def agent(tools, extra=""):
    return f"---\nname: sample-agent\ndescription: Sample role.\ntools: {tools}\n{extra}---\n\nYou are a sample.\n"


def frontmatter_tools(text):
    head = text.split("---\n")[1]
    return [line[4:] for line in head.splitlines() if line.startswith("  - ")]


class AntigravityAgentFormatTests(unittest.TestCase):
    def test_read_only_role_gets_read_tools_and_no_commands(self):
        text = installer.md_to_antigravity_agent(agent("Read, Grep, Glob, Bash", "permissionMode: plan\n"))
        self.assertEqual(frontmatter_tools(text), ["view_file", "grep_search", "find_by_name", "list_dir"])
        self.assertIn("commandExecutionPolicy: off\n", text)
        self.assertIn("subagent: true\n", text)
        self.assertIn("mainAgent: false\n", text)

    def test_editing_role_gets_edit_tools_and_a_sandbox(self):
        tools = frontmatter_tools(installer.md_to_antigravity_agent(agent("Read, Grep, Glob, Bash, Edit, Write")))
        for name in ("replace_file_content", "multi_replace_file_content", "write_to_file", "run_command"):
            self.assertIn(name, tools)
        self.assertIn("commandExecutionPolicy: sandbox\n",
                      installer.md_to_antigravity_agent(agent("Read, Bash")))

    def test_unknown_claude_tools_are_dropped(self):
        tools = frontmatter_tools(installer.md_to_antigravity_agent(agent("Read, NotebookEdit, Task")))
        self.assertEqual(tools, ["view_file"])

    def test_every_shipped_agent_uses_only_known_tool_names(self):
        files = sorted(glob.glob(str(ROOT / "plugins/*/agents/*.md")))
        self.assertTrue(files)
        for path in files:
            text = installer.md_to_antigravity_agent(pathlib.Path(path).read_text(encoding="utf-8"))
            self.assertTrue(set(frontmatter_tools(text)) <= KNOWN, path)

    def test_target_points_at_the_current_personal_folders(self):
        cfg = installer.TARGETS["antigravity"]
        home = installer.HOME
        self.assertEqual(cfg["skills"], home / ".gemini/config/skills")
        self.assertEqual(cfg["agents"], home / ".gemini/config/agents")
        self.assertEqual(cfg["agent_fmt"], "antigravity")


class AntigravityLegacyMigrationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.home = pathlib.Path(self.tmp.name).resolve()
        self.repo = self.home / "repo"
        folder = self.repo / "skills" / "alpha"
        folder.mkdir(parents=True)
        (folder / "SKILL.md").write_text("---\nname: alpha\ndescription: alpha.\n---\nBody.\n")
        self.skills = [(folder, "alpha")]
        self.cfg = {**installer.TARGETS["antigravity"],
                    "skills": self.home / ".gemini/config/skills",
                    "agents": self.home / ".gemini/config/agents",
                    "legacy_roots": (self.home / ".gemini/antigravity/skills",
                                     self.home / ".gemini/antigravity/agents")}
        self.patches = [patch.object(installer, "HOME", self.home), patch.object(installer, "REPO", self.repo),
                        patch.object(installer, "MANIFEST_ROOT", self.home / ".skillry/manifests")]
        for item in self.patches:
            item.start()
        self.legacy_skill = self.home / ".gemini/antigravity/skills/alpha/SKILL.md"
        self.legacy_skill.parent.mkdir(parents=True)
        self.legacy_skill.write_text("old skill\n")
        manifest = self.home / ".skillry/manifests/antigravity.json"
        manifest.parent.mkdir(parents=True)
        manifest.write_text(json.dumps({
            "schema_version": installer.MANIFEST_VERSION, "target": "antigravity",
            "files": [{"path": str(self.legacy_skill),
                       "sha256": hashlib.sha256(b"old skill\n").hexdigest()}]}))

    def tearDown(self):
        for item in self.patches:
            item.stop()
        self.tmp.cleanup()

    def plan(self):
        return installer.build_target_plan("antigravity", self.cfg, self.skills, [], {})

    def test_unchanged_legacy_files_are_removed_and_their_folders_pruned(self):
        plan = self.plan()
        self.assertIn(self.legacy_skill, plan["removals"])
        installer.apply_target_plan(plan)
        self.assertFalse(self.legacy_skill.exists())
        self.assertFalse(self.legacy_skill.parent.exists())
        self.assertTrue((self.home / ".gemini/antigravity/skills").is_dir())
        self.assertTrue((self.home / ".gemini/config/skills/alpha/SKILL.md").is_file())
        recorded = json.loads((self.home / ".skillry/manifests/antigravity.json").read_text())
        self.assertNotIn(str(self.legacy_skill), [entry["path"] for entry in recorded["files"]])

    def test_a_locally_modified_legacy_file_stops_the_install(self):
        self.legacy_skill.write_text("edited by the user\n")
        with self.assertRaises(installer.SafetyError):
            self.plan()
        self.assertTrue(self.legacy_skill.exists())


if __name__ == "__main__":
    unittest.main()
