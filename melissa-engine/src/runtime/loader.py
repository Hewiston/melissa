import httpx

async def post_json(url: str, data: dict) -> dict:
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.post(url, json=data)
        r.raise_for_status()
        return r.json()

async def get_bytes(url: str, etag: str | None = None) -> tuple[int, bytes | None, str | None]:
    headers = {}
    if etag:
        headers["If-None-Match"] = etag
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.get(url, headers=headers)
        if r.status_code == 304:
            return 304, None, None
        r.raise_for_status()
        return r.status_code, r.content, r.headers.get("ETag")
