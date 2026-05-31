---
name: ecommerce-integration-review
description: Use when you need to review ecommerce catalogs, checkout, payments, inventory, orders, taxes, and integration boundaries.
---

# Ecommerce Integration Review

## Purpose
Review the correctness, security, and resilience of ecommerce integration code: product catalog sync, cart and checkout logic, payment provider integration (Stripe, PayPal, Adyen), webhook handling, inventory sync, tax/shipping calculation, and order lifecycle management.

## When to use
- Reviewing Stripe, PayPal, Adyen, or similar payment gateway integration code.
- Auditing webhook handlers that receive payment, order, or fulfillment events from external platforms.
- Reviewing catalog sync pipelines between a PIM, ERP, or marketplace and a storefront.
- Evaluating checkout flow code for race conditions, double-charge risks, or inventory oversell.
- Reviewing tax engine integration (Avalara, TaxJar) or shipping rate API calls.
- Auditing integration between Shopify, WooCommerce, BigCommerce, or headless commerce and third-party services.

## When not to use
- Pure UI/UX review of a product listing page with no integration logic — use a front-end review.
- Database schema design with no commerce business logic.
- Infrastructure (CDN, caching layer) unless it directly affects checkout availability.

## Procedure

### 1. Map the integration boundaries
- Identify all external systems: payment provider, shipping carrier API, tax engine, ERP/warehouse.
- Document each integration point: direction (inbound/outbound), protocol (REST/webhook/GraphQL/EDI), authentication method (API key, OAuth, HMAC signature).
- Check that secrets are stored in environment variables — never hardcoded.

### 2. Payment integration
- Stripe: verify `PaymentIntent` creation with correct `amount` (in smallest currency unit), `currency`, and `idempotency_key`.
- Confirm `payment_intent.succeeded` webhook is used to fulfill orders — not the client-side redirect alone.
- PayPal: verify IPN or Webhook signature validation before order fulfillment.
- Check that partial captures and refunds are handled; confirm `amount_to_capture` does not exceed authorized amount.
- Ensure test mode / sandbox credentials are never deployed to production (detect by key prefix: `sk_test_`, sandbox endpoints).

### 3. Idempotency and duplicate prevention
- Every payment initiation must use an idempotency key tied to the order ID, not a random UUID generated per retry.
- Webhook handlers must be idempotent: processing the same event twice must not create duplicate orders or double-charge.
- Implement event deduplication using the provider's event ID stored in a processed-events table or cache (TTL ≥ 24 h).

### 4. Inventory and stock sync
- Check for race conditions: concurrent checkouts for the same SKU must use a database-level lock or a reservation pattern (reserve → purchase → confirm/release).
- Catalog sync must handle partial failures: if 500 of 1,000 SKUs sync, the remaining 500 must retry, not silently drop.
- Stock level writes must be atomic — use transactions or compare-and-swap (`UPDATE stock SET qty = qty - 1 WHERE qty > 0 AND sku = ?`).
- Oversell prevention: enforce `qty >= 0` constraint at the DB level, not only in application code.

### 5. Tax and shipping
- Tax calculations must be performed server-side at checkout — never trust a client-supplied tax amount.
- Verify tax engine is called with accurate `ship_from`, `ship_to`, and line-item details.
- Shipping rate API calls must be cached per quote session, not re-fetched per page load.
- Confirm that free-shipping thresholds and discount stacking are evaluated after discounts are applied to the subtotal.

### 6. Order lifecycle
- Order state machine: define allowed transitions (pending → processing → shipped → delivered → refunded). Block invalid transitions.
- Fulfillment webhooks (shipment created, delivered) must update order status and notify the customer.
- Refund flow: verify refund amount ≤ captured amount; reversal must mark order line items as refunded in the local DB.
- Cancellation: release reserved inventory before cancelling payment.

### 7. PCI and data handling
- Card data must never touch application servers — use client-side tokenization (Stripe Elements, Braintree Drop-in).
- No raw PAN, CVV, or full track data in logs, analytics payloads, or error messages.
- Webhook payloads containing card info (rare but seen in older integrations) must be immediately truncated before storage.
- Confirm the integration is scoped to SAQ A or SAQ A-EP — if the server handles raw card data, escalate as critical.

### 8. Error handling and retries
- Retry transient failures (network timeout, 5xx from payment provider) with exponential back-off and jitter.
- Do not retry on 4xx (bad request, invalid card) — surface the error to the user.
- Failed webhook deliveries: implement a dead-letter queue and alerting after N retries.
- Log every payment event with order ID, provider event ID, amount, currency, and outcome — redact card details.

## Checklist

Payment:
- [ ] Idempotency key used for payment initiation, tied to order/session ID.
- [ ] Server-side webhook signature verified before fulfillment.
- [ ] Test/sandbox credentials absent from production config.
- [ ] Partial capture and refund paths handled.
- [ ] Double-charge prevention: webhook deduplication implemented.

Inventory:
- [ ] Stock reservation or DB-level locking prevents oversell.
- [ ] Atomic stock decrement at checkout confirmation.
- [ ] Catalog sync handles partial failure with retry.

Compliance:
- [ ] No raw card data on application servers.
- [ ] No PAN/CVV in logs or analytics.
- [ ] Tax calculated server-side, not from client payload.

Resilience:
- [ ] Retry with back-off for transient provider errors.
- [ ] Dead-letter queue for failed webhooks.
- [ ] Order state machine rejects invalid transitions.

## Common issues & anti-patterns

- **Fulfilling on client redirect**: relying on the browser returning to a success URL to mark an order paid. Network failures prevent this; always use server-side webhooks.
- **Random idempotency key per retry**: generates duplicate charges on retry. Use a deterministic key: `order_id + attempt_number`.
- **No webhook signature check**: any external caller can spoof a `payment_intent.succeeded` event and get free orders.
- **Oversell via concurrent requests**: two simultaneous checkouts both read `qty = 1`, both decrement — oversell by 1. Fix with `SELECT FOR UPDATE` or optimistic locking.
- **Tax from client payload**: a modified frontend POST can set tax to $0. Always recalculate on the server.
- **Logging `req.body` for payment webhooks**: inadvertently logs raw card data or sensitive bank details. Log only the event ID and type.
- **Synchronous inventory update during payment**: if the payment step is slow and the inventory write times out, the transaction is left in a limbo state. Use eventual consistency with a saga pattern.

## Required output

Return a structured report with:
- **Summary**: pass / conditional pass / blocked, and the primary risk category.
- **Evidence**: file + line references for each finding.
- **Findings table**: severity (critical / high / medium / low / info), category, description, remediation.
- **PCI note**: explicit statement on card data scope and SAQ level.
- **Resilience assessment**: idempotency, retry logic, and webhook deduplication status.
- **Next handoff**: staging test plan with specific scenarios (concurrent checkout, webhook replay, refund flow).

## Safety

- Never print live API keys, Stripe secret keys, or payment provider webhooks secrets.
- Do not execute payment API calls or trigger test charges during review.
- Flag any PAN, CVV, or bank account data found in code or config as critical.
- If a vulnerability enables free-order fraud or double-charge, mark critical and block deployment.
