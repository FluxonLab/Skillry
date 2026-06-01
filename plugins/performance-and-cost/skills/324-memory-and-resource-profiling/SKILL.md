---
name: memory-and-resource-profiling
description: Use when you need to profile memory and OS resources — heap profiling, finding leaks and unbounded growth, GC pressure, and leaked file descriptors, sockets, or connections, including processes that hit container memory limits and get OOM-killed.
---

# Memory and Resource Profiling

## Purpose

Diagnose why a process grows without bound, gets OOM-killed, or runs out of file descriptors and connections. This skill separates the distinct failure modes — a true memory leak (retained objects that should be freed), GC pressure (lots of short-lived allocation thrashing the collector), and handle/connection leaks (descriptors or pool slots never returned) — and gives concrete tools to confirm each. It explicitly covers containers, where the JVM/Node/Python runtime must respect the cgroup limit or the kernel OOM-killer ends the process. The output is a named retention path or leaked resource with evidence, not "it uses a lot of memory."

## When to use

- A process's memory climbs steadily over hours/days and never plateaus (suspected leak).
- A container is OOM-killed (exit code 137) even though the host has free RAM.
- Latency degrades over time and GC pause time or frequency is rising (GC pressure).
- Process RSS keeps climbing while the managed heap looks flat (suspected native/off-heap leak).
- "Too many open files" / `EMFILE`, or the connection pool reports it is exhausted while traffic is normal.
- Memory usage is high and you need to know what is actually retained on the heap.

## When not to use

- The process legitimately needs that much memory for its working set (a large in-memory index) and is stable — that is capacity planning, not a leak.
- A single one-off spike came from an obviously large input and the process recovered — not a leak.
- The growth is in a third-party service you cannot instrument or patch — escalate to its owner rather than profiling locally.
- The real issue is CPU/latency with flat memory — use backend latency profiling instead.

## Procedure

1. **Confirm the shape: leak vs. plateau vs. spike.** Plot RSS/heap over time under steady load. A leak rises monotonically and never recovers after GC; a healthy process saws up and down around a stable plateau; a spike jumps once on a large input and recedes. One sample tells you nothing — the diagnosis lives in the trend.
2. **Capture two heap snapshots and diff them.** Take a heap snapshot, run representative work, take another, and compare retained size by type/constructor. Growing object counts that never get collected point to the leak's owner. Walk the retainer/dominator path to the GC root holding them — the root is the bug, not the leaked object itself.
3. **Distinguish a leak from GC pressure.** High allocation rate with stable live heap is GC pressure, not a leak — fix by reducing per-request allocations (object reuse, streaming, avoiding large intermediate copies), not by hunting retainers. Confirm by checking whether live heap after a full GC actually grows over time.
4. **Check OS handles, not just heap.** List open file descriptors and sockets for the PID over time. A steadily rising FD count is a handle/socket leak (unclosed files, HTTP responses, or DB connections), which OOM-kills or `EMFILE`-fails the process independently of heap. This failure mode is invisible to a heap profiler, so check it explicitly.
5. **Audit pool return paths.** For every acquired connection/file/lock, confirm it is released on every path including exceptions (context managers / `try-finally` / `defer` / `using`). A pool "leak" is usually a missing release on an error branch that only triggers under partial failure, so it grows slowly and shows up days later.
6. **Set the runtime to the container limit.** In a container, configure the runtime to read the cgroup memory limit (or set max-heap explicitly) so it GCs before the kernel OOM-kills it. A runtime that assumes host RAM will happily allocate past the cgroup limit and be killed with exit 137 regardless of code quality.
7. **Bound every cache and collection.** A module-level dict, list, or memo that only grows is a leak by construction; give it a max size and an eviction policy (LRU/TTL). Unbounded growth that is "correct" today becomes an OOM at scale tomorrow.
8. **Isolate native vs. managed memory.** When the managed heap looks flat but RSS keeps climbing, the leak is likely in native allocations (C extensions, buffers, mmaps, off-heap caches). Compare heap size against process RSS; a widening gap points outside the managed runtime and needs a native allocator profiler (e.g., jemalloc stats, valgrind).
9. **Reproduce, fix one cause, re-measure.** Apply a single fix (close the handle, drop the retainer, reduce allocations, bound the collection) and re-run the same workload to confirm the curve flattens or the FD count stabilizes. A fix without a re-measured curve is a hypothesis, not a result.

## Concrete checks

- [ ] Memory is plotted over time under steady load — the trend (rising vs. plateau) is established, not inferred from one reading.
- [ ] Two heap snapshots were diffed and the growing object type + retainer path identified.
- [ ] The retainer/dominator path is traced to the actual GC root (the owner), not just the leaked leaf object.
- [ ] Leak vs. GC pressure is distinguished (live heap growth vs. high allocation churn).
- [ ] Event-listener/callback subscriptions and request-scoped state are confirmed to be cleared, not accumulating.
- [ ] Open file-descriptor / socket count for the PID is tracked and is stable, not climbing.
- [ ] Every connection/file/lock acquire has a guaranteed release on all paths (incl. exceptions).
- [ ] The connection pool's in-use count returns to baseline after load (no slow leak of slots).
- [ ] In containers, the runtime respects the cgroup memory limit (max-heap / container-aware flag set).
- [ ] OOM events (exit 137 / dmesg OOM-killer) are correlated with the memory curve.
- [ ] GC pause time and frequency are measured if latency degrades over time.
- [ ] Module-level caches/collections are bounded (max size + eviction), not free to grow forever.
- [ ] RSS (resident), not VSZ (virtual), is the tracked memory figure.
- [ ] The managed-heap size is compared against process RSS to detect a native/off-heap leak.
- [ ] A before/after measurement confirms the fix flattened growth.

## Commands or Templates

```bash
# --- OS-level: watch RSS and open handles for a PID over time ---
# RSS in MB, sampled
while true; do ps -o rss= -p <PID> | awk '{print strftime("%T"), $1/1024 " MB"}'; sleep 5; done
# Open file descriptors (climbing count = handle/socket leak)
ls -1 /proc/<PID>/fd | wc -l            # Linux
lsof -p <PID> | wc -l                   # macOS/Linux
# Which kinds of FDs are growing (sockets, regular files, pipes)
lsof -p <PID> | awk '{print $5}' | sort | uniq -c | sort -rn
# Confirm a container OOM-kill (exit 137)
dmesg -T | grep -i 'killed process'     # kernel OOM-killer log
```

```bash
# --- Python: tracemalloc top allocators + objgraph growth ---
python -X tracemalloc=25 app.py    # then in code: see snippet below
```

```python
# Python: snapshot diff to find what is growing between two points
import tracemalloc, gc
tracemalloc.start(25)
snap1 = tracemalloc.take_snapshot()
# ... run representative workload ...
gc.collect()
snap2 = tracemalloc.take_snapshot()
for stat in snap2.compare_to(snap1, "lineno")[:10]:
    print(stat)          # shows file:line and net size growth per allocation site
```

```bash
# --- Node.js: heap snapshots + GC trace ---
node --expose-gc --inspect app.js          # take heap snapshots in DevTools, diff two
node --trace-gc app.js 2>&1 | tail -40     # GC frequency/pause (rising = pressure)
# Container-aware memory cap (avoid OOM kill): cap old space below the cgroup limit
node --max-old-space-size=384 app.js       # e.g. for a 512Mi container

# --- JVM: container-aware + heap dump on OOM ---
java -XX:MaxRAMPercentage=75 \
     -XX:+HeapDumpOnOutOfMemoryError -XX:HeapDumpPath=/tmp/heap.hprof \
     -Xlog:gc*:file=/tmp/gc.log -jar app.jar
```

```bash
# --- GC pressure signal: how much wall time is spent collecting? ---
# Rising "GC%" with a flat live heap means pressure (allocation churn), not a leak.
grep -oE 'Pause.*[0-9.]+ms' gc.log | awk -F'[ m]' '{s+=$(NF-1)} END {print "total GC pause ms:", s}'

# --- Container reality check: cgroup memory limit vs. current usage ---
# If the runtime ignores this limit, the kernel OOM-kills the process (exit 137).
cat /sys/fs/cgroup/memory.max 2>/dev/null || cat /sys/fs/cgroup/memory/memory.limit_in_bytes
cat /sys/fs/cgroup/memory.current 2>/dev/null || cat /sys/fs/cgroup/memory/memory.usage_in_bytes
```

## Common issues & anti-patterns

- **One memory reading.** A single high RSS sample says nothing; a leak is defined by the trend over time, not a snapshot.
- **Calling GC pressure a leak (or vice versa).** Hunting retainers when the real problem is allocation churn wastes time — confirm whether live heap actually grows.
- **Ignoring file descriptors.** A process can OOM or hit `EMFILE` from leaked sockets/files while the heap looks fine; always check FD count.
- **Missing release on the error path.** A connection acquired before a line that can throw, with `close()` only on the happy path, leaks one slot per error until the pool is exhausted.
- **Unbounded cache/collection.** A module-level dict/list that only ever grows is a leak by design; bound it (LRU + max size).
- **Runtime unaware of the container limit.** A JVM/Node that sizes its heap to host RAM blows past the cgroup limit and is OOM-killed (exit 137) regardless of code quality.
- **Forcing GC to "fix" it.** Manually triggering GC masks the symptom; if memory returns after a forced GC the objects were collectable — the issue is pressure/timing, not retention.
- **Lingering event-listener / callback registrations.** Subscribing without ever unsubscribing keeps the subscriber (and everything it closes over) alive — a common leak in long-lived processes and SPAs.
- **Thread-local or request-scoped state never cleared.** Data stashed per request that is not reset leaks across the worker's lifetime and grows with traffic.
- **Confusing virtual memory with resident.** A large VSZ is not a leak; track RSS (actually resident pages), or you will chase a number that does not cost RAM.
- **Blaming the managed heap for a native leak.** A C extension, buffer, or off-heap cache can grow RSS while the managed heap stays flat; a heap profiler will show nothing — compare heap against RSS.
- **Memory fragmentation read as a leak.** Some allocators hold freed pages from the OS, so RSS stays high after a spike without a true leak; confirm with allocator stats before hunting retainers.

## Required output

Produce a report containing:
1. **Memory trend** — RSS/heap over time under steady load, classified as leak / plateau / spike, with the chart or samples.
2. **Retention finding** — for a leak, the growing object type and the retainer path to the GC root (file:line where it is held).
3. **GC assessment** — allocation rate and GC pause/frequency if pressure is suspected, with the allocation hot spot.
4. **Handle/connection finding** — FD/socket/pool counts over time and the specific unclosed resource or missing release path.
5. **Container fit** — whether the runtime respects the cgroup limit and any correlated OOM-kill (exit 137) events.
6. **Native vs. managed** — whether the growth is in the managed heap or in native/off-heap memory, with the heap-vs-RSS gap as evidence.
7. **Fix + verification** — the change applied and the re-measured curve showing it flattened.
8. **Next safe action** — the next resource to bound or the safest config (e.g., max-heap) to set.

## Safety

- Heap dumps and `tracemalloc` snapshots can contain secrets and PII held in memory — store them securely, do not attach them to public reports, and delete them after analysis.
- Heap dumps can be large and pause the process; capture them in staging or during a low-traffic window with a teammate aware.
- Do not raise container memory limits to "fix" an OOM without first confirming it is a leak — that only delays the crash and masks the bug.
- `lsof`/`/proc` inspection is read-only and safe; avoid killing or `SIGABRT`-ing a production process for a dump without approval.
- Do not change GC flags or max-heap on production without a rollback plan; misconfiguration can increase pause times or trigger earlier OOMs.
- Bound any new cache/collection you add as a fix; an unbounded "fix" reintroduces the leak.
- Take heap dumps from a single replica during low traffic; dumping every instance at once can stall the fleet.
- Delete heap dumps and snapshots when analysis is complete; they are large and may retain sensitive in-memory data indefinitely if left around.
