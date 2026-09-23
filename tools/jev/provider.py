"""One SDK attempt in a killable process. Never print credentials or SDK errors."""
from __future__ import annotations

import json
import logging
import os
import subprocess
import sys


def main():
    logging.disable(logging.CRITICAL)
    try:
        request = json.loads(sys.stdin.buffer.read(131073))
        from typesafe_sdk import TypeSafeClient, Choice, Noul, Score, RetryPolicy
        from typesafe_sdk import __version__
        if __version__ != "0.7.0":
            raise RuntimeError("sdk_version")
        secret = request["secret"]
        key = os.environ.get("TYPESAFE_API_KEY", "") if secret["kind"] == "environment" else ""
        if secret["kind"] == "keychain" and sys.platform == "darwin":
            found = subprocess.run(["/usr/bin/security", "find-generic-password", "-s", secret["service"],
                                    "-a", secret["account"], "-w"], capture_output=True, timeout=5)
            if found.returncode == 0:
                key = found.stdout.decode().strip()
        if not key:
            print(json.dumps({"error": "missing_key"}))
            return
        constructors = {"choice": Choice, "noul": Noul, "score": Score}
        questions = {k: constructors[q["type"]](**{field: q[field] for field in
                         ("instructions", "criteria") if field in q})
                     for k, q in request["questions"].items()}
        with TypeSafeClient(api_key=key, model="jev-1.13.0", retry=RetryPolicy(max_retries=0)) as client:
            response = client.system_one(request["state"], questions, model="jev-1.13.0",
                                         timeout=request["timeout"], retry=RetryPolicy(max_retries=0))
        # raw JSON is validated again by the parent, including unknown answer types.
        data = response.raw_http_response.json()
        print(json.dumps({"response": data}, ensure_ascii=False))
    except BaseException as exc:
        # Never stringify exceptions: HTTP errors can include request/response bodies.
        name = type(exc).__name__
        code = {"TypeSafeRateLimitError": "rate_limit", "TypeSafeAuthenticationError": "authentication",
                "TypeSafeAPITimeoutError": "timeout", "TimeoutExpired": "secret_timeout",
                "ModuleNotFoundError": "sdk_missing"}.get(name, "provider_error")
        print(json.dumps({"error": code}))


if __name__ == "__main__":
    main()
