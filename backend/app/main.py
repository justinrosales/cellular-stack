import os

from fastapi import FastAPI, HTTPException, Request, status

from .brand_registry import DEFAULT_REGISTRY
from .processor import (
    InMemoryReceiptStore,
    InvalidWebhookError,
    UnsupportedTopicError,
    WebhookProcessor,
)

app = FastAPI(title="Cellar Stack webhook edge", version="0.1.0")
processor = WebhookProcessor(
    secrets={brand.key: os.environ.get(brand.secret_env, "") for brand in DEFAULT_REGISTRY.brands},
    registry=DEFAULT_REGISTRY,
    receipts=InMemoryReceiptStore(),
)


@app.get("/healthz")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/webhooks/shopify")
async def shopify_webhook(request: Request) -> dict[str, object]:
    raw_body = await request.body()
    try:
        result = processor.process(raw_body, request.headers)
    except InvalidWebhookError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc
    except UnsupportedTopicError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc

    return {
        "status": result.status,
        "brand": result.order.brand_key if result.order else None,
    }

