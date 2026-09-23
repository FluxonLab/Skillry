"""Native Cursor format and isolated portable-install contract; no real home writes."""
import importlib.util
import pathlib
import tempfile
import unittest
from unittest.mock import patch

ROOT = pathlib.Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("cursor_installer", ROOT / "tools/install.py")
installer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(installer)


class CursorInstallTests(unittest.TestCase):
    def test_native_frontmatter_preserves_read_only_intent_with_bash(self):
        source = ('---\nname: api-reviewer\ndescription: Review API contracts.\n'
                  'model: sonnet\npermissionMode: plan\ntools: Read, Bash\n---\n\nReview only.\n')
        converted = installer.md_to_cursor_agent(source)
        self.assertEqual(installer.fm_field(converted, "name"), "api-reviewer")
        self.assertEqual(installer.fm_field(converted, "model"), "inherit")
        self.assertEqual(installer.fm_field(converted, "readonly"), "true")
        self.assertNotIn("permissionMode:", converted)
        self.assertNotIn("tools:", converted)
        self.assertTrue(converted.endswith("Review only.\n"))
        self.assertIn("readonly: false", installer.md_to_cursor_agent(
            source.replace("permissionMode: plan", "permissionMode: default").replace("Read, Bash", "Read, Edit, Write")))
        self.assertIn("readonly: true", installer.md_to_cursor_agent(
            source.replace("permissionMode: plan\n", "").replace("Read, Bash", "Read, Glob, Grep")))

    def test_native_target_preview_install_and_local_edit_preservation(self):
        self.assertEqual(installer.TARGETS["cursor"]["agent_fmt"], "cursor")
        with tempfile.TemporaryDirectory() as name:
            home = pathlib.Path(name).resolve()
            repo = home / "repo"
            skill = repo / "skills/example"
            skill.mkdir(parents=True)
            (skill / "SKILL.md").write_text("---\nname: example\ndescription: Example.\n---\nBody.\n")
            agent = repo / "example-reviewer.md"
            agent.write_text("---\nname: example-reviewer\ndescription: Review.\npermissionMode: plan\n---\nReview only.\n")
            cfg = {**installer.TARGETS["cursor"], "skills": home / ".cursor/skills", "agents": home / ".cursor/agents"}
            with patch.object(installer, "HOME", home), patch.object(installer, "REPO", repo), \
                    patch.object(installer, "MANIFEST_ROOT", home / ".skillry/manifests"):
                def plan():
                    return installer.build_target_plan("cursor", cfg, [(skill, "example")], [agent], {})
                preview = plan()
                self.assertFalse((home / ".cursor").exists())
                installer.apply_target_plan(preview)
                self.assertTrue((home / ".cursor/skills/example/SKILL.md").is_file())
                installed_agent = home / ".cursor/agents/example-reviewer.md"
                self.assertIn("readonly: true", installed_agent.read_text())
                self.assertTrue((home / ".skillry/manifests/cursor.json").is_file())
                self.assertEqual(plan()["writes"], [])
                self.assertFalse((home / "AGENTS.md").exists())
                installed_agent.write_text("Owner edit")
                with self.assertRaises(installer.SafetyError):
                    plan()
                self.assertEqual(installed_agent.read_text(), "Owner edit")


if __name__ == "__main__":
    unittest.main()
