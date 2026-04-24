from __future__ import annotations

import json
from pathlib import Path

from app.collectors.base import BaseCollector
from app.core.settings import Settings
from app.domain.models import RawItem
from app.services.browser_fetch_client import BrowserFetchClient
from app.services.html_page_parser import ParsedPage, parse_html_page
from app.services.http_fetcher import HttpFetcher
from app.services.keyword_extractor import extract_keywords


class RealExternalCollector(BaseCollector):
    def __init__(self, config_path: Path, settings: Settings) -> None:
        self.config_path = config_path
        self.settings = settings
        self.http_fetcher = HttpFetcher()
        self.browser_fetch_client = BrowserFetchClient(settings.browser_fetcher_url)

    def fetch(self, limit: int) -> list[RawItem]:
        source_items = json.loads(self.config_path.read_text(encoding="utf-8"))
        enabled_sources = [item for item in source_items if item.get("enabled", True)]
        raw_items: list[RawItem] = []

        for source in enabled_sources[:limit]:
            try:
                parsed = self._fetch_parsed_page(source)
                raw_items.append(self._build_raw_item(source, parsed))
            except Exception as exc:
                raw_items.append(
                    RawItem(
                        source_name=source["name"],
                        source_url=source["url"],
                        title=source.get("fallback_title", source["name"]),
                        summary=f"fetch failed: {exc}",
                        keywords=source.get("fallback_keywords", ["Ozon", "trend"]),
                    )
                )
        return raw_items

    def _fetch_parsed_page(self, source: dict) -> ParsedPage:
        fetch_mode = source.get("fetch_mode", "http")
        if fetch_mode == "browser":
            payload = self.browser_fetch_client.fetch_page(
                source["url"],
                wait_ms=int(source.get("wait_ms", 5000)),
            )
            if not payload.get("success"):
                raise RuntimeError(payload.get("error") or f"browser fetch failed for {source['url']}")
            return ParsedPage(
                title=payload.get("title", ""),
                summary=payload.get("summary", ""),
                headings=payload.get("headings", []),
                paragraphs=payload.get("paragraphs", []),
            )

        html = self.http_fetcher.get_text(source["url"])
        return parse_html_page(html, source["url"])

    def _build_raw_item(self, source: dict, parsed: ParsedPage) -> RawItem:
        title = parsed.title or source.get("fallback_title") or source["name"]
        summary = parsed.summary or source.get("topic_hint") or title
        joined_text = "\n".join(
            [title, summary, " ".join(parsed.headings[:4]), " ".join(parsed.paragraphs[:3])]
        )
        keywords = extract_keywords(
            joined_text,
            preferred=source.get("preferred_keywords", []),
            limit=6,
        )
        return RawItem(
            source_name=source["name"],
            source_url=source["url"],
            title=title,
            summary=summary,
            keywords=keywords,
        )
