from dataclasses import dataclass


class UnknownShopError(ValueError):
    """Raised when a webhook comes from a shop we did not configure."""


@dataclass(frozen=True)
class Brand:
    key: str
    display_name: str
    shop_domain: str
    oms_channel: str
    secret_env: str


class BrandRegistry:
    def __init__(self, brands: list[Brand]) -> None:
        by_shop = {brand.shop_domain.lower(): brand for brand in brands}
        if len(by_shop) != len(brands):
            raise ValueError("shop domains must be unique across brands")
        self._by_shop = by_shop

    @property
    def brands(self) -> tuple[Brand, ...]:
        return tuple(self._by_shop.values())

    def resolve(self, shop_domain: str) -> Brand:
        normalized = shop_domain.strip().lower()
        try:
            return self._by_shop[normalized]
        except KeyError as exc:
            raise UnknownShopError(f"shop is not allowlisted: {normalized}") from exc


DEFAULT_REGISTRY = BrandRegistry(
    [
        Brand("cellar_drop", "Cellar Drop", "cellar-drop-demo.myshopify.com", "CELLAR", "SHOPIFY_SECRET_CELLAR_DROP"),
        Brand("bright_bubbles", "Bright Bubbles", "bright-bubbles-demo.myshopify.com", "BUBBLES", "SHOPIFY_SECRET_BRIGHT_BUBBLES"),
        Brand("first_pour", "First Pour", "first-pour-demo.myshopify.com", "FIRST", "SHOPIFY_SECRET_FIRST_POUR"),
        Brand("vintner_exchange", "Vintner Exchange", "vintner-exchange-demo.myshopify.com", "VINTNER", "SHOPIFY_SECRET_VINTNER_EXCHANGE"),
    ]
)

