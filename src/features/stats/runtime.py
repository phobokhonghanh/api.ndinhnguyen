from .validators import validate_runtime_bytes


class RuntimeHandler:
    async def write(self, store, key: str, file) -> None:
        content = await file.read()
        validate_runtime_bytes(content)
        await store.put(key, content)
