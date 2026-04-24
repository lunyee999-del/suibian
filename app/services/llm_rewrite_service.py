from __future__ import annotations

import json
from textwrap import shorten
from urllib import request

from app.core.settings import Settings
from app.domain.models import ContentDraft, SourceArticle
from app.services.prompt_loader import PromptLoader


class LlmRewriteService:
    def __init__(self, settings: Settings, prompt_loader: PromptLoader) -> None:
        self.api_key = settings.llm_api_key
        self.base_url = settings.llm_base_url.rstrip("/")
        self.model = settings.llm_model
        self.prompt_loader = prompt_loader
        self.provider = self._detect_provider()
        self.prompt_version = "xhs.v1"

    def generate_from_article(self, article: SourceArticle) -> ContentDraft:
        if self.api_key:
            try:
                return self._generate_via_api(article)
            except Exception:
                pass
        return self._generate_fallback(article)

    def _generate_via_api(self, article: SourceArticle) -> ContentDraft:
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": "You rewrite Ozon source articles into polished Xiaohongshu draft JSON.",
                },
                {
                    "role": "user",
                    "content": self._build_prompt(article),
                },
            ],
            "temperature": 0.8,
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
        parsed = self._parse_json_block(message)
        return ContentDraft(
            title=str(parsed["title"]).strip(),
            cover_text=str(parsed["cover_text"]).strip(),
            body_text=str(parsed["body_text"]).strip(),
            image_prompt=str(parsed.get("image_prompt", parsed["cover_text"])).strip(),
            hashtags=[str(item).strip() for item in parsed.get("hashtags", []) if str(item).strip()],
            cta_text=str(parsed.get("cta_text", "")).strip(),
            prompt_version=self.prompt_version,
            candidate_id=article.article_id,
        )

    def _build_prompt(self, article: SourceArticle) -> str:
        template = self.prompt_loader.load("xhs_rewrite.txt")
        source_context = shorten(article.content.replace("\n", " "), width=5000, placeholder=" ...")
        return (
            template.replace("{{source_title}}", article.title)
            .replace("{{source_category}}", article.category_tag)
            .replace("{{source_summary}}", article.summary)
            .replace("{{source_url}}", article.source_url)
            .replace("{{source_content}}", source_context)
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

    def _generate_fallback(self, article: SourceArticle) -> ContentDraft:
        focus = {
            "热搜词解读": "把关键词变化讲透",
            "榜单拆解": "拆出可执行判断",
            "选品建议": "给出选品和避坑建议",
            "运营技巧": "总结运营动作和成本边界",
        }.get(article.category_tag, "提炼一线卖家可执行的动作")
        title = self._trim_title(f"{self._clean_title_seed(article.title)}，怎么做更稳")
        body = (
            "先说结论：这篇内容最值得看的，不是表面的热闹，而是背后的执行信号。\n\n"
            f"我把原文重新梳理了一遍，核心信息有三层。第一，{article.summary}\n"
            "第二，真正值得卖家关注的是成本、转化和节奏，而不是单一热点本身。\n"
            f"第三，{focus}，才更适合落到小红书内容表达里。\n\n"
            "如果你在做 Ozon，可以先用这篇原文判断市场变化，再决定是继续观察、立刻测试，还是直接避坑。"
        )
        return ContentDraft(
            title=title,
            cover_text=self._trim_cover(article.title),
            body_text=body,
            image_prompt=f"为 Ozon 干货图文生成封面，主题：{title}，风格专业、清晰、适合小红书。",
            hashtags=["#Ozon运营", "#跨境电商", "#小红书选题"],
            cta_text="如果你要继续做这类 Ozon 内容，可以把原文池先跑起来，再做稳定更新。",
            prompt_version=f"{self.prompt_version}.fallback",
            candidate_id=article.article_id,
        )

    def _detect_provider(self) -> str:
        if not self.api_key:
            return "fallback"
        if "dashscope" in self.base_url.lower():
            return "dashscope-compatible"
        return "openai-compatible"

    def _clean_title_seed(self, title: str) -> str:
        for sep in ("！", "?", "？", ":", "：", "-", "（"):
            if sep in title:
                return title.split(sep, 1)[0]
        return title

    def _trim_title(self, title: str) -> str:
        return title[:22]

    def _trim_cover(self, title: str) -> str:
        return title[:18]
