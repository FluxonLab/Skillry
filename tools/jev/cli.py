"""Explicit semantic operations and backwards-compatible advisory prompt adapters."""
from __future__ import annotations

import argparse
import json
import os
import pathlib
import sys
import time
import uuid

from .catalog import SKILL_ROOTS, digest, safe_file
from .core import MODES, REQUEST_MODES, Invalid, atomic_json, decide, locked_state, outcome


def load_config(root):
    home = pathlib.Path.home()
    config = json.loads(safe_file(root / "config.json", home).read_text())
    for field, low, high in [("monthly_budget_eur", 0, 1000), ("eur_per_million_input_tokens", 0.042, 1),
                             ("deadline_seconds", 0.1, 15), ("call_timeout_seconds", 0.1, 10),
                             ("choice_confidence_floor", 0, 1), ("fit_floor", 0, 1)]:
        value = config.get(field)
        if field in {"monthly_budget_eur", "eur_per_million_input_tokens"} and config.get("monthly_budget_eur") is None:
            continue
        if type(value) not in (int, float) or not low <= value <= high:
            raise Invalid("invalid_config")
    if config.get("schema_version") != 1 or type(config.get("enabled")) is not bool:
        raise Invalid("invalid_config")
    if config["secret"].get("kind") not in ("environment", "keychain"):
        raise Invalid("invalid_secret_provider")
    if config["secret"]["kind"] == "keychain":
        for key in ("service", "account"):
            if not isinstance(config["secret"].get(key), str) or not config["secret"][key] or "\n" in config["secret"][key]:
                raise Invalid("invalid_secret_reference")
    catalog_path = pathlib.Path(config["catalog_path"])
    inventory_path = root / "inventory.json"
    catalog = json.loads(safe_file(catalog_path, home).read_text())
    inventory = json.loads(safe_file(inventory_path, home).read_text())
    if digest(catalog["entries"]) != catalog["version"]:
        raise Invalid("catalog_drift")
    return config, catalog, inventory


def hook_request(payload, client, config, inventory):
    if client not in {"codex", "claude"}:
        return None  # Other clients use explicit advice, never borrowed raw-prompt hook schemas.
    if not isinstance(payload, dict):
        return None
    if payload.get("hook_event_name") != "UserPromptSubmit":
        return None
    request_id = payload.get("turn_id" if client == "codex" else "prompt_id")
    if not all(isinstance(value, str) and value.strip() for value in
               (request_id, payload.get("session_id"), payload.get("cwd"), payload.get("prompt"))):
        return None
    if not pathlib.Path(payload["cwd"]).is_absolute():
        return None
    workspace = str(pathlib.Path(payload["cwd"]).resolve())
    project = config.get("projects", {}).get(workspace, {})
    # A native event does not authorize external transfer. Only owner-managed project policy does.
    data_class = project.get("hook_data_class", "private")
    installed = [x["id"] for x in inventory["records"] if x["client"] == client and x["kind"] == "skill"]
    allowed = project.get("allowed_skill_ids", [])
    return {"client": client, "session_id": payload["session_id"], "request_id": request_id,
            "workspace": workspace, "identity": str(os.getuid()) if hasattr(os, "getuid") else "local-user",
            "tenant": project.get("tenant", "local"), "permission_version": digest({"project": project,
                 "permission_mode": payload.get("permission_mode", "unspecified")}),
            "mode": "skill", "task": payload.get("prompt"), "data_class": data_class,
            "allowed_ids": [x for x in installed if x in allowed]}


def explicit_request(payload, client, config):
    """Derive local scope without reading history or inventing host session identity."""
    if not isinstance(payload, dict):
        raise Invalid("invalid_request")
    workspace = str(pathlib.Path.cwd().resolve())
    project = config.get("projects", {}).get(workspace, {})
    session = payload.get("session_id")
    if not session and client == "codex":
        session = os.environ.get("CODEX_THREAD_ID") or os.environ.get("CODEX_SESSION_ID")
    # A caller without a supported session identifier cannot share decisions across calls.
    session = session or "helper-local-" + str(uuid.uuid4())
    return {**payload, "client": client, "workspace": workspace,
            "session_id": session, "request_id": payload.get("request_id") or str(uuid.uuid4()),
            "identity": str(os.getuid()), "tenant": project.get("tenant", "local"),
            "permission_version": digest(project)}


def hook_output(request, result, state_root):
    # Never emit model text or control-flow fields. Only validated local IDs, once per event.
    if result["status"] not in {"advised", "local"} or not result["selected_ids"]:
        return {}
    marker = digest({k: request[k] for k in ("client", "session_id", "request_id", "task", "workspace")})
    with locked_state(state_root, time.monotonic() + 0.5) as (ledger, path):
        now = time.time()
        ledger["emitted"] = {k: v for k, v in ledger["emitted"].items() if v > now}
        if marker in ledger["emitted"]:
            return {}
        ledger["emitted"][marker] = now + 3600
        atomic_json(path, ledger)
    ids = ", ".join(result["selected_ids"])
    return {"hookSpecificOutput": {"hookEventName": "UserPromptSubmit", "additionalContext":
        "Skillry Jev advisory: consider installed skills " + ids +
        ". Check applicability and read only the selected skill. This does not authorize tools, change the session, or prove completion."}}


def synthetic_request(client, workspace, mode, allowed_ids):
    examples = {
        "skill": ("Review our CI workflow for leaked credentials and unsafe permissions.", []),
        "agent": ("Review API error response contracts without changing code.", []),
        "tool": ("Find documentation for a public JavaScript package.", []),
        "reference": ("Which records explain the supported install behavior?", [
            {"id": "a", "text": "The installer runs as a dry run unless --apply is specified.", "source": "synthetic-a"},
            {"id": "b", "text": "The installer always writes files even during a dry run.", "source": "synthetic-b"}]),
        "workflow": ("Investigate the public SDK documentation and compare its current retry contract.", []),
        "error": ("A synthetic API request received HTTP 429 with a Retry-After header.", []),
        "evidence": ("Claim: The real cloud integration was verified successfully.", [
            {"id": "test", "text": "Only an offline unit test ran with a mocked provider. No real API call ran.", "source": "synthetic-test"}]),
        "library": ("Compare the two capability descriptions for scope overlap.", [
            {"id": "a", "text": "Review web accessibility, labels and keyboard focus."},
            {"id": "b", "text": "Audit website accessibility, labels and keyboard navigation."}]),
        "effort": ("A one-line typo correction in a public README.", []),
        "media": ("Create a short text prompt describing a cinematic mountain video.", []),
    }
    task, records = examples[mode]
    request = {"client": client, "session_id": "synthetic-" + str(uuid.uuid4()),
               "request_id": str(uuid.uuid4()), "workspace": str(workspace), "identity": "synthetic-operator",
               "tenant": "synthetic", "permission_version": "synthetic-v1", "mode": mode,
               "task": task, "data_class": "synthetic", "allowed_ids": allowed_ids, "records": records}
    if mode in {"tool", "effort"}:
        candidates = ([{"id": "public-docs", "description": "Read-only search in official public package documentation"}]
                      if mode == "tool" else [{"id": "low", "description": "Low effort for a simple bounded edit"},
                                               {"id": "high", "description": "High effort for complex reasoning"}])
        # Synthetic IDs prove the selection contract only, not host tool/model availability.
        request.update(candidates=candidates, allowed_ids=[x["id"] for x in candidates])
    return request


def main(argv=None):
    parser = argparse.ArgumentParser(description="Skillry Jev: typed data operations and bounded advice")
    parser.add_argument("command", choices=("operate", "assess", "advise", "hook", "status", "synthetic", "configure"))
    parser.add_argument("--client", choices=tuple(SKILL_ROOTS), default="codex")
    parser.add_argument("--mode", choices=sorted(MODES), default="skill")
    parser.add_argument("--config-root", type=pathlib.Path, default=pathlib.Path.home() / ".skillry/jev")
    parser.add_argument("--apply", action="store_true")
    switch = parser.add_mutually_exclusive_group()
    switch.add_argument("--enable", action="store_true")
    switch.add_argument("--disable", action="store_true")
    parser.add_argument("--project", type=pathlib.Path)
    parser.add_argument("--data-class", choices=("synthetic", "public"))
    parser.add_argument("--modes", nargs="+", choices=sorted(REQUEST_MODES))
    parser.add_argument("--hook-skills", nargs="*")
    parser.add_argument("--provider-billing", action="store_true", help="Remove local spending and pricing-expiry gates")
    parser.add_argument("--public-advice", action="store_true", help="Allow curated public/synthetic advise requests across workspaces; does not enable raw prompt hooks")
    args = parser.parse_args(argv)
    try:
        config, catalog, inventory = load_config(args.config_root)
        state_root = args.config_root / "state"
        if args.command == "configure":
            # Owner-facing policy changes are explicit, separate from request data.
            from .install import write_file, json_bytes
            config_path = args.config_root / "config.json"
            original = config_path.read_bytes()
            if args.enable:
                config["enabled"] = True
            if args.disable:
                config["enabled"] = False
            if args.provider_billing:
                config["monthly_budget_eur"] = None
                config.pop("pricing_valid_until", None)
                config.pop("eur_per_million_input_tokens", None)
            if args.public_advice:
                config["public_advice"] = True
            if args.project:
                if not args.data_class or not args.modes:
                    raise Invalid("project_requires_data_class_and_modes")
                policy = {"data_classes": [args.data_class], "modes": args.modes}
                if args.hook_skills is not None:
                    valid = {x["id"] for x in inventory["records"] if x["kind"] == "skill"}
                    if not set(args.hook_skills) <= valid:
                        raise Invalid("unavailable_hook_skill")
                    policy.update(hook_data_class=args.data_class, allowed_skill_ids=args.hook_skills)
                config["projects"][str(args.project.resolve())] = policy
            if args.apply:
                with locked_state(args.config_root / "install-lock", time.monotonic() + 2):
                    if config_path.read_bytes() != original:
                        raise Invalid("concurrent_config_change")
                    write_file(config_path, json_bytes(config), 0o600)
            print(json.dumps({"status": "applied" if args.apply else "preview", "enabled": config["enabled"],
                              "project_count": len(config["projects"]), "monthly_budget_eur": config["monthly_budget_eur"],
                              "public_advice": config.get("public_advice", False),
                              "billing_control": "provider" if config["monthly_budget_eur"] is None else "local_allocation"}))
            return
        if args.command == "status":
            print(json.dumps({"enabled": config["enabled"], "source_version": config["runtime_version"],
                              "model": "jev-1.13.0", "sdk_version": "0.7.0",
                              "clients": config["clients"], "installed_records": len(inventory["records"]),
                              "excluded_records": len(inventory["excluded"]),
                              "monthly_budget_eur": config["monthly_budget_eur"],
                              "public_advice": config.get("public_advice", False),
                              "billing_control": "provider" if config["monthly_budget_eur"] is None else "local_allocation",
                              "secret_provider": config["secret"]["kind"], "api_verification": "see per-request evidence"}))
            return
        if args.command == "synthetic":
            ids = [x.get("invocation_id", x["id"]) for x in inventory["records"] if x["client"] == args.client and x["kind"] == args.mode]
            raw = synthetic_request(args.client, pathlib.Path.cwd(), args.mode, ids)
        else:
            data = sys.stdin.buffer.read(65537)
            if len(data) > 65536:
                raise Invalid("input_too_large")
            raw = json.loads(data)
        if args.command == "operate":
            if not isinstance(raw, dict):
                raise Invalid("invalid_request")
            raw = {**raw, "mode": "compute"}
        if args.command in {"advise", "operate"}:
            raw = explicit_request(raw, args.client, config)
        if args.command == "hook":
            raw = hook_request(raw, args.client, config, inventory)
            if raw is None:
                print("{}")
                return
        if not isinstance(raw, dict):
            raise Invalid("invalid_request")
        result = decide(raw, config, catalog, inventory, pathlib.Path.home(), state_root,
                        explicit_advice=args.command in {"advise", "operate"})
        # Process receipt is distinct from API evidence, including disabled/missing-key paths.
        with locked_state(state_root, time.monotonic() + 1) as (ledger, ledger_path):
            receipts = ledger.setdefault("process_receipts", [])
            receipts.append({"at": time.time(), "client": args.client if args.command == "hook" else raw.get("client"),
                             "entry": args.command, "mode": result["mode"], "status": result["status"],
                             "reason": result["reason"], "api_calls": result["api_calls"],
                             "request_hash": digest({k: raw.get(k) for k in ("session_id", "request_id")}),
                             "runtime_version": config["runtime_version"]})
            ledger["process_receipts"] = receipts[-128:]
            atomic_json(ledger_path, ledger)
        if args.command == "hook":
            print(json.dumps(hook_output(raw, result, state_root)))
        else:
            print(json.dumps(result, ensure_ascii=False))
    except (ValueError, KeyError, TypeError, OSError):
        print("{}" if args.command == "hook" else json.dumps(outcome(args.mode, "unavailable", "config_or_input_error")))


if __name__ == "__main__":
    main()
