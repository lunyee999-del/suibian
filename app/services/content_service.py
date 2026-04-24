from __future__ import annotations

from app.domain.models import ContentDraft, TopicCandidate
from app.services.prompt_loader import PromptLoader


class ContentService:
    def __init__(self, prompt_loader: PromptLoader) -> None:
        self.prompt_loader = prompt_loader
        self.prompt_version = "v0.2"

    def build_topic_prompt(self, candidate: TopicCandidate) -> str:
        template = self.prompt_loader.load("content_generation.txt")
        return (
            template.replace("{{topic_title}}", candidate.topic_title)
            .replace("{{topic_angle}}", candidate.topic_angle)
            .replace("{{topic_brief}}", candidate.topic_brief)
            .replace("{{column_type}}", candidate.column_type)
            .replace("{{source_context}}", candidate.topic_brief)
        )

    def generate(self, candidate: TopicCandidate) -> ContentDraft:
        title = candidate.topic_title[:22]
        cover_text = candidate.topic_title[:18]
        body_text = (
            f"先说结论：{candidate.topic_title} 这类话题，值得继续观察，但不要只跟热点走。\n\n"
            f"从最近公开内容看，{candidate.topic_brief}\n"
            f"真正对卖家有价值的，不只是信息本身，而是信息背后的执行信号。"
            f"如果你准备跟进，建议先判断类目供给、价格空间和上新节奏，再决定投入强度。\n\n"
            f"做 Ozon 内容时，最好把热点、榜单、选品和运营动作拆开看，这样判断会更稳。"
        )
        return ContentDraft(
            title=title,
            cover_text=cover_text,
            body_text=body_text,
            image_prompt=f"为 Ozon 图文生成竖版封面，主题：{title}",
            hashtags=["#Ozon运营", "#跨境电商", "#选品分析"],
            cta_text="把重复动作工具化，把关键判断留给人。",
            prompt_version=self.prompt_version,
            candidate_id=candidate.candidate_id,
        )
