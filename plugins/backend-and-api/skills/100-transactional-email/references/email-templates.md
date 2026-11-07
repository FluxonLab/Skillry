# React Email Templates Specification

Technical reference and implementation blueprints for transactional emails and announcements using `@react-email/components`.

## 1. Design and Architecture Principles

1. **Framework**: Standardized on `@react-email/components` (`Html`, `Head`, `Preview`, `Body`, `Container`, `Section`, `Heading`, `Text`, `Button`, `Hr`, `Link`, `Img`).
2. **Typography**: Clean system font stack (`-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif`).
3. **Container**: Maximum width 600px, centered with responsive margin and padding.
4. **Tone and Copy**: Direct, plain language, respectful. Adapt honorifics appropriately for the target locale. Zero marketing fluff, no fake urgency, and no excessive emojis.
5. **Dual Rendering**: Every template must support both HTML and clean plaintext output (`render(component, { plainText: true })`).
6. **Regulatory Compliance**: Marketing and newsletter templates must include an instant unsubscribe link and physical publisher address.

---

## 2. Template Blueprints

### A. Welcome Email (`WelcomeEmail.tsx`)

Sent immediately upon user onboarding or account creation.

```tsx
import {
  Body,
  Button,
  Container,
  Head,
  Heading,
  Hr,
  Html,
  Link,
  Preview,
  Section,
  Text,
} from "@react-email/components";
import * as React from "react";

interface WelcomeEmailProps {
  productName: string;
  userName: string;
  actionUrl: string;
  supportEmail: string;
}

export const WelcomeEmail = ({
  productName = "Acme App",
  userName = "Customer",
  actionUrl = "https://example.com/dashboard",
  supportEmail = "support@example.com",
}: WelcomeEmailProps) => (
  <Html>
    <Head />
    <Preview>Welcome to {productName}</Preview>
    <Body style={mainStyle}>
      <Container style={containerStyle}>
        <Heading style={headingStyle}>Welcome to {productName}</Heading>
        <Text style={textStyle}>Hello {userName},</Text>
        <Text style={textStyle}>
          Your account is ready. You can now access your workspace and configure
          your project settings.
        </Text>
        <Section style={btnSectionStyle}>
          <Button style={buttonStyle} href={actionUrl}>
            Open Workspace
          </Button>
        </Section>
        <Text style={textStyle}>
          If you have questions, reply directly to this email or contact us at{" "}
          <Link href={`mailto:${supportEmail}`} style={linkStyle}>
            {supportEmail}
          </Link>
          .
        </Text>
        <Hr style={hrStyle} />
        <Text style={footerStyle}>
          © {new Date().getFullYear()} {productName}. All rights reserved.
        </Text>
      </Container>
    </Body>
  </Html>
);

export default WelcomeEmail;
```

---

### B. Payment Receipt Email (`ReceiptEmail.tsx`)

Transactional proof for completed payments or subscription renewals.

```tsx
import {
  Body,
  Container,
  Head,
  Heading,
  Hr,
  Html,
  Preview,
  Section,
  Text,
} from "@react-email/components";
import * as React from "react";

interface ReceiptEmailProps {
  productName: string;
  invoiceId: string;
  date: string;
  amount: string;
  currency: string;
  planName: string;
  billingEmail: string;
}

export const ReceiptEmail = ({
  productName = "Acme App",
  invoiceId = "INV-2026-001",
  date = "15 January 2026",
  amount = "29.00",
  currency = "EUR",
  planName = "Pro Monthly",
  billingEmail = "billing@example.com",
}: ReceiptEmailProps) => (
  <Html>
    <Head />
    <Preview>Receipt for invoice {invoiceId}</Preview>
    <Body style={mainStyle}>
      <Container style={containerStyle}>
        <Heading style={headingStyle}>Payment Receipt</Heading>
        <Text style={textStyle}>Thank you for your payment.</Text>
        <Section style={tableContainerStyle}>
          <Text style={detailRowStyle}><strong>Invoice:</strong> {invoiceId}</Text>
          <Text style={detailRowStyle}><strong>Date:</strong> {date}</Text>
          <Text style={detailRowStyle}><strong>Plan:</strong> {planName}</Text>
          <Text style={detailRowStyle}><strong>Amount Paid:</strong> {amount} {currency}</Text>
        </Section>
        <Text style={textStyle}>
          For invoice downloads or billing adjustments, contact{" "}
          <a href={`mailto:${billingEmail}`} style={linkStyle}>{billingEmail}</a>.
        </Text>
        <Hr style={hrStyle} />
        <Text style={footerStyle}>
          © {new Date().getFullYear()} {productName}. All rights reserved.
        </Text>
      </Container>
    </Body>
  </Html>
);

export default ReceiptEmail;
```

---

### C. Password Reset Email (`PasswordResetEmail.tsx`)

Authentication notification for password resets and magic login links.

```tsx
import {
  Body,
  Button,
  Container,
  Head,
  Heading,
  Hr,
  Html,
  Preview,
  Section,
  Text,
} from "@react-email/components";
import * as React from "react";

interface PasswordResetEmailProps {
  productName: string;
  resetUrl: string;
  validMinutes: number;
}

export const PasswordResetEmail = ({
  productName = "Acme App",
  resetUrl = "https://example.com/auth/reset?token=xyz",
  validMinutes = 30,
}: PasswordResetEmailProps) => (
  <Html>
    <Head />
    <Preview>Reset your {productName} password</Preview>
    <Body style={mainStyle}>
      <Container style={containerStyle}>
        <Heading style={headingStyle}>Reset Password</Heading>
        <Text style={textStyle}>
          A password reset was requested for your account. Click the button below to choose a new password.
        </Text>
        <Section style={btnSectionStyle}>
          <Button style={buttonStyle} href={resetUrl}>
            Reset Password
          </Button>
        </Section>
        <Text style={textStyle}>
          This link will expire in {validMinutes} minutes. If you did not request this change, you can safely ignore this email; your password will remain unchanged.
        </Text>
        <Hr style={hrStyle} />
        <Text style={footerStyle}>
          © {new Date().getFullYear()} {productName}. Security notification.
        </Text>
      </Container>
    </Body>
  </Html>
);

export default PasswordResetEmail;
```

---

### D. Re-engagement Email (`ReengagementEmail.tsx`)

Sent to dormant or inactive users highlighting genuine product improvements.

```tsx
import {
  Body,
  Button,
  Container,
  Head,
  Heading,
  Hr,
  Html,
  Link,
  Preview,
  Section,
  Text,
} from "@react-email/components";
import * as React from "react";

interface ReengagementEmailProps {
  productName: string;
  userName: string;
  updateSummary: string;
  actionUrl: string;
  unsubscribeUrl: string;
}

export const ReengagementEmail = ({
  productName = "Acme App",
  userName = "Customer",
  updateSummary = "We have added new automation capabilities and performance improvements to your workspace.",
  actionUrl = "https://example.com/dashboard",
  unsubscribeUrl = "https://example.com/settings/notifications",
}: ReengagementEmailProps) => (
  <Html>
    <Head />
    <Preview>Updates in {productName}</Preview>
    <Body style={mainStyle}>
      <Container style={containerStyle}>
        <Heading style={headingStyle}>Checking In</Heading>
        <Text style={textStyle}>Hello {userName},</Text>
        <Text style={textStyle}>{updateSummary}</Text>
        <Section style={btnSectionStyle}>
          <Button style={buttonStyle} href={actionUrl}>
            Review Your Workspace
          </Button>
        </Section>
        <Hr style={hrStyle} />
        <Text style={footerStyle}>
          You received this email because you have an account on {productName}.{" "}
          <Link href={unsubscribeUrl} style={linkStyle}>Manage notifications</Link>.
        </Text>
      </Container>
    </Body>
  </Html>
);

export default ReengagementEmail;
```

---

### E. Newsletter / Announcement Email (`NewsletterEmail.tsx`)

Used for periodic announcements, releases, and curated product updates.

```tsx
import {
  Body,
  Container,
  Head,
  Heading,
  Hr,
  Html,
  Link,
  Preview,
  Section,
  Text,
} from "@react-email/components";
import * as React from "react";

interface NewsletterEmailProps {
  productName: string;
  editionTitle: string;
  date: string;
  contentMarkdown: string;
  unsubscribeUrl: string;
  postalAddress?: string;
}

export const NewsletterEmail = ({
  productName = "Acme App",
  editionTitle = "Product Update — January 2026",
  date = "January 2026",
  contentMarkdown = "Summary of monthly engineering and product updates.",
  unsubscribeUrl = "https://example.com/newsletter/unsubscribe",
  postalAddress = "123 Innovation Way, Tech City, TC 10101",
}: NewsletterEmailProps) => (
  <Html>
    <Head />
    <Preview>{editionTitle}</Preview>
    <Body style={mainStyle}>
      <Container style={containerStyle}>
        <Text style={metaDateStyle}>{date}</Text>
        <Heading style={headingStyle}>{editionTitle}</Heading>
        <Section style={contentSectionStyle}>
          <Text style={textStyle}>{contentMarkdown}</Text>
        </Section>
        <Hr style={hrStyle} />
        <Text style={footerStyle}>
          Sent by {productName}, {postalAddress}.{" "}
          <Link href={unsubscribeUrl} style={linkStyle}>Unsubscribe instantly</Link>.
        </Text>
      </Container>
    </Body>
  </Html>
);

export default NewsletterEmail;
```

---

## 3. Shared Inline Styles

```ts
export const mainStyle = {
  backgroundColor: "#f6f7f8",
  fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
  margin: "0 auto",
  padding: "40px 0",
};

export const containerStyle = {
  backgroundColor: "#ffffff",
  border: "1px solid #e5e7eb",
  borderRadius: "8px",
  margin: "0 auto",
  maxWidth: "600px",
  padding: "32px",
};

export const headingStyle = {
  color: "#111827",
  fontSize: "22px",
  fontWeight: "600",
  lineHeight: "1.3",
  margin: "0 0 16px",
};

export const textStyle = {
  color: "#374151",
  fontSize: "15px",
  lineHeight: "1.6",
  margin: "0 0 16px",
};

export const btnSectionStyle = {
  margin: "24px 0",
  textAlign: "center" as const,
};

export const buttonStyle = {
  backgroundColor: "#111827",
  borderRadius: "6px",
  color: "#ffffff",
  display: "inline-block",
  fontSize: "14px",
  fontWeight: "500",
  padding: "12px 24px",
  textDecoration: "none",
};

export const tableContainerStyle = {
  backgroundColor: "#f9fafb",
  borderRadius: "6px",
  padding: "16px",
  margin: "16px 0",
};

export const detailRowStyle = {
  color: "#4b5563",
  fontSize: "14px",
  margin: "6px 0",
};

export const linkStyle = {
  color: "#2563eb",
  textDecoration: "underline",
};

export const hrStyle = {
  borderColor: "#e5e7eb",
  margin: "24px 0",
};

export const metaDateStyle = {
  color: "#6b7280",
  fontSize: "12px",
  textTransform: "uppercase" as const,
  letterSpacing: "0.05em",
  margin: "0 0 8px",
};

export const contentSectionStyle = {
  margin: "16px 0",
};

export const footerStyle = {
  color: "#6b7280",
  fontSize: "12px",
  lineHeight: "1.5",
  margin: "0",
};
```

---

## 4. Dual Rendering and Testing Helper

Generate both HTML and plaintext representations for deliverability and spam-filter compliance:

```typescript
import { render } from "@react-email/render";
import * as React from "react";

export async function renderEmail(component: React.ReactElement): Promise<{
  html: string;
  text: string;
}> {
  const html = await render(component);
  const text = await render(component, { plainText: true });
  return { html, text };
}
```
