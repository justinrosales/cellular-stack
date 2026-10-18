import base64
import hashlib
import hmac


def calculate_shopify_hmac(raw_body: bytes, secret: str) -> str:
    digest = hmac.new(secret.encode("utf-8"), raw_body, hashlib.sha256).digest()
    return base64.b64encode(digest).decode("ascii")


def verify_shopify_hmac(raw_body: bytes, supplied_hmac: str, secret: str) -> bool:
    """Compare encoded digests in constant time; never parse/re-serialize the body first."""
    if not supplied_hmac or not secret:
        return False
    expected = calculate_shopify_hmac(raw_body, secret)
    return hmac.compare_digest(expected, supplied_hmac.strip())

