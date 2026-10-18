create table if not exists public.shopify_webhook_receipts (
  shop_domain text not null,
  webhook_id uuid not null,
  topic text not null,
  api_version text not null,
  received_at timestamptz not null default now(),
  primary key (shop_domain, webhook_id)
);

create table if not exists public.shopify_order_projection (
  shop_domain text not null,
  shopify_order_id text not null,
  brand_key text not null,
  oms_channel text not null,
  order_name text not null,
  currency char(3) not null,
  total numeric(12, 2) not null check (total >= 0),
  source_updated_at timestamptz not null,
  payload jsonb not null,
  projected_at timestamptz not null default now(),
  primary key (shop_domain, shopify_order_id)
);

create table if not exists public.integration_outbox (
  id bigint generated always as identity primary key,
  shop_domain text not null,
  aggregate_id text not null,
  destination text not null check (destination in ('linnworks', 'weship', 'klaviyo')),
  event_type text not null,
  payload jsonb not null,
  attempts integer not null default 0,
  available_at timestamptz not null default now(),
  completed_at timestamptz,
  unique (shop_domain, aggregate_id, destination, event_type)
);

alter table public.shopify_webhook_receipts enable row level security;
alter table public.shopify_order_projection enable row level security;
alter table public.integration_outbox enable row level security;

-- These tables are backend-only. Create no anon/authenticated policies; the service
-- role bypasses RLS. Expose customer-facing data through a narrower view or RPC.

