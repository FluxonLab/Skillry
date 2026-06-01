---
name: docker-image-hardening
description: Use when you need to review or author a Dockerfile for multi-stage builds, minimal or distroless base images, non-root runtime, layer caching, .dockerignore hygiene, pinned digests, image vulnerability scanning, and SBOM generation.
---

# Docker Image Hardening

## Purpose

Conduct a structured review-and-author pass over a Dockerfile and its build context — covering multi-stage build structure, minimal/distroless base selection, non-root runtime user, layer-cache efficiency, `.dockerignore` hygiene, pinned base digests, secret leakage in layers, image vulnerability scanning, and SBOM generation. The goal is a small, reproducible, low-CVE image that runs as an unprivileged user and never bakes secrets into a layer. Findings must come from the actual Dockerfile and scan output, not assumptions.

## When to use

- A PR adds or modifies a `Dockerfile`, `Containerfile`, `.dockerignore`, or compose build context.
- An image is large, slow to build, or rebuilds from scratch on every code change (bad cache order).
- The container runs as root or uses a `latest`/unpinned base tag.
- A vulnerability scan has not been run and CVE exposure of the image is unknown.
- You need an SBOM for supply-chain compliance.
- You are reviewing a base image choice (full OS vs slim vs distroless).

## When not to use

- The change is orchestration only (Kubernetes manifests, compose service wiring) — use the Kubernetes or compose review instead.
- There is no container build in the repo at all.
- The image is a throwaway local-only dev sandbox with no distribution or production intent.

## Procedure

### 1. Orient to the build context

```bash
find . -maxdepth 3 -iname "Dockerfile*" -o -iname "Containerfile" 2>/dev/null
cat .dockerignore 2>/dev/null || echo "NO .dockerignore — context may leak secrets/.git"
# Base images in use and whether tags are pinned
grep -nE "^FROM " Dockerfile
```

### 2. Check multi-stage structure and base image

```bash
# Count build stages — a build/runtime split should exist for compiled langs
grep -cE "^FROM " Dockerfile
# Flag floating tags (latest / no tag) and missing digest pins
grep -nE "^FROM .*(:latest|^FROM [^@]+$)" Dockerfile
grep -nE "^FROM .*@sha256:" Dockerfile || echo "no digest pins (tags can move)"
```

### 3. Verify non-root runtime

```bash
# Must create and switch to a non-root USER before CMD/ENTRYPOINT
grep -nE "^USER " Dockerfile || echo "NO USER — container runs as root (HIGH)"
grep -nE "adduser|useradd|addgroup|--chown" Dockerfile
# distroless nonroot variants imply UID 65532
grep -n "nonroot" Dockerfile
```

### 4. Audit secret leakage and layer hygiene

```bash
# Secrets must never be COPYd or ARG-baked into a layer
grep -nE "ARG .*(SECRET|TOKEN|PASSWORD|KEY)|ENV .*(SECRET|TOKEN|PASSWORD)" Dockerfile
grep -nE "COPY .*(\.env|id_rsa|\.pem|credentials)" Dockerfile
# .git, node_modules, secrets should be excluded from context
grep -E "\.git|node_modules|\.env|\*\.pem" .dockerignore 2>/dev/null || echo "context not trimmed"
```

### 5. Review layer-cache ordering

```bash
# Dependency manifests should be COPYd and installed BEFORE app source,
# so code edits don't bust the dependency cache layer.
grep -nE "^COPY |^RUN .*(install|ci|build)" Dockerfile
```

### 6. Scan the image and generate an SBOM

```bash
# Build for scanning (local tag, no push)
docker build -t app:scan .
# Vulnerability scan (choose one available)
trivy image --severity HIGH,CRITICAL app:scan 2>/dev/null \
  || docker scout cves app:scan 2>/dev/null \
  || grype app:scan 2>/dev/null
# SBOM
syft app:scan -o spdx-json > sbom.spdx.json 2>/dev/null \
  || docker sbom app:scan 2>/dev/null
# Image size
docker image inspect app:scan --format '{{.Size}}' | numfmt --to=iec 2>/dev/null
```

## Concrete checks

- [ ] Multi-stage build separates build dependencies from the runtime image.
- [ ] Base image is minimal (slim, alpine, or distroless) appropriate to the language.
- [ ] Every `FROM` is pinned to a specific tag, ideally with an `@sha256:` digest.
- [ ] A non-root `USER` is set before `CMD`/`ENTRYPOINT`.
- [ ] No secrets are passed via `ARG`/`ENV` or `COPY`d into any layer.
- [ ] A `.dockerignore` excludes `.git`, `node_modules`, `.env`, keys, and build artifacts.
- [ ] Dependency install layers come before application source for cache reuse.
- [ ] `RUN` commands clean their package caches in the same layer (no orphaned cache bloat).
- [ ] A vulnerability scan reports no unaddressed HIGH/CRITICAL CVEs.
- [ ] An SBOM can be generated for the final image.
- [ ] `HEALTHCHECK` is defined (or health is handled by the orchestrator).
- [ ] No unnecessary build tools (compilers, curl, package managers) remain in the final stage.

## Commands or Templates

```dockerfile
# syntax=docker/dockerfile:1
# ---- build stage ----
FROM golang:1.22-bookworm AS build
WORKDIR /src
COPY go.mod go.sum ./
RUN go mod download            # cached unless go.mod/go.sum change
COPY . .
RUN CGO_ENABLED=0 go build -o /app ./cmd/server

# ---- runtime stage (distroless, non-root) ----
FROM gcr.io/distroless/static-debian12:nonroot
COPY --from=build /app /app
USER nonroot:nonroot           # UID 65532, no shell, no package manager
EXPOSE 8080
ENTRYPOINT ["/app"]
```

```dockerfile
# Node example: pinned digest, non-root, cache-friendly
FROM node:20-slim@sha256:<digest> AS deps
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci --omit=dev && npm cache clean --force
COPY . .
USER node
CMD ["node", "server.js"]
```

```bash
# Safe build + scan + SBOM (local, no registry push)
docker build -t app:scan .
trivy image --severity HIGH,CRITICAL --exit-code 1 app:scan
syft app:scan -o spdx-json > sbom.spdx.json
```

## Common issues & anti-patterns

- `FROM ubuntu:latest` (or no tag) — non-reproducible and large attack surface.
- Single-stage build shipping compilers, git, and dev headers into production.
- Container runs as root because no `USER` is set.
- `ARG GITHUB_TOKEN=...` or `COPY .env .` — secrets persist in image history forever.
- `COPY . .` before `RUN npm ci` — every code edit invalidates the dependency cache.
- No `.dockerignore`, so `.git` and local secrets get copied into the build context.
- `RUN apt-get install` without removing `/var/lib/apt/lists` in the same layer — cache bloat.
- Pushing an unscanned image to a registry.

## Required output

Produce a structured report with:
1. **Base & structure** — base image, tag/digest pin status, number of stages.
2. **Runtime user** — root vs non-root; where `USER` is set.
3. **Secret hygiene** — any secrets in ARG/ENV/COPY (redacted); `.dockerignore` coverage.
4. **Cache efficiency** — layer ordering issues that bust caching.
5. **Scan results** — HIGH/CRITICAL CVE count from the scanner; SBOM availability.
6. **Size** — final image size and the largest avoidable contributors.
7. **Findings table** — `Dockerfile:line | issue | severity | concrete fix`.
8. **Next safe action** — highest-priority hardening change.

## Safety

- This is a review and authoring skill. Building and scanning a local image is safe; NEVER `docker push` to a registry, deploy, or run a container with mounted host secrets or privileged flags without explicit human approval.
- Never bake real secret values into a Dockerfile, `ARG`, or `ENV`; use build secrets (`--mount=type=secret`) or runtime injection.
- Redact any discovered credentials to `****` and flag them for rotation; treat secrets in image history as compromised.
- Do not run untrusted images with `--privileged`, host networking, or host volume mounts.
- Do not delete existing images/volumes on the host without approval.
- Report scanner findings; do not auto-upgrade base images in a way that silently changes runtime behavior — propose the change for human review.
