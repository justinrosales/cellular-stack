import json
import os
import urllib.request
import uuid

from app.security import calculate_shopify_hmac


secret = os.environ.get("SHOPIFY_SECRET_CELLAR_DROP", "dev-secret")
body = json.dumps(
    {
        "admin_graphql_api_id": "gid://shopify/Order/123",
        "name": "#1001",
        "currency": "USD",
        "current_total_price": "149.00",
        "email": "buyer@example.com",
    },
    separators=(",", ":"),
).encode()

request = urllib.request.Request(
    os.environ.get("WEBHOOK_URL", "http://127.0.0.1:8000/webhooks/shopify"),
    data=body,
    method="POST",
    headers={
        "Content-Type": "application/json",
        "X-Shopify-Hmac-Sha256": calculate_shopify_hmac(body, secret),
        "X-Shopify-Shop-Domain": "cellar-drop-demo.myshopify.com",
        "X-Shopify-Webhook-Id": str(uuid.uuid4()),
        "X-Shopify-Topic": "orders/create",
    },
)
with urllib.request.urlopen(request) as response:
    print(response.read().decode())
