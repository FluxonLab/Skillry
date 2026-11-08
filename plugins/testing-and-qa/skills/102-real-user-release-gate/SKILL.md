---
name: real-user-release-gate
description: "Use this skill before a release and right after deploy to test the product end to end as a real customer on real providers: a full baseline once per product, then only touched journeys on a local, staging, or preview candidate; after deploy, read-only checks, with production-only live steps done by a human or approved step by step."
---

# Real-User Release Gate

## Purpose

Test the integrated product end to end the way a real customer meets it, on real upstream providers, without seeded authentication state, mocked responses, or skipped onboarding. Run the whole product once as a baseline; on every later release run only the journeys whose areas the release touches. Run them where an agent may act on its own: a local development host, or a staging or preview host the team designated. After deploy, check production read-only (error tracker, touched pages, and delivered mail). Creating accounts, signing in, paying with a 100%-off promotion code, and deleting accounts on live production are a human's steps, or need explicit approval for each step, and happen only when a touched area exists only in production. Keep a per-product test ledger, and emit a YAML evidence packet recording scope, journeys, provider spend, error-tracker status, and account teardown. During the baseline, and whenever a release touches user-facing screens, the same session and test account run `customer-lens-testing`, the customer layer: the agent uses the scoped screens as a real free and paid customer at three levels of expertise and proposes what it would want.

## When to use

- A release candidate is integrated and ready for pre-release sign-off before production deploy or app store upload.
- A production deployment just completed and needs its read-only live check.
- Authentication, onboarding, billing, or live upstream provider integrations changed before a release.
- A product has no baseline in its test ledger yet.

## When not to use

- During unfinished implementation work or after individual file edits before a phase boundary.
- For isolated unit checks or static layout reviews covered by `smoke-test-and-repair` or `web-design-review`.
- Rerunning passing journeys when only a single failed journey was fixed.
- Repeating the baseline, or running journeys whose areas the release did not touch.

## When it runs: once, when missing, or when touched

- **Test ledger:** Keep one ledger per product outside the repository (for example `<evidence-dir>/<project>/test-ledger.json`). It lists each test with its kind (`one-time`, `when-missing`, `on-touch`), last run, release or commit, evidence path, and result. Read it before a run and update it after.
- **Baseline (one-time):** The full `J1`–`J8` run, an exploratory charter, and `customer-lens-testing` over every page and app, free and paid plan, once per product. End-to-end user testing done at launch counts when it is recorded in the ledger. Repeat the baseline only on request or after a rewrite changes most of the product.
- **When missing:** A test with no ledger record runs once.
- **On touch (every later release):** Take the release diff (since the last release tag or deploy) and run only the journeys of the touched areas:

| Touched area | Runs |
|---|---|
| Sign-up, auth, sessions, email or SMS sending | `J1`, `J5` |
| Onboarding, empty states, first-run flows | `J2` |
| A provider integration or core job | `J3` on that provider |
| Payment, plans, credits, entitlements | `J4` |
| Settings, profile, locale strings | `J6` |
| Account deletion, data export, retention | `J8` |
| A user-facing screen or component | `customer-lens-testing` on that screen |
| Large UI changes across flows | a short `J7` charter over the changed flows |

## Where it runs

- **Before release (release candidate):** On a local development host, or on a staging or preview host the team designated, with test accounts, real providers, and minimal payloads. Store apps run the selected journeys on the simulator or emulator build before upload.
- **Test payments:** An agent completes processor test-mode checkouts only on a local development host. On a hosted staging or preview environment, a human completes the test checkout.
- **After deploy (read-only):** Query the error tracker for new errors, load the touched pages or screens, and read any mail the touched area delivered. No account is needed.
- **Live journeys (human steps):** Only when a touched area depends on something that exists only in production, such as live payment webhooks, a live provider account, or mail from the production domain. A human creates the test account, signs in, pays with a 100%-off promotion code, and deletes the account, or explicitly approves each step. The agent prepares the checklist (account address, promotion code, expected results), watches, and verifies the outcome read-only; it runs a live step itself only after the human explicitly approves that step. A release without such an area, such as a dependency update, has no live journey.

## Personas

- **`P1-FreshVisitor` (Cold Unauthenticated -> New Sign-Up):** Starts in a clean browser profile (`--user-data-dir`) or erased simulator (`xcrun simctl erase` or clean Android AVD) using a shipped locale (`EN`, `TR`, `DE`, or target locale) and runs sign-up through account deletion.
- **`P2-PaidBuyer` (Trial / Free -> Paid Checkout -> Paid Feature -> Billing Portal):** Completes checkout, receives a real receipt email, runs a paid core job, opens the billing portal, and cancels or refunds.
- **`P3-ReturningUpgrader` (Existing Persisted Account Across Upgrade):** Signs into a persisted canary account with historical data to confirm the new build and migrations keep existing projects, sessions, credits, settings, and API keys intact.
- **`P4-EdgeAdversarialUser` (Clumsy / Impatient / Restricted User):** Double-clicks submit buttons, enters diacritics (`ğüşiöçİĞÜŞİÖÇ`, `äöüß`) and 35%-expanded strings, paste-floods inputs, denies push/camera/microphone permissions, toggles network offline/online mid-job, and hits back or refresh during streaming or payment redirects.

## Mandatory journeys (J1–J8)

The baseline runs every applicable journey; a later release runs the touched set.

- **`J1` Discovery & Sign-Up:** Load the candidate URL or binary in a clean profile, register via the real auth provider (OAuth, magic link, OTP, or password), receive the real email or SMS, and click the verification link or enter the OTP; on live production a human creates the account or approves each step; pass condition: an authenticated session starts without seeded state.
- **`J2` Onboarding & Empty-State-to-First-Value:** Walk every first-run onboarding screen without database seeding and create the first entity or project; pass condition: empty states clear and onboarding state persists across reload or app restart.
- **`J3` Core Jobs with Real Live Providers:** Run the primary value workflow against live upstream APIs (LLMs, embeddings, media, search, storage, or exports) with minimal real payloads; pass condition: valid non-empty output renders in the UI and request ID, latency, and spend are recorded.
- **`J4` Payments, Entitlements & Invoicing:** Trigger the paywall or upgrade flow, complete checkout in processor test mode (by an agent only on a local development host; on hosted staging or preview, by a human), and open the customer billing portal; on live production, only for a production-only touched area, a human completes checkout with a 100%-off promotion code or explicitly approves the step; pass condition: the webhook updates entitlements within 10 seconds, the receipt email arrives, and the billing portal opens.
- **`J5` Transactional Email & Notification Loop:** Read the delivered email in a subaddressed mailbox the team owns (`qa+<project>-<date>-<sha>@<team-domain>`) via IMAP or mail API instead of trusting an HTTP 200 send response; pass condition: `From`/`Reply-To` headers and SPF/DKIM pass, HTML/text links render, and action links work.
- **`J6` Settings, Locale & Profile Mutation:** Change display name, avatar, shipped locales, notification preferences, and API tokens, then reload; pass condition: all mutations persist after reload.
- **`J7` Exploratory Charter:** Run a 10–15 minute time-boxed Session-Based Test Management (SBTM) tour on changed and adjacent surfaces using `P4-EdgeAdversarialUser` inputs; pass condition: zero uncaught console errors, zero unexpected 4xx/5xx responses, zero new error-tracker issues, and no broken layouts.
- **`J8` Self-Serve Account Deletion & Right-to-Erasure:** Delete the test account from the product UI and confirm re-authentication (on live production a human does it, or the agent after explicit approval); pass condition: the session revokes immediately, retry login fails, database rows delete or tombstone, and idempotent teardown removes any leftover `qa_test` data.

## Procedure

1. **Read the ledger, select scope, and prepare a clean client and test identity.**
   - Read the product's test ledger: the full baseline when it has none, otherwise the touched journeys from the release diff.
   - Reset the browser profile (`--user-data-dir`) or mobile simulator (`xcrun simctl erase` or clean AVD).
   - Create a subaddressed address (`qa+<project>-<date>-<sha>@<team-domain>`) in a mailbox the team owns.
   - Flag the test account (`qa_test: true`) so it is excluded from analytics and mailing lists.
2. **Execute the selected journeys among `J1`–`J3` on real providers on the candidate host.**
   - (`J1`, `J2`) Complete cold sign-up, real inbox or SMS verification, and the onboarding screens without seeding.
   - (`J3`) Execute the touched core workflow against live providers with minimal payloads and log request IDs, latency, and spend.
3. **Verify payments (`J4`, when selected) under processor rules.**
   - Use payment processor test mode or sandbox test clocks on the release candidate: an agent completes test checkouts only on a local development host; on hosted staging or preview, a human completes them.
   - In production, and only for a touched area that exists only there, a human completes checkout with a 100%-off live promotion code at 0.00, or explicitly approves the step, because processors forbid live testing with real card details.
   - A real charge after a payment-code change is a human decision each time, made against the processor's terms.
   - Refund any real-money charge the same day and issue a credit note (check your local invoicing rules for real charges).
4. **Execute the selected journeys among `J5`–`J8` and capture artifacts.**
   - (`J5`–`J7`) Verify inbox messages, mutate profile and locale settings, and run exploratory charters: 1–3 on the baseline, or a short charter over the changed flows.
   - Record Playwright traces (`trace.zip` with DOM snapshots and network HAR) or mobile video (`xcrun simctl io booted recordVideo` or `maestro record`) plus runtime logs (`xcrun simctl spawn booted log collect` or `adb logcat`).
   - (`J8`) Delete the account through the product UI and run the idempotent teardown script; do the same for any disposable test account created for the run. On live production a human does both, or explicitly approves each step.
5. **Check production read-only after deploy, verify the error tracker, record, and sign off.**
   - After deploy, load the touched pages or screens and read any mail the touched area delivered; no account is needed.
   - Query the error-tracking API for the release tag and environment to confirm zero new unhandled exceptions.
   - Update the test ledger with each test's run, release or commit, evidence path, and result.
   - Workers may run journeys and collect artifacts on candidate hosts, while the lead reviewer signs off on visual quality and the gate verdict. Live steps are never handed to unattended workers.

## Concrete checks

- The test ledger was read before the run and updated after it; after the baseline, only touched journeys ran.
- Candidate journeys ran on a local development host or a designated staging or preview host.
- (`J1`, `J2`) `P1-FreshVisitor` starts in a clean browser profile or freshly erased simulator, and sign-up and onboarding finish without seeded database state or injected auth tokens.
- (`J5`) Transactional emails are read from the team's subaddressed inbox with SPF/DKIM, headers, and links verified.
- (`J3`) Live AI and upstream provider calls use minimal payloads with request IDs and spend recorded.
- (`J4`) Candidate payment checks use processor test mode, agent-run only on a local development host and otherwise completed by a human; production checks, only for a production-only touched area, are completed by a human or with explicit per-step approval using a 100%-off live promotion code.
- Any explicitly approved real-money charge has a same-day refund ID and credit note recorded.
- Test accounts are flagged and excluded from analytics and mailing lists; any account created for the run is deleted via the product UI and swept by idempotent teardown.
- After deploy, the touched pages and any delivered mail were checked read-only, and the error-tracking API shows zero new unhandled exceptions for the release tag.

## Exploratory charter template

```markdown
Charter ID: CHARTER-<project>-<YYYYMMDD>-01
Target Surface: <new or changed feature + adjacent billing or auth surface>
Persona: <P1 | P2 | P3 | P4>
Time Box: 10 minutes (or max 40 agent actions)
Mission: Explore <surface> with <real inputs and edge cases> to find unhandled state transitions, console or network failures, broken layouts or translations, or provider timeouts.
Required Oracles: Browser console (0 uncaught errors), Network tab (0 unexpected 4xx/5xx), Error-tracker API (0 new issues for release tag), Visual check of every visited state.
```

## Evidence packet template

```yaml
gate: real-user-release-gate
stage: release-candidate | post-deploy-live
run_scope: baseline | on-touch
verdict: pass | fail
scope:
  project: <project-name>
  commit_hash: <git-commit-sha>
  environment: <release-candidate | production>
  host: local | staging | preview | production
  touched_areas: [<area from the release diff> | all]
  test_account: qa+<project>-<date>-<sha>@<team-domain> | not_applicable
  analytics_and_mailing_excluded: true | not_applicable
  personas_run: [<personas used by the selected journeys>]
journeys:
  J1_signup: pass | fail | not_run
  J2_onboarding: pass | fail | not_run
  J3_core_jobs: pass | fail | not_run
  J4_payments: pass | fail | not_applicable | not_run
  J5_transactional_email: pass | fail | not_run
  J6_settings_locale: pass | fail | not_run
  J7_exploratory_charter: pass | fail | not_run
  J8_account_deletion: pass | fail | not_run
payment_verification:
  mode: processor-test-mode | live-100pct-promo-code | approved-real-charge | not_applicable
  completed_by: agent-local | human | agent-with-approval | not_applicable
  session_or_charge_id: <id>
  refund_id: <id | not_applicable>
  credit_note_id: <id | not_applicable>
live_steps_by: human | agent-with-approval | not_applicable
provider_spend:
  requests: <count>
  total_cost_usd: <amount>
  receipt_ids: [<provider-request-id>]
error_tracker:
  release_tag: <version>
  new_unhandled_events: 0
findings:
  s0_blocker: 0
  s1_high: 0
  s2_medium: 0
  s3_low: 0
artifacts_dir: <path-outside-git-repo>
test_ledger_updated: true
teardown_status: ui_deleted_and_idempotent_sweep_clean | not_run | not_applicable
completed_at: <ISO-8601 timestamp>
```

## Severity, pass/fail, and retest rules

- **`S0` (Blocker):** Crash, blank screen, auth or sign-up failure, payment or webhook failure, data loss or corruption, secret leak, account deletion failure, or unhandled error-tracker exception on `J1`–`J8`.
- **`S1` (High):** Core provider feature fails without graceful recovery, email delivery exceeds 60 seconds, layout overlap blocks a primary button, or untranslated/placeholder text appears on a primary screen.
- **`S2` (Medium):** Non-blocking UX friction, minor visual misalignment on a secondary screen, or response time 10–25% over budget with a working loading state.
- **`S3` (Low):** Cosmetic polish note or minor copy adjustment.
- **Pass:** 100% of the selected journeys (the baseline, or the touched set) complete on real providers with `0` `S0` findings, `0` `S1` findings, `0` uncaught console errors, `0` unexpected 4xx/5xx responses, and `0` new unhandled error-tracker events.
- **Fail:** Any `S0` or `S1` finding, any skipped selected journey, or any mocked provider where a live provider is required.
- **Retest rule:** Fix the root cause, build or deploy the patched candidate, and retest only the failed journey and directly coupled flows instead of restarting the full passing suite.

## Human-only steps

- Creating accounts, signing in with passwords or one-time codes, paying, and deleting accounts on live production, unless a human explicitly approves each step.
- Completing processor test-mode checkouts on a hosted staging or preview environment.
- Completing anti-bot CAPTCHA or proof-of-work challenges.
- Approving real-money 3D Secure (3DS) bank prompts when a live charge is explicitly authorized.
- Confirming app store biometric prompts (Face ID, Touch ID, or store purchase authentication).
- Granting first-time OS permission prompts that automation tools cannot accept directly.

## Common issues & anti-patterns

- **Seeding auth or onboarding state:** Injecting tokens or database rows hides broken sign-up and first-run transitions.
- **Trusting HTTP 200 for email:** Checking only the send API response misses DNS, SPF/DKIM, and broken link bugs.
- **Running unapproved live card tests:** Processors forbid live testing with real card details; use test mode on candidates and, when a touched area exists only in production, a 100%-off promotion code completed by a human or with explicit per-step approval.
- **Re-running everything each release:** After the baseline, run only the touched journeys; a full run repeats work and adds provider spend.
- **Agent actions on live accounts:** An agent that signs up, pays, or deletes accounts on production without a human's approval acts outside its authority; keep agent runs on candidate hosts.
- **Leaving test users in analytics:** Unflagged test accounts distort funnels and receive marketing emails.
- **Committing evidence to git:** Traces and videos bloat the repository and may expose session data.

## Required output

- Stage executed (`release-candidate` or `post-deploy-live`), run scope (`baseline` or `on-touch`) with the touched areas, the host, and personas run.
- Per-journey results (`J1`–`J8`, with `not_run` for untouched journeys) and exploratory charter outcomes.
- Payment mode used and who completed it, recorded provider spend, and error-tracker event count.
- Updated test ledger entry, completed YAML evidence packet, and path to the external evidence directory.

## Safety

- Never create accounts, enter passwords or one-time codes, pay, or delete accounts on live production without a human's explicit approval for that step.
- Never run a real-money charge on your own; it is a human decision each time, checked against the processor's terms, and is refunded the same day with a credit note.
- Keep API keys and mailbox credentials in environment variables or secret stores; never print them in logs or evidence packets.
- Store recordings, screenshots, and `trace.zip` archives outside version control.
- Restrict idempotent teardown to accounts flagged `qa_test: true` or matching the `qa+` subaddress prefix, and run it on production only with a human's approval.

## Completion criteria

Done means the scoped candidate run (the full baseline once per product, otherwise the journeys the release touched) ran end to end on a local development host or a designated staging or preview host against real providers without auth or onboarding bypasses, all selected journeys passed with zero `S0`/`S1` findings, the post-deploy read-only check of the error tracker, the touched pages, and any delivered mail found zero new issues, any production-only live journey was completed by a human or with explicit per-step approval, any test account created for the run was deleted through the UI and swept by idempotent teardown, the test ledger was updated, and the YAML evidence packet was written.
