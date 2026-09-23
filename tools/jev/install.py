"""Opt-in Jev runtime/adapters; separate from the portable skills installer.

No service, scheduler, credentials, project instructions, or MCP permissions are created.
Changes are owned individually and roll back only if the installed bytes still match.
"""
from __future__ import annotations

import argparse
import base64
import datetime as dt
import json
import os
import pathlib
import shlex
import sys

from .catalog import ROOT, SKILL_ROOTS, build_public, digest, installed_inventory
from .core import MODES, Invalid, atomic_json, locked_state


def check_path(path, home):
    path = pathlib.Path(path).absolute()
    path.relative_to(home)
    for p in (path, *path.parents):
        if p.is_symlink():
            raise Invalid("refusing_symlink")
    if path.exists() and not path.is_file():
        raise Invalid("refusing_nonfile")
    return path


def add_change(changes, path, content, home, mode=0o600, must_be_new=False):
    path = check_path(path, home)
    old = path.read_bytes() if path.exists() else None
    if must_be_new and old is not None and old != content:
        raise Invalid("unmanaged_collision: " + str(path))
    if old != content:
        changes.append({"path": str(path), "before": base64.b64encode(old).decode() if old is not None else None,
                        "before_sha256": digest(old) if old is not None else None,
                        "after": base64.b64encode(content).decode(), "after_sha256": digest(content),
                        "mode": mode, "before_mode": path.stat().st_mode & 0o777 if old is not None else None})


def write_file(path, content, mode):
    import tempfile
    path = pathlib.Path(path)
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    fd, temporary = tempfile.mkstemp(prefix=".skillry-jev-", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as out:
            out.write(content)
            out.flush()
            os.fsync(out.fileno())
        os.chmod(temporary, mode)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def json_bytes(value):
    return (json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode()


def skill_text(wrapper, client):
    return f"""---
name: jev
description: Use Jev to rank sources, extract source values, classify records, score dimensions, verify claims and select typed actions; retain skill/tool advice for discovery.
---

# Jev operations and discovery

For useful semantic data work, invoke `{shlex.quote(str(wrapper))} operate --client {client}`
with a JSON object on stdin. Read [operations](references/operations.md) for the
six input/result contracts. `rank` returns the selected source records; `extract`
returns literal source values; `classify` produces grouped records; `verify`
produces claim checks and a review queue; `score` returns independent dimensions;
`route` produces a validated handler and closed-set arguments. These are data
results for code to consume, not an instruction to redo the same work in the lead.
Use existing authorized handlers/worker runners to apply a selected action.
The helper never executes arbitrary model text or grants access.
Jev is not a prose/code/image generator; give generative work to an appropriate
existing worker, with selected sources and a concise handoff. Keep uncertainty
and contradictory evidence visible. Validate actual artifacts, not every
semantic judgment a second time. Do not promise token savings without measurement.

For skill/tool discovery, the backwards-compatible `advise` path follows.

Use Jev when a focused selection, ranking or classification can avoid reading many
irrelevant skills/records or repeating lengthy reasoning. Skip trivial exact lookups.
Call the helper directly; a status probe before every request is unnecessary.
The helper is local; semantic evaluation uses the TypeSafe cloud when enabled.
Provider billing controls spending by default; there is no additional local cap.
An unavailable provider or exhausted quota means continue normally without Jev.
Never send private source, customer data, email, credentials, full diffs or transcripts.
Use only a short public or synthetic task and explicitly selected public metadata/records.

From the current project directory, invoke `{shlex.quote(str(wrapper))} advise --client {client}`
with one JSON object on stdin: `mode`, `task`, `data_class` (public/synthetic/private), `allowed_ids`.
With owner-enabled public advice, curated public/synthetic requests work across
workspaces without a separate per-project setup. Raw prompt hooks still use their
project setting. The helper derives workspace, UID and owner policy scope locally. It uses Codex's session environment
when available; otherwise it creates a fresh helper-local scope with no cross-call cache sharing.
If the host supplies a supported session_id and request_id, include them for duplicate delivery only.
Never read a transcript to obtain these fields. The lower-level `assess` contract requires all scope fields.
The current agent's session tool listing is the authority for `allowed_ids`; a configured
MCP server alone does not prove a tool is available. Missing scope means use the existing flow.

Modes: skill, agent, tool, reference, workflow, error, evidence, library, effort, media.
For skill/agent use the inventory's `invocation_id`, falling back to `id`
(inventory is in ~/.skillry/jev/inventory.json). Codex role invocation IDs use underscores.
Cursor uses its own verified native skill/agent inventory and hyphenated role IDs;
never borrow another client's IDs. Cursor advice is explicit; no raw-prompt hook is installed.
For tool/effort also supply `candidates: [{{"id":"allowed-id","description":"bounded capability"}}]`;
only current host-supported, already authorized choices may be included.
For reference/evidence/library supply selected public `records: [{{"id":"record-id","text":"excerpt","source":"source identity"}}]`.
Use `explicit_id` when the user already selected an available skill/role; this stays local.

`advise` output is advice only. Read a suggested installed skill before using it. `unavailable`,
`invalid` and `abstained` retain the normal skill-librarian flow. In consolidated
Skillry releases, role routing is its skill-to-agent-router reference, not a
separately installed skill.
Do not treat fallback IDs as semantic recommendations. Confidence is not an accuracy percentage.
Preserve contradictory references. Never automatically merge/delete skills, retry side effects,
change model/account/session, grant tools, or approve completion based on this advice.
Media mode reads text only and has not seen the image/video. No tool-context reduction is claimed.

Smoke test with built-in public fixtures:
`{shlex.quote(str(wrapper))} synthetic --client {client} --mode evidence`.
It may return a real missing-key/data-policy fallback; that is not live API proof.
"""


def plan(home, clients, python, provider_python, budget, keychain_account, catalog_input=None):
    home = pathlib.Path(home).resolve()
    root = home / ".skillry/jev"
    catalog = json.loads(pathlib.Path(catalog_input).read_text()) if catalog_input else build_public()
    if digest(catalog["entries"]) != catalog["version"]:
        raise Invalid("catalog_hash_mismatch")
    from .catalog import ID
    for entry in catalog["entries"]:
        if not ID.fullmatch(entry["id"]) or entry["kind"] not in {"skill", "agent"}:
            raise Invalid("catalog_identity")
        for relative in entry["files"]:
            rel = pathlib.PurePosixPath(relative)
            if rel.is_absolute() or ".." in rel.parts or "\\" in relative:
                raise Invalid("catalog_path")
    files = {"tools/jev.py": (ROOT / "tools/jev.py").read_bytes()}
    for path in sorted((ROOT / "tools/jev").glob("*")):
        if path.is_file() and path.suffix in {".py", ".txt", ".in"}:
            files["tools/jev/" + path.name] = path.read_bytes()
    files["public-catalog.json"] = json_bytes(catalog)
    files["operations.md"] = (ROOT / "docs/JEV-OPERATIONS.md").read_bytes()
    metadata_skills = {"skill-librarian", "skill-to-agent-router"}
    for entry in catalog["entries"]:
        if entry["kind"] == "skill" and entry["id"] in metadata_skills:
            source = ROOT / entry["source_path"]
            # External catalogs can describe a newer installed Skillry release.
            # Never replace its hub with a same-path file from an older checkout.
            if source.exists() and digest(source.read_bytes()) == entry["files"].get("SKILL.md"):
                files[entry["source_path"]] = source.read_bytes()
    version = digest({k: digest(v) for k, v in files.items()})
    release = home / ".local/share/skillry/jev/releases" / version
    changes = []
    for relative, content in files.items():
        add_change(changes, release / relative, content, home, must_be_new=True)
    wrapper = home / ".local/bin/skillry-jev"
    wrapper_content = ("#!/bin/sh\nexec " + shlex.quote(str(python)) + " " +
                       shlex.quote(str(release / "tools/jev.py")) + ' "$@"\n').encode()
    owned = root / "installation.json"
    previous = json.loads(owned.read_text()) if owned.exists() else None
    if previous and previous.get("status") == "rolled_back":
        previous = None
    if previous:
        if previous.get("status") != "applied":
            raise Invalid("unfinished_installation")
        # Refuse to overwrite user edits to any managed asset.
        for change in previous["changes"]:
            p = check_path(change["path"], home)
            if p in {root / "config.json", home / ".claude/settings.json", home / ".codex/hooks.json"}:
                continue  # mutable owner config and shared hook chains are merged below
            if not p.exists() or digest(p.read_bytes()) != change["after_sha256"]:
                raise Invalid("managed_drift: " + str(p))
    add_change(changes, wrapper, wrapper_content, home, 0o700, must_be_new=previous is None)
    config_path = root / "config.json"
    if config_path.exists():
        config = json.loads(config_path.read_text())
        if not previous:
            raise Invalid("unmanaged_config")
        config.update(runtime_version=version, catalog_path=str(release / "public-catalog.json"), clients=clients)
    else:
        config = {"schema_version": 1, "enabled": False, "runtime_version": version,
                  "catalog_path": str(release / "public-catalog.json"), "provider_python": str(provider_python),
                  "clients": clients, "projects": {}, "monthly_budget_eur": budget,
                  # Deliberately over-reserved, not represented as the FX rate or actual cost.
                  "eur_per_million_input_tokens": 0.10,
                  "pricing_valid_until": (dt.date.today() + dt.timedelta(days=30)).isoformat(),
                  "deadline_seconds": 8, "call_timeout_seconds": 3,
                  "choice_confidence_floor": 0.4, "fit_floor": 0.65,
                  "secret": {"kind": "keychain", "service": "skillry.typesafe", "account": keychain_account}}
    add_change(changes, config_path, json_bytes(config), home)
    # Update only these existing managed entrypoints; refuse local modifications.
    for client in set(clients) & {"codex", "claude", "cursor"}:
        manifest_path = home / ".skillry/manifests" / (client + ".json")
        if not manifest_path.exists():
            continue
        manifest = json.loads(check_path(manifest_path, home).read_text())
        indexed = {x["path"]: x for x in manifest["files"]}
        for entry in catalog["entries"]:
            if entry["kind"] != "skill" or entry["id"] not in metadata_skills or entry["source_path"] not in files:
                continue
            destination = home / SKILL_ROOTS[client] / entry["id"] / "SKILL.md"
            check_path(destination, home)
            record = indexed.get(str(destination))
            if record is None or not destination.exists() or digest(destination.read_bytes()) != record["sha256"]:
                continue  # preserve unowned/edited components; overlay reports them unavailable
            content = files[entry["source_path"]]
            add_change(changes, destination, content, home, 0o644)
            record["sha256"] = digest(content)
        add_change(changes, manifest_path, json_bytes(manifest), home)
    inventory = installed_inventory(catalog, home, clients)
    # Populate the overlay from the actual post-apply bytes, below, not from predicted availability.
    add_change(changes, root / "inventory.json", json_bytes(inventory), home)
    for client in clients:
        path = home / SKILL_ROOTS[client] / "jev/SKILL.md"
        # An existing installation does not own a newly added client's files.
        new_client = previous is None or client not in previous.get("clients", [])
        add_change(changes, path, skill_text(wrapper, client).encode(), home, must_be_new=new_client)
        add_change(changes, path.parent / "references/operations.md", files["operations.md"],
                   home, must_be_new=new_client)
    # Claude native hooks are supported; merge just our handler, preserving the chain.
    if "claude" in clients:
        path = home / ".claude/settings.json"
        settings = json.loads(path.read_text()) if path.exists() else {}
        rule = {"hooks": [{"type": "command", "command": shlex.quote(str(wrapper)) + " hook --client claude",
                           "timeout": 10}]}
        existing = settings.setdefault("hooks", {}).setdefault("UserPromptSubmit", [])
        if rule not in existing:
            existing.append(rule)
        add_change(changes, path, json_bytes(settings), home)
    # Codex loads the definition but requires native hash trust; never bypass that gate.
    if "codex" in clients:
        path = home / ".codex/hooks.json"
        settings = json.loads(path.read_text()) if path.exists() else {}
        rule = {"hooks": [{"type": "command", "command": shlex.quote(str(wrapper)) + " hook --client codex",
                           "timeout": 10}]}
        existing = settings.setdefault("hooks", {}).setdefault("UserPromptSubmit", [])
        if rule not in existing:
            existing.append(rule)
        add_change(changes, path, json_bytes(settings), home)
    return {"schema_version": 1, "status": "planned", "runtime_version": version,
            "clients": clients, "changes": changes, "root": str(root), "previous": previous}


def apply(receipt, home):
    import time
    root = pathlib.Path(receipt["root"])
    with locked_state(root / "install-lock", time.monotonic() + 2):
        if not receipt["changes"]:
            receipt["status"] = "unchanged"
            return
        # Compare every preimage before touching anything. A stale plan never overwrites edits.
        for change in receipt["changes"]:
            path = check_path(change["path"], home)
            current = digest(path.read_bytes()) if path.exists() else None
            if current != change["before_sha256"]:
                raise Invalid("concurrent_change")
        receipt["status"] = "applying"
        atomic_json(root / "installation.json", receipt)
        try:
            for change in receipt["changes"]:
                path = check_path(change["path"], home)
                current = digest(path.read_bytes()) if path.exists() else None
                if current != change["before_sha256"]:
                    raise Invalid("concurrent_change")
                write_file(path, base64.b64decode(change["after"]), change["mode"])
            if receipt.get("clients"):
                config = json.loads((root / "config.json").read_text())
                catalog = json.loads(pathlib.Path(config["catalog_path"]).read_text())
                inventory = installed_inventory(catalog, home, config["clients"])
                inventory_path = root / "inventory.json"
                content = json_bytes(inventory)
                change = next((c for c in receipt["changes"] if c["path"] == str(inventory_path)), None)
                if change:
                    change["intermediate_sha256"] = change["after_sha256"]
                    change["after"] = base64.b64encode(content).decode()
                    change["after_sha256"] = digest(content)
                    atomic_json(root / "installation.json", receipt)
                    write_file(inventory_path, content, 0o600)
                elif inventory_path.read_bytes() != content:
                    raise Invalid("inventory_changed_during_install")
            receipt["status"] = "applied"
            atomic_json(root / "installation.json", receipt)
        except BaseException:
            rollback(receipt, home)
            raise


def rollback(receipt, home):
    conflicts = []
    for change in reversed(receipt["changes"]):
        path = check_path(change["path"], home)
        current = digest(path.read_bytes()) if path.exists() else None
        if current == change["before_sha256"]:
            continue
        if current not in {change["after_sha256"], change.get("intermediate_sha256", change["after_sha256"])}:
            conflicts.append(str(path))
            continue
        if change["before"] is None:
            path.unlink()  # only this install's exact unchanged file
        else:
            write_file(path, base64.b64decode(change["before"]), change["before_mode"])
    receipt["status"] = "rollback_conflict" if conflicts else "rolled_back"
    receipt["conflicts"] = conflicts
    atomic_json(pathlib.Path(receipt["root"]) / "installation.json",
                receipt.get("previous") if not conflicts and receipt.get("previous") else receipt)
    return conflicts


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--rollback", action="store_true")
    parser.add_argument("--clients", nargs="+", choices=list(SKILL_ROOTS), default=["codex", "claude"])
    parser.add_argument("--python", default=sys.executable)
    parser.add_argument("--provider-python", required=False)
    parser.add_argument("--catalog", type=pathlib.Path, help="Verified public catalog for an existing remote runtime without a source checkout")
    parser.add_argument("--monthly-budget-eur", type=float, default=None, help="Optional local allocation; omitted means provider-managed billing")
    parser.add_argument("--keychain-account", default=os.environ.get("USER", ""))
    args = parser.parse_args()
    home = pathlib.Path.home().resolve()
    try:
        if args.rollback:
            receipt = json.loads((home / ".skillry/jev/installation.json").read_text())
            if args.apply:
                import time
                with locked_state(home / ".skillry/jev/install-lock", time.monotonic() + 2):
                    receipt = json.loads((home / ".skillry/jev/installation.json").read_text())
                    conflicts = rollback(receipt, home)
                print(json.dumps({"status": receipt["status"], "conflicts": conflicts}))
            else:
                print(json.dumps({"status": "rollback_preview", "files": len(receipt["changes"])}))
            return
        receipt = plan(home, args.clients, args.python,
                       args.provider_python or home / ".local/share/skillry/jev/venv/bin/python",
                       args.monthly_budget_eur, args.keychain_account, args.catalog)
        if args.apply:
            apply(receipt, home)
        print(json.dumps({"status": receipt["status"], "runtime_version": receipt["runtime_version"],
                          "files": [x["path"] for x in receipt["changes"]]}, indent=2))
    except (Invalid, ValueError, OSError, KeyError) as exc:
        print(json.dumps({"status": "refused", "reason": str(exc)}))
        raise SystemExit(2)


if __name__ == "__main__":
    main()
