from __future__ import annotations

import json
from textwrap import shorten
from urllib import request

from app.core.settings import Settings
from app.domain.models import ContentDraft, SourceArticle
from app.services.prompt_loader import PromptLoader


class CoverLayoutService:
    def __init__(self, settings: Settings, prompt_loader: PromptLoader) -> None:
        self.api_key = settings.llm_api_key
        self.base_url = settings.llm_base_url.rstrip("/")
        self.model = settings.llm_model
        self.prompt_loader = prompt_loader

    def generate_from_article(self, article: SourceArticle, draft: ContentDraft) -> dict:
        if self.api_key:
            try:
                return self._generate_via_api(article, draft)
            except Exception:
                pass
        return self._generate_fallback(article, draft)

    def _generate_via_api(self, article: SourceArticle, draft: ContentDraft) -> dict:
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You turn full Ozon articles into structured Xiaohongshu cover copy. "
                        "Output concise Chinese only. No fake UI text."
                    ),
                },
                {
                    "role": "user",
                    "content": self._build_prompt(article, draft),
                },
            ],
            "temperature": 0.6,
        }
        req = request.Request(
            f"{self.base_url}/chat/completions",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
            },
            method="POST",
        )
        with request.urlopen(req, timeout=90) as response:
            raw = json.loads(response.read().decode("utf-8"))

        message = raw["choices"][0]["message"]["content"]
        return self._parse_json_block(message)

    def _build_prompt(self, article: SourceArticle, draft: ContentDraft) -> str:
        template = self.prompt_loader.load("cover_layout_xhs.txt")
        full_content = shorten(article.content.replace("\n", " "), width=10000, placeholder=" ...")
        return (
            template.replace("{{source_title}}", article.title)
            .replace("{{source_category}}", article.category_tag)
            .replace("{{source_summary}}", article.summary)
            .replace("{{full_article_content}}", full_content)
            .replace("{{draft_title}}", draft.title)
            .replace("{{draft_cover_text}}", draft.cover_text)
        )

    def _parse_json_block(self, content: str) -> dict:
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            start = content.find("{")
            end = content.rfind("}")
            if start >= 0 and end > start:
                return json.loads(content[start : end + 1])
            raise

    def _generate_fallback(self, article: SourceArticle, draft: ContentDraft) -> dict:
        cards = {
            "热搜词解读": ["关键词变化", "流量判断", "跟进动作"],
            "榜单拆解": ["榜单信号", "类目机会", "优先顺序"],
            "选品建议": ["适合谁做", "利润测算", "避坑提醒"],
            "运营技巧": ["核心动作", "成本边界", "执行节奏"],
        }.get(article.category_tag, ["核心信息", "执行要点", "避坑提醒"])
        return {
            "eyebrow": "OZON 干货",
            "main_title": draft.cover_text[:14],
            "sub_title": draft.title[:20],
            "cards": cards,
            "badge": article.category_tag,
            "footer": "跨境卖家内容笔记",
            "palette": "cream-navy-orange",
        }
