from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import requests
from playwright.sync_api import sync_playwright

from social_crawl_skill.browser_runtime import BrowserRuntime
from social_crawl_skill.query_planner import QueryPlanner


class KuaishouCrawler:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.runtime = BrowserRuntime(root)
        self.base_output_dir = root / "outputs" / "raw_crawl" / "kuaishou"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36 Edg/146.0.0.0",
            "Referer": "https://www.kuaishou.com/",
            "Accept": "*/*",
            "Accept-Encoding": "identity",
            "Connection": "keep-alive",
        }

    def build_material_queries(self) -> list[str]:
        plan = QueryPlanner(self.root).generate()
        query_groups = plan.get("query_groups", {})
        ordered: list[str] = []
        for group_name in ["pain_points", "competitor_style", "market_scene", "product_core"]:
            for query in query_groups.get(group_name, []):
                if query not in ordered:
                    ordered.append(query)
        return ordered

    def crawl_search_videos_multi(self, queries: list[str], limit: int = 5) -> dict[str, Any]:
        base_query = queries[0] if queries else "kuaishou"
        output_dir = self.base_output_dir / f"search_videos_multi_{self._slug(base_query)}"
        output_dir.mkdir(parents=True, exist_ok=True)
        all_items: list[dict[str, Any]] = []
        attempts: list[dict[str, Any]] = []

        for query in queries:
            result = self._capture_search_feed(query, output_dir / self._slug(query))
            items = result.get("items", [])
            unique_new = []
            for item in items:
                if any(existing["photo_id"] == item["photo_id"] for existing in all_items):
                    continue
                all_items.append(item)
                unique_new.append(item)
                if len(all_items) >= limit:
                    break
            attempts.append({"query": query, "count": len(unique_new)})
            if len(all_items) >= limit:
                break

        selected = all_items[:limit]
        self._download_videos(selected, output_dir)
        payload = {
            "platform": "kuaishou",
            "queries": queries,
            "mode": "search_videos_multi_query",
            "count": len(selected),
            "attempts": attempts,
            "items": selected,
        }
        (output_dir / "samples.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        return payload

    def _capture_search_feed(self, query: str, output_dir: Path) -> dict[str, Any]:
        output_dir.mkdir(parents=True, exist_ok=True)
        playwright, ctx, page = self.runtime.connect_existing("kuaishou")
        captured = []
        try:
            def on_response(resp):
                if "/rest/v/search/feed" in resp.url:
                    try:
                        captured.append({"url": resp.url, "status": resp.status, "body": resp.json()})
                    except Exception:
                        captured.append({"url": resp.url, "status": resp.status, "body": None})
            page.on("response", on_response)
            page.goto("https://www.kuaishou.com/new-reco", wait_until="domcontentloaded")
            page.wait_for_timeout(3000)
            page.locator("input").first.fill(query)
            page.keyboard.press("Enter")
            page.wait_for_timeout(10000)
            (output_dir / "page.html").write_text(page.content(), encoding="utf-8")
        finally:
            playwright.stop()
        (output_dir / "raw_responses.json").write_text(json.dumps(captured, ensure_ascii=False, indent=2), encoding="utf-8")

        items = []
        for block in captured:
            body = block.get("body") or {}
            feeds = body.get("feeds") or ((body.get("data") or {}).get("feeds") or [])
            for feed in feeds:
                if not isinstance(feed, dict):
                    continue
                photo = feed.get("photo") or {}
                author = feed.get("author") or {}
                photo_id = photo.get("id") or ""
                if not photo_id or any(existing["photo_id"] == photo_id for existing in items):
                    continue
                photo_urls = photo.get("photoUrls") or []
                first_video = photo_urls[0]["url"] if photo_urls else ""
                items.append(
                    {
                        "photo_id": photo_id,
                        "title": photo.get("caption", ""),
                        "author_name": author.get("name", ""),
                        "author_id": author.get("id", ""),
                        "like_count": photo.get("likeCount", ""),
                        "view_count": photo.get("viewCount", ""),
                        "comment_count": photo.get("commentCount", ""),
                        "cover_url": photo.get("coverUrl", ""),
                        "video_url": first_video,
                        "detail_url": f"https://www.kuaishou.com/short-video/{photo_id}",
                    }
                )
        return {"query": query, "items": items}

    def _download_videos(self, items: list[dict[str, Any]], output_dir: Path) -> None:
        downloads_dir = output_dir / "downloads"
        downloads_dir.mkdir(parents=True, exist_ok=True)
        completed = []
        for idx, item in enumerate(items, start=1):
            try:
                folder = downloads_dir / f"{idx:02d}_{item['photo_id']}"
                folder.mkdir(parents=True, exist_ok=True)
                (folder / "title.txt").write_text(item["title"], encoding="utf-8")
                (folder / "metadata.json").write_text(json.dumps(item, ensure_ascii=False, indent=2), encoding="utf-8")
                if item["cover_url"]:
                    cover_path = folder / "cover.jpg"
                    with requests.get(item["cover_url"], headers=self.headers, stream=True, timeout=120) as r:
                        r.raise_for_status()
                        with open(cover_path, "wb") as f:
                            for chunk in r.iter_content(chunk_size=1024 * 128):
                                if chunk:
                                    f.write(chunk)
                video_path = folder / f"{self._safe_name(item['title'])}.mp4"
                with requests.get(item["video_url"], headers=self.headers, stream=True, timeout=120) as r:
                    r.raise_for_status()
                    with open(video_path, "wb") as f:
                        for chunk in r.iter_content(chunk_size=1024 * 256):
                            if chunk:
                                f.write(chunk)
                item["rank"] = idx
                item["download_dir"] = str(folder)
                item["video_path"] = str(video_path)
                completed.append(item)
            except Exception:
                continue
        (output_dir / "downloads_summary.json").write_text(json.dumps({"count": len(completed), "items": completed}, ensure_ascii=False, indent=2), encoding="utf-8")

    def _slug(self, text: str) -> str:
        slug = re.sub(r"[^0-9A-Za-z\u4e00-\u9fff]+", "_", text).strip("_")
        return slug or "query"

    def _safe_name(self, text: str) -> str:
        text = re.sub(r'[\\\\/:*?"<>|\r\n]+', "_", text)
        return text[:80].strip(" ._") or "untitled"
