"""Keep source provenance, installed bytes, and caller permissions separate."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import pathlib
import re
import subprocess

ROOT = pathlib.Path(__file__).resolve().parents[2]
SKILL_ROOTS = {
    "codex": ".codex/skills", "claude": ".claude/skills",
    "cursor": ".cursor/skills",
    "antigravity": ".gemini/config/skills",
    "antigravity-cli": ".gemini/antigravity-cli/skills",
}
AGENT_ROOTS = {"codex": ".codex/agents", "claude": ".claude/agents", "cursor": ".cursor/agents"}
ID = re.compile(r"^[a-z0-9][a-z0-9_-]{0,99}$")


def digest(value):
    if not isinstance(value, bytes):
        value = json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode()
    return hashlib.sha256(value).hexdigest()


def safe_file(path, root):
    path, root = pathlib.Path(path).absolute(), pathlib.Path(root).absolute()
    rel = path.relative_to(root)
    current = root
    if current.is_symlink():
        raise ValueError("symlink_root")
    for part in rel.parts:
        current = current / part
        if current.is_symlink():
            raise ValueError("symlink_component")
    if not path.is_file():
        raise ValueError("missing_file")
    return path


def file_hash(path, root):
    return digest(safe_file(path, root).read_bytes())


def frontmatter(path):
    # Only metadata is exposed to the selector. Bodies are never sent to Jev.
    with path.open(encoding="utf-8") as stream:
        if stream.readline().strip() != "---":
            return {}
        lines = []
        for line in stream:
            if line.strip() == "---" or len(lines) > 80:
                break
            lines.append(line)
    text = "".join(lines)
    result = {}
    for key in ("name", "description", "tools"):
        m = re.search(r"^" + key + r":\s*(.+)$", text, re.M)
        result[key] = m.group(1).strip().strip("\"'") if m else ""
    return result


def build_public(repo=ROOT):
    """Use Skillry's existing checksum/path validation; never invent registry IDs."""
    repo = pathlib.Path(repo).resolve()
    spec = importlib.util.spec_from_file_location("skillry_installer", repo / "tools/install.py")
    installer = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(installer)
    skills, agents = installer.verified_components(True)
    commit = subprocess.run(["git", "-C", str(repo), "rev-parse", "HEAD"],
                            capture_output=True, text=True, check=True).stdout.strip()
    modified = set(subprocess.run(["git", "-C", str(repo), "diff", "--name-only", "HEAD"],
                                  capture_output=True, text=True, check=True).stdout.splitlines())
    entries = []
    for kind, path, name in [("skill", p, n) for p, n in skills] + [
            ("agent", p, p.stem) for p in agents]:
        source = path / "SKILL.md" if kind == "skill" else path
        metadata = frontmatter(source)
        files = installer.source_tree_files(path) if kind == "skill" else [path]
        hashes = {p.relative_to(path if kind == "skill" else path.parent).as_posix():
                  digest(p.read_bytes()) for p in files}
        content = source.read_text(encoding="utf-8")
        dirty = any(p.relative_to(repo).as_posix() in modified for p in files)
        entries.append({
            "id": name, "kind": kind, "description": metadata["description"],
            "origin": "community" if source.relative_to(repo).parts[0] == "community" else "original",
            "visibility": "public",
            "source_path": source.relative_to(repo).as_posix(), "source_commit": None if dirty else commit,
            "base_commit": commit, "source_state": "working_tree" if dirty else "committed",
            "checksum": installer.sha_tree(path) if kind == "skill" else digest(source.read_bytes()),
            "files": hashes,
            "codex_hash": digest(installer.md_to_toml_agent(content).encode()) if kind == "agent" else None,
            "cursor_hash": digest(installer.md_to_cursor_agent(content).encode()) if kind == "agent" else None,
            "suitable": metadata["description"],
            "unsuitable": "Unavailable bindings, unreviewed origin, or work outside the declared scope.",
            "tools": metadata.get("tools", ""),
        })
    return {"schema_version": 1, "source_commit": commit, "version": digest(entries), "entries": entries}


def installed_inventory(catalog, home, clients):
    """Record an overlay, not a second authoritative source registry."""
    home = pathlib.Path(home).resolve()
    records, excluded = [], []
    for client in clients:
        for entry in catalog["entries"]:
            kind = entry["kind"]
            if kind == "agent":
                if client not in AGENT_ROOTS:
                    continue
                p = home / AGENT_ROOTS[client] / (entry["id"] + (".toml" if client == "codex" else ".md"))
                expected = entry.get(client + "_hash") if client in {"codex", "cursor"} else entry["checksum"]
                files = {str(p): expected}
            else:
                root = home / SKILL_ROOTS[client] / entry["id"]
                # Installed agy currently also discovers the shared app root.
                if client == "antigravity-cli" and not root.exists():
                    root = home / SKILL_ROOTS["antigravity"] / entry["id"]
                files = {str(root / rel): sha for rel, sha in entry["files"].items()}
            try:
                if any(file_hash(p, home) != sha for p, sha in files.items()):
                    raise ValueError("installed_drift")
                records.append({"id": entry["id"], "kind": kind, "client": client,
                                "invocation_id": entry["id"].replace("-", "_") if kind == "agent" and client == "codex" else entry["id"],
                                "origin": entry["origin"], "visibility": "public",
                                "source_checksum": entry["checksum"], "files": files})
            except (ValueError, OSError):
                excluded.append({"id": entry["id"], "kind": kind, "client": client,
                                 "reason": "missing_or_modified"})
    private_entries = []
    for lock_file in sorted((home / ".skillry/profiles").glob("*/effective-lock.json")):
        try:
            lock = json.loads(safe_file(lock_file, home).read_text())
            policy = next(x for x in lock["outputs"] if x["kind"] == "effective-policy")
            if file_hash(lock_file.parent / "effective-policy.md", home) != policy["sha256"]:
                continue
            for item in lock.get("private_components", []):
                if item.get("kind") != "skill" or not ID.fullmatch(item["id"]):
                    continue
                for client in clients:
                    target = "antigravity" if client == "antigravity-cli" else client
                    if target not in item.get("install_targets", []):
                        continue
                    root = home / SKILL_ROOTS[target] / item["id"]
                    files = {str(root / "SKILL.md"): item["sha256"]}
                    for extra in item.get("files", []):
                        rel = pathlib.PurePosixPath(extra["path"])
                        if rel.is_absolute() or ".." in rel.parts:
                            raise ValueError("private_path")
                        files[str(root / rel)] = extra["sha256"]
                    if any(file_hash(p, home) != sha for p, sha in files.items()):
                        continue
                    metadata = frontmatter(root / "SKILL.md")
                    entry = {"id": item["id"], "kind": "skill", "description": metadata["description"],
                             "suitable": metadata["description"], "unsuitable": "Outside the installed profile scope",
                             "origin": "private-profile", "visibility": "private",
                             "checksum": digest({str(pathlib.Path(p).relative_to(root)): sha for p, sha in files.items()}),
                             "source_commit": None, "profile_lock_checksum": digest(lock_file.read_bytes())}
                    if not any(x["id"] == entry["id"] for x in private_entries):
                        private_entries.append(entry)
                    records.append({"id": entry["id"], "kind": "skill", "client": client,
                                    "origin": entry["origin"], "visibility": "private",
                                    "source_checksum": entry["checksum"], "files": files})
        except (ValueError, OSError, KeyError, StopIteration):
            excluded.append({"kind": "profile", "reason": "private_profile_invalid"})
    return {"schema_version": 1, "catalog_version": catalog["version"],
            "version": digest(records), "records": records, "excluded": excluded,
            "private_entries": private_entries}


def eligible(catalog, inventory, home, client, kind, allowed_ids):
    if inventory.get("catalog_version") != catalog.get("version"):
        return []
    source = {(x["kind"], x["id"]): x for x in catalog["entries"] + inventory.get("private_entries", [])}
    result = []
    for record in inventory["records"]:
        invocation_id = record.get("invocation_id", record["id"])
        if record["client"] != client or record["kind"] != kind or invocation_id not in allowed_ids:
            continue
        entry = source.get((kind, record["id"]))
        if not entry or entry["checksum"] != record["source_checksum"]:
            continue
        try:
            if any(file_hash(p, home) != sha for p, sha in record["files"].items()):
                continue
        except (ValueError, OSError):
            continue
        result.append({**entry, "source_id": entry["id"], "id": invocation_id})
    return result
