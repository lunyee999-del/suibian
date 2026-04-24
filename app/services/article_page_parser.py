from __future__ import annotations

from dataclasses import dataclass, field
from html import unescape
from html.parser import HTMLParser
from urllib.parse import urlparse
import re


WHITESPACE_RE = re.compile(r"\s+")

BLOCKED_TAGS = {
    "script",
    "style",
    "noscript",
    "svg",
    "path",
    "footer",
    "header",
    "nav",
    "form",
    "button",
    "aside",
}

TEXT_TAGS = {"title", "h1", "h2", "h3", "h4", "p", "li", "blockquote", "time"}


def _clean_text(value: str) -> str:
    return WHITESPACE_RE.sub(" ", unescape(value)).strip()


def _looks_like_noise(value: str) -> bool:
    lowered = value.lower()
    if len(value) < 18:
        return True
    return any(
        noise in lowered
        for noise in (
            "上一篇",
            "下一篇",
            "相关阅读",
            "猜你喜欢",
            "立即咨询",
            "扫码",
            "返回顶部",
            "copyright",
        )
    )


@dataclass(slots=True)
class ParsedArticlePage:
    title: str = ""
    site_name: str = ""
    published_at: str | None = None
    author: str | None = None
    summary: str = ""
    content: str = ""
    paragraphs: list[str] = field(default_factory=list)


class _ArticleParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.page = ParsedArticlePage()
        self.tag_stack: list[str] = []
        self.block_depth = 0
        self.capture_tag: str | None = None
        self.capture_buffer: list[str] = []
        self.paragraphs: list[str] = []

    def handle_starttag(self, tag: str, attrs) -> None:
        lowered = tag.lower()
        self.tag_stack.append(lowered)
        attrs_dict = {key.lower(): value for key, value in attrs}

        if lowered in BLOCKED_TAGS:
            self.block_depth += 1

        if lowered == "meta":
            self._apply_meta(attrs_dict)
            return

        if self.block_depth == 0 and lowered in TEXT_TAGS:
            self.capture_tag = lowered
            self.capture_buffer = []

        if lowered == "time" and not self.page.published_at:
            datetime_value = attrs_dict.get("datetime")
            if datetime_value:
                self.page.published_at = _clean_text(datetime_value)

    def handle_endtag(self, tag: str) -> None:
        lowered = tag.lower()
        if self.capture_tag == lowered:
            text = _clean_text("".join(self.capture_buffer))
            if text:
                self._commit_text(lowered, text)
            self.capture_tag = None
            self.capture_buffer = []

        if self.tag_stack:
            self.tag_stack.pop()
        if lowered in BLOCKED_TAGS and self.block_depth:
            self.block_depth -= 1

    def handle_data(self, data: str) -> None:
        if self.block_depth == 0 and self.capture_tag:
            self.capture_buffer.append(data)

    def _apply_meta(self, attrs: dict[str, str]) -> None:
        name = (attrs.get("name") or attrs.get("property") or attrs.get("itemprop") or "").lower()
        content = _clean_text(attrs.get("content") or "")
        if not content:
            return

        if name in {"og:title", "twitter:title", "title"} and not self.page.title:
            self.page.title = content
        elif name in {"description", "og:description", "twitter:description"} and not self.page.summary:
            self.page.summary = content
        elif name in {"og:site_name", "application-name"} and not self.page.site_name:
            self.page.site_name = content
        elif name in {"author", "article:author"} and not self.page.author:
            self.page.author = content
        elif name in {
            "article:published_time",
            "publishdate",
            "pubdate",
            "date",
            "og:published_time",
        } and not self.page.published_at:
            self.page.published_at = content

    def _commit_text(self, tag: str, text: str) -> None:
        if tag == "title" and not self.page.title:
            self.page.title = text
            return

        if tag == "h1" and not self.page.title:
            self.page.title = text

        if tag in {"p", "li", "blockquote"}:
            if not _looks_like_noise(text) and text not in self.paragraphs:
                self.paragraphs.append(text)

        if tag == "time" and not self.page.published_at:
            self.page.published_at = text


def parse_article_page(html: str, url: str) -> ParsedArticlePage:
    parser = _ArticleParser()
    parser.feed(html)
    page = parser.page
    page.paragraphs = parser.paragraphs

    if not page.content:
        page.content = "\n\n".join(parser.paragraphs[:80])
    if not page.summary:
        summary_source = next((item for item in parser.paragraphs if len(item) >= 40), "")
        page.summary = summary_source[:180] if summary_source else ""
    if not page.title:
        page.title = url
    if not page.site_name:
        hostname = urlparse(url).netloc.lower()
        page.site_name = hostname.removeprefix("www.")

    return page
