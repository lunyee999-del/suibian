from __future__ import annotations

import json
import re
import urllib.parse
from pathlib import Path
from typing import Any

import requests

from social_crawl_skill.browser_runtime import BrowserRuntime
from social_crawl_skill.query_planner import QueryPlanner


class XiaohongshuCrawler:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.profile_dir = root / "runtime" / "browser_profiles" / "xiaohongshu"
        self.base_output_dir = root / "outputs" / "raw_crawl" / "xiaohongshu"
        self.runtime = BrowserRuntime(root)
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36 Edg/146.0.0.0",
            "Referer": "https://www.xiaohongshu.com/",
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

    def crawl_image_posts_multi(self, queries: list[str], limit: int = 5) -> dict[str, Any]:
        base_query = queries[0] if queries else "xiaohongshu"
        output_dir = self.base_output_dir / f"image_posts_multi_{self._slug(base_query)}"
        output_dir.mkdir(parents=True, exist_ok=True)
        all_items: list[dict[str, Any]] = []
        attempts: list[dict[str, Any]] = []
        login_required = False

        for query in queries:
            result = self._capture_search_feeds(query, output_dir / self._slug(query))
            if result.get("status") == "login_required":
                login_required = True
                attempts.append({"query": query, "status": "login_required", "count": 0})
                break
            items = result.get("items", [])
            unique_new = []
            for item in items:
                if any(existing["note_id"] == item["note_id"] for existing in all_items):
                    continue
                all_items.append(item)
                unique_new.append(item)
                if len(all_items) >= limit:
                    break
            attempts.append({"query": query, "status": "ok", "count": len(unique_new)})
            if len(all_items) >= limit:
                break

        selected = all_items[:limit]
        if selected:
            self._download_image_posts(selected, output_dir)
        payload = {
            "platform": "xiaohongshu",
            "queries": queries,
            "mode": "image_posts_multi_query",
            "count": len(selected),
            "attempts": attempts,
            "login_required": login_required,
            "items": selected,
        }
        (output_dir / "samples.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        return payload

    def crawl_video_posts_multi(self, queries: list[str], limit: int = 5) -> dict[str, Any]:
        base_query = queries[0] if queries else "xiaohongshu"
        output_dir = self.base_output_dir / f"video_posts_multi_{self._slug(base_query)}"
        output_dir.mkdir(parents=True, exist_ok=True)
        all_items: list[dict[str, Any]] = []
        attempts: list[dict[str, Any]] = []
        login_required = False

        for query in queries:
            result = self._capture_search_feeds(query, output_dir / self._slug(query), include_video=True)
            if result.get("status") == "login_required":
                login_required = True
                attempts.append({"query": query, "status": "login_required", "count": 0})
                break
            items = result.get("items", [])
            unique_new = []
            for item in items:
                if any(existing["note_id"] == item["note_id"] for existing in all_items):
                    continue
                all_items.append(item)
                unique_new.append(item)
                if len(all_items) >= limit:
                    break
            attempts.append({"query": query, "status": "ok", "count": len(unique_new)})
            if len(all_items) >= limit:
                break

        selected = all_items[:limit]
        if selected:
            self._download_video_posts(selected, output_dir)
        payload = {
            "platform": "xiaohongshu",
            "queries": queries,
            "mode": "video_posts_multi_query",
            "count": len(selected),
            "attempts": attempts,
            "login_required": login_required,
            "items": selected,
        }
        (output_dir / "samples.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        return payload

    def _capture_search_feeds(self, query: str, output_dir: Path, include_video: bool = False) -> dict[str, Any]:
        output_dir.mkdir(parents=True, exist_ok=True)
        search_url = f"https://www.xiaohongshu.com/search_result?keyword={urllib.parse.quote(query)}&source=web_explore_feed"
        playwright, ctx, page = self.runtime.connect_existing("xiaohongshu")
        try:
            page.goto(search_url, wait_until="domcontentloaded")
            page.wait_for_timeout(8000)
            current_url = page.url
            body = page.locator("body").inner_text()[:3000]
            (output_dir / "page.html").write_text(page.content(), encoding="utf-8")
            page.screenshot(path=str(output_dir / "page.png"), full_page=True)
            if "website-login/error" in current_url or "登录探索更多内容" in body:
                return {"status": "login_required", "query": query, "current_url": current_url, "items": []}
            data = page.evaluate(
                """
() => {
  if (window.__INITIAL_STATE__ && window.__INITIAL_STATE__.search && window.__INITIAL_STATE__.search.feeds) {
    const feeds = window.__INITIAL_STATE__.search.feeds;
    return feeds.value !== undefined ? feeds.value : feeds._value;
  }
  return [];
}
"""
            )
        finally:
            playwright.stop()

        items = []
        if isinstance(data, list):
            for feed in data:
                if not isinstance(feed, dict):
                    continue
                note_id = feed.get("id") or ""
                xsec_token = feed.get("xsecToken") or ""
                note_card = feed.get("noteCard") or {}
                if not note_id or not xsec_token or not isinstance(note_card, dict):
                    continue
                has_video = note_card.get("type") == "video" or bool(note_card.get("video"))
                if include_video and not has_video:
                    continue
                if not include_video and has_video:
                    continue
                cover = note_card.get("cover") or {}
                user = note_card.get("user") or {}
                interact = note_card.get("interactInfo") or {}
                items.append(
                    {
                        "note_id": note_id,
                        "xsec_token": xsec_token,
                        "title": note_card.get("displayTitle", ""),
                        "author_nickname": user.get("nickname") or user.get("nickName", ""),
                        "author_user_id": user.get("userId", ""),
                        "liked_count": interact.get("likedCount", ""),
                        "comment_count": interact.get("commentCount", ""),
                        "collected_count": interact.get("collectedCount", ""),
                        "cover_url": cover.get("urlDefault") or cover.get("url") or "",
                        "detail_url": f"https://www.xiaohongshu.com/explore/{note_id}?xsec_token={xsec_token}&xsec_source=pc_search",
                        "video_note": has_video,
                    }
                )
        return {"status": "ok", "query": query, "current_url": search_url, "items": items}

    def _download_image_posts(self, items: list[dict[str, Any]], output_dir: Path) -> None:
        posts_dir = output_dir / "downloads"
        posts_dir.mkdir(parents=True, exist_ok=True)

        def download_post(index: int, item: dict[str, Any]) -> dict[str, Any]:
            folder = posts_dir / f"{index:02d}_{item['note_id']}"
            folder.mkdir(parents=True, exist_ok=True)
            (folder / "title.txt").write_text(item["title"], encoding="utf-8")
            (folder / "metadata.json").write_text(json.dumps(item, ensure_ascii=False, indent=2), encoding="utf-8")
            detail = self._fetch_note_detail(item["note_id"], item["xsec_token"], folder)
            local_images = []
            for img_index, image_url in enumerate(detail.get("image_urls", []), start=1):
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
            item["detail_title"] = detail.get("title", "")
            item["detail_desc"] = detail.get("desc", "")
            item["image_urls"] = detail.get("image_urls", [])
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

    def _fetch_note_detail(self, note_id: str, xsec_token: str, folder: Path) -> dict[str, Any]:
        detail_url = f"https://www.xiaohongshu.com/explore/{note_id}?xsec_token={xsec_token}&xsec_source=pc_search"
        playwright, ctx, page = self.runtime.connect_existing("xiaohongshu")
        try:
            page.goto(detail_url, wait_until="domcontentloaded")
            page.wait_for_timeout(6000)
            (folder / "detail_page.html").write_text(page.content(), encoding="utf-8")
            page.screenshot(path=str(folder / "detail_page.png"), full_page=True)
            data = page.evaluate(
                f"""
() => {{
  if (window.__INITIAL_STATE__ && window.__INITIAL_STATE__.note && window.__INITIAL_STATE__.note.noteDetailMap) {{
    const map = window.__INITIAL_STATE__.note.noteDetailMap;
    const note = map['{note_id}'];
    return note || null;
  }}
                return null;
}}
"""
            )
        finally:
            playwright.stop()
        note = (data or {}).get("note") or {}
        image_list = note.get("imageList") or []
        image_urls = []
        for image in image_list:
            if not isinstance(image, dict):
                continue
            image_urls.append(image.get("urlDefault") or image.get("urlPre") or "")
        return {
            "title": note.get("title", ""),
            "desc": note.get("desc", ""),
            "image_urls": [url for url in image_urls if url],
            "video_urls": self._extract_video_urls(note),
        }

    def _extract_video_urls(self, note: dict[str, Any]) -> list[str]:
        video = note.get("video") or {}
        media = video.get("media") or {}
        stream = media.get("stream") or {}
        urls = []
        for key in ["h264", "h265"]:
            for item in stream.get(key) or []:
                if not isinstance(item, dict):
                    continue
                if item.get("masterUrl"):
                    urls.append(item["masterUrl"])
        # 去重
        deduped = []
        seen = set()
        for url in urls:
            if url not in seen:
                seen.add(url)
                deduped.append(url)
        return deduped

    def _download_video_posts(self, items: list[dict[str, Any]], output_dir: Path) -> None:
        posts_dir = output_dir / "downloads"
        posts_dir.mkdir(parents=True, exist_ok=True)

        completed = []
        for idx, item in enumerate(items, start=1):
            try:
                folder = posts_dir / f"{idx:02d}_{item['note_id']}"
                folder.mkdir(parents=True, exist_ok=True)
                (folder / "title.txt").write_text(item["title"], encoding="utf-8")
                (folder / "metadata.json").write_text(json.dumps(item, ensure_ascii=False, indent=2), encoding="utf-8")
                detail = self._fetch_note_detail(item["note_id"], item["xsec_token"], folder)
                video_urls = detail.get("video_urls", [])
                if not video_urls:
                    continue
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
                video_path = folder / f"{self._safe_name(detail.get('title') or item['title'])}.mp4"
                with requests.get(video_urls[0], headers=self.headers, stream=True, timeout=120) as response:
                    response.raise_for_status()
                    with open(video_path, "wb") as handle:
                        for chunk in response.iter_content(chunk_size=1024 * 256):
                            if chunk:
                                handle.write(chunk)
                item["rank"] = idx
                item["download_dir"] = str(folder)
                item["detail_title"] = detail.get("title", "")
                item["detail_desc"] = detail.get("desc", "")
                item["video_urls"] = video_urls
                item["video_path"] = str(video_path)
                completed.append(item)
            except Exception:
                continue
        (output_dir / "downloads_summary.json").write_text(
            json.dumps({"count": len(completed), "items": completed}, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def _slug(self, text: str) -> str:
        slug = re.sub(r"[^0-9A-Za-z\u4e00-\u9fff]+", "_", text).strip("_")
        return slug or "query"

    def _safe_name(self, text: str) -> str:
        text = re.sub(r'[\\\\/:*?"<>|\r\n]+', "_", text)
        return text[:80].strip(" ._") or "untitled"
