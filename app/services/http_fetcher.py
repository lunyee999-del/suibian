from __future__ import annotations

import gzip
import subprocess
from urllib import request
from urllib.error import URLError, HTTPError


class HttpFetcher:
    def __init__(self, timeout: int = 20) -> None:
        self.timeout = timeout
        self.headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/123.0.0.0 Safari/537.36"
            ),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8,ru;q=0.7",
            "Accept-Encoding": "gzip",
            "Cache-Control": "no-cache",
        }

    def get_text(self, url: str) -> str:
        try:
            return self._get_text_urllib(url)
        except (URLError, HTTPError, TimeoutError, OSError):
            return self._get_text_curl(url)

    def _get_text_urllib(self, url: str) -> str:
        req = request.Request(url, headers=self.headers, method="GET")
        with request.urlopen(req, timeout=self.timeout) as response:
            raw = response.read()
            encoding = response.headers.get("Content-Encoding", "")
            if "gzip" in encoding.lower():
                raw = gzip.decompress(raw)
            charset = response.headers.get_content_charset() or "utf-8"
            try:
                return raw.decode(charset, errors="replace")
            except LookupError:
                return raw.decode("utf-8", errors="replace")

    def _get_text_curl(self, url: str) -> str:
        command = [
            "curl.exe",
            "-L",
            "--compressed",
            "--max-time",
            str(self.timeout),
            "-A",
            self.headers["User-Agent"],
            "-H",
            f"Accept-Language: {self.headers['Accept-Language']}",
            "-H",
            f"Accept: {self.headers['Accept']}",
            url,
        ]
        completed = subprocess.run(
            command,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
        if completed.returncode != 0:
            raise RuntimeError(completed.stderr.strip() or f"curl failed for {url}")
        return completed.stdout
