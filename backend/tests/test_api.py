import json
import unittest

from fastapi.testclient import TestClient

from app import main
from app.brand_registry import Brand, BrandRegistry
from app.processor import InMemoryReceiptStore, WebhookProcessor
from app.security import calculate_shopify_hmac


SECRET = "http-test-secret"
SHOP = "cellar-drop-demo.myshopify.com"


class WebhookApiTests(unittest.TestCase):
    def setUp(self) -> None:
        registry = BrandRegistry(
            [Brand("cellar_drop", "Cellar Drop", SHOP, "CELLAR", "SECRET_CELLAR")]
        )
        main.processor = WebhookProcessor(
            {"cellar_drop": SECRET}, registry, InMemoryReceiptStore()
        )
        self.client = TestClient(main.app)

    def test_accepts_a_signed_order(self) -> None:
        body = json.dumps(
            {
                "admin_graphql_api_id": "gid://shopify/Order/123",
                "name": "#1001",
                "currency": "USD",
                "current_total_price": "149.00",
            },
            separators=(",", ":"),
        ).encode()
        response = self.client.post(
            "/webhooks/shopify",
            content=body,
            headers={
                "Content-Type": "application/json",
                "X-Shopify-Hmac-Sha256": calculate_shopify_hmac(body, SECRET),
                "X-Shopify-Shop-Domain": SHOP,
                "X-Shopify-Webhook-Id": "4ea6be33-4f85-4da7-9b7a-f22bc29f2e34",
                "X-Shopify-Topic": "orders/create",
            },
        )
        self.assertEqual(200, response.status_code)
        self.assertEqual({"status": "accepted", "brand": "cellar_drop"}, response.json())

    def test_rejects_an_unsigned_order(self) -> None:
        response = self.client.post(
            "/webhooks/shopify",
            content=b"{}",
            headers={
                "X-Shopify-Shop-Domain": SHOP,
                "X-Shopify-Webhook-Id": "31a72e55-e3f1-4d51-8f7e-b5e46b9e94e1",
                "X-Shopify-Topic": "orders/create",
            },
        )
        self.assertEqual(401, response.status_code)


if __name__ == "__main__":
    unittest.main()
