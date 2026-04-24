from __future__ import annotations

import json
from pathlib import Path

from app.domain.models import RawItem, SourceArticle
from app.services.article_page_parser import parse_article_page
from app.services.chwang_article_parser import parse_chwang_article_detail, parse_chwang_article_list
from app.services.http_fetcher import HttpFetcher
from app.services.keyword_extractor import extract_keywords


CATEGORY_RULES = (
    (
        "榜单拆解",
        ("榜单", "排行", "排名", "热销", "爆款", "top", "best seller", "类目趋势"),
    ),
    (
        "选品建议",
        ("选品", "品类", "推荐", "机会", "蓝海", "新品", "爆品", "产品建议"),
    ),
    (
        "运营技巧",
        ("运营", "转化", "广告", "推广", "物流", "上架", "店铺", "链接合并", "利润", "定价", "开通", "仓库"),
    ),
    (
        "热搜词解读",
        ("热搜", "流量词", "搜索词", "搜索流量", "主题标签", "标签打法", "hashtag", "keyword trend"),
    ),
)


class DomesticArticleCollector:
    def __init__(self, config_path: Path) -> None:
        self.config_path = config_path
        self.http_fetcher = HttpFetcher()
        self.last_errors: list[dict[str, str]] = []

    def fetch_articles(self, limit: int) -> list[SourceArticle]:
        source_items = json.loads(self.config_path.read_text(encoding="utf-8"))
        enabled_sources = [item for item in source_items if item.get("enabled", True)]
        articles: list[SourceArticle] = []
        self.last_errors = []

        for source in enabled_sources:
            if len(articles) >= limit:
                break
            try:
                source_articles = self._fetch_source_articles(
                    source,
                    remaining=limit - len(articles),
                )
                articles.extend(source_articles)
            except Exception as exc:
                self.last_errors.append(
                    {
                        "source_name": str(source.get("name") or source["url"]),
                        "source_url": source["url"],
                        "error": str(exc),
                    }
                )

        if not articles:
            raise RuntimeError("no domestic Ozon articles collected successfully")

        return articles

    def _fetch_source_articles(self, source: dict, remaining: int) -> list[SourceArticle]:
        if source.get("source_type") == "chwang_article_list":
            return self._fetch_chwang_list_articles(source, remaining)
        return [self._fetch_single_article(source)]

    def _fetch_single_article(self, source: dict) -> SourceArticle:
        html = self.http_fetcher.get_text(source["url"])
        parsed = parse_article_page(html, source["url"])
        content = parsed.content.strip()
        if not content:
            raise RuntimeError(f"article body not found for {source['url']}")

        title = parsed.title or source.get("fallback_title") or source["name"]
        site_name = source.get("site_name") or parsed.site_name
        summary = parsed.summary or content[:180]
        category_tag = self._classify_article(source, title, summary, content)
        keywords = extract_keywords(
            "\n".join([title, summary, content[:2000]]),
            preferred=source.get("preferred_keywords", []),
            limit=8,
        )
        return SourceArticle(
            title=title,
            source_url=source["url"],
            site_name=site_name,
            published_at=parsed.published_at,
            author=parsed.author,
            content=content,
            category_tag=category_tag,
            summary=summary,
            keywords=keywords,
        )

    def _fetch_chwang_list_articles(self, source: dict, remaining: int) -> list[SourceArticle]:
        list_html = self.http_fetcher.get_text(source["url"])
        list_items = parse_chwang_article_list(list_html, source["url"])
        if not list_items:
            raise RuntimeError(f"no article entries found on {source['url']}")

        articles: list[SourceArticle] = []
        for item in list_items[:remaining]:
            detail_html = self.http_fetcher.get_text(item.url)
            detail = parse_chwang_article_detail(detail_html)
            content = detail.content.strip()
            if not content:
                self.last_errors.append(
                    {
                        "source_name": item.title,
                        "source_url": item.url,
                        "error": "article body not found",
                    }
                )
                continue

            title = detail.title or item.title
            summary = detail.summary or item.summary or content[:180]
            keywords = extract_keywords(
                "\n".join([title, summary, content[:2000], " ".join(item.tags)]),
                preferred=source.get("preferred_keywords", []),
                limit=8,
            )
            articles.append(
                SourceArticle(
                    title=title,
                    source_url=item.url,
                    site_name=source.get("site_name", "出海网"),
                    published_at=detail.published_at or item.published_at,
                    author=detail.author or item.author,
                    content=content,
                    category_tag=self._classify_article(
                        {
                            **source,
                            "name": item.title,
                            "preferred_keywords": source.get("preferred_keywords", []) + item.tags,
                        },
                        title,
                        summary,
                        content,
                    ),
                    summary=summary,
                    keywords=keywords,
                )
            )
        return articles

    def to_raw_items(self, articles: list[SourceArticle]) -> list[RawItem]:
        raw_items: list[RawItem] = []
        for article in articles:
            raw_items.append(
                RawItem(
                    source_name=article.site_name,
                    source_url=article.source_url,
                    title=article.title,
                    summary=article.summary,
                    keywords=article.keywords[:6] or [article.category_tag, "Ozon"],
                )
            )
        return raw_items

    def _classify_article(self, source: dict, title: str, summary: str, content: str) -> str:
        if source.get("category_tag"):
            return str(source["category_tag"])

        haystack = " ".join(
            [
                str(source.get("name", "")),
                title,
                summary,
                content[:2500],
            ]
        ).lower()

        for category, keywords in CATEGORY_RULES:
            if any(keyword.lower() in haystack for keyword in keywords):
                return category

        return "运营技巧"
