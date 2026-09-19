#!/usr/bin/env python3
"""Framework-agnostic multilingual i18n SEO checker over HTML files or URL lists.

Python 3.11+. Standard library only.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.error
import urllib.request
from dataclasses import asdict, dataclass, field
from html.parser import HTMLParser
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import urljoin, urlparse


@dataclass
class Finding:
    severity: str  # error | warning | info
    code: str
    message: str
    path: str = ""
    evidence: str = ""


@dataclass
class PageData:
    path: str
    title: str | None = None
    description: str | None = None
    canonical: str | None = None
    robots: str | None = None
    og_url: str | None = None
    og_locale: str | None = None
    html_lang: str | None = None
    html_dir: str | None = None
    h1_count: int = 0
    json_ld_count: int = 0
    hreflang: list[tuple[str, str]] = field(default_factory=list)  # (lang, href)
    og_locale_alternates: list[str] = field(default_factory=list)


class PageHTMLParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.data = PageData(path="")
        self._in_title = False
        self._title_chunks: list[str] = []
        self._in_h1 = False
        self._capture_json_ld = False
        self._json_ld_chunks: list[str] = []
        self._depth_ignore = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attr = {k.lower(): (v or "") for k, v in attrs}
        if tag == "html":
            if "lang" in attr:
                self.data.html_lang = attr["lang"]
            if "dir" in attr:
                self.data.html_dir = attr["dir"]
        elif tag == "title":
            self._in_title = True
            self._title_chunks = []
        elif tag == "meta":
            name = attr.get("name", "").lower()
            prop = attr.get("property", "").lower()
            content = attr.get("content", "")
            if name == "description":
                self.data.description = content
            elif name == "robots":
                self.data.robots = content
            elif prop == "og:url":
                self.data.og_url = content
            elif prop == "og:locale":
                self.data.og_locale = content
            elif prop == "og:locale:alternate":
                self.data.og_locale_alternates.append(content)
        elif tag == "link":
            rel = attr.get("rel", "").lower().split()
            href = attr.get("href", "")
            if "canonical" in rel:
                self.data.canonical = href
            if "alternate" in rel and attr.get("hreflang"):
                self.data.hreflang.append((attr["hreflang"], href))
        elif tag == "h1":
            self.data.h1_count += 1
            self._in_h1 = True
        elif tag == "script":
            t = attr.get("type", "").lower()
            if t in ("application/ld+json", "application/ld+json; charset=utf-8"):
                self._capture_json_ld = True
                self._json_ld_chunks = []

    def handle_endtag(self, tag: str) -> None:
        if tag == "title" and self._in_title:
            self._in_title = False
            self.data.title = "".join(self._title_chunks).strip()
        elif tag == "h1":
            self._in_h1 = False
        elif tag == "script" and self._capture_json_ld:
            self._capture_json_ld = False
            raw = "".join(self._json_ld_chunks).strip()
            if raw:
                self.data.json_ld_count += 1

    def handle_data(self, data: str) -> None:
        if self._in_title:
            self._title_chunks.append(data)
        if self._capture_json_ld:
            self._json_ld_chunks.append(data)


def load_registry(path: Path | None) -> dict[str, Any] | None:
    if path is None:
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def prefix_to_locale(registry: dict[str, Any]) -> dict[str, dict[str, Any]]:
    mapping: dict[str, dict[str, Any]] = {}
    for loc in registry.get("locales", []):
        if not loc.get("enabled", True):
            continue
        mapping[loc.get("urlPrefix", "").lower()] = loc
    return mapping


def expected_hreflang(loc: dict[str, Any]) -> str:
    bcp47 = loc["bcp47"]
    if loc.get("hreflangCase", "bcp47") == "lowercase":
        return bcp47.lower()
    # Prefer canonical region casing: language lower, region upper
    parts = bcp47.split("-")
    if len(parts) == 1:
        return parts[0].lower()
    return parts[0].lower() + "-" + "-".join(
        p.upper() if len(p) == 2 and p.isalpha() else p for p in parts[1:]
    )


def detect_path_locale(rel_path: str, registry: dict[str, Any] | None) -> dict[str, Any] | None:
    if not registry:
        return None
    parts = Path(rel_path).parts
    # expect .../<prefix>/file.html or <prefix>/index.html
    for part in parts:
        key = part.lower()
        mapping = prefix_to_locale(registry)
        if key in mapping:
            return mapping[key]
    return None


def is_noindex(robots: str | None) -> bool:
    if not robots:
        return False
    return "noindex" in robots.lower()


def normalize_url(url: str, trailing_slash: str = "as-is") -> str:
    url = url.strip()
    if trailing_slash == "always":
        parsed = urlparse(url)
        if not parsed.path.endswith("/") and not Path(parsed.path).suffix:
            url = url + "/"
    elif trailing_slash == "never":
        parsed = urlparse(url)
        if parsed.path.endswith("/") and parsed.path != "/":
            url = url.rstrip("/")
            if parsed.query:
                url += "?" + parsed.query
    return url


def parse_html(text: str, path: str) -> PageData:
    parser = PageHTMLParser()
    parser.feed(text)
    parser.data.path = path
    return parser.data


def iter_html_files(root: Path) -> Iterable[Path]:
    for p in sorted(root.rglob("*.html")):
        if p.is_file():
            yield p


def fetch_url(url: str, timeout: float = 20.0) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": "multilingual-i18n-seo-skill/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:  # noqa: S310
        return resp.read().decode("utf-8", errors="replace")


def check_page(
    page: PageData,
    *,
    registry: dict[str, Any] | None,
    site_origin: str | None,
    require_json_ld: bool,
) -> list[Finding]:
    findings: list[Finding] = []
    path = page.path

    if not page.title:
        findings.append(Finding("error", "missing_title", "Missing <title>", path))
    if not page.description:
        findings.append(
            Finding("error", "missing_description", "Missing meta description", path)
        )
    if not page.canonical:
        findings.append(
            Finding("error", "missing_canonical", "Missing link rel=canonical", path)
        )
    if page.robots is None:
        findings.append(
            Finding("warning", "missing_robots", "Missing meta robots (implicit index)", path)
        )
    if page.h1_count != 1:
        findings.append(
            Finding(
                "error",
                "h1_count",
                f"Expected exactly 1 H1, found {page.h1_count}",
                path,
                evidence=str(page.h1_count),
            )
        )
    if require_json_ld and page.json_ld_count < 1:
        findings.append(
            Finding("error", "missing_json_ld", "Missing JSON-LD script", path)
        )
    elif page.json_ld_count < 1:
        findings.append(
            Finding("warning", "missing_json_ld", "Missing JSON-LD script", path)
        )

    if page.canonical and page.og_url and page.canonical != page.og_url:
        findings.append(
            Finding(
                "error",
                "og_url_mismatch",
                "og:url does not equal canonical",
                path,
                evidence=f"canonical={page.canonical} og:url={page.og_url}",
            )
        )
    elif page.canonical and not page.og_url:
        findings.append(
            Finding("error", "missing_og_url", "Missing og:url", path)
        )

    if page.canonical:
        parsed = urlparse(page.canonical)
        if parsed.scheme not in ("http", "https") or not parsed.netloc:
            findings.append(
                Finding(
                    "error",
                    "canonical_not_absolute",
                    "Canonical must be an absolute URL",
                    path,
                    evidence=page.canonical,
                )
            )
        if site_origin:
            origin = urlparse(site_origin)
            if parsed.netloc and origin.netloc and parsed.netloc != origin.netloc:
                findings.append(
                    Finding(
                        "error",
                        "canonical_origin",
                        "Canonical host does not match siteOrigin",
                        path,
                        evidence=page.canonical,
                    )
                )
        if registry and registry.get("trailingSlash") in ("always", "never"):
            normalized = normalize_url(page.canonical, registry["trailingSlash"])
            if normalized != page.canonical:
                findings.append(
                    Finding(
                        "error",
                        "canonical_trailing_slash",
                        f"Canonical trailing slash violates registry policy ({registry['trailingSlash']})",
                        path,
                        evidence=page.canonical,
                    )
                )

    loc = detect_path_locale(path, registry) if registry else None
    if loc:
        expected_lang = loc["bcp47"]
        if not page.html_lang:
            findings.append(
                Finding("error", "missing_html_lang", "Missing html[lang]", path)
            )
        elif page.html_lang != expected_lang and page.html_lang.lower() != expected_lang.lower():
            # Allow exact BCP47 match preferring registry casing
            if page.html_lang != expected_hreflang(loc) and page.html_lang != expected_lang:
                findings.append(
                    Finding(
                        "error",
                        "html_lang_mismatch",
                        f"html[lang]={page.html_lang!r} does not match registry bcp47={expected_lang!r}",
                        path,
                    )
                )
        expected_dir = loc.get("dir")
        if expected_dir and page.html_dir and page.html_dir.lower() != expected_dir:
            findings.append(
                Finding(
                    "error",
                    "html_dir_mismatch",
                    f"html[dir]={page.html_dir!r} expected {expected_dir!r}",
                    path,
                )
            )
        elif expected_dir == "rtl" and not page.html_dir:
            findings.append(
                Finding("error", "missing_html_dir", "Missing html[dir] for RTL locale", path)
            )

    noindex = is_noindex(page.robots)
    if noindex:
        if page.hreflang:
            findings.append(
                Finding(
                    "error",
                    "hreflang_on_noindex",
                    "hreflang alternates must not be present on noindex pages",
                    path,
                    evidence=str(page.hreflang),
                )
            )
        if page.og_locale_alternates:
            findings.append(
                Finding(
                    "error",
                    "og_locale_alternate_on_noindex",
                    "og:locale:alternate must not be present on noindex pages",
                    path,
                )
            )
    else:
        if not page.hreflang:
            findings.append(
                Finding(
                    "error",
                    "missing_hreflang",
                    "Indexable page missing hreflang alternates",
                    path,
                )
            )
        else:
            langs = [h[0] for h in page.hreflang]
            if "x-default" not in langs:
                findings.append(
                    Finding(
                        "error",
                        "missing_x_default",
                        "Indexable page missing hreflang x-default",
                        path,
                    )
                )
            for lang, href in page.hreflang:
                if lang != "x-default" and registry:
                    # Validate casing against registry when possible
                    known = {expected_hreflang(l): l for l in registry.get("locales", []) if l.get("enabled", True)}
                    known_lower = {k.lower(): k for k in known}
                    if lang.lower() in known_lower and lang != known_lower[lang.lower()]:
                        findings.append(
                            Finding(
                                "error",
                                "hreflang_bcp47_case",
                                f"hreflang {lang!r} should be {known_lower[lang.lower()]!r} per registry",
                                path,
                                evidence=lang,
                            )
                        )
                    # slug-style mistake: fr-ca when fr-CA expected
                    if re.fullmatch(r"[a-z]{2}-[a-z]{2}", lang):
                        fixed = lang[:3] + lang[3:].upper()
                        if fixed in known and lang != fixed:
                            findings.append(
                                Finding(
                                    "error",
                                    "hreflang_slug_case",
                                    f"hreflang {lang!r} looks slug-cased; expected BCP47 {fixed!r}",
                                    path,
                                )
                            )
                parsed = urlparse(href)
                if parsed.scheme != "https" or not parsed.netloc:
                    findings.append(
                        Finding(
                            "error",
                            "hreflang_not_absolute_https",
                            f"hreflang href must be absolute HTTPS ({lang})",
                            path,
                            evidence=href,
                        )
                    )

    return findings


def check_duplicates(pages: list[PageData]) -> list[Finding]:
    findings: list[Finding] = []
    titles: dict[str, list[str]] = {}
    descriptions: dict[str, list[str]] = {}
    for p in pages:
        if is_noindex(p.robots):
            continue
        if p.title:
            titles.setdefault(p.title.strip(), []).append(p.path)
        if p.description:
            descriptions.setdefault(p.description.strip(), []).append(p.path)
    for title, paths in titles.items():
        if len(paths) > 1:
            findings.append(
                Finding(
                    "warning",
                    "duplicate_title",
                    f"Duplicate title across {len(paths)} pages",
                    paths[0],
                    evidence=title,
                )
            )
    for desc, paths in descriptions.items():
        if len(paths) > 1:
            findings.append(
                Finding(
                    "warning",
                    "duplicate_description",
                    f"Duplicate description across {len(paths)} pages",
                    paths[0],
                    evidence=desc[:120],
                )
            )
    return findings


def check_sitemap(
    sitemap_path: Path,
    registry: dict[str, Any] | None,
) -> list[Finding]:
    findings: list[Finding] = []
    text = sitemap_path.read_text(encoding="utf-8", errors="replace")
    if "<urlset" not in text and "<sitemapindex" not in text:
        findings.append(
            Finding(
                "error",
                "sitemap_invalid",
                "Sitemap does not look like XML sitemap",
                str(sitemap_path),
            )
        )
        return findings
    locs = re.findall(r"<loc>\s*([^<]+)\s*</loc>", text, flags=re.I)
    if not locs:
        findings.append(
            Finding("error", "sitemap_empty", "Sitemap has no <loc> entries", str(sitemap_path))
        )
    xhtml = re.findall(
        r'rel=["\']alternate["\'][^>]*hreflang=["\']([^"\']+)["\']',
        text,
        flags=re.I,
    )
    if not xhtml:
        # also xhtml:link form
        xhtml = re.findall(r'hreflang=["\']([^"\']+)["\']', text, flags=re.I)
    if locs and not xhtml:
        findings.append(
            Finding(
                "warning",
                "sitemap_missing_xhtml_alternates",
                "Sitemap has URLs but no hreflang xhtml alternates detected",
                str(sitemap_path),
            )
        )
    if registry:
        prefixes = [
            loc["urlPrefix"]
            for loc in registry.get("locales", [])
            if loc.get("enabled", True)
            and loc.get("id") != registry.get("defaultLocale")
            and loc.get("urlPrefix")
        ]
        joined = "\n".join(locs)
        missing_prefix = [p for p in prefixes if f"/{p}/" not in joined and not any(
            u.rstrip("/").endswith(f"/{p}") for u in locs
        )]
        if missing_prefix:
            findings.append(
                Finding(
                    "error",
                    "sitemap_missing_non_default_locale",
                    f"Sitemap samples missing non-default locale prefixes: {', '.join(missing_prefix)}",
                    str(sitemap_path),
                )
            )
    return findings


def render_text(findings: list[Finding], pages_scanned: int) -> str:
    errors = sum(1 for f in findings if f.severity == "error")
    warnings = sum(1 for f in findings if f.severity == "warning")
    lines = [
        f"Scanned pages: {pages_scanned}",
        f"Findings: {len(findings)} (errors={errors}, warnings={warnings})",
        "",
    ]
    for f in findings:
        loc = f" @ {f.path}" if f.path else ""
        ev = f" | {f.evidence}" if f.evidence else ""
        lines.append(f"[{f.severity.upper()}] {f.code}{loc}: {f.message}{ev}")
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, help="Directory of HTML files (e.g. dist/)")
    parser.add_argument(
        "--urls-file",
        type=Path,
        help="Optional text file with one URL per line to fetch",
    )
    parser.add_argument("--registry", type=Path, help="locale-registry.json")
    parser.add_argument("--sitemap", type=Path, help="Optional sitemap XML path")
    parser.add_argument(
        "--format",
        choices=("text", "json", "both"),
        default="text",
        help="Report format",
    )
    parser.add_argument(
        "--fail-on",
        choices=("error", "warning", "never"),
        default="error",
        help="Exit non-zero threshold",
    )
    parser.add_argument(
        "--require-json-ld",
        action="store_true",
        help="Treat missing JSON-LD as error",
    )
    parser.add_argument(
        "--site-origin",
        help="Override site origin (else registry.siteOrigin)",
    )
    args = parser.parse_args(argv)

    if not args.root and not args.urls_file:
        parser.error("Provide --root and/or --urls-file")

    registry = load_registry(args.registry) if args.registry else None
    site_origin = args.site_origin or (registry.get("siteOrigin") if registry else None)

    pages: list[PageData] = []
    findings: list[Finding] = []

    if args.root:
        if not args.root.is_dir():
            print(f"ERROR: --root not a directory: {args.root}", file=sys.stderr)
            return 2
        for html_path in iter_html_files(args.root):
            rel = str(html_path.relative_to(args.root))
            text = html_path.read_text(encoding="utf-8", errors="replace")
            page = parse_html(text, rel)
            pages.append(page)
            findings.extend(
                check_page(
                    page,
                    registry=registry,
                    site_origin=site_origin,
                    require_json_ld=args.require_json_ld,
                )
            )

    if args.urls_file:
        for line in args.urls_file.read_text(encoding="utf-8").splitlines():
            url = line.strip()
            if not url or url.startswith("#"):
                continue
            try:
                text = fetch_url(url)
            except (urllib.error.URLError, TimeoutError) as exc:
                findings.append(
                    Finding("error", "fetch_failed", f"Failed to fetch URL: {exc}", url)
                )
                continue
            page = parse_html(text, url)
            pages.append(page)
            findings.extend(
                check_page(
                    page,
                    registry=registry,
                    site_origin=site_origin,
                    require_json_ld=args.require_json_ld,
                )
            )

    findings.extend(check_duplicates(pages))

    if args.sitemap:
        if args.sitemap.is_file():
            findings.extend(check_sitemap(args.sitemap, registry))
        else:
            findings.append(
                Finding("error", "sitemap_missing_file", "Sitemap path not found", str(args.sitemap))
            )

    errors = sum(1 for f in findings if f.severity == "error")
    warnings = sum(1 for f in findings if f.severity == "warning")
    report = {
        "version": "1.0.0",
        "pagesScanned": len(pages),
        "summary": {
            "errors": errors,
            "warnings": warnings,
            "info": sum(1 for f in findings if f.severity == "info"),
        },
        "findings": [asdict(f) for f in findings],
    }

    if args.format in ("text", "both"):
        sys.stdout.write(render_text(findings, len(pages)))
    if args.format in ("json", "both"):
        if args.format == "both":
            sys.stdout.write("\n--- JSON ---\n")
        json.dump(report, sys.stdout, indent=2)
        sys.stdout.write("\n")

    if args.fail_on == "never":
        return 0
    if args.fail_on == "warning" and (errors or warnings):
        return 1
    if args.fail_on == "error" and errors:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
