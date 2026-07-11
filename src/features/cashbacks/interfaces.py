from typing import Any, Protocol, runtime_checkable

@runtime_checkable
class PlatformAdapter(Protocol):
    def map_status(self, raw_status: Any) -> str:
        """
        Maps platform-specific status (int or str) to generic cashback status:
        'pending', 'completed', 'approved', 'cancelled'.
        """
        ...

    def extract_orders(self, record: dict[str, Any]) -> list[dict[str, Any]]:
        """
        Extracts standardized order details from a raw platform conversion record.
        Returns a list of dicts:
        {
            "checkout_id": str,
            "order_id": str,
            "cashback_amount": float,
            "conversion_data": dict[str, Any]
        }
        """
        ...

class PlatformRegistry:
    _adapters: dict[str, PlatformAdapter] = {}

    @classmethod
    def register(cls, platform: str, adapter: PlatformAdapter) -> None:
        cls._adapters[platform.lower()] = adapter

    @classmethod
    def get(cls, platform: str) -> PlatformAdapter:
        adapter = cls._adapters.get(platform.lower())
        if not adapter:
            raise ValueError(f"No platform adapter registered for platform: {platform}")
        return adapter
