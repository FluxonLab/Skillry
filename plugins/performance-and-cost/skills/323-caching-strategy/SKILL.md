---
name: caching-strategy
description: Use when you need to design or review a caching strategy across layers (CDN/edge/application/database), choose TTLs and cache keys, prevent cache stampedes, handle invalidation correctly, and measure hit rate to prove the cache is actually helping.
---

# Caching Strategy

## Purpose

Design and review caching so it reduces latency and load without serving stale or wrong data. This covers the full stack of cache layers (CDN, edge, application/in-memory, database/result cache), key design, TTL selection, invalidation, and the two failure modes that bite hardest in production: cache stampede (thundering herd on a cold or expired key) and silent staleness. It insists on measuring hit rate and origin offload, because an unmeasured cache is just a guess. The output is a layer-by-layer plan with keys, TTLs, an invalidation policy, and a hit-rate measurement.

## When to use

- A read-heavy endpoint or page repeatedly recomputes or refetches the same data.
- Origin/database load spikes whenever a popular key expires (stampede symptoms).
- Data is served stale after an update and you need a correct invalidation policy.
- A cache exists but nobody knows its hit rate or whether it offloads the origin.
- You are adding a CDN or edge layer and need to decide what is cacheable and for how long.

## When not to use

- The data is highly personalized and changes on every request, where caching would add complexity for near-zero hit rate.
- Strong read-after-write consistency is a hard requirement on that path and no staleness window is acceptable (cache only with care, or not at all).
- The real problem is an unindexed query — fix the query first; caching a slow query hides a fixable bug.

## Procedure

1. **Map the layers and pick where to cache.** Identify which of CDN, edge/reverse-proxy, application (in-process or Redis/Memcached), and database result cache applies. Cache as close to the user as the data's freshness allows; cache the most expensive-to-compute, most-reused data.
2. **Classify each item by volatility and shareability.** Public + slow-changing → CDN/edge with long TTL. Per-user but reused within a session → application cache. Expensive aggregate → result cache with explicit invalidation. Never cache per-request unique data.
3. **Design the cache key.** Include every input that changes the output: route, query params that matter, locale, auth/role scope, and a version/namespace prefix. Exclude volatile junk (request IDs, timestamps). A wrong key either never hits or leaks one user's data to another.
4. **Choose TTL and a staleness strategy.** Set TTL from how stale the data may acceptably be. Prefer stale-while-revalidate / stale-if-error so users get a fast (slightly stale) response while the cache refreshes in the background.
5. **Protect against stampede.** On expiry, prevent every request from hitting the origin at once: use a per-key lock / single-flight, early/probabilistic re-computation before expiry, or serve stale while one worker revalidates.
6. **Define invalidation.** Prefer event-driven invalidation (delete/update the key on write) plus a TTL as a safety net. Document who invalidates what on which write. Avoid blanket flushes that cause a stampede.
7. **Measure hit rate and origin offload.** Instrument hits, misses, and evictions. Report hit rate per cache and the reduction in origin requests/latency. Tune TTL and keys from the numbers, not intuition.

## Concrete checks

- [ ] Each cached item is classified by volatility and shareability (public/CDN vs. per-user/app).
- [ ] Cache keys include all output-affecting inputs (params, locale, auth scope) and a version/namespace prefix.
- [ ] No per-user or sensitive data is cached in a shared/public layer (no auth-scoped data behind a CDN without a Vary/key on the user).
- [ ] TTLs are set from an explicit acceptable-staleness window, not copied blindly.
- [ ] Stale-while-revalidate (or single-flight) protects hot keys from a stampede on expiry.
- [ ] Invalidation is event-driven on writes, with TTL as a backstop; no routine full-flush.
- [ ] A cache version/namespace prefix exists so a deploy can invalidate atomically.
- [ ] Hit rate, miss rate, and eviction rate are measured per cache layer.
- [ ] Origin offload (request/latency reduction) is quantified, proving the cache helps.
- [ ] Negative results (e.g., 404s) have a separate, short TTL to avoid hammering the origin.
- [ ] Every read path correctly handles a cache miss / cold cache (the cache is not treated as source of truth).
- [ ] Cached values are immutable snapshots, not shared references that later code can mutate.

## Commands or Templates

```bash
# Redis hit-rate and memory health (application cache)
redis-cli INFO stats | grep -E 'keyspace_hits|keyspace_misses'
# hit rate = hits / (hits + misses)
redis-cli INFO memory  | grep -E 'used_memory_human|maxmemory_policy|evicted_keys'
# Inspect a key's TTL and find suspicious never-expiring keys
redis-cli TTL "v3:user:42:dashboard"
redis-cli --scan --pattern 'v3:*' | head
```

```bash
# Verify CDN/edge cache behavior from the response headers
curl -sI https://example.com/asset.js | grep -iE 'cache-control|age|x-cache|cf-cache-status|etag|vary'
# Cache-Control example for a shared, revalidatable response:
#   Cache-Control: public, max-age=60, stale-while-revalidate=600, stale-if-error=86400
```

```python
# Single-flight / lock to prevent cache stampede (Redis + app code)
import time, redis
r = redis.Redis()

def get_with_singleflight(key, ttl, recompute, lock_ttl=10):
    val = r.get(key)
    if val is not None:
        return val                      # cache hit
    lock = f"lock:{key}"
    if r.set(lock, "1", nx=True, ex=lock_ttl):   # only one worker recomputes
        try:
            fresh = recompute()
            r.set(key, fresh, ex=ttl)
            return fresh
        finally:
            r.delete(lock)
    # someone else is recomputing: briefly wait, then read what they wrote
    for _ in range(50):
        time.sleep(0.05)
        val = r.get(key)
        if val is not None:
            return val
    return recompute()                  # last-resort fallback
```

```python
# Versioned cache key: a bump of CACHE_VERSION invalidates everything atomically
CACHE_VERSION = "v3"
def cache_key(route, user_scope, locale, **params):
    parts = "&".join(f"{k}={params[k]}" for k in sorted(params))
    return f"{CACHE_VERSION}:{route}:{user_scope}:{locale}:{parts}"
```

```python
# Probabilistic early expiration (XFetch): refresh hot keys slightly BEFORE expiry
# so they never all expire at once. delta = cost of recompute; beta tunes eagerness.
import math, random, time

def should_recompute(value_age, ttl, delta, beta=1.0):
    # returns True early, with rising probability as the key approaches expiry
    return value_age - delta * beta * math.log(random.random()) >= ttl
```

```bash
# Measure CDN offload: ratio of edge HITs to total over a sample of requests.
for i in $(seq 1 50); do
  curl -s -o /dev/null -D - https://example.com/asset.js | grep -i 'x-cache\|cf-cache-status'
done | grep -ioE 'hit|miss' | sort | uniq -c
```

## Common issues & anti-patterns

- **Caching per-user data in a shared layer.** The classic CDN leak: user A's response served to user B because the key/Vary omitted the auth scope.
- **No stampede protection.** A popular key expires and thousands of requests hit the origin simultaneously, causing the exact overload the cache should prevent.
- **TTL chosen by feel.** Pick TTL from the acceptable-staleness window; "5 minutes because it sounds safe" is not a strategy.
- **Blanket FLUSHALL on deploy.** Flushing everything causes an instant cold-cache stampede; use a version prefix bump instead.
- **Caching a slow, unindexed query.** The cache hides a bug that returns on every miss; fix the query first.
- **Never measuring hit rate.** An unmeasured cache can be at 10% hit rate and pure overhead; instrument it.
- **Forgetting negative caching.** Not caching 404s/errors lets a missing key hammer the origin repeatedly.
- **Unbounded memory / no eviction policy.** Without `maxmemory` + an eviction policy, the cache OOMs or evicts unpredictably.
- **Caching mutable objects by reference.** Storing a reference rather than a snapshot lets later mutations corrupt the cached value; cache an immutable copy.
- **One TTL for everything.** A single global TTL ignores that different data has different volatility; set TTL per item class.
- **Thundering herd on cache restart.** A cache restart/deploy empties everything at once; warm hot keys or roll the restart to avoid a cold-cache origin spike.
- **Treating the cache as the source of truth.** Code that assumes a key is always present breaks on eviction or a cold cache; always handle the miss path correctly.

## Required output

Produce a report containing:
1. **Layer map** — which layers cache what, with a one-line justification (volatility × shareability) per item.
2. **Key & TTL table** — cache key format, included inputs, TTL, and staleness strategy per cached item.
3. **Invalidation policy** — event-driven triggers per write path, the TTL backstop, and the version/namespace scheme.
4. **Stampede protection** — the mechanism used (single-flight / SWR / early refresh) for each hot key.
5. **Measurement** — current/expected hit rate per layer and the origin offload (load/latency reduction).
6. **Findings & risks** — any shared-layer leakage, unbounded memory, or full-flush risks, with fixes.
7. **Next safe action** — the highest-value change (often adding SWR to the hottest key or fixing a leaky key).

## Safety

- Never cache authenticated or PII responses in a shared/public layer without a per-user key or correct `Vary` — this is a data-leak risk; flag and stop if found.
- Do not run `FLUSHALL`/`FLUSHDB` against a shared or production cache; prefer namespace/version bumps and confirm before any flush.
- Validate invalidation in staging before relying on it; an incorrect policy serves stale data silently.
- Set `maxmemory` and an eviction policy so the cache cannot exhaust host memory.
- Treat cache keys and values as potentially sensitive; do not print full values or keys containing tokens in logs or reports.
- Get approval before changing TTLs or eviction policy on a production cache; cold-cache effects can overload the origin.
