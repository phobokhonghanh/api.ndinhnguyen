import json

from features.stats.validators import validate_runtime_bytes


class RuntimeHandler:
    async def write(self, store, key: str, file, machine_id: str) -> None:
        content = await file.read()
        validate_runtime_bytes(content)

        text = content.decode("utf-8")
        parsed_data = [line.strip() for line in text.splitlines() if line.strip()]

        processed = {
            "machine_id": machine_id,
            "data": parsed_data,
        }
        output = json.dumps(processed, ensure_ascii=False) + "\n"
        await store.put(key, output.encode("utf-8"))
