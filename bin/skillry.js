#!/usr/bin/env node
'use strict';
/*
 * Skillry CLI — a thin, dependency-free wrapper around the repo's Python tools.
 * Works when installed globally (`npm i -g skillry`), via `npx github:FluxonLab/Skillry`,
 * or from a clone (`node bin/skillry.js ...`). All real work is done by tools/*.py.
 */
const { spawnSync } = require('child_process');
const path = require('path');

const REPO = path.resolve(__dirname, '..');
const argv = process.argv.slice(2);
const cmd = argv[0];
const rest = argv.slice(1);

const HELP = `Skillry — installable, permission-bounded, multi-platform agent skills & subagents

Usage:
  skillry install [--apply] [--targets <p..>] [--community]   Install into AI platforms
  skillry validate                                            Lint structure, frontmatter, permissions
  skillry sync <discover|import|normalize> [args]             Import/normalize an upstream skill repo
  skillry lock [--apply]                                      Rebuild SHA-256 lockfiles
  skillry help                                                Show this help

Platforms (for --targets): claude  codex  copilot  antigravity
Dry-run is the default; nothing is written without --apply.

Examples:
  npx github:FluxonLab/Skillry install                          # preview, all platforms
  npx github:FluxonLab/Skillry install --apply --targets claude
  skillry install --apply --targets claude codex --community

Claude Code users can also use the native plugin marketplace:
  /plugin marketplace add FluxonLab/Skillry
  /plugin install core-operations@skillry`;

function runPython(script, args) {
  for (const py of ['python3', 'python']) {
    const r = spawnSync(py, [path.join(REPO, 'tools', script), ...args], { stdio: 'inherit' });
    if (r.error && r.error.code === 'ENOENT') continue; // try next interpreter
    process.exit(r.status == null ? 1 : r.status);
  }
  console.error('Skillry requires Python 3. Install it from https://python.org and retry.');
  process.exit(1);
}

switch (cmd) {
  case 'install':  runPython('install.py', rest); break;
  case 'validate': runPython('validate.py', rest); break;
  case 'sync':     runPython('skill-sync.py', rest); break;
  case 'lock':     runPython('build-lock.py', rest); break;
  case undefined:
  case 'help':
  case '-h':
  case '--help':
    console.log(HELP);
    break;
  default:
    console.error(`Unknown command: ${cmd}\n`);
    console.log(HELP);
    process.exit(1);
}
