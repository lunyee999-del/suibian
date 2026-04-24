from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from social_crawl_skill.douyin_crawler import DouyinCrawler
from social_crawl_skill.kuaishou_crawler import KuaishouCrawler
from social_crawl_skill.xiaohongshu_crawler import XiaohongshuCrawler


class SocialCrawlTool:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.douyin = DouyinCrawler(root)
        self.xiaohongshu = XiaohongshuCrawler(root)
        self.kuaishou = KuaishouCrawler(root)

    def run(
        self,
        platform: str,
        keyword: str | None = None,
        limit: int = 5,
        content_mode: str = "auto",
        use_material_queries: bool = True,
    ) -> dict[str, Any]:
        platform = platform.lower()
        if platform not in {"douyin", "xiaohongshu", "kuaishou"}:
            raise ValueError(f"Unsupported platform: {platform}")

        if platform == "douyin":
            queries = self.douyin.build_material_queries() if use_material_queries else []
            if keyword:
                queries = [keyword] + [query for query in queries if query != keyword]
            if content_mode == "image":
                return self.douyin.crawl_image_posts_multi(queries=queries or [keyword or "跨境电商"], limit=limit)
            if content_mode == "video":
                return self.douyin.crawl_video_posts_multi(queries=queries or [keyword or "跨境电商"], limit=limit)
            raise ValueError("Douyin supports content_mode=image or video.")

        if platform == "xiaohongshu":
            queries = self.xiaohongshu.build_material_queries() if use_material_queries else []
            if keyword:
                queries = [keyword] + [query for query in queries if query != keyword]
            if content_mode == "image":
                return self.xiaohongshu.crawl_image_posts_multi(queries=queries or [keyword or "跨境电商"], limit=limit)
            if content_mode == "video":
                return self.xiaohongshu.crawl_video_posts_multi(queries=queries or [keyword or "跨境电商"], limit=limit)
            raise ValueError("Xiaohongshu supports content_mode=image or video.")

        queries = self.kuaishou.build_material_queries() if use_material_queries else []
        if keyword:
            queries = [keyword] + [query for query in queries if query != keyword]
        if content_mode not in {"video", "auto"}:
            raise ValueError("Kuaishou currently supports content_mode=video only.")
        return self.kuaishou.crawl_search_videos_multi(queries=queries or [keyword or "跨境电商"], limit=limit)

    def save_result(self, result: dict[str, Any], output_path: Path) -> Path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
        return output_path
