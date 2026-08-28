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
    "copilot": {
        "skills": HOME / ".copilot/skills",
        "agents": HOME / ".copilot/agents",
        "agent_ext": ".agent.md",
        "agent_fmt": "md",
    },
    "antigravity": {
        "skills": HOME / ".gemini/antigravity/skills",
        "agents": HOME / ".gemini/antigravity/agents",
        "agent_ext": ".md",
        "agent_fmt": "md",
    },
}

READ_ONLY_TOOLS = frozenset({"Read", "Glob", "Grep", "WebSearch", "WebFetch"})
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
    if path.exists() and not path.is_file():
        raise SafetyError(f"destination is not a regular file: {path}")
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
    sandbox = "read-only" if has_read_only_tools(text) else "workspace-write"
    return (
        f"name = {toml_string(name)}\n"
        f"description = {toml_string(description)}\n"
        'model_reasoning_effort = "medium"\n'
        f"sandbox_mode = {toml_string(sandbox)}\n"
        f"developer_instructions = {toml_string(body)}\n"
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


def build_target_plan(
    name: str,
    cfg: dict,
    skills: list[tuple[pathlib.Path, str]],
    agents: list[pathlib.Path],
    claimed: dict[pathlib.Path, str],
) -> dict:
    skill_root = prepare_target_root(cfg["skills"])
    agent_root = prepare_target_root(cfg["agents"])
    roots = tuple(dict.fromkeys((skill_root, agent_root)))
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
        if cfg["agent_fmt"] == "toml":
            try:
                text = source_bytes.decode("utf-8")
            except UnicodeDecodeError as exc:
                raise SafetyError(f"agent is not valid UTF-8: {source}") from exc
            content = md_to_toml_agent(text).encode("utf-8")
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
    unchanged = []
    for destination, item in sorted(
        desired.items(), key=lambda pair: os.fspath(pair[0])
    ):
        if not destination.exists():
            writes.append(destination)
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

    return {
        "name": name,
        "skills": len(skills),
        "skill_files": skill_file_count,
        "agents": len(agents),
        "desired": desired,
        "writes": writes,
        "removals": removals,
        "unchanged": unchanged,
        "manifest_path": manifest_path,
    }


def manifest_bytes(plan: dict) -> bytes:
    files = [
        {
            "path": os.fspath(destination),
            "sha256": item["sha256"],
        }
        for destination, item in sorted(
            plan["desired"].items(), key=lambda pair: os.fspath(pair[0])
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


def apply_target_plan(plan: dict) -> None:
    for destination in plan["writes"]:
        item = plan["desired"][destination]
        safe_destination(destination, item["root"], HOME)
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination = safe_destination(destination, item["root"], HOME)
        destination.write_bytes(item["content"])
        if item["mode"] is not None:
            destination.chmod(item["mode"])

    for destination in plan["removals"]:
        root = managed_root(
            destination,
            tuple(
                dict.fromkeys(
                    item["root"] for item in plan["desired"].values()
                )
            ),
        )
        destination = safe_destination(destination, root, HOME)
        if destination.exists():
            destination.unlink()

    atomic_write_manifest(
        plan["manifest_path"],
        manifest_bytes(plan),
    )


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


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    parser.add_argument(
        "--apply",
        action="store_true",
        help="write verified platform components; default is dry-run",
    )
    parser.add_argument(
        "--community",
        action="store_true",
        help="include reviewed community skills and agents",
    )
    parser.add_argument(
        "--targets",
        nargs="+",
        choices=sorted(TARGETS),
        help="one or more target platforms; default is all",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    selected = args.targets or list(TARGETS)
    skills, agents = verified_components(args.community)

    claimed: dict[pathlib.Path, str] = {}
    plans = [
        build_target_plan(
            name,
            TARGETS[name],
            skills,
            agents,
            claimed,
        )
        for name in selected
    ]

    print(f"{'APPLY' if args.apply else 'DRY-RUN'} - Skillry install")
    print(
        f"Targets: {', '.join(selected)}   "
        f"Community: {'yes' if args.community else 'no'}\n"
    )
    for plan in plans:
        report_plan(plan, args.apply)

    if args.apply:
        for plan in plans:
            apply_target_plan(plan)

    print("\nDone" + ("" if args.apply else " (dry-run; no files written)"))


if __name__ == "__main__":
    try:
        main()
    except SafetyError as exc:
        print(f"REFUSED: {exc}", file=sys.stderr)
        sys.exit(2)
