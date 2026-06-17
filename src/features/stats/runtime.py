import json

from features.stats.validators import validate_runtime_bytes


class RuntimeHandler:
    async def write(self, store, key: str, file, machine_id: str) -> None:
        content = await file.read()
        validate_runtime_bytes(content)

        text = content.decode("utf-8")
        try:
            # First try parsing the entire file as a single JSON array/object
            parsed = json.loads(text)
            if isinstance(parsed, list):
                parsed_data = parsed
            else:
                parsed_data = [parsed]
        except json.JSONDecodeError:
            # Otherwise parse as line-by-line JSON/JSONL, fallback to raw string line
            parsed_data = []
            for line in text.splitlines():
                line = line.strip()
                if not line:
                    continue
                try:
                    parsed_data.append(json.loads(line))
                except json.JSONDecodeError:
                    parsed_data.append(line)

        processed = {
            "machine_id": machine_id,
            "data": parsed_data,
        }
        output = json.dumps(processed, ensure_ascii=False) + "\n"
        await store.put(key, output.encode("utf-8"))
