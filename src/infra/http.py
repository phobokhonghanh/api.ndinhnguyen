import json
from typing import Any


async def fetch_json(url: str, headers: dict[str, str] | None = None) -> Any:
    """
    Fetches JSON from a URL, using native Cloudflare js.fetch in workers,
    and falling back to httpx in development/test environments.
    """
    try:
        # pyrefly: ignore [missing-import]
        from js import fetch, Headers

        js_headers = None
        if headers:
            js_headers = Headers.new()
            for k, v in headers.items():
                js_headers.append(k, v)

        options = {}
        if js_headers:
            options["headers"] = js_headers

        response = await fetch(url, **options)
        if response.status != 200:
            raise RuntimeError(f"HTTP error {response.status}")
        text = await response.text()
        return json.loads(text)
    except ImportError:
        import httpx

        async with httpx.AsyncClient() as client:
            resp = await client.get(url, headers=headers)
            resp.raise_for_status()
            return resp.json()
