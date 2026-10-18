import json
import unittest

from app.brand_registry import Brand, BrandRegistry
from app.processor import InMemoryReceiptStore, InvalidWebhookError, WebhookProcessor
from app.security import calculate_shopify_hmac


SECRET = "test-secret"
SHOP = "cellar-drop-demo.myshopify.com"
OTHER_SHOP = "vintner-exchange-demo.myshopify.com"
OTHER_SECRET = "other-test-secret"


def order_body(**overrides: object) -> bytes:
    payload = {
        "admin_graphql_api_id": "gid://shopify/Order/123",
        "name": "#1001",
        "currency": "USD",
        "current_total_price": "149.00",
        "email": "buyer@example.com",
        # Deliberately hostile: tenant identity must not come from the payload.
        "brand": "vintner_exchange",
    }
    payload.update(overrides)
    return json.dumps(payload, separators=(",", ":")).encode()


def headers(body: bytes, **overrides: str) -> dict[str, str]:
    values = {
        "X-Shopify-Hmac-Sha256": calculate_shopify_hmac(body, SECRET),
        "X-Shopify-Shop-Domain": SHOP,
        "X-Shopify-Webhook-Id": "delivery-1",
        "X-Shopify-Topic": "orders/create",
    }
    values.update(overrides)
    return values


class WebhookProcessorTests(unittest.TestCase):
    def setUp(self) -> None:
        registry = BrandRegistry(
            [
                Brand("cellar_drop", "Cellar Drop", SHOP, "CELLAR", "SECRET_CELLAR"),
                Brand("vintner_exchange", "Vintner Exchange", OTHER_SHOP, "VINTNER", "SECRET_VINTNER"),
            ]
        )
        self.processor = WebhookProcessor(
            {"cellar_drop": SECRET, "vintner_exchange": OTHER_SECRET},
            registry,
            InMemoryReceiptStore(),
        )

    def test_routes_order_by_verified_shop_not_payload_brand(self) -> None:
        body = order_body()
        result = self.processor.process(body, headers(body))
        self.assertEqual("accepted", result.status)
        self.assertEqual("cellar_drop", result.order.brand_key)
        self.assertEqual("CELLAR", result.order.oms_channel)

    def test_rejects_body_tampering(self) -> None:
        original = order_body()
        tampered = order_body(current_total_price="1.00")
        with self.assertRaisesRegex(InvalidWebhookError, "invalid Shopify delivery"):
            self.processor.process(tampered, headers(original))

    def test_duplicate_delivery_is_a_successful_noop(self) -> None:
        body = order_body()
        first = self.processor.process(body, headers(body))
        second = self.processor.process(body, headers(body))
        self.assertEqual("accepted", first.status)
        self.assertEqual("duplicate", second.status)
        self.assertIsNone(second.order)

    def test_unknown_shop_fails_closed(self) -> None:
        body = order_body()
        spoofed = headers(body, **{"X-Shopify-Shop-Domain": "evil.myshopify.com"})
        with self.assertRaisesRegex(InvalidWebhookError, "invalid Shopify delivery"):
            self.processor.process(body, spoofed)

    def test_valid_delivery_cannot_be_replayed_as_another_brand(self) -> None:
        body = order_body()
        replay = headers(body, **{"X-Shopify-Shop-Domain": OTHER_SHOP})
        with self.assertRaisesRegex(InvalidWebhookError, "invalid Shopify delivery"):
            self.processor.process(body, replay)


if __name__ == "__main__":
    unittest.main()

