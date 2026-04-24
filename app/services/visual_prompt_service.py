from __future__ import annotations

import json
from textwrap import shorten
from urllib import request

from app.core.settings import Settings
from app.domain.models import ContentDraft, SourceArticle
from app.services.prompt_loader import PromptLoader


class VisualPromptService:
    def __init__(self, settings: Settings, prompt_loader: PromptLoader) -> None:
        self.api_key = settings.llm_api_key
        self.base_url = settings.llm_base_url.rstrip("/")
        self.model = settings.llm_model
        self.prompt_loader = prompt_loader

    def generate_from_article(self, article: SourceArticle, draft: ContentDraft) -> str:
        if self.api_key:
            try:
                return self._generate_via_api(article, draft)
            except Exception:
                pass
        return self._generate_fallback(article, draft)

    def _generate_via_api(self, article: SourceArticle, draft: ContentDraft) -> str:
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You write Chinese text-to-image prompts for Xiaohongshu covers. "
                        "Style must be blogger dry-goods card poster, not fake software UI."
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
        content = raw["choices"][0]["message"]["content"]
        parsed = self._parse_json_block(content)
        return str(parsed["final_image_prompt"]).strip()

    def _build_prompt(self, article: SourceArticle, draft: ContentDraft) -> str:
        template = self.prompt_loader.load("visual_prompt_xhs_poster.txt")
        full_content = shorten(article.content.replace("\n", " "), width=10000, placeholder=" ...")
        cards = draft.cover_layout.get("cards", [])
        return (
            template.replace("{{source_title}}", article.title)
            .replace("{{source_category}}", article.category_tag)
            .replace("{{source_summary}}", article.summary)
            .replace("{{full_article_content}}", full_content)
            .replace("{{draft_title}}", draft.title)
            .replace("{{draft_cover_text}}", draft.cover_text)
            .replace("{{eyebrow}}", str(draft.cover_layout.get("eyebrow", "")))
            .replace("{{sub_title}}", str(draft.cover_layout.get("sub_title", "")))
            .replace("{{card1}}", str(cards[0] if len(cards) > 0 else ""))
            .replace("{{card2}}", str(cards[1] if len(cards) > 1 else ""))
            .replace("{{card3}}", str(cards[2] if len(cards) > 2 else ""))
            .replace("{{badge}}", str(draft.cover_layout.get("badge", "")))
            .replace("{{footer}}", str(draft.cover_layout.get("footer", "")))
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

    def _generate_fallback(self, article: SourceArticle, draft: ContentDraft) -> str:
        cards = draft.cover_layout.get("cards", [])
        card_text = "、".join(str(item) for item in cards if item)
        return (
            "小红书竖版封面，博主干货卡片风，杂志感信息海报，"
            f"主题围绕“{draft.title}”，"
            f"大字主标题为“{draft.cover_layout.get('main_title', draft.cover_text)}”，"
            f"副标题为“{draft.cover_layout.get('sub_title', draft.title[:18])}”，"
            f"中部是三张清晰干货卡片，内容分别是“{card_text}”，"
            "使用奶油白背景、深海军蓝标题块、橙色强调贴纸，版式整洁，中文排版清晰，"
            "加入少量跨境电商元素，如地图轮廓、物流箱、数据箭头、小标签贴纸，"
            "整体像高质量小红书运营博主封面，避免复杂软件界面，避免假英文，避免乱码，避免真人。"
        )
