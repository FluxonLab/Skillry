# Email Delivery and Threading Specification

Technical reference for delivering transactional email and constructing RFC 5322 threaded replies via modern mail APIs such as Resend.

## 1. Sending Domain Configuration and Secret Management

Automated delivery requires a verified sending domain and provider API credentials.

- **Sender Addresses:** Send from authenticated domain addresses (for example, `support@example.com` or `notifications@example.com`).
- **Environment Variables:** Store API keys in environment variables (for example, `RESEND_API_KEY`).
- **Secret Hygiene:** Read credentials in-process at runtime. Never hardcode credentials, commit `.env` files with live values, or print keys in diagnostic output.

---

## 2. Inbound Forwarding and Thread Extraction

When customer inquiries sent to domain addresses (such as `support@example.com`) are forwarded by DNS email routing services (such as Cloudflare Email Routing, AWS SES, or standard mail aliases) into an operational mailbox, outbound replies sent via the mail API must maintain RFC 5322 thread continuity.

### Thread Continuity Algorithm

1. **Locate Source Message-ID:**
   - Inspect the forwarded message headers or body block.
   - If raw headers are forwarded: read the original `Message-ID`.
   - If forwarded inline by an email client: extract `Message-ID` from the forwarded header block (`From:`, `Date:`, `Subject:`, `Message-ID:`).
   - If the original `Message-ID` cannot be located, mark the thread as unverified and use the outer message's identifier.

2. **Construct `In-Reply-To`:**
   - Set `In-Reply-To` exactly to the original message identifier, enclosed in angle brackets:
     ```text
     In-Reply-To: <original-message-id@domain.com>
     ```

3. **Construct `References`:**
   - If the original message had an existing `References` header, append the current `<original-message-id@domain.com>`:
     ```text
     References: <ancestor-id-1> <ancestor-id-2> <original-message-id@domain.com>
     ```
   - If no prior references exist, set `References` to the original `<original-message-id@domain.com>`.

4. **Format Subject Line:**
   - Normalize the subject: strip leading `Fwd:`, `FW:`, or duplicate `Re:` prefixes.
   - Prepend a single `Re: `:
     ```text
     Subject: Re: Original Subject Here
     ```

5. **Recipient Mapping:**
   - Set the destination (`To`) to the customer's actual address (from `Reply-To` or original `From`), never to the internal forwarding alias.

---

## 3. Resend API Request Payload and Dispatch Helper

Deliver via `POST https://api.resend.com/emails` with Bearer token authentication:

### JSON Payload Schema

```json
{
  "from": "Acme Support <support@example.com>",
  "to": ["customer@example.com"],
  "subject": "Re: Issue with subscription",
  "html": "<p>Hello,</p><p>Here is the update regarding your issue...</p>",
  "text": "Hello,\n\nHere is the update regarding your issue...",
  "headers": {
    "In-Reply-To": "<20260115123456.ABCD1234@customer-mail.org>",
    "References": "<20260115123456.ABCD1234@customer-mail.org>"
  }
}
```

### TypeScript Dispatch Helper

```typescript
import { Resend } from "resend";

const apiKey = process.env.RESEND_API_KEY;
if (!apiKey) {
  throw new Error("Missing RESEND_API_KEY environment variable");
}

const resend = new Resend(apiKey);

export interface ThreadedReplyOptions {
  from?: string;
  to: string;
  subject: string;
  html: string;
  text: string;
  originalMessageId: string;
  existingReferences?: string;
}

export async function sendThreadedReply({
  from = "Support <support@example.com>",
  to,
  subject,
  html,
  text,
  originalMessageId,
  existingReferences,
}: ThreadedReplyOptions) {
  // Normalize subject line
  const cleanSubject = subject
    .replace(/^(fwd|fw|re):\s*/gi, "")
    .trim();
  const normalizedSubject = `Re: ${cleanSubject}`;

  // Ensure Message-ID is bracketed
  const bracketedId = originalMessageId.startsWith("<") && originalMessageId.endsWith(">")
    ? originalMessageId
    : `<${originalMessageId}>`;

  // Build References chain
  const references = existingReferences
    ? `${existingReferences.trim()} ${bracketedId}`
    : bracketedId;

  const response = await resend.emails.send({
    from,
    to: [to],
    subject: normalizedSubject,
    html,
    text,
    headers: {
      "In-Reply-To": bracketedId,
      References: references,
    },
  });

  if (response.error) {
    throw new Error(`Failed to send threaded reply: ${response.error.message}`);
  }

  return response.data;
}
```

### Response Handling

- Successful transmission returns HTTP 200/201 with `{"id": "msg_xxx"}`.
- Record the returned message ID in audit logs for traceability.
- If HTTP 401 or 422 occurs, inspect API key permissions and verify that the sending domain is active and authenticated in the provider dashboard.

---

## 4. DNS Deliverability Prerequisites

Before sending from any custom domain, verify that the required DNS authentication records are established:

- **DKIM:** CNAME record (for example, `resend._domainkey.<domain>`) pointing to the provider's DKIM verification host.
- **SPF:** TXT record on the sending domain or subdomain including the provider mechanism (for example, `v=spf1 include:resend.com ~all`).
- **DMARC:** TXT record at `_dmarc.<domain>` publishing a valid policy (such as `v=DMARC1; p=none;` or stricter).

### Verification Commands

```bash
# Check SPF record
dig +short TXT example.com | grep "v=spf1"

# Check DKIM CNAME record
dig +short CNAME resend._domainkey.example.com

# Check DMARC policy
dig +short TXT _dmarc.example.com
```
