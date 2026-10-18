from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Mapping, Protocol

from .brand_registry import BrandRegistry, UnknownShopError
from .security import verify_shopify_hmac


class InvalidWebhookError(ValueError):
    pass


class UnsupportedTopicError(ValueError):
    pass


class ReceiptStore(Protocol):
    def claim(self, shop_domain: str, webhook_id: str) -> bool:
        """Atomically return True only for the first delivery of this shop/id pair."""


class InMemoryReceiptStore:
    def __init__(self) -> None:
        self._seen: set[tuple[str, str]] = set()

    def claim(self, shop_domain: str, webhook_id: str) -> bool:
        key = (shop_domain, webhook_id)
        if key in self._seen:
            return False
        self._seen.add(key)
        return True


@dataclass(frozen=True)
class NormalizedOrder:
    brand_key: str
    shop_domain: str
    oms_channel: str
    shopify_order_id: str
    order_name: str
    currency: str
    total: str
    email: str | None


@dataclass(frozen=True)
class ProcessResult:
    status: str
    order: NormalizedOrder | None = None


class WebhookProcessor:
    def __init__(
        self,
        secrets: Mapping[str, str],
        registry: BrandRegistry,
        receipts: ReceiptStore,
    ) -> None:
        self._secrets = secrets
        self._registry = registry
        self._receipts = receipts

    def process(self, raw_body: bytes, headers: Mapping[str, str]) -> ProcessResult:
        normalized_headers = {key.lower(): value for key, value in headers.items()}
        shop = normalized_headers.get("x-shopify-shop-domain", "")
        webhook_id = normalized_headers.get("x-shopify-webhook-id", "")
        topic = normalized_headers.get("x-shopify-topic", "")
        if not shop or not webhook_id:
            raise InvalidWebhookError("missing shop or webhook delivery id")
        if topic != "orders/create":
            raise UnsupportedTopicError(f"unsupported topic: {topic}")

        # HMAC covers the body, not this header. A shop-specific secret binds both.
        try:
            brand = self._registry.resolve(shop)
        except UnknownShopError as exc:
            raise InvalidWebhookError("invalid Shopify delivery") from exc

        supplied_hmac = normalized_headers.get("x-shopify-hmac-sha256", "")
        secret = self._secrets.get(brand.key, "")
        if not verify_shopify_hmac(raw_body, supplied_hmac, secret):
            raise InvalidWebhookError("invalid Shopify delivery")

        try:
            payload = json.loads(raw_body)
            order = NormalizedOrder(
                brand_key=brand.key,
                shop_domain=brand.shop_domain,
                oms_channel=brand.oms_channel,
                shopify_order_id=str(payload["admin_graphql_api_id"]),
                order_name=str(payload["name"]),
                currency=str(payload["currency"]),
                total=str(payload["current_total_price"]),
                email=payload.get("email"),
            )
        except (json.JSONDecodeError, KeyError, TypeError) as exc:
            raise InvalidWebhookError("malformed order payload") from exc

        # Do not poison the idempotency key until validation succeeds.
        if not self._receipts.claim(brand.shop_domain, webhook_id):
            return ProcessResult(status="duplicate")

        return ProcessResult(status="accepted", order=order)

