# Cellar Stack

An interview lab for a fictional multi-brand Shopify Plus wine estate. The project is
deliberately small, but it exercises realistic production concerns for the role:

- a FastAPI webhook edge with raw-body HMAC verification;
- idempotent order ingestion and strict shop-to-brand routing;
- a Supabase/Postgres schema for webhook receipts and order projections;
- current Shopify Admin GraphQL mutations and Storefront Cart API drills;
- a JavaScript Shopify Discount Function with executable unit tests;
- a Liquid product-compliance snippet that uses namespaced metafields;
- deployment guardrails that prevent one brand's config reaching another store.

The point is not to pretend this is a complete Shopify app. It is a compact system
you can explain, test, extend, and discuss honestly in an interview.

## Architecture

```text
Shopify stores                         Shopify checkout
  Cellar Drop / Bright Bubbles /             |
  First Pour / Vintner Exchange              |
            | signed webhook               | Function input (GraphQL)
            v                              v
      FastAPI webhook edge          Discount Function (Wasm in Shopify)
       | verify raw-body HMAC        | pure deterministic output
       | allowlist shop -> brand     |
       | deduplicate delivery        |
       v                             v
  Supabase/Postgres projection   buyer sees eligible discount
       |
       +--> OMS / shipping outbox (next exercise)
```

The important boundary is the brand registry plus per-store credentials. Shopify's
HMAC authenticates the raw body but does not cover the shop-domain header. Resolving a
different secret for each configured storefront prevents a valid delivery from being
replayed under another brand. Brand identity is never trusted from JSON or a query
parameter.

## Run the core tests

```bash
cd backend
python3 -m unittest discover -s tests -p 'test_webhooks.py' -v

cd ../shopify-function
npm test
```

After installing the API dependencies, run the full suite with
`uv run python -m pytest -q`.

## Run the API

```bash
cd backend
uv sync --extra dev
SHOPIFY_SECRET_CELLAR_DROP=dev-secret uv run uvicorn app.main:app --reload
```

Then generate a signed fixture and post it:

```bash
uv run python -m scripts.send_fixture
```

The API defaults to an in-memory receipt store so it is easy to demo. The SQL in
`backend/sql/001_init.sql` shows the production persistence shape for Supabase.

## Suggested walkthrough (five minutes)

1. Start in `backend/app/processor.py`: raw bytes are verified before JSON parsing.
2. Show `brand_registry.py`: unknown shops fail closed; payload brand fields are ignored.
3. Run the webhook tests, including tampering, duplicate delivery, and spoofed brand cases.
4. Run the Function tests and explain that Shopify supplies only the GraphQL-selected input.
5. Open `graphql/admin.graphql` and write one mutation from memory.

## What to build next

1. Replace the in-memory receipt store with Supabase and add an outbox worker.
2. Add an OMS adapter with retry/backoff and a deterministic external idempotency key.
3. Scaffold a real Checkout UI Extension with Shopify CLI in a development store.
4. Add PostHog business events and Datadog operational metrics without mixing their roles.
5. Add a matrix CI job that validates each store against exactly one brand config.

See `docs/architecture.md` for the decisions worth discussing.

