#!/usr/bin/env python3
"""Discover, normalize and stage third-party skills for human review.

Imports are staging-only. Symlinks, out-of-root paths and ambiguous target
collisions are rejected before any staged file is written.
"""
from __future__ import annotations

import hashlib
import os
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile

REPO = pathlib.Path(__file__).resolve().parents[1]
COMMUNITY = REPO / "community"

PERMISSIVE = (
    "mit license",
    "isc license",
    "bsd ",
    "apache license",
    "permission is hereby granted",
)
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


def detect_license(root: pathlib.Path) -> tuple[str, str]:
    for candidate in ("LICENSE", "LICENSE.md", "LICENSE.txt", "LICENCE", "COPYING"):
        path = root / candidate
        if path.exists() or path.is_symlink():
            path = safe_regular_file(path, root)
            text = path.read_text(encoding="utf-8")
            head = text[:600].lower()
            for phrase in PERMISSIVE:
                if phrase in head:
                    name = (
                        "MIT"
                        if "mit" in head
                        else "ISC"
                        if "isc" in head
                        else "Apache-2.0"
                        if "apache" in head
                        else "BSD"
                        if "bsd" in head
                        else "permissive"
                    )
                    return name, text
            return "NON-PERMISSIVE", text
    return "UNKNOWN", ""


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


def clone(url: str) -> pathlib.Path:
    tmp = pathlib.Path(tempfile.mkdtemp(prefix="skillsync-"))
    print(f"  cloning {url} (shallow) ...")
    result = subprocess.run(
        ["git", "clone", "--depth", "1", url, str(tmp)],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print("  ERROR cloning:", result.stderr.strip()[:200])
        shutil.rmtree(tmp, ignore_errors=True)
        sys.exit(2)
    return ensure_no_symlinks(tmp)


def cmd_discover(url: str):
    tmp = clone(url)
    try:
        license_name, _ = detect_license(tmp)
        skills = find_skills(tmp)
        print(f"\nSource: {url}")
        print(f"License: {license_name}")
        print(f"Skills found: {len(skills)}")
        redistributable = license_name in {
            "MIT",
            "ISC",
            "Apache-2.0",
            "BSD",
            "permissive",
        }
        print(f"Redistributable: {'YES' if redistributable else 'NO'}")
        risky = 0
        for skill_dir in skills[:200]:
            text = safe_regular_file(
                skill_dir / "SKILL.md", tmp
            ).read_text(encoding="utf-8")
            if scan_risk(text):
                risky += 1
        print(f"Skills with risk signals: {risky}/{len(skills)}")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def cmd_import(url: str, apply: bool):
    tmp = clone(url)
    try:
        license_name, license_text = detect_license(tmp)
        if license_name not in {
            "MIT",
            "ISC",
            "Apache-2.0",
            "BSD",
            "permissive",
        }:
            print(
                f"\nREFUSED: license is {license_name}. "
                "Only permissive licenses may be redistributed."
            )
            sys.exit(3)

        slug = slug_from_url(url)
        dest = safe_destination(COMMUNITY / slug, COMMUNITY)
        if dest.exists() or dest.is_symlink():
            raise SafetyError(
                f"staging destination already exists: {dest}; "
                "use a new reviewed snapshot instead of overwriting"
            )

        records = []
        seen_names: set[str] = set()
        for skill_dir in find_skills(tmp):
            name = safe_component(skill_dir.name)
            if name in seen_names:
                raise SafetyError(f"duplicate imported skill name: {name}")
            seen_names.add(name)
            source = safe_regular_file(skill_dir / "SKILL.md", tmp)
            text = source.read_text(encoding="utf-8")
            records.append(
                (
                    name,
                    text,
                    "ok" if frontmatter_ok(text) else "MISSING",
                    scan_risk(text),
                )
            )

        report = [
            f"# Import review - {markdown_cell(slug)}",
            "",
            f"- Source: {url}",
            f"- License: {license_name}",
            f"- Skills discovered: {len(records)}",
            "",
            "| skill | frontmatter | risk signals |",
            "|---|---|---|",
        ]
        for name, _, frontmatter_state, risks in records:
            report.append(
                f"| {markdown_cell(name)} | {frontmatter_state} | "
                f"{markdown_cell(', '.join(risks) or 'none')} |"
            )

        if apply:
            for name, text, _, _ in records:
                out = safe_destination(
                    dest / "skills" / name / "SKILL.md", COMMUNITY
                )
                out.parent.mkdir(parents=True, exist_ok=True)
                safe_destination(out, COMMUNITY)
                out.write_text(
                    normalize_skill(text, name, url, license_name),
                    encoding="utf-8",
                )

            dest.mkdir(parents=True, exist_ok=True)
            safe_destination(dest / "LICENSE", COMMUNITY).write_text(
                license_text or f"{license_name} License\n", encoding="utf-8"
            )
            safe_destination(dest / "REVIEW.md", COMMUNITY).write_text(
                "\n".join(report) + "\n", encoding="utf-8"
            )
            safe_destination(dest / "README.md", COMMUNITY).write_text(
                f"# {slug} (redistributed)\n\n"
                f"Content from {url}, redistributed under {license_name}.\n"
                f"- Skills: {len(records)}\n"
                "- See REVIEW.md for security review and LICENSE for terms.\n",
                encoding="utf-8",
            )
            print(f"\nStaged {len(records)} skills -> community/{slug}/")
        else:
            print("\n".join(report))
            print(
                f"\nDRY-RUN - {len(records)} skills would be staged to "
                f"community/{slug}/."
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


def main():
    args = sys.argv[1:]
    if len(args) < 2 or args[0] not in {"discover", "import", "normalize"}:
        print(__doc__)
        sys.exit(1)

    subcommand, target = args[0], args[1]
    if subcommand == "discover":
        cmd_discover(target)
    elif subcommand == "normalize":
        cmd_normalize(target, "--apply" in args)
    else:
        cmd_import(target, "--apply" in args)


if __name__ == "__main__":
    try:
        main()
    except SafetyError as exc:
        print(f"REFUSED: {exc}", file=sys.stderr)
        sys.exit(4)
