---
name: path-hygiene-repair
description: Use when you need to detect misplaced AI agent system files, repair canonical placement, and leave thin pointers.
---

# Path Hygiene Repair

## Purpose

Detect files belonging to the Claude AI agent system that are in the wrong location, fix their placement to the canonical path, and optionally leave a thin pointer (symlink or redirect note) at the old location. Specifically handles username path mismatches (e.g., `/Users/` vs `$HOME`), SSD vs. local drive placement confusion, project-scoped vs. global-scoped placement errors, and accidental nesting.

## When to use

- A skill, agent, or config file is not loading and the path in a config points to a non-existent location.
- `~/.claude/claude-system.toml` contains paths referencing an old username or home directory.
- Files were installed on an external SSD (`/Volumes/...`) but the system expects them under `$HOME/`.
- A `SKILL.md` was placed at `~/.claude/SKILL.md` (root level) instead of `~/.claude/skills/skill-name/SKILL.md`.
- A global skill was placed inside a project directory (`~/project/.claude/skills/`) and should be at `~/.claude/skills/`.
- After migrating a user account, paths contain the old username throughout config files.

## When not to use

- The file placement is correct and the issue is malformed content — use `global-installation-audit` to diagnose.
- The path issue is inside source code or a project repo (not the `~/.claude/` installation) — fix it directly in the project.
- The goal is to move large directories across volumes — this skill handles `~/.claude/` files, not bulk data migrations.
- The path error is in a third-party tool's config that is outside the Claude system.

## Procedure

### Phase 1: Identify the canonical path map

The canonical installation for user `-m1` on macOS:

```
Home: $HOME/
Claude: $HOME/.claude/
Skills: $HOME/.claude/skills/<skill-name>/SKILL.md
Agents: $HOME/.claude/agents/<agent-name>/AGENT.md
Config: $HOME/.claude/claude-system.toml
System: $HOME/.claude/CLAUDE.md
Tools: $HOME/.claude/tools/
Backups: $HOME/.claude/backups/
```

Non-canonical paths to detect:
- `/Users//` (missing `-m1` suffix)
- `/Volumes/*$HOME/` (SSD path, not local)
- `~/Documents/.claude/` or any non-home location
- `.claude/` at project root intended as global

### Phase 2: Detect misplaced files

```bash
# 1. Find any .claude directories not under ~/.claude
find $HOME -name ".claude" -type d \
 ! -path "$HOME/.claude" \
 ! -path "*/node_modules/*" 2>/dev/null

# 2. Find SKILL.md files not under ~/.claude/skills/
find $HOME -name "SKILL.md" \
 ! -path "$HOME/.claude/skills/*" 2>/dev/null

# 3. Find AGENT.md files not under ~/.claude/agents/
find $HOME -name "AGENT.md" \
 ! -path "$HOME/.claude/agents/*" 2>/dev/null

# 4. Check for SSD-based files
find /Volumes -name "SKILL.md" -o -name "AGENT.md" -o -name "CLAUDE.md" \
 2>/dev/null | head -20

# 5. Check for old username in config files
grep -rn "[^-]" ~/.claude/ 2>/dev/null | grep -v ".bak"
grep -rn "/Volumes/" ~/.claude/ 2>/dev/null
```

### Phase 3: Verify canonical destination is writable

```bash
ls -la $HOME/.claude/
touch $HOME/.claude/.write-test && \
 rm $HOME/.claude/.write-test && \
 echo "Writable" || echo "NOT WRITABLE"
```

### Phase 4: Backup before repair

```bash
BACKUP_TS=$(date +%Y%m%d-%H%M%S)
BACKUP_DIR="$HOME/.claude/backups/pre-repair-$BACKUP_TS"
mkdir -p "$BACKUP_DIR"
# Only back up files being moved, not the entire ~/.claude
cp -r [affected-file-or-dir] "$BACKUP_DIR/"
echo "Backed up to $BACKUP_DIR"
```

### Phase 5: Execute repairs (one at a time, with confirmation)

**Pattern A — Move misplaced skill to canonical location:**
```bash
# Create canonical slot
mkdir -p ~/.claude/skills/<skill-name>
# Move
mv /path/to/wrong/location/SKILL.md ~/.claude/skills/<skill-name>/SKILL.md
# Verify
ls -la ~/.claude/skills/<skill-name>/SKILL.md
```

**Pattern B — Fix username in config file:**
```bash
# Preview what will change
grep -n "[^-]" ~/.claude/claude-system.toml
# Apply with sed (macOS syntax)
sed -i '' 's|/Users//|$HOME/|g' ~/.claude/claude-system.toml
# Verify
grep "Users/" ~/.claude/claude-system.toml
```

**Pattern C — Fix SSD path to local path:**
```bash
# Identify SSD path prefix
VOLUME_PATH=$(ls /Volumes/ | grep -i macintosh 2>/dev/null || echo "IDENTIFY MANUALLY")
# Replace in config
sed -i '' "s|/Volumes/$VOLUME_PATH$HOME|$HOME|g" \
 ~/.claude/claude-system.toml
```

**Pattern D — Leave a thin pointer at old location:**
```bash
# Symlink (preferred — transparent to file reads)
ln -s $HOME/.claude/skills/<skill-name>/SKILL.md \
 /path/to/old/location/SKILL.md
# OR: Leave a redirect note (if symlink is not appropriate)
echo "This file has moved to: ~/.claude/skills/<skill-name>/SKILL.md" > \
 /path/to/old/location/SKILL.md.moved
```

### Phase 6: Post-repair verification

```bash
# Re-run the audit commands from global-installation-audit Phase 1–3
ls ~/.claude/skills/ | wc -l
ls ~/.claude/agents/ | wc -l
cat ~/.claude/claude-system.toml
# Confirm no remaining stale paths
grep -rn "[^-]" ~/.claude/ 2>/dev/null | grep -v ".bak" | grep -v backups/
grep -rn "/Volumes/" ~/.claude/ 2>/dev/null | grep -v backups/
```

## Checklist

- [ ] Canonical path map reviewed for current username (`-m1`)
- [ ] Misplaced files found via `find` (not assumed)
- [ ] SSD / volume paths checked
- [ ] Old username (``) in config files checked
- [ ] Canonical destination verified as writable
- [ ] Backup created before any file is moved or overwritten
- [ ] Each repair executed one at a time with verification
- [ ] Thin pointer (symlink or redirect note) left at old location when required
- [ ] Post-repair verification confirms canonical paths resolve correctly
- [ ] No stale paths remain in `claude-system.toml` or other config files

## Common issues & anti-patterns

- **Moving without backing up**: A misidentified "misplaced" file that was actually correct in context is unrecoverable without a backup.
- **Fixing the symlink instead of the source**: If a symlink at the canonical path points to the SSD, fix the symlink target — do not move the file from the SSD and break the symlink.
- **Username confusion between `` and `-m1`**: These are different home directories. `/Users/` may not exist or may belong to a different account. Never assume they are equivalent.
- **sed on the wrong file**: Running sed to replace paths without checking which files contain stale paths first.
- **No pointer left at old location**: Scripts or agents with hardcoded old paths will silently fail. Always leave a pointer during a transition.
- **Project `.claude/` confused for global `~/.claude/`**: A project-scoped `.claude/skills/` is intentional and correct for that project. Do not move project skills to global unless the user confirms intent.
- **Repair applied to all files at once**: Run repairs one file at a time. A batch `sed -i` across all of `~/.claude/` can corrupt files that were correct.

## Required output

```
## Path Hygiene Repair Report

Date: [date]
User home: $HOME/
Canonical Claude root: $HOME/.claude/

### Detection findings

#### Misplaced SKILL.md files
| Found path | Canonical path | Action |
|---|---|---|
| [path] | [canonical] | [move / already correct] |

#### Misplaced AGENT.md files
[same format]

#### Stale username references in config
| File | Line | Stale value | Correct value |
|---|---|---|---|
| [file] | [N] | /Users// | $HOME/ |

#### SSD / volume path references
| File | Line | Value | Action |
|---|---|---|---|

### Backup created
[backup path and contents]

### Repairs applied
1. [Action] [from-path] → [to-path] — [DONE / SKIPPED (reason)]

### Pointers left
| Old path | Points to |
|---|---|
| [old] | [canonical] |

### Post-repair verification
- Skills found at canonical path: [N]
- Agents found at canonical path: [N]
- Stale paths remaining: [none / list]

### Status
[CLEAN / ISSUES REMAIN] — [summary]
```

## Safety

- Never delete a file during path repair — always move (preserve the original bytes).
- Do not repair paths in project repositories; confine all operations to `~/.claude/` and its subdirectories.
- If a file exists at both the old and new canonical paths, halt and report the conflict — do not overwrite silently.
- Confirm with the user before applying any `sed -i` to config files that affect all agents and skills.
