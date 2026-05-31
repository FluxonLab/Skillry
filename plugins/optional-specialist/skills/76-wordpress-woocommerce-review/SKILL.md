---
name: wordpress-woocommerce-review
description: Use when you need to review WordPress, WooCommerce, PHP plugin, theme, checkout, payment, and extension changes.
---

# WordPress & WooCommerce Review

## Purpose
Perform a structured security, correctness, and architecture review of WordPress plugins, themes, and WooCommerce extensions. Focus on WordPress-specific attack surfaces (XSS, CSRF, SQLi, privilege escalation) and WooCommerce commerce integrity (order flow, payment hooks, stock sync).

## When to use
- Reviewing a custom plugin or theme before deployment to a WordPress site.
- Auditing WooCommerce checkout, order, or payment extension code.
- Evaluating a PR that modifies `functions.php`, a plugin's main file, REST endpoints, shortcodes, or Gutenberg blocks.
- Security review of any code that touches `$wpdb`, `$_POST`/`$_GET`, user capability checks, or nonces.
- Code uses WooCommerce action/filter hooks (`woocommerce_*`, `wc_*`) and the behavior needs verification.

## When not to use
- Pure front-end review with no PHP and no WordPress APIs involved — use a general JS/CSS review instead.
- Infrastructure (server config, Nginx, MySQL tuning) — that is outside plugin/theme scope.
- Reviewing a headless setup that uses WP only as a data source and has no PHP execution path in scope.

## Procedure

### 1. Identify entry points
- List all hooks registered: `add_action`, `add_filter`, `add_shortcode`, `register_rest_route`.
- Map each hook to its callback and note whether it fires on the front-end, admin, or both.
- Identify REST endpoints and their `permission_callback`.

### 2. Nonce (CSRF) verification
- Every form submission and AJAX handler must call `check_ajax_referer()` or `wp_verify_nonce()` before processing data.
- Nonce field must be printed with `wp_nonce_field()` in forms.
- REST endpoints that mutate state must use `permission_callback` — `__return_true` is a red flag.

### 3. Capability checks
- Admin-only actions must call `current_user_can('manage_options')` or the appropriate capability before executing.
- WooCommerce shop management requires `manage_woocommerce`.
- Never rely on `is_admin()` alone — it is true for AJAX requests too.

### 4. Input sanitization and output escaping
- Sanitize on the way in: `sanitize_text_field()`, `sanitize_email()`, `absint()`, `wp_kses_post()` depending on data type.
- Escape on the way out: `esc_html()`, `esc_attr()`, `esc_url()`, `wp_kses()`.
- Never echo raw `$_POST`/`$_GET`/`$_REQUEST` values.
- Translated strings with variables must use `esc_html_e()` or wrap with `esc_html()`.

### 5. Database queries — `$wpdb` prepared statements
- Direct queries must use `$wpdb->prepare()` with `%s`, `%d`, `%f` placeholders.
- `$wpdb->get_results( $wpdb->prepare(...) )` — never string-interpolate user input into SQL.
- Prefer WP_Query / WC_Order_Query over raw SQL when the ORM supports the use case.

### 6. WooCommerce hook correctness
- Checkout flow: verify hooks fire in the right order (`woocommerce_checkout_process` → `woocommerce_checkout_order_processed` → `woocommerce_payment_complete`).
- Stock deduction must use `wc_reduce_stock_levels()` or `WC_Product::set_stock_quantity()` — never raw DB writes to `_stock`.
- Order status transitions via `$order->update_status()`, not direct `wp_update_post()`.
- Payment gateway classes must extend `WC_Payment_Gateway` and implement `process_payment()` returning a result array with `result` and `redirect` keys.

### 7. Plugin/theme structure
- Plugin must have a valid file header (`Plugin Name`, `Version`, `Requires at least`, `Requires PHP`).
- No business logic in template files — templates should only render.
- `load_plugin_textdomain()` called on `plugins_loaded` for i18n.
- Assets enqueued via `wp_enqueue_scripts` / `wp_enqueue_style`, not inline `<script>` tags.
- Activation/deactivation hooks must not run upgrade routines that can break on repeated execution.

### 8. WooCommerce extension specifics
- Custom product types extend `WC_Product` and register via `woocommerce_product_class` filter.
- Meta stored with `update_post_meta()` or `$product->update_meta_data()` + `$product->save()`.
- Admin columns and order actions added via correct WooCommerce hooks, not raw `manage_posts_columns`.
- Webhooks and payment IPN handlers verify signature before touching order state.

## Checklist

Security:
- [ ] All AJAX/form handlers call `wp_verify_nonce()` or `check_ajax_referer()`.
- [ ] All state-changing REST routes have a real `permission_callback`.
- [ ] `current_user_can()` checked before any privileged action.
- [ ] Every `$_POST`/`$_GET` value sanitized before use.
- [ ] Every dynamic value escaped before output.
- [ ] No raw `$wpdb->query()` with unsanitized input — all use `$wpdb->prepare()`.

WooCommerce correctness:
- [ ] Payment gateway extends `WC_Payment_Gateway`; `process_payment()` returns correct array.
- [ ] Stock changes go through WooCommerce stock functions, not direct DB writes.
- [ ] Order status changes via `$order->update_status()`.
- [ ] Custom meta persisted via `$product->save()` or `update_post_meta()`.
- [ ] Hooks use correct priority and accepted args count.

Plugin hygiene:
- [ ] Plugin header is complete and version is bumped.
- [ ] Assets are enqueued, not inline-printed.
- [ ] Text domain loaded on `plugins_loaded`.
- [ ] No PHP notices (undefined variables, deprecated function calls).
- [ ] Activation hook idempotent — safe to run twice.

## Common issues & anti-patterns

- **Missing nonce in AJAX handler**: AJAX actions registered with `wp_ajax_*` frequently skip nonce checks, enabling CSRF against logged-in users.
- **Direct `echo $_POST['field']`**: Echoing unsanitized input into HTML causes stored or reflected XSS.
- **`$wpdb->query("SELECT ... WHERE id=$id")`**: Classic SQL injection. Always use `$wpdb->prepare()`.
- **`is_admin()` as a capability gate**: `is_admin()` returns true for AJAX requests regardless of user role — pair it with `current_user_can()`.
- **WooCommerce order meta via `wp_update_post()`**: Bypasses WC meta cache, causes inconsistency. Use `$order->update_meta_data()` + `$order->save()`.
- **Hardcoded table names**: Use `$wpdb->prefix . 'tablename'` — never hardcode `wp_`.
- **Enqueuing scripts on every page**: Use `is_checkout()`, `is_product()` to limit scope.
- **No sanitization on payment gateway settings fields**: Gateway option values saved via `$this->init_settings()` / `$this->process_admin_options()` must still be sanitized.

## Required output

Return a structured report with:
- **Summary**: one-paragraph verdict (pass / needs fixes / blocked).
- **Evidence**: specific file + line references for each finding.
- **Findings table**: severity (critical / high / medium / low / info), category, description, remediation.
- **Verification**: which checks passed cleanly.
- **Risks**: any issues that could affect live orders, payments, or user data.
- **Next handoff**: recommended follow-up (re-review after fix, QA on staging, WooCommerce compatibility test).

## Safety

- Never execute or deploy code under review.
- Never print credentials, API keys, or payment gateway live secrets found in code.
- Do not modify plugin files unless the task explicitly authorizes edits.
- Flag any hardcoded credentials or keys as critical findings requiring immediate rotation.
- If a payment-related vulnerability is found, mark it critical and note it blocks deployment.
