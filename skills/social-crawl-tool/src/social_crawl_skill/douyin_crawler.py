from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import requests

from social_crawl_skill.browser_runtime import BrowserRuntime
from social_crawl_skill.query_planner import QueryPlanner


class DouyinCrawler:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.profile_dir = root / "runtime" / "browser_profiles" / "douyin"
        self.base_output_dir = root / "outputs" / "raw_crawl" / "douyin"
        self.runtime = BrowserRuntime(root)
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36 Edg/146.0.0.0",
            "Referer": "https://www.douyin.com/",
            "Accept": "*/*",
            "Accept-Encoding": "identity",
            "Connection": "keep-alive",
        }

    def crawl_image_posts(self, query: str, limit: int = 5) -> dict[str, Any]:
        output_dir = self.base_output_dir / f"image_posts_{self._slug(query)}"
        output_dir.mkdir(parents=True, exist_ok=True)
        raw_responses = self._capture_search_responses(query, output_dir)
        image_posts = self._extract_image_posts(raw_responses)[:limit]
        self._download_image_posts(image_posts, output_dir)
        payload = {
            "platform": "douyin",
            "query": query,
            "mode": "image_posts_only",
            "count": len(image_posts),
            "items": image_posts,
        }
        (output_dir / "samples.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        return payload

    def crawl_image_posts_multi(self, queries: list[str], limit: int = 5) -> dict[str, Any]:
        base_query = queries[0] if queries else "douyin"
        output_dir = self.base_output_dir / f"image_posts_multi_{self._slug(base_query)}"
        output_dir.mkdir(parents=True, exist_ok=True)
        all_items: list[dict[str, Any]] = []
        attempts: list[dict[str, Any]] = []

        for query in queries:
            raw_responses = self._capture_search_responses(query, output_dir / self._slug(query))
            items = self._extract_image_posts(raw_responses)
            unique_new = []
            for item in items:
                if any(existing["aweme_id"] == item["aweme_id"] for existing in all_items):
                    continue
                all_items.append(item)
                unique_new.append(item)
                if len(all_items) >= limit:
                    break
            attempts.append({"query": query, "count": len(unique_new)})
            if len(all_items) >= limit:
                break

        selected = all_items[:limit]
        self._download_image_posts(selected, output_dir)
        payload = {
            "platform": "douyin",
            "queries": queries,
            "mode": "image_posts_multi_query",
            "count": len(selected),
            "attempts": attempts,
            "items": selected,
        }
        (output_dir / "samples.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        return payload

    def crawl_video_posts_multi(self, queries: list[str], limit: int = 5) -> dict[str, Any]:
        base_query = queries[0] if queries else "douyin"
        output_dir = self.base_output_dir / f"video_posts_multi_{self._slug(base_query)}"
        output_dir.mkdir(parents=True, exist_ok=True)
        all_items: list[dict[str, Any]] = []
        attempts: list[dict[str, Any]] = []

        for query in queries:
            raw_responses = self._capture_search_responses(query, output_dir / self._slug(query))
            items = self._extract_video_posts(raw_responses)
            unique_new = []
            for item in items:
                if any(existing["aweme_id"] == item["aweme_id"] for existing in all_items):
                    continue
                all_items.append(item)
                unique_new.append(item)
                if len(all_items) >= limit:
                    break
            attempts.append({"query": query, "count": len(unique_new)})
            if len(all_items) >= limit:
                break

        selected = all_items[:limit]
        self._download_video_posts(selected, output_dir)
        payload = {
            "platform": "douyin",
            "queries": queries,
            "mode": "video_posts_multi_query",
            "count": len(selected),
            "attempts": attempts,
            "items": selected,
        }
        (output_dir / "samples.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        return payload

    def build_material_queries(self) -> list[str]:
        plan = QueryPlanner(self.root).generate()
        query_groups = plan.get("query_groups", {})
        ordered: list[str] = []
        for group_name in ["pain_points", "competitor_style", "market_scene", "product_core"]:
            for query in query_groups.get(group_name, []):
                if query not in ordered:
                    ordered.append(query)
        return ordered

    def _capture_search_responses(self, query: str, output_dir: Path) -> list[dict[str, Any]]:
        output_dir.mkdir(parents=True, exist_ok=True)
        captured: list[dict[str, Any]] = []
        playwright, context, page = self.runtime.connect_existing("douyin")
        try:

            def on_response(resp) -> None:
                url = resp.url
                if "/aweme/v1/web/general/search/stream/" in url or "/aweme/v1/web/general/search/single/" in url:
                    try:
                        body = resp.json()
                    except Exception:
                        body = None
                    captured.append({"url": url, "status": resp.status, "body": body})

            page.on("response", on_response)
            page.goto("https://www.douyin.com/", wait_until="domcontentloaded")
            page.wait_for_timeout(5000)
            page.locator("input").first.fill(query)
            page.keyboard.press("Enter")
            page.wait_for_timeout(15000)
            (output_dir / "page.html").write_text(page.content(), encoding="utf-8")
            try:
                page.screenshot(path=str(output_dir / "page.png"), full_page=True, timeout=5000)
            except Exception:
                pass
        finally:
            playwright.stop()
        (output_dir / "raw_responses.json").write_text(json.dumps(captured, ensure_ascii=False, indent=2), encoding="utf-8")
        return captured

    def _extract_image_posts(self, raw_responses: list[dict[str, Any]]) -> list[dict[str, Any]]:
        items: list[dict[str, Any]] = []
        for block in raw_responses:
            body = block.get("body")
            if not isinstance(body, dict):
                continue
            data = body.get("data")
            if isinstance(data, list):
                rows = data
            elif isinstance(data, dict):
                rows = data.get("data") or []
            else:
                rows = []
            if not isinstance(rows, list):
                continue
            for row in rows:
                if not isinstance(row, dict):
                    continue
                aweme = row.get("aweme_info") or row
                if not isinstance(aweme, dict):
                    continue
                aweme_id = aweme.get("aweme_id") or ""
                if not aweme_id or any(existing["aweme_id"] == aweme_id for existing in items):
                    continue
                images = aweme.get("images") or []
                if not images:
                    continue
                author = aweme.get("author") or {}
                stat = aweme.get("statistics") or {}
                image_urls = []
                for image in images:
                    if not isinstance(image, dict):
                        continue
                    download_list = image.get("download_url_list") or []
                    url_list = image.get("url_list") or []
                    image_urls.append((download_list or url_list or [""])[0])
                items.append(
                    {
                        "aweme_id": aweme_id,
                        "title": (aweme.get("desc") or "").strip(),
                        "author_nickname": author.get("nickname", ""),
                        "author_sec_uid": author.get("sec_uid", ""),
                        "like_count": stat.get("digg_count", ""),
                        "comment_count": stat.get("comment_count", ""),
                        "share_count": stat.get("share_count", ""),
                        "collect_count": stat.get("collect_count", ""),
                        "detail_url": f"https://www.douyin.com/video/{aweme_id}",
                        "image_urls": image_urls,
                    }
                )
        return items

    def _extract_video_posts(self, raw_responses: list[dict[str, Any]]) -> list[dict[str, Any]]:
        items: list[dict[str, Any]] = []
        for block in raw_responses:
            body = block.get("body")
            if not isinstance(body, dict):
                continue
            data = body.get("data")
            if isinstance(data, list):
                rows = data
            elif isinstance(data, dict):
                rows = data.get("data") or []
            else:
                rows = []
            if not isinstance(rows, list):
                continue
            for row in rows:
                if not isinstance(row, dict):
                    continue
                aweme = row.get("aweme_info") or row
                if not isinstance(aweme, dict):
                    continue
                aweme_id = aweme.get("aweme_id") or ""
                if not aweme_id or any(existing["aweme_id"] == aweme_id for existing in items):
                    continue
                if aweme.get("images"):
                    continue
                author = aweme.get("author") or {}
                stat = aweme.get("statistics") or {}
                video = aweme.get("video") or {}
                play_list = (video.get("play_addr") or {}).get("url_list") or []
                cover_list = (video.get("cover") or {}).get("url_list") or []
                items.append(
                    {
                        "aweme_id": aweme_id,
                        "title": (aweme.get("desc") or "").strip(),
                        "author_nickname": author.get("nickname", ""),
                        "author_sec_uid": author.get("sec_uid", ""),
                        "like_count": stat.get("digg_count", ""),
                        "comment_count": stat.get("comment_count", ""),
                        "share_count": stat.get("share_count", ""),
                        "collect_count": stat.get("collect_count", ""),
                        "detail_url": f"https://www.douyin.com/video/{aweme_id}",
                        "video_url": play_list[0] if play_list else "",
                        "cover_url": cover_list[0] if cover_list else "",
                    }
                )
        return items

    def _download_image_posts(self, items: list[dict[str, Any]], output_dir: Path) -> None:
        posts_dir = output_dir / "downloads"
        posts_dir.mkdir(parents=True, exist_ok=True)

        def download_post(index: int, item: dict[str, Any]) -> dict[str, Any]:
            folder = posts_dir / f"{index:02d}_{item['aweme_id']}"
            folder.mkdir(parents=True, exist_ok=True)
            (folder / "title.txt").write_text(item["title"], encoding="utf-8")
            (folder / "metadata.json").write_text(json.dumps(item, ensure_ascii=False, indent=2), encoding="utf-8")
            local_images = []
            for img_index, image_url in enumerate(item["image_urls"], start=1):
                ext = ".jpg"
                if ".webp" in image_url:
                    ext = ".webp"
                image_path = folder / f"image_{img_index:02d}{ext}"
                with requests.get(image_url, headers=self.headers, stream=True, timeout=120) as response:
                    response.raise_for_status()
                    with open(image_path, "wb") as handle:
                        for chunk in response.iter_content(chunk_size=1024 * 128):
                            if chunk:
                                handle.write(chunk)
                local_images.append(str(image_path))
            item["rank"] = index
            item["download_dir"] = str(folder)
            item["local_images"] = local_images
            return item

        completed = []
        for idx, item in enumerate(items, start=1):
            try:
                completed.append(download_post(idx, item))
            except Exception:
                continue
        completed.sort(key=lambda item: item["rank"])
        (output_dir / "downloads_summary.json").write_text(
            json.dumps({"count": len(completed), "items": completed}, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def _download_video_posts(self, items: list[dict[str, Any]], output_dir: Path) -> None:
        posts_dir = output_dir / "downloads"
        posts_dir.mkdir(parents=True, exist_ok=True)

        completed = []
        for idx, item in enumerate(items, start=1):
            try:
                folder = posts_dir / f"{idx:02d}_{item['aweme_id']}"
                folder.mkdir(parents=True, exist_ok=True)
                (folder / "title.txt").write_text(item["title"], encoding="utf-8")
                (folder / "metadata.json").write_text(json.dumps(item, ensure_ascii=False, indent=2), encoding="utf-8")
                if item["cover_url"]:
                    cover_path = folder / "cover.jpg"
                    try:
                        with requests.get(item["cover_url"], headers=self.headers, stream=True, timeout=120) as response:
                            response.raise_for_status()
                            with open(cover_path, "wb") as handle:
                                for chunk in response.iter_content(chunk_size=1024 * 128):
                                    if chunk:
                                        handle.write(chunk)
                    except Exception:
                        pass
                video_path = folder / f"{self._safe_name(item['title'])}.mp4"
                with requests.get(item["video_url"], headers=self.headers, stream=True, timeout=120) as response:
                    response.raise_for_status()
                    with open(video_path, "wb") as handle:
                        for chunk in response.iter_content(chunk_size=1024 * 256):
                            if chunk:
                                handle.write(chunk)
                item["rank"] = idx
                item["download_dir"] = str(folder)
                item["video_path"] = str(video_path)
                completed.append(item)
            except Exception:
                continue
        (output_dir / "downloads_summary.json").write_text(
            json.dumps({"count": len(completed), "items": completed}, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def _safe_name(self, text: str) -> str:
        text = re.sub(r'[\\\\/:*?"<>|\r\n]+', "_", text)
        return text[:80].strip(" ._") or "untitled"

    def _slug(self, text: str) -> str:
        slug = re.sub(r"[^0-9A-Za-z\u4e00-\u9fff]+", "_", text).strip("_")
        return slug or "query"
