from __future__ import annotations

from dataclasses import dataclass, field
from html import unescape
import re
from urllib.parse import urljoin


WHITESPACE_RE = re.compile(r"\s+")
TAG_RE = re.compile(r"<[^>]+>")
LIST_ITEM_RE = re.compile(
    r'<a[^>]+class="chw-articleItem"[^>]+href="(?P<href>/article/\d+)"[^>]*>.*?'
    r'<h2[^>]*class="chw-articleItem__title[^"]*"[^>]*>(?P<title>.*?)</h2>.*?'
    r'<div[^>]*class="chw-articleItem__description[^"]*"[^>]*>(?P<summary>.*?)</div>.*?'
    r'<div[^>]*class="chw-articleItem__author[^"]*"[^>]*>(?P<author>.*?)</div>.*?'
    r'<div[^>]*class="chw-articleItem__time[^"]*"[^>]*>.*?</i>\s*(?P<published_at>.*?)</div>.*?'
    r'<div[^>]*class="chw-articleItem__tags[^"]*"[^>]*>(?P<tags>.*?)</div>.*?'
    r"</a>",
    re.S,
)
DETAIL_CONTENT_RE = re.compile(
    r'<div[^>]*class="chw-articleDetail__content"[^>]*>.*?<div[^>]*class="chw-vHtmlOwn"[^>]*>(?P<content>.*?)</div></div>',
    re.S,
)
DETAIL_SUMMARY_RE = re.compile(
    r'<div[^>]*class="chw-articleDetail__description"[^>]*>.*?<div[^>]*class="chw-beyond__cont2"[^>]*>(?P<summary>.*?)</div>',
    re.S,
)
DETAIL_TITLE_RE = re.compile(
    r'<h1[^>]*class="chw-articleDetail__title"[^>]*>(?P<title>.*?)</h1>',
    re.S,
)
DETAIL_AUTHOR_RE = re.compile(
    r'<div[^>]*class="chw-articleDetail__author"[^>]*>(?P<author>.*?)(?:<!---->|<div)',
    re.S,
)
DETAIL_TIME_RE = re.compile(
    r'<div[^>]*class="chw-articleDetail__time"[^>]*>.*?</i>\s*(?P<time>.*?)</div>',
    re.S,
)


def _clean_html_text(value: str) -> str:
    text = TAG_RE.sub(" ", value)
    return WHITESPACE_RE.sub(" ", unescape(text)).strip()


def _normalize_content_html(value: str) -> str:
    text = re.sub(r"<br\s*/?>", "\n", value, flags=re.I)
    text = re.sub(r"</p\s*>", "\n\n", text, flags=re.I)
    text = re.sub(r"</h[1-6]\s*>", "\n\n", text, flags=re.I)
    text = re.sub(r"</li\s*>", "\n", text, flags=re.I)
    text = re.sub(r"<li[^>]*>", "• ", text, flags=re.I)
    text = TAG_RE.sub(" ", text)
    text = unescape(text)
    text = re.sub(r"[ \t\r\f\v]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return "\n".join(line.strip() for line in text.splitlines() if line.strip()).strip()


@dataclass(slots=True)
class ChwangListItem:
    title: str
    url: str
    summary: str
    author: str | None
    published_at: str | None
    tags: list[str] = field(default_factory=list)


@dataclass(slots=True)
class ChwangArticleDetail:
    title: str
    author: str | None
    published_at: str | None
    summary: str
    content: str


def parse_chwang_article_list(html: str, base_url: str) -> list[ChwangListItem]:
    items: list[ChwangListItem] = []
    for match in LIST_ITEM_RE.finditer(html):
        tags_html = match.group("tags")
        tags = [
            cleaned
            for cleaned in (_clean_html_text(tag) for tag in re.findall(r"<h6[^>]*>(.*?)</h6>", tags_html, re.S))
            if cleaned
        ]
        items.append(
            ChwangListItem(
                title=_clean_html_text(match.group("title")),
                url=urljoin(base_url, match.group("href")),
                summary=_clean_html_text(match.group("summary")),
                author=_clean_html_text(match.group("author")) or None,
                published_at=_clean_html_text(match.group("published_at")) or None,
                tags=tags,
            )
        )
    return items


def parse_chwang_article_detail(html: str) -> ChwangArticleDetail:
    title_match = DETAIL_TITLE_RE.search(html)
    author_match = DETAIL_AUTHOR_RE.search(html)
    time_match = DETAIL_TIME_RE.search(html)
    summary_match = DETAIL_SUMMARY_RE.search(html)
    content_match = DETAIL_CONTENT_RE.search(html)

    content = _normalize_content_html(content_match.group("content")) if content_match else ""
    return ChwangArticleDetail(
        title=_clean_html_text(title_match.group("title")) if title_match else "",
        author=_clean_html_text(author_match.group("author")) if author_match else None,
        published_at=_clean_html_text(time_match.group("time")) if time_match else None,
        summary=_clean_html_text(summary_match.group("summary")) if summary_match else "",
        content=content,
    )
