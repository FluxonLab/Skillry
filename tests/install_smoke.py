#!/usr/bin/env python3
"""Install Skillry into a throwaway home and count what landed (CI smoke on Linux, macOS and Windows).

  python tests/install_smoke.py repo      install from this checkout: tools/install.py --apply
  python tests/install_smoke.py package   npm pack, unpack, then install with the packed CLI --apply

The throwaway home is set through both HOME and USERPROFILE: on Windows, Python's
Path.home() reads USERPROFILE, so HOME alone would install into the runner's real profile.
"""
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tarfile
import tempfile

ROOT = Path(__file__).resolve().parents[1]
ALL_TARGETS = ["claude", "codex", "copilot", "antigravity", "cursor"]
MIN_SKILLS = 50
MIN_AGENTS = 60


def target_table():
    """Each target's skill and agent folders, relative to the home folder."""
    spec = importlib.util.spec_from_file_location("skillry_install", ROOT / "tools" / "install.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    home = Path.home()
    return {name: {"skills": Path(t["skills"]).relative_to(home), "agents": Path(t["agents"]).relative_to(home),
                   "agent_ext": t["agent_ext"]}
            for name, t in module.TARGETS.items()}


def throwaway_env(home):
    env = dict(os.environ)
    env["HOME"] = str(home)
    env["USERPROFILE"] = str(home)
    return env


def count(home, table, targets):
    found = {}
    for name in targets:
        skills_dir = home / table[name]["skills"]
        agents_dir = home / table[name]["agents"]
        skills = len(list(skills_dir.glob("*/SKILL.md"))) if skills_dir.is_dir() else 0
        agents = 0
        if agents_dir.is_dir():
            agents = len(list(agents_dir.glob("*" + table[name]["agent_ext"])))
            agents += len(list(agents_dir.glob("*/agent.md")))
        found[name] = {"skills": skills, "agents": agents}
    return found


def check(found):
    low = {name: n for name, n in found.items() if n["skills"] < MIN_SKILLS or n["agents"] < MIN_AGENTS}
    print(json.dumps({"installed": found, "below_minimum": low}, indent=2))
    return 1 if low else 0


def run(argv, env, cwd=None):
    print("+", " ".join(str(a) for a in argv), flush=True)
    subprocess.run([str(a) for a in argv], env=env, cwd=cwd, check=True)


def from_repo(table):
    home = Path(tempfile.mkdtemp(prefix="skillry-home-"))
    run([sys.executable, ROOT / "tools" / "install.py", "--apply", "--targets", *ALL_TARGETS], throwaway_env(home))
    return check(count(home, table, ALL_TARGETS))


def from_package(table):
    npm = shutil.which("npm") or shutil.which("npm.cmd")
    node = shutil.which("node")
    if not npm or not node:
        print("npm and node are required for the package smoke test")
        return 1
    work = Path(tempfile.mkdtemp(prefix="skillry-pack-"))
    packed = subprocess.run([npm, "pack", "--pack-destination", str(work)], cwd=ROOT, check=True,
                            capture_output=True, text=True).stdout.strip().splitlines()[-1]
    with tarfile.open(work / packed) as archive:
        archive.extractall(work)
    cli = work / "package" / "bin" / "skillry.js"
    home = Path(tempfile.mkdtemp(prefix="skillry-home-"))
    env = throwaway_env(home)
    run([node, cli, "version"], env)
    run([node, cli, "install", "--apply", "--targets", "claude"], env)
    status = check(count(home, table, ["claude"]))
    storage = subprocess.run([node, cli, "storage", "--help"], env=env, capture_output=True, text=True)
    if os.name == "nt":
        answer = json.loads(storage.stdout or "{}")
        if answer.get("error", {}).get("code") != "unsupported_platform":
            print("storage on Windows did not answer unsupported_platform:", storage.stdout, storage.stderr)
            return 1
    elif storage.returncode != 0:
        print("storage --help failed:", storage.stdout, storage.stderr)
        return 1
    return status


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "repo"
    table = target_table()
    sys.exit(from_repo(table) if mode == "repo" else from_package(table))
