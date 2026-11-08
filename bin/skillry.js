#!/usr/bin/env node
'use strict';
/*
 * Skillry CLI — a thin, dependency-free wrapper around the repo's Python tools.
 * Works when installed globally (`npm i -g skillry`), via `npx github:FluxonLab/Skillry`,
 * or from a clone (`node bin/skillry.js ...`). All real work is done by tools/*.py.
 */
const { spawnSync } = require('child_process');
const path = require('path');
const fs = require('fs');
const https = require('https');

const REPO = path.resolve(__dirname, '..');
const argv = process.argv.slice(2);
const cmd = argv[0];
const rest = argv.slice(1);

function localVersion() {
  try { return require(path.join(REPO, 'package.json')).version || 'unknown'; }
  catch { return 'unknown'; }
}

const HELP = `Skillry v${localVersion()} — installable, permission-bounded, multi-platform agent skills & subagents

Usage:
  skillry install [--apply] [--targets <p..>] [--community]     Install skills and agents
          [--departments <d..>] [--skills <s..>] [--no-agents] [--all] [--allow-removal]
  skillry list [--json]                                       Departments, skills, agents and what is installed
  skillry doctor [--json]                                     Check installed files against their manifests
  skillry uninstall --targets <p..> [--apply]                 Remove what Skillry installed (keeps your edits)
  skillry jev <status|assess|hook|synthetic|install> [args]      Optional bounded Jev advice
  skillry storage [--config PATH] <command> [args]            Optional local storage lifecycle engine
  skillry validate                                            Lint structure, frontmatter, permissions
  skillry sync <discover|import|normalize> [args]             Import/normalize an upstream skill repo
  skillry lock [--apply]                                      Rebuild SHA-256 lockfiles
  skillry version                                             Print the installed version
  skillry update                                              Check for a newer release and show how to update
  skillry help                                                Show this help

Platforms (for --targets): claude  codex  cursor  copilot  antigravity  opencode
Install choices (departments, skills, community, agents) are remembered for the next update;
an update that would remove components you installed needs --allow-removal.
Skill installation previews by default; --apply is required to install.
Storage actions use explicit commands and the owner's configured lifecycle scope.

Examples:
  npx github:FluxonLab/Skillry install                          # preview, all platforms
  npx github:FluxonLab/Skillry install --apply --targets claude
  skillry install --apply --targets claude codex

Claude Code users can also use the native plugin marketplace:
  /plugin marketplace add FluxonLab/Skillry
  /plugin install skillry-core-operations@skillry`;

function runPython(script, args) {
  // On Windows the Python launcher comes first: `python3` there is often the Microsoft Store
  // alias, which answers 9009 when no Store Python is installed behind it.
  const candidates = process.platform === 'win32'
    ? [['py', ['-3']], ['python', []], ['python3', []]]
    : [['python3', []], ['python', []]];
  for (const [py, pre] of candidates) {
    const r = spawnSync(py, [...pre, path.join(REPO, 'tools', script), ...args], { stdio: 'inherit' });
    if (r.error && r.error.code === 'ENOENT') continue; // try next interpreter
    if (process.platform === 'win32' && r.status === 9009) continue; // Store alias without Python
    process.exit(r.status == null ? 1 : r.status);
  }
  console.error('Skillry requires Python 3. Install it from https://python.org and retry.');
  process.exit(1);
}

function cmp(a, b) { // semver-ish compare; returns 1 if a>b, -1 if a<b, 0 equal
  const pa = String(a).replace(/^v/, '').split('.').map(Number);
  const pb = String(b).replace(/^v/, '').split('.').map(Number);
  for (let i = 0; i < 3; i++) { if ((pa[i] || 0) > (pb[i] || 0)) return 1; if ((pa[i] || 0) < (pb[i] || 0)) return -1; }
  return 0;
}

function update() {
  const current = localVersion();
  const fromClone = fs.existsSync(path.join(REPO, '.git'));
  const opts = { headers: { 'User-Agent': 'skillry-cli', 'Accept': 'application/vnd.github+json' } };
  https.get('https://api.github.com/repos/FluxonLab/Skillry/releases/latest', opts, (res) => {
    let body = '';
    res.on('data', (c) => (body += c));
    res.on('end', () => {
      let latest = null;
      try { latest = JSON.parse(body).tag_name; } catch { /* ignore */ }
      console.log(`Skillry: installed v${current}` + (latest ? `, latest ${latest}` : ''));
      if (latest && cmp(latest, current) > 0) console.log(`\nA newer version (${latest}) is available. To update:`);
      else if (latest) console.log(`\nYou are up to date. (If you still want to refresh files:)`);
      else console.log(`\nCould not reach GitHub to check. To update anyway:`);
      console.log(`  Claude Code:   /plugin marketplace update skillry   (then re-run /plugin install <plugin>@skillry)`);
      console.log(`  npm (global):  npm install -g skillry@latest`);
      console.log(`  npx:           npx github:FluxonLab/Skillry${latest ? '#' + latest : ''} install --apply --targets <platforms>`);
      console.log(fromClone
        ? `  this clone:    git pull && python3 tools/install.py --apply --targets <platforms>`
        : `  from a clone:  git clone https://github.com/FluxonLab/Skillry && cd Skillry && python3 tools/install.py --apply --targets <platforms>`);
      console.log(`\nNote: installed skill files don't self-update — re-run the installer (or the command above) to refresh them.`);
    });
  }).on('error', () => {
    console.log(`Skillry: installed v${current} (offline — could not check latest).`);
    console.log(`Update with: npm install -g skillry@latest  ·  or re-run the installer from a fresh clone.`);
  });
}

switch (cmd) {
  case 'install':  runPython('install.py', rest); break;
  case 'list':     runPython('install.py', ['--list', ...rest]); break;
  case 'doctor':   runPython('install.py', ['--doctor', ...rest]); break;
  case 'uninstall': runPython('install.py', ['--uninstall', ...rest]); break;
  case 'validate': runPython('validate.py', rest); break;
  case 'sync':     runPython('skill-sync.py', rest); break;
  case 'lock':     runPython('build-lock.py', rest); break;
  case 'jev':      runPython('jev.py', rest); break;
  case 'storage':  runPython('storage.py', rest); break;
  case 'version':
  case '--version':
  case '-v':
    console.log(`skillry v${localVersion()}`);
    break;
  case 'update':   update(); break;
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
