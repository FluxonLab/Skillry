---
name: transactional-email
description: "Send transactional email and threaded replies via modern mail APIs, author React Email templates, enforce deliverability and release gates."
---

# Transactional Email

## Purpose

Deliver transactional notifications, lifecycle updates, and threaded customer support replies through authenticated mail APIs such as Resend. This skill establishes standards for component-based email authoring using React Email, automated dual-format rendering (HTML and plaintext), RFC 5322 conversation threading, DNS authentication (SPF, DKIM, DMARC), pre-send human approval protocols, and release readiness gates for all customer communication flows.

## When to use

- Designing, building, or refactoring transactional email flows (welcome, billing receipts, password resets, account notifications, updates).
- Authoring responsive email components and templates with `@react-email/components`.
- Implementing RFC 5322 threaded replies to customer inquiries forwarded from domain routing rules.
- Auditing email deliverability, DNS authentication records (DKIM, SPF, DMARC), and bounce handling.
- Enforcing production release gates for email completeness before deploying customer-facing systems.

## When not to use

- Bulk marketing campaigns, cold outreach, or unsolicited spam lists.
- Internal IMAP or POP3 mailbox infrastructure administration.
- Real-time in-app notifications or push alerts; use dedicated push or WebSocket services.
- Transmitting sensitive credentials in plaintext (never email raw passwords, secrets, or payment credentials; cross-link `security-and-secrets-review`).
- Designing general application REST interfaces; follow `api-and-interface-design`.

## Procedure

1. **Configure sender domain and environment credentials:**
   - Verify that the sending domain has valid DNS authentication records (DKIM, SPF, DMARC).
   - Store provider credentials in secure environment variables (for example, `RESEND_API_KEY`), loaded in-process. Never commit or print keys.
2. **Build and validate lifecycle templates:**
   - Implement the core lifecycle flows using `@react-email/components`: Welcome, Payment Receipt, Password Reset, Re-engagement, and Announcements.
   - Enforce dual rendering: compile both HTML and plaintext representations for every template via `render(component, { plainText: true })`.
   - Maintain clear, concise copy with zero marketing fluff, no fake urgency, and valid legal or unsubscribe footers where applicable.
   - See [references/email-templates.md](references/email-templates.md) for full component source and shared styling primitives.
3. **Handle threaded replies to forwarded mail:**
   - When answering forwarded customer messages, extract the original `Message-ID` from the inbound headers.
   - Set the outbound `In-Reply-To` header to `<original-message-id>`.
   - Set `References` by appending the current `<original-message-id>` to any prior references.
   - Clean the subject line by stripping redundant `Fwd:`, `FW:`, or duplicate `Re:` prefixes, prefixing a single `Re: `.
   - Direct the response (`To`) to the actual customer address, never to an internal forwarding alias.
   - Consult [references/resend-and-threading.md](references/resend-and-threading.md) for API schemas and header extraction logic.
4. **Enforce the pre-send verification and operator approval protocol:**
   - Before any live dispatch, generate a dry-run preview containing sender, recipient, subject, threading headers, and plaintext body.
   - Obtain explicit operator confirmation before transmitting through the mail provider API. Halt if approval is withheld.
5. **Run the production release readiness gate:**
   - Verify that all required email templates exist and compile without layout degradation.
   - Confirm plaintext generation and inspect link destinations.
   - Ensure DNS records for the sending domain are verified with the email provider. Cross-link `release-readiness-check` and `backend-implementation-review`.

## Concrete checks

- **DNS deliverability:** DKIM CNAME is active; SPF TXT includes the sending provider; DMARC policy is published.
- **Credential hygiene:** API key is read from environment variables; zero credentials logged to console or committed to version control.
- **Template completeness:** All five baseline flows (Welcome, Receipt, Reset, Re-engagement, Announcement) exist in the codebase.
- **Dual rendering:** Every template compiles to valid responsive HTML and clean plaintext output.
- **Threading integrity:** `In-Reply-To` and `References` headers contain properly formatted, bracketed message identifiers.
- **Address routing:** Outbound `To` matches the customer recipient; `From` uses a verified domain address.
- **Content standards:** Copy is direct and free of spam-trigger keywords; broadcast emails include physical address and unsubscribe links.
- **Operator confirmation:** Live send commands are blocked until explicit human approval is granted in the current session.

## Commands

```bash
# Verify DNS deliverability records for the sending domain
dig +short TXT example.com | grep "v=spf1"
dig +short CNAME resend._domainkey.example.com
dig +short TXT _dmarc.example.com

# Verify environment configuration contains the API key (names only, never echo values)
env | grep -E '^[A-Z0-9_]*KEY' | cut -d= -f1

# Run email template build and typecheck
npm run build:emails 2>/dev/null || pnpm build:emails 2>/dev/null
```

```typescript
// Sample dispatch using Resend with RFC 5322 threading headers
import { Resend } from "resend";

const resend = new Resend(process.env.RESEND_API_KEY);

interface SendReplyParams {
  to: string;
  subject: string;
  html: string;
  text: string;
  originalMessageId: string;
  existingReferences?: string;
}

export async function sendThreadedReply({
  to,
  subject,
  html,
  text,
  originalMessageId,
  existingReferences,
}: SendReplyParams) {
  const references = existingReferences
    ? `${existingReferences} ${originalMessageId}`
    : originalMessageId;

  return await resend.emails.send({
    from: "Support <support@example.com>",
    to: [to],
    subject: subject.startsWith("Re:") ? subject : `Re: ${subject}`,
    html,
    text,
    headers: {
      "In-Reply-To": originalMessageId,
      References: references,
    },
  });
}
```

## Common issues & anti-patterns

- **Autonomous dispatch without confirmation:** Sending live emails automatically in scripts without a human-in-the-loop preview risks customer spam and accidental data leaks.
- **Replying to forwarding aliases:** Sending outbound replies to an internal inbox alias instead of the customer's actual address breaks the communication loop.
- **Broken thread continuity:** Omitting `In-Reply-To` or stripping `References` creates disconnected threads in customer email clients.
- **Missing plaintext alternatives:** Sending HTML-only messages triggers spam filters and renders poorly in text-only mail clients.
- **Hardcoded API keys:** Committing email service API keys in repository files or scripts invites credential compromise.
- **Missing authentication records:** Sending from domains without verified SPF, DKIM, and DMARC leads to high bounce rates and spam folder placement.
- **Missing compliance footers:** Omitting unsubscribe links or sender identification on announcements violates anti-spam regulations (such as CAN-SPAM and GDPR).
- **Ignoring authentication flows:** Building auth-related emails without linking to `auth-session-review` for token lifetime and CSRF safety.

## Required output

When verifying or sending email flows, provide:
1. Sender identity (`From`) and destination recipient (`To`).
2. Subject line and RFC 5322 threading headers (`In-Reply-To`, `References`).
3. Render status (confirmation of both HTML and plaintext representations).
4. Template name and release gate checklist verification.
5. Confirmation of operator approval and provider message identifier on successful delivery.

## Safety

- Never send real emails autonomously; always present a formatted preview and await explicit confirmation.
- Never hardcode or echo API keys or secrets in logs, terminal outputs, or artifacts; cross-link `security-and-secrets-review`.
- Redact customer personally identifiable information (PII) from test outputs and diagnostic traces.
- Use dedicated test mailboxes or sandbox environments during automated CI and development tests; cross-link `smoke-test-and-repair`.

## Completion criteria

The transactional email implementation or audit is complete when:
- Sender domain DNS authentication (SPF, DKIM, DMARC) is validated.
- Core lifecycle templates compile cleanly with both HTML and plaintext versions verified.
- Outbound threading logic preserves conversation continuity using valid RFC 5322 headers.
- Pre-send preview and explicit operator approval workflows are respected.
- Release gate requirements are documented and verified before production deployment.
