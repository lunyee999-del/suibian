from __future__ import annotations

import json
from urllib import request


class BrowserFetchClient:
    def __init__(self, base_url: str) -> None:
        self.base_url = base_url.rstrip("/")

    def fetch_page(self, url: str, wait_ms: int = 5000) -> dict:
        body = json.dumps({"url": url, "wait_ms": wait_ms}).encode("utf-8")
        req = request.Request(
            f"{self.base_url}/internal/fetch/page",
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with request.urlopen(req, timeout=90) as response:
            return json.loads(response.read().decode("utf-8"))
