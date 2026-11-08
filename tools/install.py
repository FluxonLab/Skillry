#!/usr/bin/env python3
"""Install verified Skillry platform skills and agents.

Dry-run is the default. Nothing is written without --apply. Project instruction
files are never managed by this installer.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import pathlib
import re
import stat
import sys
import tempfile

REPO = pathlib.Path(__file__).resolve().parents[1]
PLUGINS = REPO / "plugins"
COMMUNITY = REPO / "community"
REGISTRY = REPO / "registry"
HOME = pathlib.Path.home().resolve()
MANIFEST_ROOT = HOME / ".skillry/manifests"
LOCK_VERSION = "0.2.0"
MANIFEST_VERSION = 1

TARGETS = {
    "claude": {
        "skills": HOME / ".claude/skills",
        "agents": HOME / ".claude/agents",
        "agent_ext": ".md",
        "agent_fmt": "md",
    },
    "codex": {
        "skills": HOME / ".codex/skills",
        "agents": HOME / ".codex/agents",
        "agent_ext": ".toml",
        "agent_fmt": "toml",
    },
    "cursor": {
        "skills": HOME / ".cursor/skills",
        "agents": HOME / ".cursor/agents",
        "agent_ext": ".md",
        "agent_fmt": "cursor",
    },
    "copilot": {
        "skills": HOME / ".copilot/skills",
        "agents": HOME / ".copilot/agents",
        "agent_ext": ".agent.md",
        "agent_fmt": "md",
    },
    "opencode": {
        # OpenCode reads personal skills from ~/.config/opencode/skills and agents from
        # ~/.config/opencode/agents (opencode.ai/docs/skills, opencode.ai/docs/agents).
        "skills": HOME / ".config/opencode/skills",
        "agents": HOME / ".config/opencode/agents",
        "agent_ext": ".md",
        "agent_fmt": "opencode",
    },
    "antigravity": {
        # The current Antigravity app and CLI read personal skills and agents from
        # ~/.gemini/config (antigravity.google/docs/extend/customization-discovery).
        "skills": HOME / ".gemini/config/skills",
        "agents": HOME / ".gemini/config/agents",
        "agent_ext": ".md",
        "agent_fmt": "antigravity",
        # Earlier releases installed here; unchanged files Skillry put there are removed
        # on the next install, locally modified ones stop the install with a message.
        "legacy_roots": (
            HOME / ".gemini/antigravity/skills",
            HOME / ".gemini/antigravity/agents",
        ),
    },
}

READ_ONLY_TOOLS = frozenset({"Read", "Glob", "Grep", "WebSearch", "WebFetch"})
# Antigravity agent tool names, checked against agy 1.5.3 (8 Nov 2026). An unknown name stops
# the agent ("tool not found in registry"), so only these names are ever written.
ANTIGRAVITY_TOOLS = {
    "Read": ("view_file",),
    "Grep": ("grep_search",),
    "Glob": ("find_by_name", "list_dir"),
    "WebSearch": ("search_web",),
    "WebFetch": ("read_url_content",),
    "Edit": ("replace_file_content", "multi_replace_file_content"),
    "MultiEdit": ("multi_replace_file_content",),
    "Write": ("write_to_file",),
    "Bash": ("run_command",),
}
ANTIGRAVITY_READ_ONLY = frozenset(
    {"view_file", "grep_search", "find_by_name", "list_dir", "search_web", "read_url_content"}
)
SKILL_NAME = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
AGENT_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]*$")
SHA256 = re.compile(r"^[0-9a-f]{64}$")


class SafetyError(RuntimeError):
    """Raised when verification or a filesystem trust boundary fails."""


def _lexical(path: pathlib.Path) -> pathlib.Path:
    return pathlib.Path(os.path.abspath(os.fspath(path.expanduser())))


def _relative(path: pathlib.Path, root: pathlib.Path) -> pathlib.Path:
    try:
        return path.relative_to(root)
    except ValueError as exc:
        raise SafetyError(f"path escapes allowed root: {path} (root: {root})") from exc


def _reject_symlink_components(path: pathlib.Path, anchor: pathlib.Path) -> None:
    path = _lexical(path)
    anchor = _lexical(anchor)
    rel = _relative(path, anchor)
    current = anchor
    if current.is_symlink():
        raise SafetyError(f"symlink root is not allowed: {current}")
    for index, part in enumerate(rel.parts):
        current = current / part
        if current.is_symlink():
            raise SafetyError(f"symlink path component is not allowed: {current}")
        if (
            index < len(rel.parts) - 1
            and current.exists()
            and not current.is_dir()
        ):
            raise SafetyError(f"path component is not a directory: {current}")


def safe_source_file(path: pathlib.Path, root: pathlib.Path) -> pathlib.Path:
    root = root.resolve(strict=True)
    path = _lexical(path)
    _relative(path, root)
    _reject_symlink_components(path, root)
    try:
        resolved = path.resolve(strict=True)
    except FileNotFoundError as exc:
        raise SafetyError(f"source file is missing: {path}") from exc
    _relative(resolved, root)
    if not path.is_file():
        raise SafetyError(f"source is not a regular file: {path}")
    return path


def source_tree_files(root: pathlib.Path) -> list[pathlib.Path]:
    root = _lexical(root)
    if root.is_symlink() or not root.is_dir():
        raise SafetyError(f"component root is not a regular directory: {root}")
    files = []
    for path in root.rglob("*"):
        if path.is_symlink():
            raise SafetyError(f"component tree contains a symlink: {path}")
        # Bytecode caches from running a skill's script in place are neither verified nor installed.
        if "__pycache__" in path.relative_to(root).parts or path.suffix in (".pyc", ".pyo"):
            continue
        if path.is_file():
            safe_source_file(path, REPO)
            files.append(path)
    return sorted(files, key=lambda item: item.relative_to(root).as_posix())


def prepare_target_root(root: pathlib.Path) -> pathlib.Path:
    root = _lexical(root)
    _relative(root, HOME)
    _reject_symlink_components(root, HOME)
    if root.exists() and not root.is_dir():
        raise SafetyError(f"target root is not a directory: {root}")
    return root


def safe_destination(
    path: pathlib.Path, root: pathlib.Path, anchor: pathlib.Path
) -> pathlib.Path:
    path = _lexical(path)
    root = _lexical(root)
    anchor = _lexical(anchor)
    _relative(root, anchor)
    if path == root:
        raise SafetyError(f"destination must be below target root: {path}")
    _relative(path, root)
    _reject_symlink_components(root, anchor)
    if root.exists() and not root.is_dir():
        raise SafetyError(f"target root is not a directory: {root}")
    _reject_symlink_components(path, root)
    if path.exists():
        if not path.is_file():
            raise SafetyError(f"destination is not a regular file: {path}")
        if path.lstat().st_nlink > 1:
            raise SafetyError(f"hardlinked destination is not allowed: {path}")
    return path


def fm_field(text: str, key: str) -> str:
    match = re.search(rf"^{key}:\s*(.+)$", text, re.M)
    return (
        match.group(1).strip().strip(chr(34) + chr(39))
        if match
        else ""
    )


def declared_tools(text: str) -> set[str]:
    return set(
        re.findall(r"[A-Za-z][A-Za-z0-9_-]*", fm_field(text, "tools"))
    )


def has_read_only_tools(text: str) -> bool:
    tools = declared_tools(text)
    return bool(tools) and tools <= READ_ONLY_TOOLS


def skill_identity(skill_dir: pathlib.Path) -> str:
    text = safe_source_file(skill_dir / "SKILL.md", REPO).read_text(
        encoding="utf-8"
    )
    name = fm_field(text, "name")
    if not SKILL_NAME.fullmatch(name):
        raise SafetyError(
            f"invalid Agent Skills name in {skill_dir / 'SKILL.md'}: {name!r}"
        )
    return name


def agent_identity(agent_file: pathlib.Path) -> str:
    text = safe_source_file(agent_file, REPO).read_text(encoding="utf-8")
    name = fm_field(text, "name")
    if not AGENT_ID.fullmatch(name):
        raise SafetyError(f"invalid agent name in {agent_file}: {name!r}")
    return name


def sha_bytes(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def sha_file(path: pathlib.Path) -> str:
    path = safe_source_file(path, REPO)
    return sha_bytes(path.read_bytes())


def sha_tree(root: pathlib.Path) -> str:
    digest = hashlib.sha256()
    digest.update(b"skillry-component-tree-v1\0")
    for path in source_tree_files(root):
        relative = path.relative_to(root).as_posix().encode("utf-8")
        content = path.read_bytes()
        digest.update(len(relative).to_bytes(4, "big"))
        digest.update(relative)
        digest.update(len(content).to_bytes(8, "big"))
        digest.update(content)
    return digest.hexdigest()


def load_lock(name: str, collection: str) -> list[dict]:
    path = safe_source_file(REGISTRY / name, REPO)
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SafetyError(f"invalid lock JSON: {path}: {exc}") from exc
    if data.get("version") != LOCK_VERSION:
        raise SafetyError(
            f"{name} version is {data.get('version')!r}; "
            f"expected {LOCK_VERSION}. Regenerate the reviewed lock."
        )
    items = data.get(collection)
    if not isinstance(items, list):
        raise SafetyError(f"{name} has no {collection} list")
    return items


def skill_lock_key(entry: dict) -> tuple[str, str, str]:
    origin = entry.get("origin", "")
    owner = (
        entry.get("department", "")
        if origin == "original"
        else entry.get("source", "")
    )
    return origin, owner, entry.get("folder", "")


def agent_lock_key(entry: dict) -> tuple[str, str, str]:
    origin = entry.get("origin", "")
    owner = (
        entry.get("department", "")
        if origin == "original"
        else entry.get("source", "")
    )
    return origin, owner, entry.get("id", "")


def skill_source_key(skill_dir: pathlib.Path) -> tuple[str, str, str]:
    if PLUGINS in skill_dir.parents:
        return "original", skill_dir.parent.parent.name, skill_dir.name
    return "community", skill_dir.parent.parent.name, skill_dir.name


def agent_source_key(agent_file: pathlib.Path) -> tuple[str, str, str]:
    if PLUGINS in agent_file.parents:
        return "original", agent_file.parent.parent.name, agent_file.stem
    return "community", agent_file.parent.parent.name, agent_file.stem


def verified_components(with_community: bool):
    skill_entries = {
        skill_lock_key(entry): entry
        for entry in load_lock("skill-lock.json", "skills")
    }
    agent_entries = {
        agent_lock_key(entry): entry
        for entry in load_lock("agent-lock.json", "agents")
    }

    skill_dirs = sorted(PLUGINS.glob("*/skills/*"))
    agent_files = sorted(PLUGINS.glob("*/agents/*.md"))
    if with_community:
        skill_dirs += sorted(COMMUNITY.glob("*/skills/*"))
        agent_files += sorted(COMMUNITY.glob("*/agents/*.md"))

    skills = []
    seen_skill_names: dict[str, pathlib.Path] = {}
    for skill_dir in skill_dirs:
        source_tree_files(skill_dir)
        name = skill_identity(skill_dir)
        if name in seen_skill_names:
            raise SafetyError(
                f"skill name collision: {name}: "
                f"{seen_skill_names[name]} and {skill_dir}"
            )
        seen_skill_names[name] = skill_dir

        key = skill_source_key(skill_dir)
        entry = skill_entries.get(key)
        if not entry:
            raise SafetyError(f"skill is missing from lock: {key}")
        if entry.get("checksum_scope") != "component-tree-v1":
            raise SafetyError(f"skill lock has wrong checksum scope: {key}")
        actual = sha_tree(skill_dir)
        if actual != entry.get("checksum"):
            raise SafetyError(f"skill checksum mismatch: {key}")
        skills.append((skill_dir, name))

    agents = []
    seen_agent_ids: dict[str, pathlib.Path] = {}
    for agent_file in agent_files:
        identity = agent_identity(agent_file)
        output_id = agent_file.stem
        if identity != output_id:
            raise SafetyError(
                f"agent filename and name differ: {agent_file}: {identity!r}"
            )
        if output_id in seen_agent_ids:
            raise SafetyError(
                f"agent ID collision: {output_id}: "
                f"{seen_agent_ids[output_id]} and {agent_file}"
            )
        seen_agent_ids[output_id] = agent_file

        key = agent_source_key(agent_file)
        entry = agent_entries.get(key)
        if not entry:
            raise SafetyError(f"agent is missing from lock: {key}")
        if sha_file(agent_file) != entry.get("checksum"):
            raise SafetyError(f"agent checksum mismatch: {key}")
        agents.append(agent_file)

    return skills, agents


def toml_string(value: str) -> str:
    return json.dumps(value, ensure_ascii=False)


def md_to_toml_agent(text: str) -> str:
    name = fm_field(text, "name").replace("-", "_")
    description = re.sub(r"\s+", " ", fm_field(text, "description"))
    body = re.sub(
        r"^---\n.*?\n---\n", "", text, count=1, flags=re.S
    ).strip()
    readonly = fm_field(text, "permissionMode") == "plan" or has_read_only_tools(text)
    sandbox = "read-only" if readonly else "workspace-write"
    return (
        f"name = {toml_string(name)}\n"
        f"description = {toml_string(description)}\n"
        'model_reasoning_effort = "medium"\n'
        f"sandbox_mode = {toml_string(sandbox)}\n"
        f"developer_instructions = {toml_string(body)}\n"
    )


def md_to_cursor_agent(text: str) -> str:
    """Translate role intent to Cursor's native schema, not Claude-only fields."""
    name = fm_field(text, "name")
    if not SKILL_NAME.fullmatch(name):
        raise SafetyError(f"invalid Cursor agent name: {name!r}")
    description = re.sub(r"\s+", " ", fm_field(text, "description"))
    body = re.sub(r"^---\n.*?\n---\n", "", text, count=1, flags=re.S).strip()
    readonly = fm_field(text, "permissionMode") == "plan" or has_read_only_tools(text)
    return (
        "---\n"
        f"name: {name}\n"
        f"description: {json.dumps(description, ensure_ascii=False)}\n"
        "model: inherit\n"
        f"readonly: {'true' if readonly else 'false'}\n"
        "---\n\n"
        f"{body}\n"
    )


def md_to_antigravity_agent(text: str) -> str:
    """Translate a role to Antigravity's native agent schema with a verified tool list."""
    name = fm_field(text, "name")
    if not SKILL_NAME.fullmatch(name):
        raise SafetyError(f"invalid Antigravity agent name: {name!r}")
    description = re.sub(r"\s+", " ", fm_field(text, "description"))
    body = re.sub(r"^---\n.*?\n---\n", "", text, count=1, flags=re.S).strip()
    readonly = fm_field(text, "permissionMode") == "plan" or has_read_only_tools(text)
    declared = declared_tools(text)
    tools: list[str] = []
    for claude_tool, native in ANTIGRAVITY_TOOLS.items():
        if claude_tool in declared:
            tools.extend(tool for tool in native if tool not in tools)
    if readonly:
        tools = [tool for tool in tools if tool in ANTIGRAVITY_READ_ONLY]
    policy = "sandbox" if "run_command" in tools else "off"
    tool_lines = "".join(f"  - {tool}\n" for tool in tools) if tools else ""
    return (
        "---\n"
        f"name: {name}\n"
        f"description: {json.dumps(description, ensure_ascii=False)}\n"
        + ("tools:\n" + tool_lines if tools else "tools: []\n")
        + "mcpServers: []\n"
        "mainAgent: false\n"
        "subagent: true\n"
        "model: inherit\n"
        f"commandExecutionPolicy: {policy}\n"
        "---\n\n"
        f"{body}\n"
    )


def md_to_opencode_agent(text: str) -> str:
    """Translate a role to an OpenCode agent: description, subagent mode, least-privilege rules.

    The `permission` map is the format OpenCode 1.19 applies (checked with `opencode debug
    agent`); 1.19 ignores the V2 `permissions` list, and V2 still reads this map.
    """
    name = fm_field(text, "name")
    if not SKILL_NAME.fullmatch(name):
        raise SafetyError(f"invalid OpenCode agent name: {name!r}")
    description = re.sub(r"\s+", " ", fm_field(text, "description"))
    body = re.sub(r"^---\n.*?\n---\n", "", text, count=1, flags=re.S).strip()
    readonly = fm_field(text, "permissionMode") == "plan" or has_read_only_tools(text)
    declared = declared_tools(text)
    denied = []
    if readonly or not declared & {"Edit", "Write", "MultiEdit"}:
        denied.append("edit")
    if readonly or "Bash" not in declared:
        denied.append("bash")
    if "WebFetch" not in declared:
        denied.append("webfetch")
    if "WebSearch" not in declared:
        denied.append("websearch")
    rules = "".join(f"  {action}: deny\n" for action in denied)
    return (
        "---\n"
        f"description: {json.dumps(description, ensure_ascii=False)}\n"
        "mode: subagent\n"
        + ("permission:\n" + rules if rules else "")
        + "---\n\n"
        f"{body}\n"
    )


def manifest_location(target: str) -> pathlib.Path:
    root = _lexical(MANIFEST_ROOT)
    _relative(root, HOME)
    _reject_symlink_components(root, HOME)
    if root.exists() and not root.is_dir():
        raise SafetyError(f"manifest root is not a directory: {root}")
    return safe_destination(root / f"{target}.json", root, HOME)


def managed_root(
    path: pathlib.Path, roots: tuple[pathlib.Path, ...]
) -> pathlib.Path:
    matches = []
    for root in roots:
        try:
            relative = path.relative_to(root)
        except ValueError:
            continue
        if relative.parts:
            matches.append(root)
    if len(matches) != 1:
        raise SafetyError(
            f"managed path is outside or ambiguous for target roots: {path}"
        )
    return matches[0]


def _unique_json_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key!r}")
        result[key] = value
    return result


def load_manifest(
    target: str, roots: tuple[pathlib.Path, ...]
) -> tuple[pathlib.Path, dict[pathlib.Path, str], bool]:
    path = manifest_location(target)
    if not path.exists():
        return path, {}, False

    try:
        raw = path.read_bytes()
        data = json.loads(
            raw.decode("utf-8"),
            object_pairs_hook=_unique_json_object,
        )
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
        raise SafetyError(f"malformed managed-state manifest {path}: {exc}") from exc

    if not isinstance(data, dict) or set(data) != {
        "schema_version",
        "target",
        "files",
    }:
        raise SafetyError(f"malformed managed-state manifest structure: {path}")
    if (
        type(data["schema_version"]) is not int
        or data["schema_version"] != MANIFEST_VERSION
    ):
        raise SafetyError(
            f"unsupported managed-state manifest version in {path}: "
            f"{data['schema_version']!r}"
        )
    if data["target"] != target:
        raise SafetyError(
            f"managed-state manifest target mismatch in {path}: "
            f"{data['target']!r}"
        )
    if not isinstance(data["files"], list):
        raise SafetyError(f"managed-state manifest files must be a list: {path}")

    managed: dict[pathlib.Path, str] = {}
    for index, item in enumerate(data["files"]):
        if not isinstance(item, dict) or set(item) != {"path", "sha256"}:
            raise SafetyError(
                f"malformed managed-state entry {index} in {path}"
            )
        raw_path = item["path"]
        digest = item["sha256"]
        if (
            not isinstance(raw_path, str)
            or not raw_path
            or "\0" in raw_path
            or not pathlib.Path(raw_path).is_absolute()
        ):
            raise SafetyError(
                f"invalid managed path at entry {index} in {path}: "
                f"{raw_path!r}"
            )
        normalized = _lexical(pathlib.Path(raw_path))
        if os.fspath(normalized) != raw_path:
            raise SafetyError(
                f"managed path is not normalized at entry {index} in {path}: "
                f"{raw_path!r}"
            )
        if not isinstance(digest, str) or not SHA256.fullmatch(digest):
            raise SafetyError(
                f"invalid SHA-256 at entry {index} in {path}: {digest!r}"
            )
        root = managed_root(normalized, roots)
        safe_destination(normalized, root, HOME)
        if normalized in managed:
            raise SafetyError(
                f"duplicate managed path in manifest {path}: {normalized}"
            )
        managed[normalized] = digest

    return path, managed, True


def add_destination(
    desired: dict[pathlib.Path, dict],
    claimed: dict[pathlib.Path, str],
    target: str,
    destination: pathlib.Path,
    root: pathlib.Path,
    content: bytes,
    mode: int | None,
) -> None:
    destination = safe_destination(destination, root, HOME)
    if destination in desired:
        raise SafetyError(f"duplicate destination for {target}: {destination}")
    owner = claimed.get(destination)
    if owner is not None and owner != target:
        raise SafetyError(
            f"duplicate destination across targets {owner} and {target}: "
            f"{destination}"
        )
    claimed[destination] = target
    desired[destination] = {
        "content": content,
        "sha256": sha_bytes(content),
        "mode": mode,
        "root": root,
    }


def destination_hash(path: pathlib.Path, root: pathlib.Path) -> str:
    path = safe_destination(path, root, HOME)
    try:
        return sha_bytes(path.read_bytes())
    except OSError as exc:
        raise SafetyError(f"cannot read destination for hashing: {path}: {exc}") from exc


def target_roots(cfg: dict) -> tuple[pathlib.Path, ...]:
    legacy_roots = tuple(prepare_target_root(root) for root in cfg.get("legacy_roots", ()))
    return tuple(dict.fromkeys(
        (prepare_target_root(cfg["skills"]), prepare_target_root(cfg["agents"]), *legacy_roots)
    ))


def build_target_plan(
    name: str,
    cfg: dict,
    skills: list[tuple[pathlib.Path, str]],
    agents: list[pathlib.Path],
    claimed: dict[pathlib.Path, str],
) -> dict:
    skill_root = prepare_target_root(cfg["skills"])
    agent_root = prepare_target_root(cfg["agents"])
    roots = target_roots(cfg)
    desired: dict[pathlib.Path, dict] = {}
    skill_file_count = 0

    for skill_dir, skill_name in skills:
        for source_file in source_tree_files(skill_dir):
            relative = source_file.relative_to(skill_dir)
            content = source_file.read_bytes()
            mode = stat.S_IMODE(source_file.stat().st_mode)
            add_destination(
                desired,
                claimed,
                name,
                skill_root / skill_name / relative,
                skill_root,
                content,
                mode,
            )
            skill_file_count += 1

    for agent_file in agents:
        source = safe_source_file(agent_file, REPO)
        source_bytes = source.read_bytes()
        if cfg["agent_fmt"] in {"toml", "cursor", "antigravity", "opencode"}:
            try:
                text = source_bytes.decode("utf-8")
            except UnicodeDecodeError as exc:
                raise SafetyError(f"agent is not valid UTF-8: {source}") from exc
            convert = {"cursor": md_to_cursor_agent, "antigravity": md_to_antigravity_agent,
                       "opencode": md_to_opencode_agent}.get(
                cfg["agent_fmt"], md_to_toml_agent
            )
            content = convert(text).encode("utf-8")
        else:
            content = source_bytes
        add_destination(
            desired,
            claimed,
            name,
            agent_root / f"{agent_file.stem}{cfg['agent_ext']}",
            agent_root,
            content,
            None,
        )

    manifest_path, prior, has_manifest = load_manifest(name, roots)
    for destination in prior:
        owner = claimed.get(destination)
        if owner is not None and owner != name:
            raise SafetyError(
                f"managed path overlaps targets {owner} and {name}: "
                f"{destination}"
            )
        claimed[destination] = name

    writes = []
    preimages: dict[pathlib.Path, str | None] = {}
    unchanged = []
    for destination, item in sorted(
        desired.items(), key=lambda pair: os.fspath(pair[0])
    ):
        if not destination.exists():
            writes.append(destination)
            preimages[destination] = None
            continue

        current = destination_hash(destination, item["root"])
        if destination not in prior:
            if not has_manifest:
                raise SafetyError(
                    f"destination exists but {manifest_path} is absent; "
                    f"refusing to overwrite untracked file: {destination}. "
                    "Remove or relocate the file, then rerun."
                )
            raise SafetyError(
                f"untracked destination collision: {destination}. "
                "Remove or relocate the file, then rerun."
            )

        if current == item["sha256"]:
            unchanged.append(destination)
        elif current == prior[destination]:
            writes.append(destination)
            preimages[destination] = prior[destination]
        else:
            raise SafetyError(
                f"locally modified managed file would be overwritten: "
                f"{destination}"
            )

    removals = []
    for destination, previous_hash in sorted(
        prior.items(), key=lambda pair: os.fspath(pair[0])
    ):
        if destination in desired or not destination.exists():
            continue
        root = managed_root(destination, roots)
        current = destination_hash(destination, root)
        if current != previous_hash:
            raise SafetyError(
                f"locally modified stale managed file would be removed: "
                f"{destination}"
            )
        removals.append(destination)
        preimages[destination] = previous_hash

    return {
        "name": name,
        "skills": len(skills),
        "skill_files": skill_file_count,
        "agents": len(agents),
        "desired": desired,
        "prior": dict(prior),
        "preimages": preimages,
        "writes": writes,
        "removals": removals,
        "unchanged": unchanged,
        "manifest_path": manifest_path,
        "roots": roots,
    }


def manifest_bytes(plan: dict, managed: dict[pathlib.Path, str] | None = None) -> bytes:
    entries = (
        managed
        if managed is not None
        else {dest: item["sha256"] for dest, item in plan["desired"].items()}
    )
    files = [
        {
            "path": os.fspath(destination),
            "sha256": sha256,
        }
        for destination, sha256 in sorted(
            entries.items(), key=lambda pair: os.fspath(pair[0])
        )
    ]
    data = {
        "schema_version": MANIFEST_VERSION,
        "target": plan["name"],
        "files": files,
    }
    return (json.dumps(data, indent=2, sort_keys=True) + "\n").encode("utf-8")


def atomic_write_manifest(path: pathlib.Path, content: bytes) -> None:
    root = _lexical(MANIFEST_ROOT)
    _relative(root, HOME)
    _reject_symlink_components(root, HOME)
    root.mkdir(parents=True, exist_ok=True)
    _reject_symlink_components(root, HOME)
    if not root.is_dir():
        raise SafetyError(f"manifest root is not a directory: {root}")
    path = safe_destination(path, root, HOME)

    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.",
        suffix=".tmp",
        dir=root,
    )
    temporary = pathlib.Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


def atomic_write_destination(
    destination: pathlib.Path, content: bytes, mode: int | None
) -> None:
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{destination.name}.",
        suffix=".tmp",
        dir=destination.parent,
    )
    temporary = pathlib.Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        if mode is not None:
            temporary.chmod(mode)
        os.replace(temporary, destination)
    finally:
        if temporary.exists():
            temporary.unlink()


def apply_target_plan(plan: dict) -> None:
    # The manifest records only what reached disk, so an interrupted run leaves a
    # manifest that matches the files and the next run resumes safely.
    committed: dict[pathlib.Path, str] = dict(plan.get("prior", {}))
    for destination in plan["unchanged"]:
        committed[destination] = plan["desired"][destination]["sha256"]
    preimages: dict[pathlib.Path, str | None] = plan.get("preimages", {})
    completed = False
    try:
        for destination in plan["writes"]:
            item = plan["desired"][destination]
            safe_destination(destination, item["root"], HOME)
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination = safe_destination(destination, item["root"], HOME)
            expected = preimages.get(destination)
            if expected is None:
                if destination.exists() or destination.is_symlink():
                    raise SafetyError(
                        f"untracked destination collision: {destination}. "
                        "Remove or relocate the file, then rerun."
                    )
            elif not destination.exists() or destination_hash(destination, item["root"]) != expected:
                raise SafetyError(
                    f"locally modified managed file would be overwritten: {destination}"
                )
            atomic_write_destination(destination, item["content"], item["mode"])
            committed[destination] = item["sha256"]

        removal_roots = plan.get("roots") or tuple(
            dict.fromkeys(item["root"] for item in plan["desired"].values())
        )
        for destination in plan["removals"]:
            root = managed_root(destination, removal_roots)
            destination = safe_destination(destination, root, HOME)
            if destination.exists():
                expected = preimages.get(destination)
                if expected is not None and destination_hash(destination, root) != expected:
                    raise SafetyError(
                        f"locally modified stale managed file would be removed: {destination}"
                    )
                destination.unlink()
                prune_empty_parents(destination, root)
            committed.pop(destination, None)
        completed = True
    finally:
        if completed or committed or plan["manifest_path"].exists():
            atomic_write_manifest(
                plan["manifest_path"],
                manifest_bytes(plan, None if completed else committed),
            )


def prune_empty_parents(path: pathlib.Path, root: pathlib.Path) -> None:
    """Remove folders a removal left empty, up to but not including the target root."""
    parent = path.parent
    while parent != root and root in parent.parents:
        try:
            parent.rmdir()
        except OSError:
            return
        parent = parent.parent


def display_path(path: pathlib.Path) -> str:
    try:
        return "~/" + path.relative_to(HOME).as_posix()
    except ValueError:
        return os.fspath(path)


def report_plan(plan: dict, apply: bool) -> None:
    prefix = "" if apply else "WOULD "
    print(
        f"  {plan['name']:12} skills:{plan['skills']} "
        f"files:{plan['skill_files']} agents:{plan['agents']} "
        f"write:{len(plan['writes'])} remove:{len(plan['removals'])} "
        f"unchanged:{len(plan['unchanged'])}"
    )
    for destination in plan["writes"]:
        print(f"    {prefix}WRITE  {display_path(destination)}")
    for destination in plan["removals"]:
        print(f"    {prefix}REMOVE {display_path(destination)}")
    print(
        f"    {prefix}WRITE  {display_path(plan['manifest_path'])} "
        "[managed-state manifest]"
    )


SELECTION_VERSION = 1
DEFAULT_SELECTION = {"community": False, "departments": None, "skills": None, "agents": True}


def component_group(path: pathlib.Path) -> str:
    """The department of a first-party component, or community/<source> for a community one."""
    parts = path.relative_to(REPO).parts
    return parts[1] if parts[0] == "plugins" else f"community/{parts[1]}"


def is_community(path: pathlib.Path) -> bool:
    return path.relative_to(REPO).parts[0] == "community"


def selection_location() -> pathlib.Path:
    root = _lexical(MANIFEST_ROOT)
    _relative(root, HOME)
    _reject_symlink_components(root, HOME)
    return safe_destination(root / "selection.json", root, HOME)


def load_selections() -> dict:
    path = selection_location()
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=_unique_json_object)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
        raise SafetyError(f"malformed install selection {path}: {exc}") from exc
    if (not isinstance(data, dict) or data.get("schema_version") != SELECTION_VERSION
            or not isinstance(data.get("targets"), dict)):
        raise SafetyError(f"malformed install selection structure: {path}")
    for target, selection in data["targets"].items():
        if target not in TARGETS:
            continue
        if (not isinstance(selection, dict) or set(selection) != set(DEFAULT_SELECTION)
                or not isinstance(selection["community"], bool)
                or not isinstance(selection["agents"], bool)
                or not all(value is None or (isinstance(value, list) and all(isinstance(v, str) for v in value))
                           for value in (selection["departments"], selection["skills"]))):
            raise SafetyError(f"malformed install selection for {target}: {path}")
    return data["targets"]


def save_selections(selections: dict) -> None:
    content = json.dumps(
        {"schema_version": SELECTION_VERSION, "targets": selections}, indent=2, sort_keys=True
    ) + "\n"
    root = _lexical(MANIFEST_ROOT)
    _relative(root, HOME)
    _reject_symlink_components(root, HOME)
    root.mkdir(parents=True, exist_ok=True)
    path = selection_location()
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=root)
    temporary = pathlib.Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(content.encode("utf-8"))
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


def component_of(destination: pathlib.Path, cfg: dict) -> str | None:
    """The skill name or agent id a managed destination belongs to."""
    skill_roots = [_lexical(cfg["skills"])] + [
        _lexical(root) for root in cfg.get("legacy_roots", ()) if _lexical(root).name == "skills"
    ]
    agent_roots = [_lexical(cfg["agents"])] + [
        _lexical(root) for root in cfg.get("legacy_roots", ()) if _lexical(root).name == "agents"
    ]
    for root in skill_roots:
        try:
            return destination.relative_to(root).parts[0]
        except ValueError:
            pass
    for root in agent_roots:
        try:
            relative = destination.relative_to(root)
        except ValueError:
            continue
        name = relative.parts[0]
        for ext in (cfg["agent_ext"], ".md"):
            if name.endswith(ext):
                return name[: -len(ext)]
        return name
    return None


def infer_selection(target: str, cfg: dict, community_names: set[str]) -> dict:
    """Releases before 3.3 did not store the choice; read it from what the manifest lists."""
    _, prior, has_manifest = load_manifest(target, target_roots(cfg))
    selection = dict(DEFAULT_SELECTION)
    if has_manifest:
        installed = {component_of(destination, cfg) for destination in prior}
        selection["community"] = bool(installed & community_names)
    return selection


def resolve_selection(target: str, cfg: dict, args, saved: dict, library) -> dict:
    skills, agents = library
    community_names = {name for folder, name in skills if is_community(folder)} | {
        agent.stem for agent in agents if is_community(agent)
    }
    if target in saved:
        selection = dict(saved[target])
    else:
        selection = infer_selection(target, cfg, community_names)
    if args.all:
        selection.update(departments=None, skills=None, agents=True)
    if args.departments:
        groups = {component_group(folder) for folder, _ in skills} | {component_group(a) for a in agents}
        unknown = sorted(set(args.departments) - groups)
        if unknown:
            raise SafetyError(f"unknown department: {', '.join(unknown)}")
    if args.skills:
        names = {name for _, name in skills}
        unknown = sorted(set(args.skills) - names)
        if unknown:
            raise SafetyError(f"unknown skill: {', '.join(unknown)}")
    if args.departments or args.skills:
        # A command that names departments or skills replaces both remembered filters.
        selection["departments"] = sorted(set(args.departments)) if args.departments else None
        selection["skills"] = sorted(set(args.skills)) if args.skills else None
    if args.no_agents:
        selection["agents"] = False
    if args.community:
        selection["community"] = True
    if args.no_community:
        selection["community"] = False
    return selection


def select_components(library, selection: dict):
    skills, agents = library
    if not selection["community"]:
        skills = [item for item in skills if not is_community(item[0])]
        agents = [agent for agent in agents if not is_community(agent)]
    departments, names = selection["departments"], selection["skills"]
    if departments is not None or names is not None:
        # The skills of the named departments plus the named skills; agents follow departments.
        groups, wanted = set(departments or ()), set(names or ())
        skills = [item for item in skills if component_group(item[0]) in groups or item[1] in wanted]
    if departments is not None:
        agents = [agent for agent in agents if component_group(agent) in set(departments)]
    if not selection["agents"]:
        agents = []
    return skills, agents


def deselected_components(plan: dict, cfg: dict, library, selected) -> list[str]:
    """Components still in the library that this run would remove because they were deselected."""
    skills, agents = library
    library_names = {name for _, name in skills} | {agent.stem for agent in agents}
    chosen = {name for _, name in selected[0]} | {agent.stem for agent in selected[1]}
    names = {component_of(destination, cfg) for destination in plan["removals"]}
    return sorted(name for name in names if name in library_names and name not in chosen)


def describe_selection(selection: dict) -> str:
    parts = ["community" if selection["community"] else "first-party"]
    if selection["departments"] is not None:
        parts.append("departments=" + ",".join(selection["departments"]))
    if selection["skills"] is not None:
        parts.append("skills=" + ",".join(selection["skills"]))
    if not selection["agents"]:
        parts.append("no agents")
    return " ".join(parts)


def list_library(library, as_json: bool) -> int:
    skills, agents = library
    groups: dict[str, dict[str, list[str]]] = {}
    for folder, name in skills:
        groups.setdefault(component_group(folder), {"skills": [], "agents": []})["skills"].append(name)
    for agent in agents:
        groups.setdefault(component_group(agent), {"skills": [], "agents": []})["agents"].append(agent.stem)
    saved = load_selections()
    installed = {}
    for target, cfg in TARGETS.items():
        _, prior, has_manifest = load_manifest(target, target_roots(cfg))
        if has_manifest:
            names = {component_of(destination, cfg) for destination in prior}
            installed[target] = {"components": len(names), "files": len(prior),
                                 "selection": saved.get(target)}
    if as_json:
        print(json.dumps({"departments": groups, "installed": installed}, indent=2, sort_keys=True))
        return 0
    print("Departments (skills / agents):")
    for group in sorted(groups):
        print(f"  {group:34} {len(groups[group]['skills']):3} / {len(groups[group]['agents']):3}")
    print("\nInstalled:" if installed else "\nInstalled: nothing yet")
    for target, info in installed.items():
        selection = info["selection"]
        text = describe_selection(selection) if selection else "selection not recorded (before 3.3)"
        print(f"  {target:12} {info['components']} components, {info['files']} files ({text})")
    return 0


def doctor(as_json: bool) -> int:
    report = {"python": sys.version.split()[0], "platform": sys.platform, "targets": {}, "notes": []}
    problems = 0
    if sys.version_info < (3, 9):
        report["notes"].append("Python 3.9 or newer is required")
        problems += 1
    if os.name == "nt":
        report["notes"].append("skillry storage runs on macOS and Linux only; installs work on Windows")
    for target, cfg in TARGETS.items():
        roots = target_roots(cfg)
        try:
            _, prior, has_manifest = load_manifest(target, roots)
        except SafetyError as exc:
            report["targets"][target] = {"error": str(exc)}
            problems += 1
            continue
        if not has_manifest:
            continue
        missing, modified = [], []
        for destination, digest in sorted(prior.items(), key=lambda pair: os.fspath(pair[0])):
            root = managed_root(destination, roots)
            if not destination.exists():
                missing.append(display_path(destination))
            elif destination_hash(destination, root) != digest:
                modified.append(display_path(destination))
        report["targets"][target] = {"files": len(prior), "missing": missing, "modified": modified}
        problems += len(missing) + len(modified)
    if as_json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(f"Python {report['python']} on {report['platform']}")
        if not report["targets"]:
            print("No Skillry install found.")
        for target, info in report["targets"].items():
            if "error" in info:
                print(f"  {target:12} ERROR {info['error']}")
                continue
            state = "ok" if not info["missing"] and not info["modified"] else "needs attention"
            print(f"  {target:12} {info['files']} files, {len(info['missing'])} missing, "
                  f"{len(info['modified'])} changed locally: {state}")
            for path in info["missing"][:10]:
                print(f"      missing  {path}")
            for path in info["modified"][:10]:
                print(f"      changed  {path}")
        for note in report["notes"]:
            print(f"  note: {note}")
    return 1 if problems else 0


def uninstall(targets: list[str], apply: bool) -> int:
    saved = load_selections()
    prefix = "" if apply else "WOULD "
    for target in targets:
        cfg = TARGETS[target]
        roots = target_roots(cfg)
        manifest_path, prior, has_manifest = load_manifest(target, roots)
        if not has_manifest:
            print(f"  {target:12} nothing installed by Skillry")
            continue
        remove, keep = [], []
        for destination, digest in sorted(prior.items(), key=lambda pair: os.fspath(pair[0])):
            root = managed_root(destination, roots)
            if not destination.exists():
                continue
            if destination_hash(destination, root) == digest:
                remove.append((destination, root))
            else:
                keep.append(destination)
        print(f"  {target:12} remove:{len(remove)} keep (changed locally):{len(keep)}")
        for destination, _ in remove:
            print(f"    {prefix}REMOVE {display_path(destination)}")
        for destination in keep:
            print(f"    {prefix}KEEP   {display_path(destination)} (changed locally; no longer managed)")
        if apply:
            for destination, root in remove:
                destination = safe_destination(destination, root, HOME)
                if destination.exists() and destination_hash(destination, root) == prior[destination]:
                    destination.unlink()
                    prune_empty_parents(destination, root)
            manifest_path.unlink()
            saved.pop(target, None)
    if apply:
        save_selections(saved)
    print("\nDone" + ("" if apply else " (dry-run; nothing removed)"))
    return 0


def parse_args(argv=None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    action = parser.add_mutually_exclusive_group()
    action.add_argument("--list", action="store_true", help="list departments, skills and agents, and what is installed")
    action.add_argument("--doctor", action="store_true", help="check installed files against their manifests")
    action.add_argument("--uninstall", action="store_true", help="remove what Skillry installed for --targets")
    parser.add_argument("--json", action="store_true", help="machine-readable output for --list and --doctor")
    parser.add_argument(
        "--apply",
        action="store_true",
        help="write (or with --uninstall remove) files; default is dry-run",
    )
    parser.add_argument(
        "--community",
        action="store_true",
        help="include reviewed community skills and agents (remembered)",
    )
    parser.add_argument("--no-community", action="store_true", help="leave community content out (remembered)")
    parser.add_argument(
        "--targets",
        nargs="+",
        choices=sorted(TARGETS),
        help="one or more target platforms; default is all",
    )
    parser.add_argument("--departments", nargs="+", metavar="NAME",
                        help="install only these departments (remembered); see --list")
    parser.add_argument("--skills", nargs="+", metavar="NAME", help="install only these skills (remembered)")
    parser.add_argument("--no-agents", action="store_true", help="install skills only (remembered)")
    parser.add_argument("--all", action="store_true", help="go back to every department, skill and agent")
    parser.add_argument("--allow-removal", action="store_true",
                        help="allow an --apply that removes components you deselected")
    args = parser.parse_args(argv)
    if args.community and args.no_community:
        parser.error("--community and --no-community exclude each other")
    if args.uninstall and not args.targets:
        parser.error("--uninstall needs --targets")
    return args


def main(argv=None) -> int:
    args = parse_args(argv)
    if args.doctor:
        verified_components(True)
        return doctor(args.json)
    if args.uninstall:
        return uninstall(args.targets, args.apply)
    library = verified_components(True)
    if args.list:
        return list_library(library, args.json)

    selected = args.targets or list(TARGETS)
    saved = load_selections()
    claimed: dict[pathlib.Path, str] = {}
    plans, selections, blocked = [], {}, []
    for name in selected:
        selection = resolve_selection(name, TARGETS[name], args, saved, library)
        components = select_components(library, selection)
        plan = build_target_plan(name, TARGETS[name], components[0], components[1], claimed)
        dropped = deselected_components(plan, TARGETS[name], library, components)
        if dropped and not args.allow_removal:
            blocked.append((name, dropped))
        plans.append(plan)
        selections[name] = selection

    print(f"{'APPLY' if args.apply else 'DRY-RUN'} - Skillry install")
    print(f"Targets: {', '.join(selected)}\n")
    for plan in plans:
        print(f"  {plan['name']:12} selection: {describe_selection(selections[plan['name']])}")
        report_plan(plan, args.apply)
    for name, dropped in blocked:
        print(f"\n  {name}: this selection removes components you installed earlier: {', '.join(dropped)}."
              " Pass --allow-removal to remove them, or widen the selection.")

    if args.apply:
        if blocked:
            raise SafetyError("the selection would remove installed components; nothing was changed")
        for plan in plans:
            apply_target_plan(plan)
        saved.update(selections)
        save_selections(saved)

    print("\nDone" + ("" if args.apply else " (dry-run; no files written)"))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except SafetyError as exc:
        print(f"REFUSED: {exc}", file=sys.stderr)
        sys.exit(2)
