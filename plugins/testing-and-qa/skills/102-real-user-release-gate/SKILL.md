---
name: real-user-release-gate
description: "Use this skill before any release and right after a production deploy to test the integrated product end to end as a real customer with live providers, inbox verification, bounded payments, and exploratory charters."
---

# Real-User Release Gate

## Purpose

Test the integrated product end to end the way a real customer meets it before shipping a release and right after deploying to production. Run against real upstream providers without seeded authentication state, mocked responses, or skipped onboarding. Emit a YAML evidence packet recording journeys, provider spend, error-tracker status, and account teardown. The same session and test account run `customer-lens-testing`, the customer layer: the agent uses the product as a real free and paid customer at three levels of expertise and proposes what it would want.

## When to use

- A release candidate is integrated and ready for pre-release sign-off before production deploy or app store upload.
- A production deployment just completed and needs immediate live verification.
- Authentication, onboarding, billing, or live upstream provider integrations changed before a release.

## When not to use

- During unfinished implementation work or after individual file edits before a phase boundary.
- For isolated unit checks or static layout reviews covered by `smoke-test-and-repair` or `web-design-review`.
- Rerunning passing journeys when only a single failed journey was fixed.

## Two-stage execution

- **Stage 1 — Full release candidate run (pre-release):** Run all four personas (`P1`–`P4`) and all applicable journeys (`J1`–`J8`) end to end on the release candidate before release.
- **First gate of a product (baseline):** the whole product once, end to end: every page and app, free and paid plan. Later releases cover the changed surfaces and the flows they touch.
- **Stage 2 — Short live check (post-deploy):** Run a 5-minute check on live production right after deploy covering cold sign-up (`J1`), inbox verification (`J5`), one live core job (`J3`), 100%-off promotion code payment (`J4`), account deletion (`J8`), and error-tracker verification.

## Personas

- **`P1-FreshVisitor` (Cold Unauthenticated -> New Sign-Up):** Starts in a clean browser profile (`--user-data-dir`) or erased simulator (`xcrun simctl erase` or clean Android AVD) using a shipped locale (`EN`, `TR`, `DE`, or target locale) and runs sign-up through account deletion.
- **`P2-PaidBuyer` (Trial / Free -> Paid Checkout -> Paid Feature -> Billing Portal):** Completes checkout, receives a real receipt email, runs a paid core job, opens the billing portal, and cancels or refunds.
- **`P3-ReturningUpgrader` (Existing Persisted Account Across Upgrade):** Signs into a persisted canary account with historical data to confirm the new build and migrations keep existing projects, sessions, credits, settings, and API keys intact.
- **`P4-EdgeAdversarialUser` (Clumsy / Impatient / Restricted User):** Double-clicks submit buttons, enters diacritics (`ğüşiöçİĞÜŞİÖÇ`, `äöüß`) and 35%-expanded strings, paste-floods inputs, denies push/camera/microphone permissions, toggles network offline/online mid-job, and hits back or refresh during streaming or payment redirects.

## Mandatory journeys (J1–J8)

- **`J1` Discovery & Sign-Up:** Load the candidate or live URL/binary in a clean profile, register via the real auth provider (OAuth, magic link, OTP, or password), receive the real email or SMS, and click the verification link or enter the OTP; pass condition: an authenticated session starts without seeded state.
- **`J2` Onboarding & Empty-State-to-First-Value:** Walk every first-run onboarding screen without database seeding and create the first entity or project; pass condition: empty states clear and onboarding state persists across reload or app restart.
- **`J3` Core Jobs with Real Live Providers:** Run the primary value workflow against live upstream APIs (LLMs, embeddings, media, search, storage, or exports) with minimal real payloads; pass condition: valid non-empty output renders in the UI and request ID, latency, and spend are recorded.
- **`J4` Payments, Entitlements & Invoicing:** Trigger the paywall or upgrade flow, complete checkout, and open the customer billing portal; pass condition: the webhook updates entitlements within 10 seconds, the receipt email arrives, and the billing portal opens.
- **`J5` Transactional Email & Notification Loop:** Read the delivered email in a subaddressed mailbox the team owns (`qa+<project>-<date>-<sha>@<team-domain>`) via IMAP or mail API instead of trusting an HTTP 200 send response; pass condition: `From`/`Reply-To` headers and SPF/DKIM pass, HTML/text links render, and action links work.
- **`J6` Settings, Locale & Profile Mutation:** Change display name, avatar, shipped locales, notification preferences, and API tokens, then reload; pass condition: all mutations persist after reload.
- **`J7` Exploratory Charter:** Run a 10–15 minute time-boxed Session-Based Test Management (SBTM) tour on changed and adjacent surfaces using `P4-EdgeAdversarialUser` inputs; pass condition: zero uncaught console errors, zero unexpected 4xx/5xx responses, zero new error-tracker issues, and no broken layouts.
- **`J8` Self-Serve Account Deletion & Right-to-Erasure:** Delete the test account from the product UI and confirm re-authentication; pass condition: the session revokes immediately, retry login fails, database rows delete or tombstone, and idempotent teardown removes any leftover `qa_test` data.

## Procedure

1. **Prepare clean client state and subaddressed test identity.**
   - Reset the browser profile (`--user-data-dir`) or mobile simulator (`xcrun simctl erase` or clean AVD).
   - Create a subaddressed address (`qa+<project>-<date>-<sha>@<team-domain>`) in a mailbox the team owns.
   - Flag the test account (`qa_test: true`) so it is excluded from analytics and mailing lists.
2. **Execute journeys `J1`–`J3` on real providers.**
   - Complete cold sign-up, real inbox or SMS verification, and all onboarding screens without seeding.
   - Execute the core workflow against live providers with minimal payloads and log request IDs, latency, and spend.
3. **Verify payments (`J4`) under processor rules.**
   - Use payment processor test mode or sandbox test clocks on the release candidate.
   - Use a 100%-off live promotion code at 0.00 in production because processors forbid live testing with real card details.
   - Processors generally forbid live-mode testing with real card details, so the 100%-off code is the default. A real charge after a payment-code change is a human decision each time, made against the processor's terms.
   - Refund any real-money charge the same day and issue a credit note (check your local invoicing rules for real charges).
4. **Execute journeys `J5`–`J8` and capture artifacts.**
   - Verify inbox messages, mutate profile and locale settings, and run 1–3 exploratory charters.
   - Record Playwright traces (`trace.zip` with DOM snapshots and network HAR) or mobile video (`xcrun simctl io booted recordVideo` or `maestro record`) plus runtime logs (`xcrun simctl spawn booted log collect` or `adb logcat`).
   - Delete the account through the product UI (`J8`) and run the idempotent teardown script.
5. **Verify error tracker and sign off.**
   - Query the error-tracking API for the release tag and environment to confirm zero new unhandled exceptions.
   - Workers may run journeys and collect artifacts, while the lead reviewer signs off on visual quality and the gate verdict.

## Concrete checks

- `P1-FreshVisitor` starts in a clean browser profile or freshly erased simulator.
- Sign-up and onboarding finish without seeded database state or injected auth tokens.
- Transactional emails are read from the team's subaddressed inbox with SPF/DKIM, headers, and links verified.
- Live AI and upstream provider calls use minimal payloads with request IDs and spend recorded.
- Candidate payment checks use processor test mode; production checks use a 100%-off live promotion code.
- Any explicitly approved real-money charge has a same-day refund ID and credit note recorded.
- Test accounts are flagged, excluded from analytics and mailing lists, deleted via the product UI, and swept by idempotent teardown.
- Error-tracking API shows zero new unhandled exceptions for the release tag.

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
verdict: pass | fail
scope:
  project: <project-name>
  commit_hash: <git-commit-sha>
  environment: <release-candidate | production>
  test_account: qa+<project>-<date>-<sha>@<team-domain>
  analytics_and_mailing_excluded: true
  personas_run: [P1-FreshVisitor, P2-PaidBuyer, P3-ReturningUpgrader, P4-EdgeAdversarialUser]
journeys:
  J1_signup: pass | fail
  J2_onboarding: pass | fail
  J3_core_jobs: pass | fail
  J4_payments: pass | fail | not_applicable
  J5_transactional_email: pass | fail
  J6_settings_locale: pass | fail
  J7_exploratory_charter: pass | fail
  J8_account_deletion: pass | fail
payment_verification:
  mode: processor-test-mode | live-100pct-promo-code | approved-real-charge
  session_or_charge_id: <id>
  refund_id: <id | not_applicable>
  credit_note_id: <id | not_applicable>
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
teardown_status: ui_deleted_and_idempotent_sweep_clean
completed_at: <ISO-8601 timestamp>
```

## Severity, pass/fail, and retest rules

- **`S0` (Blocker):** Crash, blank screen, auth or sign-up failure, payment or webhook failure, data loss or corruption, secret leak, account deletion failure, or unhandled error-tracker exception on `J1`–`J8`.
- **`S1` (High):** Core provider feature fails without graceful recovery, email delivery exceeds 60 seconds, layout overlap blocks a primary button, or untranslated/placeholder text appears on a primary screen.
- **`S2` (Medium):** Non-blocking UX friction, minor visual misalignment on a secondary screen, or response time 10–25% over budget with a working loading state.
- **`S3` (Low):** Cosmetic polish note or minor copy adjustment.
- **Pass:** 100% of applicable journeys (`J1`–`J8`) complete on real providers with `0` `S0` findings, `0` `S1` findings, `0` uncaught console errors, `0` unexpected 4xx/5xx responses, and `0` new unhandled error-tracker events.
- **Fail:** Any `S0` or `S1` finding, any skipped applicable journey, or any mocked provider where a live provider is required.
- **Retest rule:** Fix the root cause, build or deploy the patched candidate, and retest only the failed journey and directly coupled flows instead of restarting the full passing suite.

## Human-only steps

- Completing anti-bot CAPTCHA or proof-of-work challenges.
- Approving real-money 3D Secure (3DS) bank prompts when a live charge is explicitly authorized.
- Confirming app store biometric prompts (Face ID, Touch ID, or store purchase authentication).
- Granting first-time OS permission prompts that automation tools cannot accept directly.

## Common issues & anti-patterns

- **Seeding auth or onboarding state:** Injecting tokens or database rows hides broken sign-up and first-run transitions.
- **Trusting HTTP 200 for email:** Checking only the send API response misses DNS, SPF/DKIM, and broken link bugs.
- **Running unapproved live card tests:** Processors forbid live testing with real card details; use test mode on candidates and a 100%-off promotion code in production.
- **Leaving test users in analytics:** Unflagged test accounts distort funnels and receive marketing emails.
- **Committing evidence to git:** Traces and videos bloat the repository and may expose session data.

## Required output

- Stage executed (`release-candidate` or `post-deploy-live`) and personas run.
- Per-journey pass/fail results (`J1`–`J8`) and exploratory charter outcomes.
- Payment mode used, recorded provider spend, and error-tracker event count.
- Completed YAML evidence packet and path to the external evidence directory.

## Safety

- Never run a real-money charge on your own; it is a human decision each time, checked against the processor's terms, and is refunded the same day with a credit note.
- Keep API keys and mailbox credentials in environment variables or secret stores; never print them in logs or evidence packets.
- Store recordings, screenshots, and `trace.zip` archives outside version control.
- Restrict idempotent teardown to accounts flagged `qa_test: true` or matching the `qa+` subaddress prefix.

## Completion criteria

Done means the required stage (`release-candidate` full run or `post-deploy-live` check) ran end to end against real providers without auth or onboarding bypasses, all applicable journeys (`J1`–`J8`) passed with zero `S0`/`S1` findings and zero new error-tracker events, test accounts were deleted through the UI and swept by idempotent teardown, and the YAML evidence packet was written.
