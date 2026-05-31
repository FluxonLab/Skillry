---
name: next-app-router-rsc-review
description: Use when you need to review a Next.js App Router codebase for React Server Component correctness, "use client"/"use server" boundary violations, server secret leakage into the client bundle, Server Action input validation, fetch cache strategy, and metadata/streaming patterns.
---

# Next.js App Router & RSC Review

## Purpose

Audit a Next.js 15 App Router project for correctness at the Server/Client Component boundary: detect "use client" / "use server" misuse, unserializable prop passing, accidental server-secret exposure in client bundles, missing Server Action validation, incorrect fetch caching, and broken Suspense/error-boundary wiring. Surface every finding with the exact file and line — never infer from project structure alone.

## When to use

- A PR adds or modifies pages, layouts, or components in the `app/` directory.
- A bug report mentions hydration errors, "cannot serialize a class instance", or unexpected client re-renders.
- A security review flags a `NEXT_PUBLIC_` variable being used for a secret, or a server import in a client file.
- `next build` produces a large client bundle or a missing-server-component warning.
- You are onboarding into a Next.js 15 project using the App Router for the first time.

## When not to use

- The project uses only the Pages Router (`pages/` directory) — use a legacy Next.js review instead.
- The PR is CSS/Tailwind-only with no component logic changes.
- The issue is purely a database or API concern with no rendering layer involvement.

## Procedure

### 1. Map the Server/Client component boundary

```bash
# Count "use client" directives
grep -rn '"use client"' app/ --include="*.tsx" --include="*.ts" | wc -l
grep -rn '"use client"' app/ --include="*.tsx" --include="*.ts" | head -30

# Count "use server" directives (Server Actions and server-only files)
grep -rn '"use server"' app/ --include="*.tsx" --include="*.ts" | wc -l

# Find components that have BOTH directives (always wrong)
grep -rln '"use client"' app/ | xargs grep -l '"use server"' 2>/dev/null

# Find "use client" at file level vs. inside a function (wrong position)
grep -n '"use client"' app/**/*.tsx | grep -v "^.*:1:" | head -20
```

### 2. Detect unserializable props passed from Server to Client Components

```bash
# Server Component passing a function prop to a client component — not serializable
grep -rn --include="*.tsx" \
 'onClick={[^}]*}>\|onSubmit={[^}]*}>' \
 app/ | grep -v '"use client"' | head -20

# Class instance, Map, Set, Date props — detect suspicious patterns
grep -rn --include="*.tsx" \
 'new Date()\|new Map()\|new Set()' \
 app/ | head -20
```

### 3. Audit for server secret leakage into client bundle

```bash
# "use client" files that import from server-only modules
grep -rln '"use client"' app/ | xargs grep -l \
 "server-only\|@/lib/db\|prisma\|supabase.*service_role\|process\.env\.[^N]" 2>/dev/null

# NEXT_PUBLIC_ misuse: secret stored as NEXT_PUBLIC_ (exposed to browser)
grep -rn "NEXT_PUBLIC_" .env* 2>/dev/null | grep -iE "secret|key|token|password|private" | head -20

# Server-only env var referenced inside a "use client" file
grep -rn 'process\.env\.' app/ --include="*.tsx" \
 | grep -v "NEXT_PUBLIC_" > /tmp/server-env-refs.txt
# Cross-reference with "use client" files
grep -rln '"use client"' app/ | xargs grep -ln 'process\.env\.' 2>/dev/null

# Ensure server-only is imported at the top of server utility files
grep -rn "server-only" lib/ utils/ --include="*.ts" | head -20
```

### 4. Validate Server Actions

```bash
# Find all Server Actions (files or functions with "use server")
grep -rn '"use server"' app/ --include="*.ts" --include="*.tsx" -l

# Check for input validation (zod schema) in each action file
for f in $(grep -rln '"use server"' app/); do
 if ! grep -q "z\.\|zod\|schema\.parse\|safeParse" "$f"; then
 echo "NO VALIDATION: $f"
 fi
done

# Check for auth guard in server actions (session/user check before mutation)
grep -rn '"use server"' app/ -l | xargs grep -L \
 "getServerSession\|auth()\|currentUser\|session\." 2>/dev/null | head -10

# Confirm revalidatePath/revalidateTag is called after mutations
grep -rn "revalidatePath\|revalidateTag" app/ --include="*.ts" --include="*.tsx"
```

### 5. Review fetch caching strategy

```bash
# Find fetch calls without explicit cache option (Next.js 15 default: no-store)
grep -rn "fetch(" app/ --include="*.tsx" --include="*.ts" \
 | grep -v "cache:\|next:" | head -30

# Find stale force-cache on dynamic data
grep -rn "force-cache" app/ --include="*.tsx" --include="*.ts" | head -20

# Find unstable_cache / React cache usage
grep -rn "unstable_cache\|import.*cache.*from.*react" app/ --include="*.ts" --include="*.tsx"

# Find generateStaticParams for dynamic routes
find app -name "page.tsx" | xargs grep -l "\[" 2>/dev/null \
 | xargs grep -L "generateStaticParams" 2>/dev/null | head -10
```

### 6. Check metadata API and streaming/Suspense

```bash
# Pages/layouts missing metadata export
find app -name "page.tsx" | xargs grep -L "export const metadata\|generateMetadata" | head -20

# Suspense boundaries wrapping async components
grep -rn "<Suspense" app/ --include="*.tsx" | wc -l

# error.tsx and loading.tsx presence per route segment
find app -type d | while read d; do
 has_page=$(ls "$d/page.tsx" 2>/dev/null)
 has_error=$(ls "$d/error.tsx" 2>/dev/null)
 has_loading=$(ls "$d/loading.tsx" 2>/dev/null)
 [ -n "$has_page" ] && [ -z "$has_error" ] && echo "NO error.tsx: $d"
done
```

### 7. Inspect data-fetching patterns in RSC

```bash
# Confirm await fetch / await db calls are at RSC level (not inside useEffect)
grep -rn "useEffect.*fetch\|useEffect.*await" app/ --include="*.tsx" | head -20

# Client-side data fetch that should be RSC fetch
grep -rn "useEffect\|useState" app/ --include="*.tsx" \
 | grep -v '"use client"' > /tmp/hooks-without-use-client.txt
wc -l /tmp/hooks-without-use-client.txt

# Prisma or DB client imported outside server context
grep -rn "prisma\|PrismaClient" app/ --include="*.tsx" --include="*.ts" \
 | grep -v "\.server\." | head -20
```

## Concrete checks

- [ ] Every file containing React hooks (`useState`, `useEffect`, `useRef`, etc.) has `"use client"` at line 1.
- [ ] No `"use client"` file imports `server-only`, `prisma`, or any module that transitively imports Node-only APIs.
- [ ] No `NEXT_PUBLIC_` variable holds a secret, API key, or private token.
- [ ] Server-only env vars (`process.env.DATABASE_URL`, `process.env.SECRET_*`) are never referenced in `"use client"` files.
- [ ] Every Server Action has a zod (or equivalent) `parse`/`safeParse` on incoming `FormData` or arguments.
- [ ] Every mutating Server Action checks the session/user before performing the mutation.
- [ ] `revalidatePath` or `revalidateTag` is called after each Server Action that mutates cached data.
- [ ] `fetch()` calls in RSC have an explicit `cache:` or `next: { revalidate }` option — no accidental over-caching.
- [ ] `generateStaticParams` is exported from every dynamic-segment page that should be statically generated.
- [ ] Every async RSC that may suspend is wrapped in a `<Suspense fallback={...}>` boundary.
- [ ] `error.tsx` files are present for every route segment with meaningful data-fetching.
- [ ] `loading.tsx` is present for route segments with slow data dependencies.
- [ ] `export const dynamic = 'force-dynamic'` is used intentionally, not as a catch-all fix for caching issues.
- [ ] The `client-only` package is imported in any file that must never run on the server.
- [ ] No class instances, functions, or non-serializable objects are passed as props across the Server/Client boundary.

## Commands

```bash
# Summary: boundary violation candidates
echo "=== 'use client' files with server imports ==="
grep -rln '"use client"' app/ | xargs grep -l \
 "prisma\|server-only\|process\.env\.[^N]" 2>/dev/null

echo "=== Server Actions without zod validation ==="
for f in $(grep -rln '"use server"' app/); do
 grep -q "safeParse\|schema\.parse\|z\." "$f" || echo " $f"
done

echo "=== Pages missing metadata ==="
find app -name "page.tsx" | xargs grep -rL "metadata\|generateMetadata" | head -20

echo "=== fetch() without cache option ==="
grep -rn 'fetch(' app/ --include="*.ts" --include="*.tsx" \
 | grep -v "cache:\|next:\|//\|test" | wc -l
```

## Required output

Produce a structured report with:
1. **Boundary audit** — list every `"use client"` file that imports server-only modules; severity Critical if it leaks secrets.
2. **Secret/env audit** — any `NEXT_PUBLIC_` secret or server env ref in client files; severity Critical.
3. **Server Action findings** — files missing input validation or auth guard, with exact path.
4. **Cache strategy** — fetch calls with missing or wrong cache mode, `generateStaticParams` gaps.
5. **Streaming/metadata gaps** — pages missing `error.tsx`, `loading.tsx`, `<Suspense>`, or `metadata` export.
6. **Recommended fixes** — one concrete code snippet per Critical/High finding.
7. **Next safe command** — the single highest-priority action.

## Safety checks

- Do not modify `.env*` files during review.
- Do not execute Server Actions or trigger mutations as part of the review.
- Do not force-push or amend history to remove accidentally committed secrets; flag them for rotation and `.gitignore` update instead.
- Never print raw env var values found in files.

## Completion criteria

Done means: all `"use client"` / `"use server"` files are checked for boundary correctness, secret leakage paths are enumerated, every Server Action has a validation/auth status, fetch caching strategy is assessed for each RSC data-fetch, and Suspense/error boundary coverage is documented. Every finding has file:line + severity + a concrete fix.
