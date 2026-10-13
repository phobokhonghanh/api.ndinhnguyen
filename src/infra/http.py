import json
from typing import Any


class HttpError(RuntimeError):
    def __init__(self, status: int, url: str):
        super().__init__(f"HTTP error {status} for {url}")
        self.status = status
        self.url = url


async def _request_json(
    method: str,
    url: str,
    headers: dict[str, str] | None = None,
    body: str | None = None,
) -> Any:
    try:
        # pyrefly: ignore [missing-import]
        from js import fetch as js_fetch, Headers as JsHeaders

        options: dict[str, Any] = {"method": method}
        if headers:
            js_headers = JsHeaders.new()
            for k, v in headers.items():
                js_headers.append(k, v)
            options["headers"] = js_headers
        if body is not None:
            options["body"] = body

        response = await js_fetch(url, **options)
        status = getattr(response, "status", 200)
        is_ok = getattr(response, "ok", 200 <= status < 300)
        if not is_ok:
            raise HttpError(status, url)
        return json.loads(await response.text())
    except ImportError:
        import httpx

        async with httpx.AsyncClient() as client:
            resp = await client.request(method, url, headers=headers, content=body)
            if not resp.is_success:
                raise HttpError(resp.status_code, url)
            return resp.json()


async def fetch_json(url: str, headers: dict[str, str] | None = None) -> Any:
    return await _request_json("GET", url, headers)


async def post_json(
    url: str,
    data: dict[str, Any] | None = None,
    headers: dict[str, str] | None = None,
) -> Any:
    req_headers = {"Content-Type": "application/json", **(headers or {})}
    body = json.dumps(data) if data is not None else None
    return await _request_json("POST", url, req_headers, body)
