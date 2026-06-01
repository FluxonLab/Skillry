---
name: global-installation-audit
description: Use when you need to audit global and project installation paths, backups, packages, and reinstall readiness.
---

# Global Installation Audit

## Purpose

Verify that the Claude Code global installation under `~/.claude/` is structurally complete, internally consistent, and reinstall-ready. Check for missing required files, broken symlinks, frontmatter validity, version mismatches between `claude-system.toml` and installed components, and the presence of current backups.

## When to use

- After a batch install or upgrade of skills, agents, or CLAUDE.md.
- When a skill or agent fails to load and the root cause may be a missing or malformed file.
- Before migrating the installation to a new machine or user account.
- As a periodic health check (monthly or after any bulk edit to `~/.claude/`).
- When `python3 tools/claude-smoke-check.py` reports errors and you need a full audit.

## When not to use

- The issue is isolated to one known file — inspect and fix that file directly.
- The goal is to find path placement errors across the filesystem — use `path-hygiene-repair`.
- The goal is to find duplicate skills — use `skill-deduplication`.
- You are auditing a project-scoped `.claude/` directory, not the global `~/.claude/` — adjust paths accordingly.

## Procedure

### Phase 1: Directory structure check

Verify the canonical global directory tree exists:

```bash
ls -la ~/.claude/
# Expected: skills/ agents/ CLAUDE.md claude-system.toml (optional: tools/ backups/)
```

Required paths:
```
~/.claude/
 skills/ # one directory per installed skill
 agents/ # one entry per installed agent
 CLAUDE.md # Global system instruction file
 claude-system.toml # Version and configuration manifest
```

Flag any missing top-level entry.

### Phase 2: Skill integrity check

```bash
# Count skill directories
ls ~/.claude/skills/ | wc -l

# Check each skill has a SKILL.md
for d in ~/.claude/skills/*/; do
 [ ! -f "$d/SKILL.md" ] && echo "MISSING SKILL.md: $d"
done

# Check frontmatter is present in each SKILL.md
for f in ~/.claude/skills/*/SKILL.md; do
 head -1 "$f" | grep -q "^---" || echo "BAD FRONTMATTER: $f"
done

# Check required frontmatter fields
for f in ~/.claude/skills/*/SKILL.md; do
 grep -q "^name:" "$f" || echo "MISSING name: $f"
 grep -q "^description:" "$f" || echo "MISSING description: $f"
done
```

### Phase 3: Agent integrity check

```bash
# Count agent directories
ls ~/.claude/agents/ | wc -l

# Check each agent has an AGENT.md
for d in ~/.claude/agents/*/; do
 [ ! -f "$d/AGENT.md" ] && echo "MISSING AGENT.md: $d"
done

# Check frontmatter fields
for f in ~/.claude/agents/*/AGENT.md; do
 grep -q "^name:" "$f" || echo "MISSING name: $f"
 grep -q "^description:" "$f" || echo "MISSING description: $f"
done
```

### Phase 4: CLAUDE.md check

```bash
wc -l ~/.claude/CLAUDE.md
head -5 ~/.claude/CLAUDE.md # Should show system instruction header, not frontmatter
# Check for known required sections
grep -c "## " ~/.claude/CLAUDE.md # Count H2 sections — expect ≥3
```

### Phase 5: claude-system.toml check

```bash
cat ~/.claude/claude-system.toml
# Verify: version field present, skills_path and agents_path match actual paths
python3 -c "
import tomllib, pathlib
with open(pathlib.Path.home() / '.claude/claude-system.toml', 'rb') as f:
 c = tomllib.load(f)
print('version:', c.get('version', 'MISSING'))
print('skills_path:', c.get('skills_path', 'MISSING'))
print('agents_path:', c.get('agents_path', 'MISSING'))
"
```

### Phase 6: Smoke check (if tools/ directory exists)

```bash
[ -f ~/.claude/tools/claude-smoke-check.py ] && \
 python3 ~/.claude/tools/claude-smoke-check.py || \
 echo "Smoke check script not found — skipping"
```

### Phase 7: Backup check

```bash
# Check for backups directory and recency
ls -lht ~/.claude/backups/ 2>/dev/null | head -5
# Flag if newest backup is older than 7 days
find ~/.claude/backups/ -maxdepth 1 -newer ~/.claude/CLAUDE.md 2>/dev/null | wc -l
```

### Phase 8: Broken symlinks

```bash
find ~/.claude/ -type l ! -exec test -e {} \; -print
```

## Checklist

- [ ] `~/.claude/skills/` exists and contains ≥1 directory
- [ ] `~/.claude/agents/` exists and contains ≥1 directory
- [ ] `~/.claude/CLAUDE.md` exists and is non-empty
- [ ] `~/.claude/claude-system.toml` exists and is parseable
- [ ] Every `skills/*/SKILL.md` has `---` frontmatter, `name:`, and `description:`
- [ ] Every `agents/*/AGENT.md` has `---` frontmatter, `name:`, and `description:`
- [ ] No broken symlinks under `~/.claude/`
- [ ] Backup exists and is ≤7 days old (or backup absence is accepted risk)
- [ ] Smoke check passes (if available)
- [ ] `claude-system.toml` paths match actual directory locations

## Common issues & anti-patterns

- **Skills directory exists but is empty**: A botched install copied the parent directory without contents.
- **SKILL.md with no frontmatter**: File was created manually without the `---` delimiter — breaks frontmatter parsers.
- **claude-system.toml paths pointing to wrong username**: `/Users//` in config when actual home is `$HOME/` — use `path-hygiene-repair` to fix.
- **No backups directory**: Any bulk edit to skills/agents is unrecoverable. Create a backup before every batch operation.
- **Smoke check not in tools/**: Was never installed or was accidentally deleted. Reinstall from source.
- **CLAUDE.md begins with YAML frontmatter**: CLAUDE.md is a system instruction file, not a SKILL.md — it should not have `---` frontmatter. If it does, the file may have been accidentally overwritten.

## Required output

```
## Global Installation Audit Report

Audit date: [date]
Home directory: [~/.claude resolved path]

### Phase 1: Directory structure
- skills/: [PRESENT / MISSING]
- agents/: [PRESENT / MISSING]
- CLAUDE.md: [PRESENT / MISSING]
- claude-system.toml: [PRESENT / MISSING / PARSE ERROR]

### Phase 2: Skill integrity
- Skills found: [N]
- Missing SKILL.md: [list or "none"]
- Bad frontmatter: [list or "none"]
- Missing name/description: [list or "none"]

### Phase 3: Agent integrity
- Agents found: [N]
- Missing AGENT.md: [list or "none"]
- Bad frontmatter: [list or "none"]

### Phase 4: CLAUDE.md
- Line count: [N]
- H2 sections: [N]
- Issues: [list or "none"]

### Phase 5: claude-system.toml
- version: [value]
- skills_path: [value] — [MATCHES / MISMATCH]
- agents_path: [value] — [MATCHES / MISMATCH]

### Phase 6: Smoke check
- [PASS / FAIL / SKIPPED] — [details]

### Phase 7: Backups
- Newest backup: [date or "none found"]
- Status: [CURRENT / STALE / ABSENT]

### Phase 8: Broken symlinks
- [list or "none"]

### Summary
[HEALTHY / DEGRADED / CRITICAL] — [top 3 issues to fix, or "no issues"]

### Recommended remediation commands
1. [command]
```

## Safety

- Run only read-only commands during the audit. Do not modify, move, or delete any file.
- If the audit finds a critical issue (missing CLAUDE.md, empty skills/), report it but do not attempt auto-repair — use `path-hygiene-repair` for targeted repairs.
- Do not print the contents of CLAUDE.md or claude-system.toml if they may contain credentials or API keys.
