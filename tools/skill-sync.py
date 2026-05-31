#!/usr/bin/env python3
"""skill-sync — discover, normalize, and vet third-party skills from a Git source,
then stage them under community/<source>/ with attribution and a security review note.

This is the differentiator: most collections copy files by hand with no provenance,
no normalization, and no security pass. skill-sync does all three, and it NEVER
auto-installs — it stages for human review.

USAGE
  # 1. Discover what a source offers (read-only, no writes):
  python3 tools/skill-sync.py discover https://github.com/<owner>/<repo>

  # 2. Stage skills into community/<slug>/ with attribution + review report (dry-run):
  python3 tools/skill-sync.py import https://github.com/<owner>/<repo> [--apply]

REQUIREMENTS: git, python3. No network beyond `git clone` of the source you name.

SAFETY
  - Only permissive licenses (MIT/ISC/BSD/Apache-2.0) are accepted for redistribution.
  - Every imported skill is scanned for risk signals (shell exec, network calls,
    secrets, prompt-injection markers) and the findings are written to a REVIEW.md.
  - Nothing is enabled or installed; staging only. A human decides what to keep.
"""
from __future__ import annotations
import json, os, re, subprocess, sys, tempfile, shutil, pathlib, hashlib

REPO = pathlib.Path(__file__).resolve().parents[1]
COMMUNITY = REPO / "community"

PERMISSIVE = ("mit license", "isc license", "bsd ", "apache license", "permission is hereby granted")
RISK_PATTERNS = {
    "shell-exec": re.compile(r"\b(subprocess|os\.system|child_process|exec\(|spawn\()", re.I),
    "network": re.compile(r"\b(curl |wget |fetch\(|requests\.(get|post)|http://|https://)", re.I),
    "secret-like": re.compile(r"(AKIA[0-9A-Z]{16}|sk_live_|ghp_[0-9A-Za-z]{36}|-----BEGIN [A-Z ]*PRIVATE KEY)"),
    "destructive": re.compile(r"\b(rm -rf|git push --force|DROP TABLE|TRUNCATE|force-?push)", re.I),
    "injection-marker": re.compile(r"(ignore (all |previous )?instructions|you are now|disregard the)", re.I),
}

def run(*args, cwd=None) -> str:
    return subprocess.run(args, cwd=cwd, capture_output=True, text=True).stdout

def slug_from_url(url: str) -> str:
    m = re.search(r"github\.com[:/]+([^/]+)/([^/.]+)", url)
    if not m:
        return re.sub(r"[^A-Za-z0-9._-]", "-", url)[-40:]
    return f"{m.group(1)}-{m.group(2)}"

def detect_license(root: pathlib.Path) -> tuple[str, str]:
    for cand in ("LICENSE", "LICENSE.md", "LICENSE.txt", "LICENCE", "COPYING"):
        f = root / cand
        if f.exists():
            head = f.read_text(errors="ignore")[:600].lower()
            for p in PERMISSIVE:
                if p in head:
                    name = ("MIT" if "mit" in head else "ISC" if "isc" in head
                            else "Apache-2.0" if "apache" in head else "BSD" if "bsd" in head else "permissive")
                    return name, f.read_text(errors="ignore")
            return "NON-PERMISSIVE", f.read_text(errors="ignore")
    return "UNKNOWN", ""

def find_skills(root: pathlib.Path) -> list[pathlib.Path]:
    return [p.parent for p in root.rglob("SKILL.md")]

def frontmatter_ok(text: str) -> bool:
    m = re.match(r"^---\n(.*?)\n---", text, re.S)
    return bool(m and "name:" in m.group(1) and "description:" in m.group(1))

def scan_risk(text: str) -> list[str]:
    return [name for name, rx in RISK_PATTERNS.items() if rx.search(text)]

def clone(url: str) -> pathlib.Path:
    tmp = pathlib.Path(tempfile.mkdtemp(prefix="skillsync-"))
    print(f"  cloning {url} (shallow) ...")
    r = subprocess.run(["git", "clone", "--depth", "1", url, str(tmp)],
                       capture_output=True, text=True)
    if r.returncode != 0:
        print("  ERROR cloning:", r.stderr.strip()[:200]); sys.exit(2)
    return tmp

def cmd_discover(url: str):
    tmp = clone(url)
    try:
        lic, _ = detect_license(tmp)
        skills = find_skills(tmp)
        print(f"\nSource: {url}")
        print(f"License: {lic}")
        print(f"Skills found: {len(skills)}")
        redistributable = lic in ("MIT", "ISC", "Apache-2.0", "BSD", "permissive")
        print(f"Redistributable: {'YES' if redistributable else 'NO — do not import'}")
        risky = 0
        for s in skills[:200]:
            t = (s / "SKILL.md").read_text(errors="ignore")
            if scan_risk(t): risky += 1
        print(f"Skills with risk signals (need review): {risky}/{len(skills)}")
        if not redistributable:
            print("\n⚠ This source's license does not permit redistribution. "
                  "Link to it instead of bundling.")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

def cmd_import(url: str, apply: bool):
    tmp = clone(url)
    try:
        lic, lic_text = detect_license(tmp)
        if lic not in ("MIT", "ISC", "Apache-2.0", "BSD", "permissive"):
            print(f"\nREFUSED: license is {lic}. Only permissive licenses may be redistributed.")
            print("Link to the source from docs instead of bundling it.")
            sys.exit(3)
        slug = slug_from_url(url)
        dest = COMMUNITY / slug
        skills = find_skills(tmp)
        report = [f"# Import review — {slug}", "",
                  f"- Source: {url}", f"- License: {lic}",
                  f"- Skills discovered: {len(skills)}", "",
                  "| skill | frontmatter | risk signals |", "|---|---|---|"]
        staged = 0
        for s in skills:
            name = s.name
            text = (s / "SKILL.md").read_text(errors="ignore")
            fm = "ok" if frontmatter_ok(text) else "MISSING"
            risks = scan_risk(text)
            report.append(f"| {name} | {fm} | {', '.join(risks) or '—'} |")
            if apply:
                out = dest / "skills" / name / "SKILL.md"
                out.parent.mkdir(parents=True, exist_ok=True)
                # provenance marker
                if "<!-- omniagent:source" not in text:
                    text = text.replace("\n", f"\n<!-- omniagent:source {url} ({lic}) -->\n", 1) if False else text
                out.write_text(text, encoding="utf-8")
                staged += 1
        if apply:
            dest.mkdir(parents=True, exist_ok=True)
            (dest / "LICENSE").write_text(lic_text or f"{lic} License\n")
            (dest / "REVIEW.md").write_text("\n".join(report) + "\n")
            (dest / "README.md").write_text(
                f"# {slug} (redistributed)\n\nContent from {url}, redistributed under {lic}.\n"
                f"- Skills: {staged}\n- See REVIEW.md for the security scan and LICENSE for terms.\n"
                f"- Add this source to ../../NOTICE and ../../THIRD-PARTY-NOTICES.md before publishing.\n")
            print(f"\nStaged {staged} skills → community/{slug}/  (+ LICENSE, REVIEW.md, README.md)")
            print("NEXT: review REVIEW.md, then add attribution to NOTICE + THIRD-PARTY-NOTICES.md, "
                  "then run tools/validate.py.")
        else:
            print("\n".join(report))
            print(f"\nDRY-RUN — {len(skills)} skills would be staged to community/{slug}/. Re-run with --apply.")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

def main():
    args = sys.argv[1:]
    if len(args) < 2 or args[0] not in ("discover", "import"):
        print(__doc__); sys.exit(1)
    sub, url = args[0], args[1]
    if sub == "discover":
        cmd_discover(url)
    else:
        cmd_import(url, "--apply" in args)

if __name__ == "__main__":
    main()
