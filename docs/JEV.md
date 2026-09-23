# Optional Jev advice

Skillry's optional Jev helper gives the current agent bounded advice. It does not
execute recommendations, install tools, select another account, change the model,
or authorize completion. The existing portable installer remains skills/agents only.

## Daily use

After explicit setup, use the installed `jev` skill (`$jev` in Codex, `/jev` in
Claude Code, Cursor or Antigravity), or invoke `skillry-jev advise --client <client>` with JSON on stdin from the authorized project directory.
`skillry-jev status` shows local readiness without reading a credential or calling
the provider. A helper process runs on the machine invoking it and stops when that
machine is off; the TypeSafe API is a separate cloud dependency.

Codex and Claude Code have an optional `UserPromptSubmit` hook for skill advice.
It is silent unless the owner enabled this project's data class and allowed skill
IDs. Codex requires its native `/hooks` trust flow after a hook definition changes.
Claude Desktop **local Code** shares Code configuration; Chat/Cowork are separate.
Antigravity uses the explicit skill: its `PreInvocation` event has no current user
task, and this helper never reads the transcript to reconstruct one. In headless
CLI mode, an exit code of zero can still include `denied_actions`: inspect that
field and actual helper receipts. Use interactive approval or an owner-approved,
command-specific permission rule; the installer does not change permission rules.

Cursor uses native `advise --client cursor` for all ten modes, not a Codex broker.
Install its public skills/agents with the portable Cursor target first, then add
`cursor` to the Jev installer client list. Its inventory validates native
`~/.cursor/skills` and `~/.cursor/agents` bytes; it does not borrow Codex or Claude
inventory records. Cursor role IDs remain hyphenated. No Cursor raw-prompt hook is
installed or accepted. Automatic relevant use comes from the installed skill and
applicable owner instructions, not a guarantee that every turn invokes it.

On macOS, run clients in the normal logged-in desktop session when their secret
comes from the login Keychain. An SSH process can receive `User interaction is
not allowed` even while the desktop session can read the same item; a successful
desktop call does not establish unattended SSH access. Keep the ordinary fallback
instead of adding a credential relay or daemon.

For Antigravity CLI with terminal sandboxing enabled, the Keychain-backed helper
may need a host command. An owner-approved rule can be limited to
`unsandboxed(/absolute/path/skillry-jev advise --client antigravity-cli)` alongside
the corresponding `command(...)` rule. The actual terminal call then uses
`BypassSandbox: true`. This is a permission for that helper command, not a global
sandbox change. See the [CLI permission contract](https://antigravity.google/docs/permissions?tab=cli).

| Mode | Narrow question | Owner and fallback |
|---|---|---|
| skill | Which verified installed metadata fits? | Current agent reads a selected skill; explicit selection stays local |
| agent | Which allowed existing role fits this bounded job? | Current session and one writer remain; Codex IDs map to invocation names |
| tool | Which currently allowed tool candidate fits? | Caller supplies actual session availability; no enabling or OAuth |
| reference | Is each supplied passage relevant, duplicated or contradictory? | Keep source identities and conflicts; no automatic deletion |
| workflow | Is research, implementation, review or clarification needed? | Simple checks and actual workflow control stay in code/host |
| error | What category best explains the supplied failure? | No automatic retry; host must check actual outcome and idempotency |
| evidence | Does supplied evidence support the exact claim? | Real tool/test records remain authoritative; mock/config is not live proof |
| library | Are descriptions distinct, overlapping or potential duplicates? | Human decides merge/delete; licenses/provenance remain |
| effort | Which host-supported, already allowed effort option fits? | Advice only; never switches model, subscription or account |
| media | What work does this text brief/metadata describe? | No image/video/audio observation or generation is claimed |

No MCP schemas or existing skill indexes are removed. An added recommendation is
not a reduction in the model's complete context. Role, tool and effort candidates
must come from the calling host's current allowed set, not a guessed config list.

## Setup and data policy

This opt-in runtime currently targets macOS/Linux (local file locks); the existing
portable skill installer keeps its own platform contract. The core uses Python's
standard library and preserves the existing Node wrapper.
The provider worker requires Python 3.10+ and the optional pinned official
`typesafe-sdk==0.7.0`. The supplied hash lock is resolved for Python 3.14. Install
the provider dependencies in a dedicated environment, using wheels and hashes:

```sh
python3.14 -m venv ~/.local/share/skillry/jev/venv
~/.local/share/skillry/jev/venv/bin/python -m pip install --only-binary=:all: --require-hashes -r tools/jev/requirements.txt
python3 tools/jev.py install --clients codex claude
python3 tools/jev.py install --clients codex claude --apply
```

For Cursor, preview and apply the platform components and explicit adapter:

```sh
python3 tools/install.py --targets cursor --community
python3 tools/install.py --targets cursor --community --apply
python3 tools/jev.py install --clients codex claude cursor
python3 tools/jev.py install --clients codex claude cursor --apply
```

The Jev `--clients` list describes the complete desired client set for the shared
runtime, so retain existing `antigravity` and/or `antigravity-cli` targets when
updating an installation that already uses them. Refresh Jev after platform/profile
updates so its inventory reflects the current installed hashes. The platform
installer refuses unmanaged collisions; reconcile their existing owner before
retrying instead of overwriting those files.

The installer previews by default. It creates no credential, daemon, scheduler,
tunnel, MCP server or project instruction file. Add an Antigravity target only if
that form is already installed. App and CLI skill roots are distinct targets; the
installed client's discovery result is required before claiming compatibility.

The public catalog derives from Skillry's checksum-verified source registry. A
private machine overlay records actual installed bytes separately. Missing,
modified and untrusted/unmanaged candidates are not silently accepted. Managed
private-profile skill metadata remains local. The two existing managed librarian
and router entrypoints receive a narrow update only when their prior hashes match.

The default is **disabled**, with no project approved for external transfer.
The key comes from `TYPESAFE_API_KEY` in the invoking environment or the configured
macOS Keychain service/account. Never paste its value into a request or config.
The installer defaults to Keychain service `skillry.typesafe` and the local user
account; it neither creates nor transfers a key. Separate devices use local keys.

After obtaining API access, enable curated public/synthetic advice across workspaces:

```sh
skillry-jev configure --enable --provider-billing --public-advice --apply
```

For an explicit project override or native hook setup instead:

```sh
skillry-jev configure --enable --project /absolute/public-project --data-class public --modes skill workflow evidence
skillry-jev configure --enable --project /absolute/public-project --data-class public --modes skill workflow evidence --apply
```

Native hook use additionally requires `--hook-skills` followed by exact installed
IDs. This is a project data-transfer decision: hook task text will be sent to
TypeSafe for that approved project. Do not enable it for private repositories by
assuming a redactor makes arbitrary source or transcripts safe. The `private`
data class is never sent; credentials, local user paths and email-like strings
are rejected across the entire outgoing payload. This check supplements explicit
data minimization; it is not a proof that arbitrary data is non-sensitive.

`advise` derives the workspace, UID and owner policy scope locally. It uses the
Codex session environment when present; otherwise it creates a fresh helper-local
scope, with no cross-call cache sharing. A host may supply its supported session
and request IDs without reading a transcript. Supply `mode`, short `task`,
`data_class`, and `allowed_ids`. The lower-level `assess` command additionally
requires `client`, `session_id`, `request_id`, `workspace`, `identity`, `tenant`,
and `permission_version`. Tool/effort add candidate
IDs/descriptions; reference/evidence/library add up to 12 selected records with
`id`, `text`, and optional `source`. The installed skill describes the contract.
Use inventory `invocation_id` (falling back to `id`) and exact host IDs, never model-generated paths/commands. Deliberately repeated
requests get a new ID; duplicate delivery reuses its ID.

## Limits and failure behavior

The model is pinned to `jev-1.13.0`; SDK retries are disabled. One provider attempt
runs in a subprocess with its own HTTP timeout and a separate total wall-clock
deadline. A timed-out attempt is not automatically retried. The request is bounded
to 24,000 UTF-8 bytes; skill/role choices are shortlisted to 20 and recommendations capped at
five. Probability shape, ranges, coverage, model, usage and candidate membership
are validated after SDK parsing. `none` and weak-match abstention are explicit.
The selected candidate must pass **its own** absolute-fit question.

The local filter folds Turkish dotted/dotless letters, removes function words and
weights exact or fuzzy matches by document frequency. It is a candidate filter,
not semantic proof. Candidate-fit questions ask about relevance and honor the
candidate's stated exclusions/prerequisites; they never grant permission to act.
Media classification follows the requested deliverable: writing a video prompt
is text work, not video generation.

When developing this integration, use the official
[TypeSafe agent skill](https://docs.typesafe.ai/agent-skill) and current docs.
Install it with one supported method per client; keep its upstream license and
avoid duplicate copies. This reference skill is separate from the local `jev`
helper and does not enable provider calls or alter project data policy.

The default fit/confidence floors are conservative initial settings, **not a
calibrated accuracy guarantee**. They require a separate held-out live evaluation
for the actual task/language distribution before a quality claim is made.

Cache and dedup include task, request, session, workspace, identity, tenant,
permissions, model, catalog, installed inventory and config versions. Files are
rehashed before selection. State is local, lock-protected, permission 0600; cached
results contain IDs/flags, not raw prompts. Telemetry contains metadata only.

Provider billing/quota controls spending by default (`monthly_budget_eur: null`).
There are no monetary reservations or pricing-expiry shutdowns in this mode.
The owner can keep auto top-up disabled in the provider console; the helper does
not change billing settings. A provider error or exhausted quota retains normal
agent operation without Jev.

To enable curated public/synthetic advice across workspaces, without per-project
setup or a second spending limit:

```sh
skillry-jev configure --enable --provider-billing --public-advice --apply
```

This setting applies to `advise`; it does not enable automatic transfer of raw
native prompt events. Existing explicit project rules take precedence. Private
source and transcripts stay out of requests. The installed Jev skill explains
how to send a short task summary and selected records.

An optional `--monthly-budget-eur` installation allocation remains available
for users who explicitly want a separate local cap. Only that mode uses
conservative reservations and price-age checks; reservations are not invoices.
Existing installations retain their settings until `configure --provider-billing`.

`disabled`, missing key, data-policy denial, budget exhaustion, timeout, rate limit,
invalid response or service failure keeps the current agent's normal workflow.
These are `unavailable`/`invalid`, not false claims that no skill fits.

## Disable and rollback

```sh
skillry-jev configure --disable --apply
python3 tools/jev.py install --rollback
python3 tools/jev.py install --rollback --apply
```

Disabling immediately stops external evaluation. Rollback restores exact preimages
or removes only this installation's unchanged files. If a user changes a shared
config after installation, rollback refuses that file and reports the conflict;
it never overwrites the edit. Each upgrade can roll back to its preceding receipt.
No-op installs retain rollback ownership. Provider environment files are retained
as an inert cache, not deleted by rollback.

## Verification and sources

`python3 -m unittest discover -s tests -p 'test_jev*.py'` exercises the offline
contracts with explicitly mocked provider answers. `skillry-jev synthetic` runs a
real local process with built-in synthetic data; API and client delivery are still
separate observations. Native dispatch requires a real client turn and a matching
local process receipt. A fixture piped to the hook only proves its JSON contract.

`python3 -m unittest discover -s tests -p 'test_cursor_install.py'` exercises Cursor
role conversion and isolated preview/apply/no-op/local-edit preservation. Jev's
offline suite covers all ten Cursor modes, private-metadata exclusion, native
role IDs and installed hash drift. Those mocked results are not provider or host
dispatch proof. A real Cursor turn must run the native helper and produce a
matching `client: cursor` process receipt for a live delivery claim.

Primary contracts rechecked 2026-09-19:
[TypeSafe models](https://docs.typesafe.ai/models),
[official Python SDK](https://github.com/typesafe-ai/typesafe-sdk-python),
[skill-suggestion cookbook](https://docs.typesafe.ai/cookbooks/skill_suggestion),
[Jev limitations](https://docs.typesafe.ai/model-jaggedness/jev-1.13),
[Codex hooks](https://developers.openai.com/codex/hooks),
[Claude hooks](https://code.claude.com/docs/en/hooks),
[Claude Desktop](https://code.claude.com/docs/en/desktop),
[Antigravity hooks](https://antigravity.google/docs/hooks/),
[Antigravity skills](https://antigravity.google/docs/skills/),
[Antigravity headless permission behavior](https://antigravity.google/docs/cli/headless/).

Cursor contracts rechecked 2026-09-23:
[native skill discovery](https://cursor.com/docs/skills),
[native subagents and read-only fields](https://cursor.com/docs/subagents),
[CLI structured output](https://cursor.com/docs/cli/reference/output-format).

SDK dependency licenses remain in the installed distributions. Cookbook patterns
inspired the question decomposition; their code is not copied. Internal evaluation
results stay private; review the provider's [MCA](https://typesafe.ai/legal/mca)
before publishing comparative performance claims. Training exclusion is not zero
retention; [provider legal information](https://docs.typesafe.ai/legal) distinguishes
enterprise ZDR from standard access.
