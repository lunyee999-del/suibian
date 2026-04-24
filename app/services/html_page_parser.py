from __future__ import annotations

from dataclasses import dataclass, field
from html.parser import HTMLParser
import re


def _clean(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


@dataclass(slots=True)
class ParsedPage:
    title: str = ""
    summary: str = ""
    headings: list[str] = field(default_factory=list)
    paragraphs: list[str] = field(default_factory=list)


class _PageParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.current_tag = ""
        self.capture_text = False
        self.buffer: list[str] = []
        self.page = ParsedPage()
        self._meta_name = ""

    def handle_starttag(self, tag: str, attrs) -> None:
        self.current_tag = tag.lower()
        attrs_dict = {key.lower(): value for key, value in attrs}
        if self.current_tag in {"title", "h1", "h2", "h3", "p"}:
            self.capture_text = True
            self.buffer = []
        elif self.current_tag == "meta":
            name = (attrs_dict.get("name") or attrs_dict.get("property") or "").lower()
            content = attrs_dict.get("content") or ""
            if name in {"description", "og:description", "twitter:description"} and not self.page.summary:
                self.page.summary = _clean(content)
            if name in {"og:title", "twitter:title"} and not self.page.title:
                self.page.title = _clean(content)

    def handle_endtag(self, tag: str) -> None:
        closing = tag.lower()
        if self.capture_text and closing == self.current_tag:
            text = _clean("".join(self.buffer))
            if text:
                if closing == "title" and not self.page.title:
                    self.page.title = text
                elif closing in {"h1", "h2", "h3"}:
                    self.page.headings.append(text)
                elif closing == "p":
                    self.page.paragraphs.append(text)
            self.capture_text = False
            self.buffer = []
        self.current_tag = ""

    def handle_data(self, data: str) -> None:
        if self.capture_text:
            self.buffer.append(data)


def parse_html_page(html: str, url: str) -> ParsedPage:
    parser = _PageParser()
    parser.feed(html)
    page = parser.page
    if not page.summary:
        for paragraph in page.paragraphs:
            if len(paragraph) >= 30:
                page.summary = paragraph[:180]
                break
    if not page.summary:
        page.summary = "未提取到摘要"
    if not page.title:
        page.title = url
    return page

