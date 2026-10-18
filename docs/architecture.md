# Architecture decisions to discuss

## ADR-001: derive tenant identity from the signed shop header

**Decision.** Map `X-Shopify-Shop-Domain` to one immutable brand configuration and its
own webhook secret, then validate the HMAC over the raw request bytes. Unknown shops
and missing credentials fail closed.

**Why.** A payload field, URL parameter, or frontend-supplied brand key can be spoofed.
The Shopify HMAC covers the body, not the shop-domain header. Distinct app credentials
per storefront make a cross-shop replay fail signature verification. Every database key
and downstream idempotency key also includes the shop domain.

**Tradeoff.** This requires separately managed app credentials and rotation per store.
A newly installed store receives errors until it is explicitly added to the registry.
That operational friction is preferable to cross-brand writes. If one shared app must be
installed on every shop, add a per-shop verification step before irreversible downstream
effects and document the weaker header-binding boundary.

## ADR-002: acknowledge durable receipt, then perform slow integrations asynchronously

The demo normalizes synchronously for clarity. In production, the request transaction
would claim the webhook ID, upsert the order projection, and enqueue an outbox row.
Linnworks, WeShip, AfterShip, and Klaviyo workers would consume the outbox. This keeps
the webhook response fast and makes retries observable.

The receipt claim and outbox insert must be atomic. A process-local set is useful only
for a demo; it loses state on restart and does not coordinate replicas.

## ADR-003: treat webhooks as hints and reconcile

Webhooks are at-least-once and not guaranteed to arrive in order. Upserts compare the
source `updated_at` timestamp so an older event cannot overwrite newer state. A periodic
Admin GraphQL reconciliation query repairs missed or poison events.

## ADR-004: shared code, explicit per-brand data and deployment targets

Theme/extension code is shared. Brand settings live in separate validated config files
and store-owned metafields/metaobjects. CI builds a `(commit, brand, shop)` manifest and
requires the shop domain to match the config before deploy. There is no "deploy all"
default. Rollback points to a previously recorded theme/app version per store.

## Observability

- Logs: `shop_domain`, `brand_key`, topic, webhook ID, API version, trace ID; never raw PII.
- Metrics: accepted/duplicate/rejected counts, handler latency, outbox age, attempts,
  per-destination success rate, and reconciliation drift.
- PostHog: buyer/product behavior with a governed event schema.
- Datadog: service health, traces, errors, and operational alerting.

