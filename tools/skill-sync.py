#!/usr/bin/env python3
"""Discover, normalize and stage third-party skills for human review.

Usage:
  skill-sync.py discover <url>
  skill-sync.py import <url> [--apply] [--accept-license <sha256> ...]
  skill-sync.py normalize <target> [--apply]

Imports are staging-only and never run, import or chmod imported code. Whole
skill packages are copied. Symlinks, out-of-root paths, ambiguous target
collisions, broken relative links and unreviewed licenses are rejected before
any staged file is written.
"""
from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import os
import pathlib
import posixpath
import re
import shutil
import stat
import subprocess
import sys
import tempfile
import urllib.parse

REPO = pathlib.Path(__file__).resolve().parents[1]
COMMUNITY = REPO / "community"
LICENSE_DIR = pathlib.Path(__file__).resolve().parent / "licenses"

MAX_FILE_BYTES = 1024 * 1024
MAX_FILES_PER_SKILL = 500
MAX_SKILL_BYTES = 10 * 1024 * 1024

SKIP_DIRS = {".git", "__pycache__"}
SKIP_FILES = {".DS_Store", "Thumbs.db"}
SKIP_SUFFIXES = (".pyc", ".pyo")
SCRIPT_EXTENSIONS = {
    ".py",
    ".sh",
    ".bash",
    ".zsh",
    ".js",
    ".mjs",
    ".cjs",
    ".ts",
    ".rb",
    ".pl",
    ".ps1",
    ".bat",
    ".cmd",
}
REFERENCE_EXTENSIONS = {".md", ".txt", ".json", ".yaml", ".yml", ".csv"}

LICENSE_NAMES = ("LICENSE", "LICENSE.md", "LICENSE.txt", "LICENCE", "COPYING")
LICENSE_PRIORITY = {name.upper(): index for index, name in enumerate(LICENSE_NAMES)}
SPDX_IDS = ("MIT", "ISC", "BSD-2-Clause", "BSD-3-Clause", "Apache-2.0")
LICENSE_FAMILIES = (
    ("permission is hereby granted", "MIT-like"),
    ("apache license", "Apache-like"),
    ("redistribution and use in source and binary forms", "BSD-like"),
    ("permission to use, copy, modify, and/or distribute", "ISC-like"),
)
APACHE_APPENDIX = "appendix: how to apply the apache license"

RISK_PATTERNS = {
    "shell-exec": re.compile(
        r"\b(subprocess|os\.system|child_process|exec\(|spawn\()", re.I
    ),
    "network": re.compile(
        r"\b(curl |wget |fetch\(|requests\.(get|post)|http://|https://)", re.I
    ),
    "secret-like": re.compile(
        r"(AKIA[0-9A-Z]{16}|sk_live_|ghp_[0-9A-Za-z]{36}|"
        r"-----BEGIN [A-Z ]*PRIVATE KEY)"
    ),
    "destructive": re.compile(
        r"\b(rm -rf|git push --force|DROP TABLE|TRUNCATE|force-?push)", re.I
    ),
    "injection-marker": re.compile(
        r"(ignore (all |previous )?instructions|you are now|disregard the)", re.I
    ),
}
SAFE_COMPONENT = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")

MD_LINK = re.compile(r"\]\(\s*(<[^>\n]*>|[^)\n]*)\)")
URL_SCHEME = re.compile(r"^[A-Za-z][A-Za-z0-9+.-]*:")
INLINE_PATH = re.compile(
    r"(?<![A-Za-z0-9_./~-])((?:scripts|references|templates|assets)/[A-Za-z0-9_./+-]+)"
)
INLINE_STOP_CHARS = "*?<{[$"

YEAR_LINE = re.compile(r"(?:19|20)\d{2}(?:\s*[-\u2013\u2014,]\s*(?:19|20)\d{2})*\.?")
COPYRIGHT_LINE = re.compile(r"copyright\b(?:\s*(?:\(c\)|\u00a9|\d{4}|<|\[)|\s+by\b)")
PLACEHOLDER = re.compile(r"<[a-z][a-z0-9 ._,@-]{0,60}>")
QUOTE_CHARS = {
    "'": '"',
    "\u201c": '"',
    "\u201d": '"',
    "\u2018": '"',
    "\u2019": '"',
}
MAX_COPYRIGHT_LINE = 200
# Title and notice lines that vary between copies of the same license. They are dropped on both
# sides before comparing, so they never hide a changed clause.
LICENSE_TITLE_LINES = {
    "mit license", "the mit license", "mit license (mit)", "the mit license (mit)",
    "isc license", "the isc license", "isc license (isc)",
    "bsd 2-clause license", "bsd 3-clause license", "the bsd 2-clause license",
    "the bsd 3-clause license", "bsd-2-clause license", "bsd-3-clause license",
    "simplified bsd license", "new bsd license", "modified bsd license",
    'bsd 2-clause "simplified" license', 'bsd 3-clause "new" or "revised" license',
    "all rights reserved", "all rights reserved.",
}
FENCE = re.compile(r"^\s{0,3}(```|~~~)")

_CANONICAL_CACHE: dict = {}


class SafetyError(RuntimeError):
    """Raised when imported content crosses a staging boundary."""


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
    for part in rel.parts:
        current = current / part
        if current.is_symlink():
            raise SafetyError(f"symlink path component is not allowed: {current}")


def ensure_no_symlinks(root: pathlib.Path) -> pathlib.Path:
    root = _lexical(root)
    if root.is_symlink():
        raise SafetyError(f"symlink root is not allowed: {root}")
    resolved = root.resolve(strict=True)
    for path in resolved.rglob("*"):
        if path.is_symlink():
            raise SafetyError(f"source tree contains a symlink: {path}")
    return resolved


def safe_regular_file(path: pathlib.Path, root: pathlib.Path) -> pathlib.Path:
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


def safe_destination(path: pathlib.Path, root: pathlib.Path) -> pathlib.Path:
    root = _lexical(root)
    path = _lexical(path)
    _relative(path, root)
    _reject_symlink_components(path, root)
    if path.exists() and not path.is_file():
        raise SafetyError(f"destination is not a regular file: {path}")
    return path


def safe_component(name: str) -> str:
    if name in {".", ".."} or not SAFE_COMPONENT.fullmatch(name):
        raise SafetyError(f"unsafe component name: {name!r}")
    return name


def slug_from_url(url: str) -> str:
    match = re.search(r"github\.com[:/]+([^/]+)/([^/.]+)", url)
    if match:
        raw = f"{match.group(1)}-{match.group(2)}"
    else:
        raw = re.sub(r"[^A-Za-z0-9._-]", "-", url).strip("._-") or "source"

    if len(raw) > 80:
        digest = hashlib.sha256(url.encode("utf-8")).hexdigest()[:12]
        raw = f"{raw[:63].rstrip('._-')}-{digest}"
    return safe_component(raw)


def markdown_cell(value: str) -> str:
    return (
        value.replace("\\", "\\\\")
        .replace("|", "\\|")
        .replace("\r", " ")
        .replace("\n", " ")
    )


# --- licenses -------------------------------------------------------------


def normalize_license_text(text: str, cut_apache_appendix: bool = False) -> str:
    """Reduce a license text to a comparable form (see classify_license)."""
    kept = []
    for line in text.lower().splitlines():
        stripped = line.strip()
        if stripped in LICENSE_TITLE_LINES:
            continue
        if len(stripped) <= MAX_COPYRIGHT_LINE and (
            COPYRIGHT_LINE.match(stripped)
            or (stripped.startswith("(c)") and re.search(r"\d{4}|<", stripped))
            or YEAR_LINE.fullmatch(stripped)
        ):
            continue
        kept.append(line)
    text = "\n".join(kept)
    for quote, plain in QUOTE_CHARS.items():
        text = text.replace(quote, plain)
    text = PLACEHOLDER.sub("", text)
    text = " ".join(text.split())
    if cut_apache_appendix:
        index = text.find(APACHE_APPENDIX)
        if index != -1:
            text = text[:index].rstrip()
    return text


def _canonical_normalized(spdx_id: str) -> str:
    cached = _CANONICAL_CACHE.get(spdx_id)
    if cached is None:
        path = LICENSE_DIR / f"{spdx_id}.txt"
        try:
            raw = path.read_text(encoding="utf-8", errors="replace")
        except OSError as exc:
            raise SafetyError(f"canonical license text is missing: {path}") from exc
        cached = normalize_license_text(raw, spdx_id == "Apache-2.0")
        _CANONICAL_CACHE[spdx_id] = cached
    return cached


def _license_summary(file, sha256, candidate: str, status: str) -> dict:
    return {"file": file, "sha256": sha256, "candidate": candidate, "status": status}


def classify_license(path, root=None) -> dict:
    """Classify one license file as a candidate, never as a verdict."""
    if path is None:
        return _license_summary(None, None, "unknown", "unknown")
    path = _lexical(pathlib.Path(path))
    if root is not None:
        root = _lexical(pathlib.Path(root))
        safe_regular_file(path, root)
        file_name = _relative(path, root).as_posix()
    else:
        file_name = path.name
    if path.stat().st_size > MAX_FILE_BYTES:
        raise SafetyError(f"license file is larger than 1 MiB: {path}")
    data = path.read_bytes()
    sha256 = hashlib.sha256(data).hexdigest()
    text = data.decode("utf-8", errors="replace")

    normalized = normalize_license_text(text)
    if normalized:
        for spdx_id in SPDX_IDS:
            candidate_text = (
                normalize_license_text(text, True)
                if spdx_id == "Apache-2.0"
                else normalized
            )
            if candidate_text == _canonical_normalized(spdx_id):
                return _license_summary(file_name, sha256, spdx_id, "recognized")
        for phrase, family in LICENSE_FAMILIES:
            if phrase in normalized:
                return _license_summary(file_name, sha256, family, "needs-review")
    return _license_summary(file_name, sha256, "unknown", "unknown")


def _license_files_in(directory: pathlib.Path) -> list:
    found = []
    try:
        names = sorted(os.listdir(directory))
    except OSError:
        return found
    for name in names:
        if name.upper() in LICENSE_PRIORITY:
            path = directory / name
            if path.is_file() and not path.is_symlink():
                found.append(path)
    found.sort(key=lambda p: (LICENSE_PRIORITY[p.name.upper()], p.name))
    return found


def _all_license_files(root: pathlib.Path) -> list:
    found = []
    for current, dirnames, filenames in os.walk(root, followlinks=False):
        dirnames[:] = sorted(d for d in dirnames if d != ".git")
        for name in sorted(filenames):
            if name.upper() in LICENSE_PRIORITY:
                path = pathlib.Path(current) / name
                if path.is_file() and not path.is_symlink():
                    found.append(path)
    found.sort(key=lambda p: p.relative_to(root).as_posix())
    return found


def license_report(clone_root: pathlib.Path, skill_dirs: list) -> dict:
    """Classify the root license, every license file and each skill's license."""
    root = _lexical(pathlib.Path(clone_root))
    infos = {}
    for path in _all_license_files(root):
        infos[path.relative_to(root).as_posix()] = classify_license(path, root)

    root_files = _license_files_in(root)
    if root_files:
        root_info = infos[root_files[0].relative_to(root).as_posix()]
    else:
        root_info = classify_license(None)

    skills = {}
    conflicts = []
    for skill_dir in skill_dirs:
        skill_dir = _lexical(pathlib.Path(skill_dir))
        key = _relative(skill_dir, root).as_posix()
        effective = None
        current = skill_dir
        while True:
            files = _license_files_in(current)
            if files:
                effective = infos[files[0].relative_to(root).as_posix()]
                break
            if current == root or current == current.parent:
                break
            current = current.parent
        if effective is None:
            effective = classify_license(None)
        skills[key] = effective
        if (
            effective["file"] is not None
            and effective["file"] != root_info["file"]
            and (
                effective["candidate"] != root_info["candidate"]
                or effective["sha256"] != root_info["sha256"]
            )
        ):
            conflict = dict(effective)
            conflict["skill"] = key
            conflict["root_file"] = root_info["file"]
            conflict["root_candidate"] = root_info["candidate"]
            conflicts.append(conflict)

    return {
        "root": root_info,
        "files": [infos[key] for key in sorted(infos)],
        "skills": skills,
        "conflicts": conflicts,
    }


def license_refusals(report: dict, accepted: set) -> list:
    """Return the license files that block the import, with affected skills."""
    refused = {}
    for skill, info in report["skills"].items():
        if info["status"] == "recognized" and info["candidate"] in SPDX_IDS:
            continue
        if info["status"] == "needs-review" and info["sha256"] in accepted:
            continue
        entry = refused.setdefault(
            (info["file"], info["sha256"]), dict(info, skills=[])
        )
        entry["skills"].append(skill)
    return list(refused.values())


def refusal_message(refused: list) -> str:
    lines = ["", "REFUSED: license review is required before this import."]
    for item in refused:
        lines.append(f"  license file: {item['file'] or '(none found)'}")
        lines.append(f"    candidate: {item['candidate']}")
        lines.append(f"    status:    {item['status']}")
        lines.append(f"    sha256:    {item['sha256'] or '(none)'}")
        if item["status"] == "needs-review":
            lines.append(
                f"    after human review: --accept-license {item['sha256']}"
            )
        else:
            lines.append("    cannot be accepted: license is unknown")
        lines.append(f"    skills:    {', '.join(item['skills'])}")
    return "\n".join(lines)


def _with_decision(info: dict, accepted: set) -> dict:
    result = dict(info)
    if info["status"] == "needs-review" and info["sha256"] in accepted:
        result["decision"] = "accepted-by-reviewer"
    return result


# --- skills ---------------------------------------------------------------


def find_skills(root: pathlib.Path) -> list[pathlib.Path]:
    root = ensure_no_symlinks(root)
    skill_dirs = []
    for path in sorted(root.rglob("SKILL.md")):
        safe_regular_file(path, root)
        skill_dirs.append(path.parent)
    return skill_dirs


def frontmatter_ok(text: str) -> bool:
    match = re.match(r"^---\n(.*?)\n---", text, re.S)
    return bool(
        match
        and "name:" in match.group(1)
        and "description:" in match.group(1)
    )


def scan_risk(text: str) -> list[str]:
    return [name for name, pattern in RISK_PATTERNS.items() if pattern.search(text)]


def _split_frontmatter(text: str) -> tuple[str, str]:
    match = re.match(r"^---\n(.*?)\n---[ \t]*\n?", text, re.S)
    if not match:
        return "", text
    return match.group(1), text[match.end() :]


def _first_sentence(body: str) -> str:
    for line in body.splitlines():
        line = line.strip()
        if not line or line.startswith("<!--") or line.startswith(chr(96) * 3):
            continue
        line = re.sub(r"^#+\s*", "", line)
        line = re.sub(r"[*_\x60]", "", line).strip()
        if line:
            sentence = re.split(r"(?<=[.!?])\s", line)[0]
            return sentence[:160].rstrip()
    return ""


def normalize_skill(text: str, slug: str, url: str, license_name: str) -> str:
    frontmatter, rest = _split_frontmatter(text)
    fields = dict(
        re.findall(r"(?m)^([A-Za-z0-9_-]+):[ \t]*(.*)$", frontmatter)
    )
    name = fields.get("name", "").strip()
    description = fields.get("description", "").strip()

    if not name:
        name = re.sub(r"^\d+[-_]", "", slug).replace("_", "-")
        frontmatter = (
            frontmatter + "\n" if frontmatter.strip() else ""
        ) + f"name: {name}"
    if not description:
        description = _first_sentence(rest) or f"Imported skill: {name}."
        frontmatter = frontmatter + f"\ndescription: {description}"

    text = f"---\n{frontmatter.strip()}\n---\n{rest}"
    marker = f"<!-- skillry:source {url} ({license_name}) -->"
    if "<!-- skillry:source" not in text:
        head, body = _split_frontmatter(text)
        text = f"---\n{head.strip()}\n---\n{marker}\n{body.lstrip(chr(10))}"

    def fix_h1(match: re.Match) -> str:
        current = match.group(1).strip()
        same = re.sub(r"[^a-z0-9]", "", current.lower()) == re.sub(
            r"[^a-z0-9]", "", name.lower()
        )
        return match.group(0) if same else f"# {name}"

    return re.sub(r"(?m)^#[ \t]+(.+)$", fix_h1, text, count=1)


def classify_kind(rel: str, executable: bool) -> str:
    if rel == "SKILL.md":
        return "skill"
    extension = posixpath.splitext(rel)[1].lower()
    if extension in SCRIPT_EXTENSIONS or executable:
        return "script"
    if extension in REFERENCE_EXTENSIONS:
        return "reference"
    return "asset"


def collect_skill_files(skill_dir: pathlib.Path, root: pathlib.Path) -> list[dict]:
    """Collect every regular file of one skill package, refusing unsafe content."""
    name = skill_dir.name
    found = []
    seen_lower: set[str] = set()
    total = 0
    for current, dirnames, filenames in os.walk(skill_dir, followlinks=False):
        current_path = pathlib.Path(current)
        for dirname in list(dirnames):
            if (current_path / dirname).is_symlink():
                raise SafetyError(
                    f"skill {name} contains a symlink: {current_path / dirname}"
                )
            if dirname in SKIP_DIRS:
                dirnames.remove(dirname)
        dirnames.sort()
        for filename in sorted(filenames):
            full = current_path / filename
            if full.is_symlink():
                raise SafetyError(f"skill {name} contains a symlink: {full}")
            if (
                filename == ".git"
                or filename in SKIP_FILES
                or filename.endswith(SKIP_SUFFIXES)
            ):
                continue
            info = os.lstat(full)
            if not stat.S_ISREG(info.st_mode):
                raise SafetyError(f"skill {name} contains a non-regular file: {full}")
            safe_regular_file(full, root)
            rel = full.relative_to(skill_dir).as_posix()
            if info.st_size > MAX_FILE_BYTES:
                raise SafetyError(
                    f"skill {name}: file is larger than 1 MiB: {rel} "
                    f"({info.st_size} bytes)"
                )
            if rel.lower() in seen_lower:
                raise SafetyError(
                    f"skill {name}: file names differ only by case: {rel}"
                )
            seen_lower.add(rel.lower())
            data = full.read_bytes()
            total += len(data)
            if len(found) + 1 > MAX_FILES_PER_SKILL:
                raise SafetyError(
                    f"skill {name} has more than {MAX_FILES_PER_SKILL} files"
                )
            if total > MAX_SKILL_BYTES:
                raise SafetyError(f"skill {name} is larger than 10 MiB")
            executable = bool(info.st_mode & 0o111)
            found.append(
                {
                    "path": rel,
                    "abs": full,
                    "bytes": len(data),
                    "sha256": hashlib.sha256(data).hexdigest(),
                    "kind": classify_kind(rel, executable),
                    "executable": executable,
                }
            )
    found.sort(key=lambda item: item["path"])
    return found


def _link_target(raw: str) -> str:
    raw = raw.strip()
    if raw.startswith("<"):
        end = raw.find(">")
        return raw[1:end] if end != -1 else raw[1:]
    parts = raw.split()
    return parts[0] if parts else ""


def _resolve_in_skill(md_dir: str, target: str):
    """Return the skill-relative POSIX path, or None when it escapes the skill."""
    if target.startswith("/"):
        return None
    joined = posixpath.normpath(posixpath.join(md_dir, target))
    if joined == ".." or joined.startswith("../"):
        return None
    return joined


def _without_fences(text: str) -> str:
    kept, fence = [], None
    for line in text.splitlines():
        match = FENCE.match(line)
        if match and (fence is None or match.group(1) == fence):
            fence = None if fence else match.group(1)
            kept.append("")
            continue
        kept.append("" if fence else line)
    return "\n".join(kept)


def check_links(skill_name: str, files: list[dict], root: pathlib.Path) -> list[str]:
    """Return one error line per broken relative link in the skill's .md files."""
    known = {item["path"] for item in files}
    errors: list[str] = []
    seen: set = set()

    def report(md_rel: str, target: str, reason: str) -> None:
        key = (md_rel, target, reason)
        if key not in seen:
            seen.add(key)
            errors.append(f"{skill_name}/{md_rel}: {target} ({reason})")

    def check(md_rel: str, md_dir: str, raw_target: str) -> None:
        resolved = _resolve_in_skill(md_dir, raw_target)
        if resolved is None:
            report(md_rel, raw_target, "link escapes the skill")
        elif resolved not in known and not any(path.startswith(resolved + "/") for path in known):
            # A link to a folder is fine when the folder holds at least one collected file.
            report(md_rel, raw_target, "missing link target")

    for item in files:
        md_rel = item["path"]
        if not md_rel.lower().endswith(".md"):
            continue
        text = safe_regular_file(item["abs"], root).read_bytes().decode(
            "utf-8", errors="replace"
        )
        md_dir = posixpath.dirname(md_rel)
        # Example links inside fenced code blocks are not references; inline paths below still count.
        for match in MD_LINK.finditer(_without_fences(text)):
            raw = _link_target(match.group(1))
            if not raw or raw.startswith("#") or raw.startswith("//"):
                continue
            if URL_SCHEME.match(raw):
                continue
            target = re.split(r"[#?]", raw, maxsplit=1)[0]
            if not target:
                continue
            check(md_rel, md_dir, urllib.parse.unquote(target))
        if md_rel == "SKILL.md":
            for match in INLINE_PATH.finditer(text):
                following = text[match.end() : match.end() + 1]
                if following and following in INLINE_STOP_CHARS:
                    continue
                target = match.group(1).rstrip(".")
                if target.endswith("/"):
                    continue
                check(md_rel, "", target)
    return errors


def git_head(clone_root: pathlib.Path) -> str:
    result = subprocess.run(
        ["git", "-C", str(clone_root), "rev-parse", "HEAD"],
        capture_output=True,
        text=True,
    )
    value = result.stdout.strip()
    if result.returncode == 0 and value:
        return value
    return "unknown"


def clone(url: str) -> pathlib.Path:
    tmp = pathlib.Path(tempfile.mkdtemp(prefix="skillsync-"))
    print(f"  cloning {url} (shallow) ...")
    env = dict(os.environ, GIT_TERMINAL_PROMPT="0")
    result = subprocess.run(
        ["git", "clone", "--depth", "1", "--", url, str(tmp)],
        capture_output=True,
        text=True,
        env=env,
    )
    if result.returncode != 0:
        print("  ERROR cloning:", result.stderr.strip()[:200])
        shutil.rmtree(tmp, ignore_errors=True)
        sys.exit(2)
    try:
        return ensure_no_symlinks(tmp)
    except BaseException:
        shutil.rmtree(tmp, ignore_errors=True)
        raise


def _redistributable_line(status: str) -> str:
    if status == "recognized":
        return "Redistributable: yes (recognized)"
    if status == "needs-review":
        return "Redistributable: needs human review"
    return "Redistributable: no"


def cmd_discover(url: str):
    tmp = clone(url)
    try:
        skills = find_skills(tmp)
        report = license_report(tmp, skills)
        root = report["root"]
        print(f"\nSource: {url}")
        print(f"License (candidate): {root['candidate']} - {root['status']}")
        if root["file"]:
            print(f"License file: {root['file']} (sha256 {root['sha256']})")
        print(f"Skills found: {len(skills)}")
        print(_redistributable_line(root["status"]))
        for conflict in report["conflicts"]:
            print(
                f"License conflict: {conflict['skill']} uses {conflict['file']} "
                f"({conflict['candidate']} - {conflict['status']}), "
                f"root is {conflict['root_file']} ({conflict['root_candidate']})"
            )
        risky = 0
        for skill_dir in skills[:200]:
            text = safe_regular_file(
                skill_dir / "SKILL.md", tmp
            ).read_bytes().decode("utf-8", errors="replace")
            if scan_risk(text):
                risky += 1
        print(f"Skills with risk signals: {risky}/{len(skills)}")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def _read_skill_text(path: pathlib.Path, name: str) -> str:
    try:
        text = path.read_bytes().decode("utf-8")
    except UnicodeDecodeError as exc:
        raise SafetyError(f"skill {name}: SKILL.md is not valid UTF-8") from exc
    return text.replace("\r\n", "\n").replace("\r", "\n")


def build_records(
    skills: list[pathlib.Path],
    tmp: pathlib.Path,
    report: dict,
    url: str,
    accepted: set,
) -> list[dict]:
    """Collect files, check links, scan risks and normalize SKILL.md for each skill."""
    records = []
    seen_names: set[str] = set()
    link_errors: list[str] = []
    for skill_dir in skills:
        name = safe_component(skill_dir.name)
        if name in seen_names:
            raise SafetyError(f"duplicate imported skill name: {name}")
        seen_names.add(name)
        files = collect_skill_files(skill_dir, tmp)
        link_errors.extend(check_links(name, files, tmp))
        license_info = _with_decision(
            report["skills"][skill_dir.relative_to(tmp).as_posix()], accepted
        )
        source = safe_regular_file(skill_dir / "SKILL.md", tmp)
        text = _read_skill_text(source, name)
        normalized = normalize_skill(text, name, url, license_info["candidate"])
        normalized_bytes = normalized.encode("utf-8")
        scripts = []
        for item in files:
            if item["kind"] == "script":
                script_text = safe_regular_file(item["abs"], tmp).read_bytes().decode(
                    "utf-8", errors="replace"
                )
                scripts.append((item, scan_risk(script_text)))
        records.append(
            {
                "name": name,
                "files": files,
                "license": license_info,
                "frontmatter": "ok" if frontmatter_ok(text) else "MISSING",
                "risks": scan_risk(text),
                "normalized": normalized_bytes,
                "scripts": scripts,
            }
        )
    if link_errors:
        raise SafetyError(
            "broken relative links in imported skills; nothing was written:\n  "
            + "\n  ".join(link_errors)
        )
    records.sort(key=lambda record: record["name"])
    return records


def build_manifest(
    url: str,
    commit: str,
    report: dict,
    records: list[dict],
    accepted: set,
) -> dict:
    skills = []
    for record in records:
        entries = []
        for item in record["files"]:
            if item["kind"] == "skill":
                entry = {
                    "path": item["path"],
                    "sha256": hashlib.sha256(record["normalized"]).hexdigest(),
                    "bytes": len(record["normalized"]),
                    "kind": "skill",
                    "executable": item["executable"],
                    "source_sha256": item["sha256"],
                }
            else:
                entry = {
                    "path": item["path"],
                    "sha256": item["sha256"],
                    "bytes": item["bytes"],
                    "kind": item["kind"],
                    "executable": item["executable"],
                }
            entries.append(entry)
        skills.append(
            {"name": record["name"], "license": record["license"], "files": entries}
        )
    return {
        "schema_version": 1,
        "source_url": url,
        "source_commit": commit,
        "imported_on": datetime.datetime.now(datetime.timezone.utc).strftime(
            "%Y-%m-%d"
        ),
        "license": _with_decision(report["root"], accepted),
        "license_files": report["files"],
        "conflicts": report["conflicts"],
        "accepted_licenses": [
            _with_decision(info, accepted)
            for info in report["files"]
            if info["status"] == "needs-review" and info["sha256"] in accepted
        ],
        "skills": skills,
    }


def render_review(
    slug: str, url: str, commit: str, report: dict, records: list[dict], accepted: set
) -> str:
    root = report["root"]
    file_count = sum(len(record["files"]) for record in records)
    lines = [
        f"# Import review - {markdown_cell(slug)}",
        "",
        f"- Source: {url}",
        f"- Commit: {commit}",
        f"- License (candidate): {markdown_cell(root['candidate'])} - {root['status']}",
        f"- Skills discovered: {len(records)}",
        f"- Files staged: {file_count}",
        "",
        "| skill | frontmatter | risk signals |",
        "|---|---|---|",
    ]
    for record in records:
        lines.append(
            f"| {markdown_cell(record['name'])} | {record['frontmatter']} | "
            f"{markdown_cell(', '.join(record['risks']) or 'none')} |"
        )

    lines += [
        "",
        "## Licenses",
        "",
        "License detection is a candidate, not a verdict. A human reviews every",
        "license that is not recognized.",
        "",
        "| license file | candidate | status | sha256 | decision |",
        "|---|---|---|---|---|",
    ]
    for info in report["files"]:
        decision = _with_decision(info, accepted).get("decision", "-")
        lines.append(
            f"| {markdown_cell(info['file'])} | {markdown_cell(info['candidate'])} | "
            f"{info['status']} | {info['sha256']} | {decision} |"
        )
    if not report["files"]:
        lines.append("| (none found) | unknown | unknown | - | - |")

    lines += ["", "### License conflicts", ""]
    if report["conflicts"]:
        for conflict in report["conflicts"]:
            lines.append(
                f"- {markdown_cell(conflict['skill'])}: {markdown_cell(conflict['file'])} "
                f"({markdown_cell(conflict['candidate'])}, {conflict['status']}) differs "
                f"from the root license {markdown_cell(str(conflict['root_file']))} "
                f"({markdown_cell(conflict['root_candidate'])})"
            )
    else:
        lines.append("None.")

    lines += ["", "## Scripts that need review before anyone runs them", ""]
    script_rows = [
        (record["name"], item, risks)
        for record in records
        for item, risks in record["scripts"]
    ]
    if script_rows:
        lines += [
            "Nothing was executed, imported or made executable during this import.",
            "",
            "| skill | script | executable in source | risk signals |",
            "|---|---|---|---|",
        ]
        for name, item, risks in script_rows:
            lines.append(
                f"| {markdown_cell(name)} | {markdown_cell(item['path'])} | "
                f"{'yes' if item['executable'] else 'no'} | "
                f"{markdown_cell(', '.join(risks) or 'none')} |"
            )
    else:
        lines.append("No scripts were found.")
    return "\n".join(lines) + "\n"


def cmd_import(url: str, apply: bool, accept=None):
    accepted = {value.strip().lower() for value in (accept or [])}
    tmp = clone(url)
    try:
        skills = find_skills(tmp)
        if not skills:
            print(f"No SKILL.md found in {url}")
            sys.exit(2)

        report = license_report(tmp, skills)
        refused = license_refusals(report, accepted)
        if refused:
            print(refusal_message(refused))
            sys.exit(3)
        known = {info["sha256"] for info in report["files"]}
        for value in sorted(accepted - known):
            print(f"  note: --accept-license {value} matches no license file")

        slug = slug_from_url(url)
        dest = safe_destination(COMMUNITY / slug, COMMUNITY)
        if dest.exists() or dest.is_symlink():
            raise SafetyError(
                f"staging destination already exists: {dest}; "
                "use a new reviewed snapshot instead of overwriting"
            )

        records = build_records(skills, tmp, report, url, accepted)
        commit = git_head(tmp)
        manifest = build_manifest(url, commit, report, records, accepted)
        review = render_review(slug, url, commit, report, records, accepted)
        file_count = sum(len(record["files"]) for record in records)

        if apply:
            plan = []
            for record in records:
                for item in record["files"]:
                    out = safe_destination(
                        dest.joinpath(
                            "skills", record["name"], *item["path"].split("/")
                        ),
                        COMMUNITY,
                    )
                    plan.append((out, record, item))
            for name in ("LICENSE", "REVIEW.md", "README.md", "IMPORT-MANIFEST.json"):
                safe_destination(dest / name, COMMUNITY)

            for out, record, item in plan:
                out.parent.mkdir(parents=True, exist_ok=True)
                safe_destination(out, COMMUNITY)
                if item["kind"] == "skill":
                    out.write_bytes(record["normalized"])
                    continue
                source = safe_regular_file(item["abs"], tmp)
                data = source.read_bytes()
                if hashlib.sha256(data).hexdigest() != item["sha256"]:
                    raise SafetyError(f"file changed during import: {item['path']}")
                out.write_bytes(data)

            dest.mkdir(parents=True, exist_ok=True)
            root = report["root"]
            if root["file"]:
                license_bytes = safe_regular_file(tmp / root["file"], tmp).read_bytes()
            else:
                license_bytes = (
                    b"No root license file was found in the source repository.\n"
                    b"See the license files inside each skill and IMPORT-MANIFEST.json.\n"
                )
            safe_destination(dest / "LICENSE", COMMUNITY).write_bytes(license_bytes)
            safe_destination(dest / "REVIEW.md", COMMUNITY).write_text(
                review, encoding="utf-8"
            )
            safe_destination(dest / "README.md", COMMUNITY).write_text(
                f"# {slug} (redistributed)\n\n"
                f"Content from {url}, license candidate {root['candidate']} "
                f"({root['status']}).\n"
                f"- Skills: {len(records)}\n"
                f"- Files: {file_count}\n"
                "- See REVIEW.md for security review, LICENSE for terms and "
                "IMPORT-MANIFEST.json for the file list.\n",
                encoding="utf-8",
            )
            safe_destination(dest / "IMPORT-MANIFEST.json", COMMUNITY).write_text(
                json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
            )
            print(
                f"\nStaged {len(records)} skills ({file_count} files) -> "
                f"community/{slug}/"
            )
        else:
            print(review)
            print(
                f"\nDRY-RUN - {len(records)} skills ({file_count} files) would be "
                f"staged to community/{slug}/."
            )
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def normalize_base(target: str) -> pathlib.Path:
    raw = pathlib.Path(target).expanduser()
    if raw.is_absolute():
        candidate = raw
    elif raw.parts and raw.parts[0] == "community":
        candidate = REPO / raw
    else:
        candidate = COMMUNITY / raw

    candidate = _lexical(candidate)
    _relative(candidate, _lexical(COMMUNITY))
    _reject_symlink_components(candidate, _lexical(COMMUNITY))
    if not candidate.exists():
        raise SafetyError(f"normalize target does not exist: {candidate}")
    resolved = candidate.resolve(strict=True)
    _relative(resolved, COMMUNITY.resolve(strict=True))
    return candidate


def cmd_normalize(target: str, apply: bool):
    base = normalize_base(target)
    if base.is_dir():
        ensure_no_symlinks(base)
        files = sorted(base.rglob("SKILL.md"))
    elif base.name == "SKILL.md":
        files = [base]
    else:
        files = []

    if not files:
        print(f"No SKILL.md found under {base}")
        sys.exit(2)

    updates = []
    for path in files:
        source = safe_regular_file(path, COMMUNITY.resolve(strict=True))
        text = source.read_text(encoding="utf-8")
        match = re.search(
            r"<!-- skillry:source (\S+) \(([^)]+)\) -->", text
        )
        url = match.group(1) if match else "unknown"
        license_name = match.group(2) if match else "permissive"
        new = normalize_skill(text, source.parent.name, url, license_name)
        updates.append((source, text, new))

    for source, old, new in updates:
        status = "unchanged" if new == old else "NORMALIZED"
        if new != old and apply:
            safe_destination(source, COMMUNITY).write_text(new, encoding="utf-8")
        print(f"  {status}: {source.relative_to(COMMUNITY)}")

    changed = sum(1 for _, old, new in updates if old != new)
    verb = f"Rewrote {changed}" if apply else f"{changed} would change"
    print(f"\n{verb} of {len(updates)} SKILL.md under {base}.")


class _Parser(argparse.ArgumentParser):
    """ArgumentParser that exits with 1 (usage) instead of argparse's 2."""

    def error(self, message):
        self.print_usage(sys.stderr)
        print(f"{self.prog}: error: {message}", file=sys.stderr)
        sys.exit(1)


def _sha256_arg(value: str) -> str:
    value = value.strip().lower()
    if not re.fullmatch(r"[0-9a-f]{64}", value):
        raise argparse.ArgumentTypeError(f"not a sha256 hex digest: {value!r}")
    return value


def build_parser() -> argparse.ArgumentParser:
    parser = _Parser(
        prog="skill-sync.py",
        description=__doc__.split("\n\n")[0],
    )
    sub = parser.add_subparsers(dest="command", required=True)

    discover = sub.add_parser("discover", help="report license and skills of a repo")
    discover.add_argument("url", help="git URL, file:// URL or local path")

    imp = sub.add_parser("import", help="stage a repo's skills under community/")
    imp.add_argument("url", help="git URL, file:// URL or local path")
    imp.add_argument("--apply", action="store_true", help="write the staged files")
    imp.add_argument(
        "--accept-license",
        action="append",
        default=[],
        type=_sha256_arg,
        metavar="SHA256",
        help="accept a license file after human review (repeatable)",
    )

    norm = sub.add_parser("normalize", help="normalize staged SKILL.md files")
    norm.add_argument("target", help="path under community/")
    norm.add_argument("--apply", action="store_true", help="rewrite the files")
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    if args.command == "discover":
        cmd_discover(args.url)
    elif args.command == "normalize":
        cmd_normalize(args.target, args.apply)
    else:
        cmd_import(args.url, args.apply, args.accept_license)


if __name__ == "__main__":
    try:
        main()
    except SafetyError as exc:
        print(f"REFUSED: {exc}", file=sys.stderr)
        sys.exit(4)
