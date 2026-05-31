---
name: supabase-rls-edge-functions
description: Use when implementing or auditing Supabase Row Level Security policies, Edge Functions (Deno), Realtime subscriptions, or Storage RLS — including auth.uid() policy patterns, service_role risk management, and the Supabase CLI deploy workflow.
---

# Supabase RLS & Edge Functions

## Purpose

Provide concrete, security-first patterns for Supabase: Row Level Security policies using `auth.uid()` and `auth.jwt()`, Edge Functions in Deno with JWT verification, Realtime channel subscriptions with RLS enforcement, Storage bucket policies, and the full `supabase` CLI workflow (init, link, migrate, deploy, secrets). Surfaces the `service_role` key risk and how to avoid leaking it to the client.

## When to use

- Adding RLS policies to a new or existing table in Supabase.
- Writing an Edge Function that needs to run privileged logic (email send, payment webhook, admin action) without exposing `service_role` to the browser.
- Implementing Realtime presence or broadcast in a Next.js app.
- Setting up Storage buckets with per-user folder isolation.
- Auditing a Supabase project for security misconfigurations (public tables, missing RLS, anon key misuse).
- Setting up local Supabase development with the CLI.

## When not to use

- The project uses a different database/auth provider (Prisma + NextAuth, PlanetScale, etc.).
- The task is purely frontend — no Supabase reads, writes, or subscriptions involved.
- RLS is intentionally disabled for a specific table and the reason is documented.

## Procedure

### 1. Local development setup

```bash
# Install Supabase CLI
brew install supabase/tap/supabase # macOS
# or: npm install -g supabase

# Initialise project (creates supabase/ directory)
supabase init

# Start local stack (Postgres, Auth, Storage, Edge Functions)
supabase start
# → outputs: local API URL, anon key, service_role key

# Link to remote project
supabase link --project-ref <your-project-ref>
```

### 2. Row Level Security — patterns

Enable RLS on every table; disable only with a documented justification.

```sql
-- Migration: 20240101_enable_rls.sql

-- Always enable RLS on new tables
alter table public.posts enable row level security;
alter table public.profiles enable row level security;

-- ─────────────────────────────────────────────
-- Pattern 1: owner-only CRUD
-- ─────────────────────────────────────────────
-- Users can only see and modify their own rows
create policy "owners can select own posts"
 on public.posts for select
 using (auth.uid() = user_id);

create policy "owners can insert posts"
 on public.posts for insert
 with check (auth.uid() = user_id);

create policy "owners can update own posts"
 on public.posts for update
 using (auth.uid() = user_id)
 with check (auth.uid() = user_id);

create policy "owners can delete own posts"
 on public.posts for delete
 using (auth.uid() = user_id);

-- ─────────────────────────────────────────────
-- Pattern 2: public read, owner write
-- ─────────────────────────────────────────────
create policy "anyone can read published posts"
 on public.posts for select
 using (published = true);

-- Stack with the owner policy above for full coverage

-- ─────────────────────────────────────────────
-- Pattern 3: role-based access via JWT claim
-- ─────────────────────────────────────────────
-- Requires custom claim set in auth.users app_metadata
create policy "admins can read all orders"
 on public.orders for select
 using (
 (auth.jwt() -> 'app_metadata' ->> 'role') = 'admin'
 );

-- ─────────────────────────────────────────────
-- Pattern 4: team / organisation membership
-- ─────────────────────────────────────────────
create policy "team members can read team projects"
 on public.projects for select
 using (
 exists (
 select 1 from public.team_members tm
 where tm.team_id = projects.team_id
 and tm.user_id = auth.uid()
 )
 );

-- ─────────────────────────────────────────────
-- Useful helper: is_admin() security definer function
-- ─────────────────────────────────────────────
create or replace function public.is_admin()
returns boolean
language sql security definer stable
as $$
 select (auth.jwt() -> 'app_metadata' ->> 'role') = 'admin'
$$;
```

### 3. Edge Functions — Deno with auth verification

```bash
# Create a new Edge Function
supabase functions new send-email

# Local dev with env vars
supabase functions serve send-email --env-file .env.local --debug
```

`supabase/functions/send-email/index.ts`:
```typescript
import { createClient } from 'jsr:@supabase/supabase-js@2'

const corsHeaders = {
 'Access-Control-Allow-Origin': '*',
 'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
}

Deno.serve(async (req: Request) => {
 // Handle CORS preflight
 if (req.method === 'OPTIONS') {
 return new Response('ok', { headers: corsHeaders })
 }

 try {
 // Verify caller is authenticated — use anon key + JWT from request
 const authHeader = req.headers.get('Authorization')
 if (!authHeader) {
 return new Response(JSON.stringify({ error: 'Missing Authorization header' }),
 { status: 401, headers: { ...corsHeaders, 'Content-Type': 'application/json' } })
 }

 // Create a client scoped to the requesting user (respects RLS)
 const supabaseUser = createClient(
 Deno.env.get('SUPABASE_URL')!,
 Deno.env.get('SUPABASE_ANON_KEY')!,
 { global: { headers: { Authorization: authHeader } } },
 )

 // Verify the JWT and get the user
 const { data: { user }, error: authError } = await supabaseUser.auth.getUser()
 if (authError || !user) {
 return new Response(JSON.stringify({ error: 'Unauthorized' }),
 { status: 401, headers: { ...corsHeaders, 'Content-Type': 'application/json' } })
 }

 // Privileged action: use service_role client — NEVER expose this key to the browser
 const supabaseAdmin = createClient(
 Deno.env.get('SUPABASE_URL')!,
 Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!,
 )

 const body = await req.json()
 // ... perform privileged action (e.g. send email, update admin-only column)
 const { error } = await supabaseAdmin
 .from('email_log')
 .insert({ user_id: user.id, to: body.to, subject: body.subject })

 if (error) throw error

 return new Response(JSON.stringify({ success: true }),
 { status: 200, headers: { ...corsHeaders, 'Content-Type': 'application/json' } })

 } catch (err) {
 console.error(err)
 return new Response(JSON.stringify({ error: 'Internal server error' }),
 { status: 500, headers: { ...corsHeaders, 'Content-Type': 'application/json' } })
 }
})
```

```bash
# Set production secrets (never commit to .env)
supabase secrets set RESEND_API_KEY=re_xxxxx

# Deploy
supabase functions deploy send-email --no-verify-jwt # only if you handle JWT manually
# or (let Supabase verify JWT automatically):
supabase functions deploy send-email
```

### 4. Realtime subscriptions with RLS

```typescript
// client/hooks/useRealtimePosts.ts
import { useEffect, useState } from 'react'
import { createClient } from '@supabase/supabase-js'
import type { Database } from '@/types/supabase' // generated types

const supabase = createClient<Database>(
 process.env.NEXT_PUBLIC_SUPABASE_URL!,
 process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
)

// RLS applies to Realtime: users only receive rows they can SELECT
export function useRealtimePosts(teamId: string) {
 const [posts, setPosts] = useState<Database['public']['Tables']['posts']['Row'][]>([])

 useEffect(() => {
 // Initial fetch
 supabase.from('posts').select('*').eq('team_id', teamId).then(({ data }) => {
 if (data) setPosts(data)
 })

 // Subscribe to changes — RLS filter applied server-side
 const channel = supabase.channel(`posts:${teamId}`)
 .on('postgres_changes', {
 event: '*',
 schema: 'public',
 table: 'posts',
 filter: `team_id=eq.${teamId}`,
 }, (payload) => {
 if (payload.eventType === 'INSERT') {
 setPosts(prev => [...prev, payload.new as typeof prev[0]])
 } else if (payload.eventType === 'UPDATE') {
 setPosts(prev => prev.map(p => p.id === payload.new.id ? payload.new as typeof p : p))
 } else if (payload.eventType === 'DELETE') {
 setPosts(prev => prev.filter(p => p.id !== payload.old.id))
 }
 })
 .subscribe()

 return () => { supabase.removeChannel(channel) }
 }, [teamId])

 return posts
}
```

### 5. Storage RLS — per-user folder isolation

```sql
-- Enable RLS on storage.objects (already enabled by default in Supabase)
-- Bucket: 'avatars' — each user owns their own folder

create policy "users can upload own avatar"
 on storage.objects for insert
 with check (
 bucket_id = 'avatars'
 and (storage.foldername(name))[1] = auth.uid()::text
 );

create policy "users can read own avatar"
 on storage.objects for select
 using (
 bucket_id = 'avatars'
 and (storage.foldername(name))[1] = auth.uid()::text
 );

create policy "users can delete own avatar"
 on storage.objects for delete
 using (
 bucket_id = 'avatars'
 and (storage.foldername(name))[1] = auth.uid()::text
 );

-- Public read bucket (e.g. product images — no auth required)
create policy "anyone can view product images"
 on storage.objects for select
 using (bucket_id = 'product-images');
```

Upload from client:
```typescript
const { data, error } = await supabase.storage
 .from('avatars')
 .upload(`${user.id}/avatar.png`, file, {
 cacheControl: '3600',
 upsert: true,
 })
```

### 6. Generating TypeScript types

```bash
# Generate types from local Supabase stack
supabase gen types typescript --local > src/types/supabase.ts

# Generate from remote project
supabase gen types typescript \
 --project-id <your-project-ref> > src/types/supabase.ts

# Add to package.json scripts for easy refresh
# "types:gen": "supabase gen types typescript --local > src/types/supabase.ts"
```

## Concrete checks

- [ ] Every user-facing table has `alter table ... enable row level security`.
- [ ] No `select *` policy without an `auth.uid()` or role check — public tables are intentional and documented.
- [ ] `service_role` key only in Edge Functions or server-side code — never in `NEXT_PUBLIC_` env vars.
- [ ] Edge Functions validate the `Authorization` header before performing privileged actions.
- [ ] Realtime subscriptions include a `filter` clause matching the RLS `using` condition.
- [ ] Storage policies use `storage.foldername(name)[1] = auth.uid()::text` for per-user isolation.
- [ ] `supabase gen types typescript` output is committed and used (`Database` type imported).
- [ ] CORS `Access-Control-Allow-Origin` in Edge Functions restricted to your domain in production (not `*`).

## Commands

```bash
# Start local stack
supabase start

# Run migrations against local DB
supabase db push

# Create a new migration
supabase migration new add_rls_policies

# Serve Edge Functions locally with hot reload
supabase functions serve --env-file .env.local

# Deploy all functions
supabase functions deploy

# Set a secret (production)
supabase secrets set MY_API_KEY=xxx

# List secrets (shows names, not values)
supabase secrets list

# Inspect RLS policies on a table
supabase db inspect --schema public | grep -A5 "Row security"

# Reset local DB (drops and re-runs migrations)
supabase db reset
```

## Required output

When implementing or reviewing Supabase security, deliver:
1. RLS policy SQL for each CRUD operation on each affected table.
2. `service_role` audit: confirm it appears only in Edge Functions / server env vars.
3. Edge Function auth flow: JWT verification → user scoped client → admin action.
4. Realtime subscription filter matching RLS `using` clause.
5. Storage bucket policies covering insert, select, delete per access pattern.
6. TypeScript types generation command added to `package.json` scripts.

## Safety checks

- `SUPABASE_SERVICE_ROLE_KEY` must never appear in client-side code or `NEXT_PUBLIC_` variables — if found, rotate the key immediately in the Supabase dashboard.
- `security definer` functions bypass RLS — review every `create function ... security definer` carefully.
- Policies using `auth.uid()` return `null` for unauthenticated requests — this means `null = user_id` evaluates to false, correctly denying access; do not add a `null` check thinking it is needed.
- `supabase db reset` drops all data — never run against a production database.
- Edge Function CORS headers must be sent on error responses too, not just success.

## Completion criteria

Done means: every table has RLS enabled with explicit `select`, `insert`, `update`, `delete` policies, `service_role` key is absent from all client-side code, at least one Edge Function is deployed and returns 401 for unauthenticated requests, Storage bucket policies enforce per-user isolation, and TypeScript types are generated and used throughout the codebase.
