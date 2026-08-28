#!/usr/bin/env python3
"""Fail-closed public release gate for Skillry."""

from __future__ import annotations

import sys

try:
    import tomllib
except ModuleNotFoundError:
    try:
        import tomli as tomllib
    except ModuleNotFoundError:
        print(
            "release-gate: FAIL: TOML parsing requires Python 3.11+ or "
            "the 'tomli' package; install it with: "
            "python3 -m pip install tomli",
            file=sys.stderr,
        )
        raise SystemExit(2)

import hashlib
import importlib.util
import json
import os
import pathlib
import re
import stat
import subprocess
import tempfile
from typing import Any, Optional

REPO = pathlib.Path(__file__).resolve().parents[1]
REGISTRY = REPO / "registry"
INSTALLER = REPO / "tools" / "install.py"

PACKAGE_FILES = (
    "bin/",
    "tools/build-lock.py",
    "tools/build-marketplace.py",
    "tools/install.py",
    "tools/release-gate.py",
    "tools/skill-sync.py",
    "tools/validate.py",
    "plugins/",
    "community/",
    ".claude-plugin/",
    "registry/",
    "docs/",
    "CHANGELOG.md",
    "CODE_OF_CONDUCT.md",
    "CONTRIBUTING.md",
    "GOVERNANCE.md",
    "LICENSE",
    "NOTICE",
    "README.md",
    "SECURITY.md",
    "THIRD-PARTY-NOTICES.md",
)

HEX_40 = re.compile(r"^[0-9a-f]{40}$")
HEX_64 = re.compile(r"^[0-9a-f]{64}$")
SKILL_ID = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
AGENT_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]*$")
TARGET_ID = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


class GateError(RuntimeError):
    """Raised when a release invariant fails."""


class Gate:
    def __init__(self) -> None:
        self.passed = 0
        self.failed = 0

    def require(self, condition: bool, message: str) -> None:
        if condition:
            self.passed += 1
            return
        self.failed += 1
        raise GateError(message)

    def record(
        self,
        condition: bool,
        message: str,
        failures: list[str],
    ) -> bool:
        if condition:
            self.passed += 1
            return True
        self.failed += 1
        failures.append(message)
        return False

    def fail(self, message: str) -> None:
        self.failed += 1
        raise GateError(message)


def is_within(path: pathlib.Path, root: pathlib.Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def lstat_or_fail(
    gate: Gate,
    path: pathlib.Path,
    label: str,
) -> os.stat_result:
    try:
        return os.lstat(path)
    except OSError as exc:
        gate.fail(f"{label} is unavailable: {path}: {exc}")
    raise AssertionError("unreachable")


def safe_node(
    gate: Gate,
    root: pathlib.Path,
    parts: tuple[str, ...],
    expected: str,
    label: str,
) -> pathlib.Path:
    try:
        root = root.resolve(strict=True)
    except OSError as exc:
        gate.fail(f"{label} root is unavailable: {root}: {exc}")

    root_stat = lstat_or_fail(gate, root, f"{label} root")
    gate.require(
        not stat.S_ISLNK(root_stat.st_mode),
        f"{label} root may not be a symlink: {root}",
    )
    gate.require(
        stat.S_ISDIR(root_stat.st_mode),
        f"{label} root is not a directory: {root}",
    )
    gate.require(bool(parts), f"{label} has an empty relative path")

    current = root
    for index, part in enumerate(parts):
        gate.require(
            part not in ("", ".", "..") and "/" not in part and "\\" not in part,
            f"{label} has an unsafe path component: {part!r}",
        )
        current = current / part
        node_stat = lstat_or_fail(gate, current, label)
        gate.require(
            not stat.S_ISLNK(node_stat.st_mode),
            f"{label} contains a symlink component: {current}",
        )
        node_expected = (
            "directory" if index < len(parts) - 1 else expected
        )
        if node_expected == "directory":
            gate.require(
                stat.S_ISDIR(node_stat.st_mode),
                f"{label} path component is not a directory: {current}",
            )
        else:
            gate.require(
                stat.S_ISREG(node_stat.st_mode),
                f"{label} is not a regular file: {current}",
            )

    try:
        resolved = current.resolve(strict=True)
    except OSError as exc:
        gate.fail(f"{label} cannot be resolved: {current}: {exc}")
    gate.require(
        is_within(resolved, root),
        f"{label} escapes its allowed root: {current}",
    )
    return current


def relative_posix(
    gate: Gate,
    value: Any,
    label: str,
) -> pathlib.PurePosixPath:
    gate.require(
        isinstance(value, str) and bool(value),
        f"{label} must be a non-empty string",
    )
    pure = pathlib.PurePosixPath(value)
    gate.require(
        "\\" not in value
        and not pure.is_absolute()
        and bool(pure.parts)
        and all(part not in ("", ".", "..") for part in pure.parts)
        and pure.as_posix() == value,
        f"{label} must be a normalized relative POSIX path: {value!r}",
    )
    return pure


def read_json(
    gate: Gate,
    relative: str,
    label: str,
) -> Any:
    pure = relative_posix(gate, relative, label)
    path = safe_node(gate, REPO, pure.parts, "file", label)
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        gate.fail(f"{label} is not valid UTF-8 JSON: {exc}")
    raise AssertionError("unreachable")


def check_package_manifest(gate: Gate) -> None:
    manifest = read_json(gate, "package.json", "package manifest")
    gate.require(
        isinstance(manifest, dict),
        "package.json must contain a JSON object",
    )
    files = manifest.get("files")
    gate.require(
        files == list(PACKAGE_FILES),
        "package.json files must match the portable runtime allowlist exactly",
    )

    scripts = manifest.get("scripts")
    gate.require(
        isinstance(scripts, dict),
        "package.json scripts must be an object",
    )
    expected_command = "python3 tools/release-gate.py"
    gate.require(
        scripts.get("release-check") == expected_command,
        "package.json must expose release-check through tools/release-gate.py",
    )
    gate.require(
        scripts.get("prepack") == expected_command,
        "package.json prepack must invoke tools/release-gate.py directly",
    )

    for item in PACKAGE_FILES:
        relative = item[:-1] if item.endswith("/") else item
        pure = pathlib.PurePosixPath(relative)
        safe_node(
            gate,
            REPO,
            pure.parts,
            "directory" if item.endswith("/") else "file",
            f"package runtime input {item}",
        )


def replay_output(result: subprocess.CompletedProcess) -> None:
    if result.stdout:
        sys.stdout.write(result.stdout)
        sys.stdout.flush()
    if result.stderr:
        sys.stderr.write(result.stderr)
        sys.stderr.flush()


def run_relay(
    label: str,
    command: list[str],
    env: Optional[dict[str, str]] = None,
    relay_on_success: bool = True,
) -> Optional[subprocess.CompletedProcess]:
    if relay_on_success:
        print(f"\n== {label} ==")
        sys.stdout.flush()
    try:
        result = subprocess.run(
            command,
            cwd=REPO,
            env=env,
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
    except OSError as exc:
        print(f"\n== {label} (failed to start) ==", file=sys.stderr)
        print(f"{label}: unable to start: {exc}", file=sys.stderr)
        return None

    if relay_on_success:
        replay_output(result)
    elif result.returncode != 0:
        print(f"\n== {label} (failed) ==", file=sys.stderr)
        replay_output(result)
    return result


def check_existing_tools(gate: Gate) -> None:
    failures: list[str] = []

    build = run_relay(
        "tools/build-lock.py (dry-run)",
        [sys.executable, str(REPO / "tools" / "build-lock.py")],
    )
    if build is None:
        gate.record(False, "tools/build-lock.py could not start", failures)
    else:
        combined = build.stdout + build.stderr
        gate.record(
            build.returncode == 0,
            f"tools/build-lock.py exited {build.returncode}",
            failures,
        )
        gate.record(
            "DRY-RUN - lock" in combined,
            "tools/build-lock.py did not confirm dry-run mode",
            failures,
        )
        drift = any(
            line.lstrip().startswith("DRIFT:")
            for line in combined.splitlines()
        )
        gate.record(
            not drift,
            "component registries are out of date",
            failures,
        )

    validate = run_relay(
        "tools/validate.py",
        [sys.executable, str(REPO / "tools" / "validate.py")],
    )
    if validate is None:
        gate.record(False, "tools/validate.py could not start", failures)
    else:
        gate.record(
            validate.returncode == 0,
            f"tools/validate.py exited {validate.returncode}",
            failures,
        )

    if failures:
        raise GateError("prerequisite checks failed: " + "; ".join(failures))


def sha256_bytes(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def load_source_lock(gate: Gate) -> list[dict[str, Any]]:
    data = read_json(
        gate,
        "registry/community-source-lock.json",
        "community source lock",
    )
    gate.require(
        isinstance(data, dict),
        "community source lock must contain a JSON object",
    )

    required_top = {
        "version",
        "kind",
        "policy",
        "historical_provenance_status",
        "entries",
    }
    gate.require(
        required_top <= set(data),
        "community source lock is missing required top-level fields",
    )
    gate.require(
        data.get("version") == "1.0.0",
        "community source lock version must be 1.0.0",
    )
    gate.require(
        data.get("kind") == "community-recovery-evidence-v1",
        "community source lock kind is unsupported",
    )
    gate.require(
        data.get("policy") == "component-pinned, fail-closed, no moving HEAD",
        "community source lock policy must be fail-closed and commit-pinned",
    )
    gate.require(
        isinstance(data.get("historical_provenance_status"), str)
        and bool(data["historical_provenance_status"].strip()),
        "community source lock needs historical provenance status",
    )

    entries = data.get("entries")
    gate.require(
        isinstance(entries, list) and bool(entries),
        "community source lock entries must be a non-empty list",
    )

    sidecars: list[dict[str, Any]] = []
    seen_targets: set[str] = set()
    required_entry = {
        "commit",
        "evidence",
        "repository",
        "source_path",
        "source_sha256",
        "targets",
    }

    for index, entry in enumerate(entries):
        label = f"community source lock entry {index}"
        gate.require(isinstance(entry, dict), f"{label} must be an object")
        gate.require(
            required_entry <= set(entry),
            f"{label} is missing required fields",
        )

        commit = entry.get("commit")
        digest = entry.get("source_sha256")
        repository = entry.get("repository")
        evidence = entry.get("evidence")

        gate.require(
            isinstance(commit, str) and bool(HEX_40.fullmatch(commit)),
            f"{label} commit must be immutable lowercase 40-hex",
        )
        gate.require(
            isinstance(digest, str) and bool(HEX_64.fullmatch(digest)),
            f"{label} source_sha256 must be lowercase 64-hex",
        )
        gate.require(
            isinstance(repository, str)
            and repository.startswith("https://github.com/")
            and not any(char.isspace() for char in repository),
            f"{label} repository must be an HTTPS GitHub repository URL",
        )
        gate.require(
            isinstance(evidence, str) and bool(evidence.strip()),
            f"{label} evidence must be a non-empty string",
        )
        relative_posix(gate, entry.get("source_path"), f"{label} source_path")

        targets = entry.get("targets")
        gate.require(
            isinstance(targets, list) and bool(targets),
            f"{label} targets must be a non-empty list",
        )
        gate.require(
            all(isinstance(target, str) for target in targets),
            f"{label} targets must contain only strings",
        )
        gate.require(
            len(targets) == len(set(targets)),
            f"{label} targets must be unique",
        )

        for target in targets:
            target_label = f"{label} target {target}"
            pure = relative_posix(gate, target, target_label)
            gate.require(
                len(pure.parts) >= 5
                and pure.parts[0] == "community"
                and pure.parts[2] == "skills",
                f"{target_label} must identify a community skill sidecar",
            )
            gate.require(
                target not in seen_targets,
                f"community source lock target is duplicated: {target}",
            )
            seen_targets.add(target)

            path = safe_node(
                gate,
                REPO,
                pure.parts,
                "file",
                target_label,
            )
            try:
                content = path.read_bytes()
            except OSError as exc:
                gate.fail(f"{target_label} cannot be read: {exc}")
            gate.require(
                sha256_bytes(content) == digest,
                f"{target_label} SHA-256 does not match source lock",
            )
            sidecars.append(
                {
                    "target": target,
                    "parts": pure.parts,
                    "source": path,
                    "content": content,
                }
            )

    return sidecars


def valid_basename(value: Any) -> bool:
    return (
        isinstance(value, str)
        and bool(value)
        and value not in (".", "..")
        and "/" not in value
        and "\\" not in value
    )


def load_component_registry(
    gate: Gate,
    filename: str,
    collection: str,
) -> list[dict[str, Any]]:
    data = read_json(
        gate,
        f"registry/{filename}",
        f"registry/{filename}",
    )
    gate.require(
        isinstance(data, dict),
        f"registry/{filename} must contain a JSON object",
    )
    gate.require(
        data.get("version") == "0.2.0",
        f"registry/{filename} version must be 0.2.0",
    )
    items = data.get(collection)
    gate.require(
        isinstance(items, list) and bool(items),
        f"registry/{filename} must contain a non-empty {collection} list",
    )

    seen_ids: set[str] = set()
    origin_counts = {"original": 0, "community": 0}
    for index, item in enumerate(items):
        label = f"registry/{filename} {collection}[{index}]"
        gate.require(isinstance(item, dict), f"{label} must be an object")

        identifier = item.get("id")
        pattern = SKILL_ID if collection == "skills" else AGENT_ID
        gate.require(
            isinstance(identifier, str) and bool(pattern.fullmatch(identifier)),
            f"{label} has an invalid id",
        )
        gate.require(
            identifier not in seen_ids,
            f"registry/{filename} has duplicate id {identifier}",
        )
        seen_ids.add(identifier)

        origin = item.get("origin")
        gate.require(
            origin in origin_counts,
            f"{label} origin must be original or community",
        )
        origin_counts[origin] += 1

        owner_key = "department" if origin == "original" else "source"
        gate.require(
            valid_basename(item.get(owner_key)),
            f"{label} has an invalid {owner_key}",
        )
        gate.require(
            isinstance(item.get("checksum"), str)
            and bool(HEX_64.fullmatch(item["checksum"])),
            f"{label} checksum must be lowercase 64-hex",
        )

        if collection == "skills":
            gate.require(
                valid_basename(item.get("folder")),
                f"{label} has an invalid folder",
            )
            gate.require(
                item.get("checksum_scope") == "component-tree-v1",
                f"{label} has an unsupported checksum scope",
            )

    expected_counts = {
        "original": origin_counts["original"],
        "community": origin_counts["community"],
        "total": len(items),
    }
    gate.require(
        data.get("counts") == expected_counts,
        f"registry/{filename} counts do not match its {collection} entries",
    )
    return items


def parse_skill_frontmatter_name(
    gate: Gate,
    skill_file: pathlib.Path,
    label: str,
) -> str:
    try:
        text = skill_file.read_text(encoding="utf-8-sig")
    except (OSError, UnicodeError) as exc:
        gate.fail(f"{label} cannot be read as UTF-8: {exc}")

    normalized = text.lstrip("\ufeff \t\r\n")
    frontmatter = re.match(
        r"^---[ \t]*\r?\n(.*?)\r?\n[ \t]*---[ \t]*(?:\r?\n|\Z)",
        normalized,
        re.S,
    )
    gate.require(
        frontmatter is not None,
        f"{label} has no canonical frontmatter block",
    )

    raw_names: list[str] = []
    for line in frontmatter.group(1).splitlines():
        field = re.match(
            r"^[ \t]*name[ \t]*:[ \t]*(.*?)[ \t]*$",
            line,
        )
        if field:
            raw_names.append(field.group(1).strip())

    gate.require(
        len(raw_names) == 1,
        f"{label} must declare exactly one frontmatter name; "
        f"found {len(raw_names)}",
    )
    raw_name = raw_names[0]
    gate.require(bool(raw_name), f"{label} has an empty frontmatter name")

    quoted = re.fullmatch(
        r"""(["'])(.*?)\1(?:[ \t]+#.*)?""",
        raw_name,
    )
    if quoted:
        name = quoted.group(2).strip()
    else:
        gate.require(
            raw_name[:1] not in {'"', "'"},
            f"{label} has an unterminated quoted frontmatter name",
        )
        name = raw_name.split(" #", 1)[0].strip()

    gate.require(
        bool(SKILL_ID.fullmatch(name)),
        f"{label} has an invalid canonical frontmatter name: {name!r}",
    )
    return name


def load_skill_identities(
    gate: Gate,
    skills: list[dict[str, Any]],
) -> tuple[set[str], dict[tuple[str, str], str]]:
    canonical_names: set[str] = set()
    name_sources: dict[str, str] = {}
    community_names: dict[tuple[str, str], str] = {}

    for index, item in enumerate(skills):
        if item["origin"] == "original":
            source_parts = (
                "plugins",
                item["department"],
                "skills",
                item["folder"],
                "SKILL.md",
            )
            source_key: Optional[tuple[str, str]] = None
        else:
            source_parts = (
                "community",
                item["source"],
                "skills",
                item["folder"],
                "SKILL.md",
            )
            source_key = (item["source"], item["folder"])

        label = f"skill registry entry {index} source SKILL.md"
        skill_file = safe_node(
            gate,
            REPO,
            source_parts,
            "file",
            label,
        )
        name = parse_skill_frontmatter_name(gate, skill_file, label)
        gate.require(
            name not in canonical_names,
            f"duplicate canonical skill name {name!r}: "
            f"{name_sources.get(name)} and "
            f"{skill_file.relative_to(REPO).as_posix()}",
        )
        canonical_names.add(name)
        name_sources[name] = skill_file.relative_to(REPO).as_posix()

        if source_key is not None:
            gate.require(
                source_key not in community_names,
                f"community skill source key is duplicated: {source_key}",
            )
            community_names[source_key] = name

    gate.require(
        len(canonical_names) == len(skills),
        "canonical skill identity count does not match skill registry",
    )
    return canonical_names, community_names


def prepare_sidecars(
    gate: Gate,
    sidecars: list[dict[str, Any]],
    community_names: dict[tuple[str, str], str],
) -> None:
    for sidecar in sidecars:
        parts = sidecar["parts"]
        key = (parts[1], parts[3])
        gate.require(
            key in community_names,
            f"source-lock target is not backed by a canonical skill identity: "
            f"{sidecar['target']}",
        )
        sidecar["installed_skill"] = community_names[key]
        sidecar["installed_relative"] = parts[4:]


def restore_environment(name: str, previous: Optional[str]) -> None:
    if previous is None:
        os.environ.pop(name, None)
    else:
        os.environ[name] = previous


def load_installer_contract(
    gate: Gate,
    contract_home: pathlib.Path,
) -> dict[str, dict[str, Any]]:
    previous_home = os.environ.get("HOME")
    previous_userprofile = os.environ.get("USERPROFILE")
    previous_bytecode = sys.dont_write_bytecode

    os.environ["HOME"] = str(contract_home)
    os.environ["USERPROFILE"] = str(contract_home)
    sys.dont_write_bytecode = True

    module: Any = None
    try:
        spec = importlib.util.spec_from_file_location(
            "_skillry_release_installer",
            INSTALLER,
        )
        gate.require(
            spec is not None and spec.loader is not None,
            "tools/install.py could not be loaded",
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
    except GateError:
        raise
    except Exception as exc:
        gate.fail(f"tools/install.py import failed: {exc}")
    finally:
        restore_environment("HOME", previous_home)
        restore_environment("USERPROFILE", previous_userprofile)
        sys.dont_write_bytecode = previous_bytecode

    gate.require(
        pathlib.Path(module.REPO).resolve() == REPO,
        "tools/install.py resolved a different repository root",
    )
    gate.require(
        pathlib.Path(module.HOME).resolve() == contract_home.resolve(),
        "tools/install.py did not honor the disposable HOME",
    )
    gate.require(
        not bool(getattr(module, "INSTRUCTIONS", None)),
        "tools/install.py still depends on excluded project-instruction payloads",
    )

    targets = getattr(module, "TARGETS", None)
    gate.require(
        isinstance(targets, dict) and bool(targets),
        "tools/install.py exposes no supported targets",
    )
    return targets


def home_relative(
    gate: Gate,
    value: Any,
    home: pathlib.Path,
    label: str,
) -> pathlib.Path:
    candidate = pathlib.Path(value)
    gate.require(candidate.is_absolute(), f"{label} must be absolute")
    try:
        relative = candidate.relative_to(home)
    except ValueError:
        gate.fail(f"{label} escapes the installer HOME: {candidate}")
    gate.require(
        bool(relative.parts)
        and all(part not in ("", ".", "..") for part in relative.parts),
        f"{label} has an unsafe HOME-relative path",
    )
    return relative


def delta_detail(expected: set[str], actual: set[str]) -> str:
    missing = sorted(expected - actual)[:5]
    extra = sorted(actual - expected)[:5]
    return f"missing={missing} unexpected={extra}"


def verify_target(
    gate: Gate,
    target: str,
    home: pathlib.Path,
    skill_relative: pathlib.Path,
    agent_relative: pathlib.Path,
    agent_ext: str,
    agent_fmt: str,
    expected_skills: set[str],
    expected_agents: set[str],
    sidecars: list[dict[str, Any]],
) -> dict[str, int]:
    issues: list[str] = []
    skill_root = safe_node(
        gate,
        home,
        skill_relative.parts,
        "directory",
        f"{target} installed skill root",
    )
    agent_root = safe_node(
        gate,
        home,
        agent_relative.parts,
        "directory",
        f"{target} installed agent root",
    )

    skill_entries = sorted(skill_root.iterdir(), key=lambda path: path.name)
    for entry in skill_entries:
        entry_stat = lstat_or_fail(gate, entry, f"{target} installed skill")
        gate.require(
            not stat.S_ISLNK(entry_stat.st_mode),
            f"{target} installed skill is a symlink: {entry}",
        )
        gate.require(
            stat.S_ISDIR(entry_stat.st_mode),
            f"{target} installed skill is not a directory: {entry}",
        )
    actual_skills = {entry.name for entry in skill_entries}
    gate.record(
        len(actual_skills) == len(expected_skills),
        f"{target} installed skill count is "
        f"{len(actual_skills)}; expected {len(expected_skills)}",
        issues,
    )
    gate.record(
        actual_skills == expected_skills,
        f"{target} installed skill identities differ: "
        f"{delta_detail(expected_skills, actual_skills)}",
        issues,
    )

    agent_entries = sorted(agent_root.iterdir(), key=lambda path: path.name)
    for entry in agent_entries:
        entry_stat = lstat_or_fail(gate, entry, f"{target} installed agent")
        gate.require(
            not stat.S_ISLNK(entry_stat.st_mode),
            f"{target} installed agent is a symlink: {entry}",
        )
        gate.require(
            stat.S_ISREG(entry_stat.st_mode),
            f"{target} installed agent is not a regular file: {entry}",
        )
    actual_agent_files = {entry.name for entry in agent_entries}
    expected_agent_files = {
        f"{identifier}{agent_ext}" for identifier in expected_agents
    }
    gate.record(
        len(actual_agent_files) == len(expected_agent_files),
        f"{target} installed agent count is "
        f"{len(actual_agent_files)}; expected {len(expected_agent_files)}",
        issues,
    )
    gate.record(
        actual_agent_files == expected_agent_files,
        f"{target} installed agent identities differ: "
        f"{delta_detail(expected_agent_files, actual_agent_files)}",
        issues,
    )

    toml_count = 0
    if agent_fmt == "toml":
        for path in agent_entries:
            try:
                with path.open("rb") as handle:
                    parsed = tomllib.load(handle)
                valid = isinstance(parsed, dict)
                detail = ""
            except Exception as exc:
                valid = False
                detail = str(exc)
            gate.record(
                valid,
                f"{target} generated invalid TOML {path.name}: {detail}",
                issues,
            )
            if valid:
                toml_count += 1

    sidecar_count = 0
    for sidecar in sidecars:
        installed_parts = (
            sidecar["installed_skill"],
            *sidecar["installed_relative"],
        )
        try:
            installed = safe_node(
                gate,
                skill_root,
                installed_parts,
                "file",
                f"{target} installed sidecar {sidecar['target']}",
            )
        except GateError as exc:
            issues.append(str(exc))
            continue

        try:
            installed_content = installed.read_bytes()
        except OSError as exc:
            gate.failed += 1
            issues.append(
                f"{target} installed sidecar cannot be read: "
                f"{sidecar['target']}: {exc}"
            )
            continue

        if gate.record(
            installed_content == sidecar["content"],
            f"{target} installed sidecar differs byte-for-byte: "
            f"{sidecar['target']}",
            issues,
        ):
            sidecar_count += 1

    if issues:
        raise GateError("; ".join(issues))

    return {
        "sidecar_copies": sidecar_count,
        "toml_files": toml_count,
    }


def run_disposable_installs(
    gate: Gate,
    expected_skills: set[str],
    agents: list[dict[str, Any]],
    sidecars: list[dict[str, Any]],
    metrics: dict[str, int],
) -> None:
    expected_agents = {item["id"] for item in agents}
    real_home = pathlib.Path.home().resolve()
    install_issues: list[str] = []

    with tempfile.TemporaryDirectory(
        prefix="skillry-release-gate-"
    ) as temp_name:
        temp_root = pathlib.Path(temp_name).resolve(strict=True)
        gate.require(
            temp_root != real_home and not is_within(temp_root, real_home),
            "temporary release root must be outside the real HOME",
        )

        contract_home = temp_root / "contract-home"
        contract_home.mkdir()
        targets = load_installer_contract(gate, contract_home)
        metrics["targets"] = len(targets)

        contracts: list[
            tuple[str, pathlib.Path, pathlib.Path, str, str]
        ] = []
        for target, config in targets.items():
            gate.require(
                isinstance(target, str) and bool(TARGET_ID.fullmatch(target)),
                f"installer exposes an invalid target name: {target!r}",
            )
            gate.require(
                isinstance(config, dict),
                f"installer target {target} must be an object",
            )
            required = {"skills", "agents", "agent_ext", "agent_fmt"}
            gate.require(
                required <= set(config),
                f"installer target {target} is missing output metadata",
            )
            skill_relative = home_relative(
                gate,
                config["skills"],
                contract_home,
                f"{target} skill root",
            )
            agent_relative = home_relative(
                gate,
                config["agents"],
                contract_home,
                f"{target} agent root",
            )
            agent_ext = config["agent_ext"]
            agent_fmt = config["agent_fmt"]
            gate.require(
                isinstance(agent_ext, str)
                and bool(re.fullmatch(r"\.[A-Za-z0-9.]+", agent_ext)),
                f"installer target {target} has an invalid agent extension",
            )
            gate.require(
                agent_fmt in {"md", "toml"},
                f"installer target {target} has an unsupported agent format",
            )
            contracts.append(
                (
                    target,
                    skill_relative,
                    agent_relative,
                    agent_ext,
                    agent_fmt,
                )
            )

        print(f"\nrelease-gate: disposable targets={len(contracts)}")
        for (
            target,
            skill_relative,
            agent_relative,
            agent_ext,
            agent_fmt,
        ) in contracts:
            metrics["checked_targets"] += 1
            target_home = temp_root / f"home-{target}"
            target_home.mkdir()
            temp_dir = target_home / "tmp"
            temp_dir.mkdir()

            env = os.environ.copy()
            env.update(
                {
                    "HOME": str(target_home),
                    "USERPROFILE": str(target_home),
                    "XDG_CONFIG_HOME": str(target_home / ".config"),
                    "XDG_CACHE_HOME": str(target_home / ".cache"),
                    "TMPDIR": str(temp_dir),
                    "PYTHONDONTWRITEBYTECODE": "1",
                }
            )
            result = run_relay(
                f"install:{target}",
                [
                    sys.executable,
                    str(INSTALLER),
                    "--community",
                    "--apply",
                    "--targets",
                    target,
                ],
                env=env,
                relay_on_success=False,
            )
            if result is None:
                gate.record(
                    False,
                    f"installer could not start for {target}",
                    install_issues,
                )
                print(
                    f"release-gate: target={target} FAIL "
                    "installer-start"
                )
                continue
            if not gate.record(
                result.returncode == 0,
                f"installer exited {result.returncode} for {target}",
                install_issues,
            ):
                print(
                    f"release-gate: target={target} FAIL "
                    f"installer-exit={result.returncode}"
                )
                continue

            try:
                report = verify_target(
                    gate,
                    target,
                    target_home,
                    skill_relative,
                    agent_relative,
                    agent_ext,
                    agent_fmt,
                    expected_skills,
                    expected_agents,
                    sidecars,
                )
            except GateError as exc:
                install_issues.append(f"{target}: {exc}")
                print(
                    f"release-gate: target={target} FAIL verification"
                )
                continue

            metrics["verified_targets"] += 1
            metrics["sidecar_copies"] += report["sidecar_copies"]
            metrics["toml_files"] += report["toml_files"]
            print(
                f"release-gate: target={target} PASS "
                f"skills={len(expected_skills)} "
                f"agents={len(expected_agents)} "
                f"sidecars={report['sidecar_copies']} "
                f"toml={report['toml_files']}"
            )

    if install_issues:
        raise GateError(
            "disposable install checks failed: " + "; ".join(install_issues)
        )


def summary(
    status: str,
    gate: Gate,
    metrics: dict[str, int],
    error: Optional[str] = None,
) -> str:
    message = (
        f"release-gate: {status} "
        f"pass={gate.passed} fail={gate.failed} "
        f"targets-detected={metrics['targets']} "
        f"targets-checked={metrics['checked_targets']} "
        f"targets-verified={metrics['verified_targets']} "
        f"skills={metrics['skills']} agents={metrics['agents']} "
        f"sidecars={metrics['sidecars']} "
        f"sidecar-copies={metrics['sidecar_copies']} "
        f"codex-toml={metrics['toml_files']}"
    )
    if error:
        message += f" error={error}"
    return message


def main() -> int:
    gate = Gate()
    metrics = {
        "targets": 0,
        "checked_targets": 0,
        "verified_targets": 0,
        "skills": 0,
        "agents": 0,
        "sidecars": 0,
        "sidecar_copies": 0,
        "toml_files": 0,
    }

    try:
        check_existing_tools(gate)
        check_package_manifest(gate)

        sidecars = load_source_lock(gate)
        skills = load_component_registry(
            gate,
            "skill-lock.json",
            "skills",
        )
        agents = load_component_registry(
            gate,
            "agent-lock.json",
            "agents",
        )
        expected_skills, community_names = load_skill_identities(
            gate,
            skills,
        )
        prepare_sidecars(gate, sidecars, community_names)

        metrics["skills"] = len(expected_skills)
        metrics["agents"] = len(agents)
        metrics["sidecars"] = len(sidecars)

        run_disposable_installs(
            gate,
            expected_skills,
            agents,
            sidecars,
            metrics,
        )
    except GateError as exc:
        print(
            "\n" + summary("FAIL", gate, metrics, str(exc)),
            file=sys.stderr,
        )
        return 1
    except Exception as exc:
        gate.failed += 1
        print(
            "\n"
            + summary(
                "FAIL",
                gate,
                metrics,
                f"unexpected failure: {exc}",
            ),
            file=sys.stderr,
        )
        return 1

    print("\n" + summary("PASS", gate, metrics))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
