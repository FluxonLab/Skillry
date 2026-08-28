#!/usr/bin/env python3
"""Generate reproducible skill and agent component locks.

A skill checksum covers its complete component tree, including scripts,
references and assets. Symlinks are rejected.
"""
from __future__ import annotations

import hashlib
import json
import pathlib
import re
import sys

REPO = pathlib.Path(__file__).resolve().parents[1]
PLUGINS = REPO / "plugins"
COMMUNITY = REPO / "community"
REGISTRY = REPO / "registry"
APPLY = "--apply" in sys.argv
READ_ONLY_TOOLS = frozenset({"Read", "Glob", "Grep", "WebSearch", "WebFetch"})


def sha_file(path: pathlib.Path) -> str:
    if path.is_symlink() or not path.is_file():
        raise RuntimeError(f"lock input is not a regular file: {path}")
    return hashlib.sha256(path.read_bytes()).hexdigest()


def sha_tree(root: pathlib.Path) -> tuple[str, int]:
    if root.is_symlink() or not root.is_dir():
        raise RuntimeError(f"component root is not a regular directory: {root}")

    files = []
    for path in root.rglob("*"):
        if path.is_symlink():
            raise RuntimeError(f"component tree contains a symlink: {path}")
        if path.is_file():
            files.append(path)

    digest = hashlib.sha256()
    digest.update(b"skillry-component-tree-v1\0")
    for path in sorted(files, key=lambda item: item.relative_to(root).as_posix()):
        relative = path.relative_to(root).as_posix().encode("utf-8")
        content = path.read_bytes()
        digest.update(len(relative).to_bytes(4, "big"))
        digest.update(relative)
        digest.update(len(content).to_bytes(8, "big"))
        digest.update(content)
    return digest.hexdigest(), len(files)


def fm(text: str, key: str) -> str:
    match = re.search(rf"^{key}:\s*(.+)$", text, re.M)
    return match.group(1).strip().strip(chr(34) + chr(39)) if match else ""


def declared_tools(text: str) -> set[str]:
    return set(re.findall(r"[A-Za-z][A-Za-z0-9_-]*", fm(text, "tools")))


def permission(text: str) -> str:
    tools = declared_tools(text)
    return "read-only" if tools and tools <= READ_ONLY_TOOLS else "write"


def build_skills():
    items = []
    for skill_dir in sorted(PLUGINS.glob("*/skills/*")):
        skill_file = skill_dir / "SKILL.md"
        if not skill_file.exists():
            continue
        checksum, file_count = sha_tree(skill_dir)
        text = skill_file.read_text(encoding="utf-8")
        items.append(
            {
                "id": re.sub(r"^\d+-", "", skill_dir.name),
                "folder": skill_dir.name,
                "department": skill_dir.parent.parent.name,
                "origin": "original",
                "lines": len(text.splitlines()),
                "files": file_count,
                "checksum_scope": "component-tree-v1",
                "checksum": checksum,
            }
        )

    for skill_dir in sorted(COMMUNITY.glob("*/skills/*")):
        skill_file = skill_dir / "SKILL.md"
        if not skill_file.exists():
            continue
        checksum, file_count = sha_tree(skill_dir)
        items.append(
            {
                "id": skill_dir.name,
                "folder": skill_dir.name,
                "source": skill_dir.parent.parent.name,
                "origin": "community",
                "lines": len(
                    skill_file.read_text(encoding="utf-8").splitlines()
                ),
                "files": file_count,
                "checksum_scope": "component-tree-v1",
                "checksum": checksum,
            }
        )
    return items


def agent_record(agent_file: pathlib.Path, origin: str) -> dict:
    text = agent_file.read_text(encoding="utf-8")
    record = {
        "id": agent_file.stem,
        "origin": origin,
        "permission": permission(text),
        "permission_basis": "declared-tools-v1",
        "tools": fm(text, "tools"),
        "checksum": sha_file(agent_file),
    }
    if origin == "original":
        record["department"] = agent_file.parent.parent.name
    else:
        record["source"] = agent_file.parent.parent.name
    return record


def build_agents():
    items = [
        agent_record(agent_file, "original")
        for agent_file in sorted(PLUGINS.glob("*/agents/*.md"))
    ]
    items.extend(
        agent_record(agent_file, "community")
        for agent_file in sorted(COMMUNITY.glob("*/agents/*.md"))
    )
    return items


skills = build_skills()
agents = build_agents()
original_skills = [item for item in skills if item["origin"] == "original"]
community_skills = [item for item in skills if item["origin"] == "community"]
original_agents = [item for item in agents if item["origin"] == "original"]
community_agents = [item for item in agents if item["origin"] == "community"]

skill_lock = {
    "version": "0.2.0",
    "counts": {
        "original": len(original_skills),
        "community": len(community_skills),
        "total": len(skills),
    },
    "skills": skills,
}
agent_lock = {
    "version": "0.2.0",
    "counts": {
        "original": len(original_agents),
        "community": len(community_agents),
        "total": len(agents),
    },
    "agents": agents,
}

print(f"{'APPLY' if APPLY else 'DRY-RUN'} - lock")
print(
    f"  skills: {len(original_skills)} original + "
    f"{len(community_skills)} community = {len(skills)}"
)
print(
    f"  agents: {len(original_agents)} original + "
    f"{len(community_agents)} community = {len(agents)}"
)
read_only_count = sum(
    1 for item in original_agents if item["permission"] == "read-only"
)
print(
    f"  original agents read-only by declared tools: "
    f"{read_only_count}/{len(original_agents)}"
)

if APPLY:
    REGISTRY.mkdir(parents=True, exist_ok=True)
    (REGISTRY / "skill-lock.json").write_text(
        json.dumps(skill_lock, indent=2) + "\n", encoding="utf-8"
    )
    (REGISTRY / "agent-lock.json").write_text(
        json.dumps(agent_lock, indent=2) + "\n", encoding="utf-8"
    )
    print("\nWrote registry/skill-lock.json + registry/agent-lock.json")
else:
    for name, data in (
        ("skill-lock.json", skill_lock),
        ("agent-lock.json", agent_lock),
    ):
        path = REGISTRY / name
        if path.exists() and json.loads(path.read_text(encoding="utf-8")) != data:
            print(f"  DRIFT: {name} is out of date; run with --apply")
