"""Copilot gets native custom agents: tool aliases, no Claude-only fields, read-only roles without shell."""
import glob
import importlib.util
import json
import pathlib
import sys
import unittest

sys.dont_write_bytecode = True
ROOT = pathlib.Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("copilot_installer", ROOT / "tools/install.py")
installer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(installer)

ALIASES = set(installer.COPILOT_TOOLS.values())


def agent(tools, extra=""):
    return f"---\nname: sample-agent\ndescription: Sample role.\ntools: {tools}\n{extra}---\n\nYou are a sample.\n"


def frontmatter(text):
    head = text.split("---\n")[1]
    fields = {}
    for line in head.splitlines():
        key, _, value = line.partition(": ")
        fields[key] = value
    return fields


class CopilotAgentTests(unittest.TestCase):
    def test_read_only_role_gets_no_shell_and_no_edit(self):
        text = installer.md_to_copilot_agent(agent("Read, Grep, Glob, Bash", "permissionMode: plan\n"))
        fields = frontmatter(text)
        self.assertEqual(json.loads(fields["tools"]), ["read", "search"])
        self.assertNotIn("permissionMode", text)
        self.assertNotIn("model", fields)

    def test_editing_role_keeps_edit_and_execute(self):
        tools = json.loads(frontmatter(installer.md_to_copilot_agent(
            agent("Read, Grep, Glob, Bash, Edit, Write, WebFetch")))["tools"])
        self.assertEqual(tools, ["read", "search", "edit", "execute", "web"])

    def test_claude_model_names_and_unknown_tools_are_left_out(self):
        text = installer.md_to_copilot_agent(agent("Read, NotebookEdit", "model: opus\n"))
        self.assertEqual(json.loads(frontmatter(text)["tools"]), ["read"])
        self.assertNotIn("opus", text)

    def test_every_shipped_agent_converts_to_known_aliases(self):
        files = sorted(glob.glob(str(ROOT / "plugins/*/agents/*.md")) + glob.glob(str(ROOT / "community/*/agents/*.md")))
        self.assertTrue(files)
        for path in files:
            source = pathlib.Path(path).read_text(encoding="utf-8")
            if not installer.SKILL_NAME.fullmatch(installer.fm_field(source, "name")):
                continue
            fields = frontmatter(installer.md_to_copilot_agent(source))
            self.assertTrue(set(json.loads(fields["tools"])) <= ALIASES, path)
            self.assertTrue(json.loads(fields["description"]), path)

    def test_target_writes_agent_md_files_in_the_copilot_format(self):
        cfg = installer.TARGETS["copilot"]
        self.assertEqual(cfg["agent_ext"], ".agent.md")
        self.assertEqual(cfg["agent_fmt"], "copilot")


if __name__ == "__main__":
    unittest.main()
