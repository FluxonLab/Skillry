---
name: api-reference-docs
description: Use when you need to produce or audit API reference documentation from code or an OpenAPI spec — complete endpoint/parameter coverage, runnable request/response examples, an error/status-code table, authentication notes, and a clear versioning and deprecation policy.
---

# API Reference Docs

## Purpose

Generate and verify complete, accurate API reference documentation derived from the source of truth — an OpenAPI/JSON Schema spec, typed function signatures, or route definitions. Every operation must document its parameters, request body, response shapes, authentication, error responses, and rate limits, with at least one runnable example per operation. Reference docs answer "what exactly does this endpoint accept and return", distinct from tutorials (how to accomplish a goal).

## When to use

- A service exposes a REST, GraphQL, or RPC API consumed by other teams or the public.
- An OpenAPI/Swagger spec exists and needs to be rendered into browsable, example-rich docs.
- New endpoints shipped without reference entries, or existing entries drifted from the code.
- A library/SDK needs reference docs generated from docstrings or type signatures.
- Consumers report confusion about error codes, required fields, or auth.

## When not to use

- The audience needs a goal-oriented walkthrough, not an exhaustive parameter list (use tutorial-and-how-to-writing).
- The API is purely internal, single-consumer, and fully described by inline types that the one caller already reads.
- You are documenting a release's user-facing changes (use changelog-and-release-notes).

## Procedure

### 1. Locate and validate the source of truth

```bash
# Find an OpenAPI / GraphQL / proto spec
find . -name "openapi*.y*ml" -o -name "openapi*.json" -o -name "swagger*.*" \
  -o -name "*.graphql" -o -name "*.proto" 2>/dev/null | grep -v node_modules

# Validate the OpenAPI spec before trusting it
npx --yes @redocly/cli lint openapi.yaml
# or: npx --yes @stoplight/spectral-cli lint openapi.yaml
```

### 2. Confirm endpoint and field coverage

```bash
# List every path + method declared in the spec
python3 - <<'EOF'
import yaml
spec = yaml.safe_load(open("openapi.yaml"))
for path, ops in spec.get("paths", {}).items():
    for method, op in ops.items():
        print(f"{method.upper():6} {path}  -> {op.get('summary','(no summary)')}")
EOF
```

Cross-check the live route table (framework router output) against the spec so no implemented endpoint is undocumented and no documented endpoint is dead.

### 3. Render reference docs from the spec

```bash
# Static HTML reference from OpenAPI
npx --yes @redocly/cli build-docs openapi.yaml -o site/api.html

# For library/SDK docs, generate from signatures + docstrings
#   Python:     pdoc ./pkg -o site/api      (or sphinx-apidoc)
#   TypeScript: npx typedoc --out site/api src/index.ts
```

### 4. Add a runnable example per operation

Each operation gets a complete request (method, URL, headers, body) and a real response with status code. Examples must use placeholder credentials and be copy-pasteable.

```bash
# Example block to embed, then verify against a test instance
curl -sS -X POST "$API_BASE/v1/widgets" \
  -H "Authorization: Bearer $API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "example-widget", "color": "blue"}'
# Expected: 201 Created, body: {"id":"wdg_123","name":"example-widget","color":"blue"}
```

### 5. Build the error / status-code table

Document every status code the operation can return, when it occurs, the error body schema, and the recommended client action.

### 6. Document authentication and versioning policy

State the auth scheme (bearer token, API key header, OAuth scopes) once, centrally. Define how versions are expressed (URI `/v1/`, header, or media type), the deprecation timeline, and the sunset signaling (e.g. `Deprecation` / `Sunset` response headers).

## Concrete checks

- [ ] The OpenAPI/GraphQL/proto spec lints clean before docs are generated.
- [ ] Every implemented endpoint appears in the reference (no undocumented routes).
- [ ] Every documented endpoint exists in code (no dead/phantom entries).
- [ ] Each parameter lists type, required/optional, default, and constraints.
- [ ] Each operation has at least one runnable request + real response example.
- [ ] Examples use placeholder tokens, never real secrets.
- [ ] An error table lists every status code, cause, body schema, and client action.
- [ ] The authentication scheme is documented once and linked from each operation.
- [ ] The versioning scheme and deprecation/sunset policy are stated explicitly.
- [ ] Deprecated fields/endpoints are clearly marked with the removal version.
- [ ] Pagination, rate-limit headers, and idempotency behavior are documented where applicable.
- [ ] At least one example was executed against a real/test instance and matched.

## Templates

```markdown
### POST /v1/widgets — Create a widget

Creates a widget. Requires scope `widgets:write`.

**Request body** (`application/json`)

| Field   | Type   | Required | Default | Notes                    |
|---------|--------|----------|---------|--------------------------|
| `name`  | string | yes      | —       | 1–64 chars               |
| `color` | string | no       | `gray`  | one of: gray, blue, red  |

**Responses**

| Status | Meaning      | Body schema     | Client action            |
|--------|--------------|-----------------|--------------------------|
| 201    | Created      | `Widget`        | Store the returned `id`  |
| 400    | Invalid body | `Error`         | Fix fields, retry        |
| 401    | No/expired token | `Error`     | Refresh credentials      |
| 429    | Rate limited | `Error`         | Honor `Retry-After`      |

**Example**

    curl -X POST "$API_BASE/v1/widgets" \
      -H "Authorization: Bearer $API_TOKEN" \
      -d '{"name":"demo","color":"blue"}'
    # 201 -> {"id":"wdg_123","name":"demo","color":"blue"}
```

## Common issues & anti-patterns

- Hand-written reference that silently drifts from the implementation; prefer generation from the spec.
- Examples with no response shown, so the reader cannot verify success.
- Missing error documentation — only the happy path is shown.
- Real API keys or tokens pasted into examples.
- "TODO: document this" placeholders shipped to production docs.
- No versioning policy, so consumers cannot tell stable from experimental endpoints.
- Required vs optional left ambiguous, causing avoidable 400s.

## Required output

Produce: (1) a coverage report (endpoints in spec vs in code vs documented); (2) spec lint results; (3) the rendered reference output path; (4) per-operation parameter and error tables; (5) at least one verified runnable example; (6) the documented auth + versioning/deprecation policy; (7) a list of drift or gaps to fix.

## Safety

- Never embed real credentials, tokens, or production data in examples — use placeholders.
- Run example requests only against test or sandbox instances, never destructive calls on production.
- Do not modify the API or its spec to match the docs; report drift for the owner to reconcile.
- Generate docs into a build/output directory; do not overwrite source specs.
