from typing import Any


class R2ObjectStore:
    def __init__(self, bucket: Any):
        self.bucket = bucket

    async def read_text(self, key: str) -> str:
        obj = await self.bucket.get(key)
        if obj is None:
            return ""
        text = getattr(obj, "text", None)
        if callable(text):
            result = text()
            if hasattr(result, "__await__"):
                return await result  # type: ignore
            return result
        body = getattr(obj, "body", b"")
        if isinstance(body, bytes):
            return body.decode("utf-8")
        return str(body)

    async def put(self, key: str, body: bytes | str) -> None:
        await self.bucket.put(key, body)
