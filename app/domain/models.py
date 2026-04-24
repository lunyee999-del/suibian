from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from uuid import uuid4


def _id() -> str:
    return uuid4().hex


@dataclass(slots=True)
class RawItem:
    source_name: str
    source_url: str
    title: str
    summary: str
    keywords: list[str]
    fetched_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    raw_id: str = field(default_factory=_id)


@dataclass(slots=True)
class SourceArticle:
    title: str
    source_url: str
    site_name: str
    published_at: str | None
    author: str | None
    content: str
    category_tag: str
    summary: str
    keywords: list[str]
    collected_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    article_id: str = field(default_factory=_id)


@dataclass(slots=True)
class TrendTopic:
    topic_name: str
    topic_type: str
    keywords: list[str]
    source_names: list[str]
    summary: str
    heat_score: float
    topic_id: str = field(default_factory=_id)


@dataclass(slots=True)
class TopicCandidate:
    column_type: str
    topic_title: str
    topic_angle: str
    topic_brief: str
    priority_score: float
    trend_topic_id: str
    candidate_id: str = field(default_factory=_id)


@dataclass(slots=True)
class ContentDraft:
    title: str
    cover_text: str
    body_text: str
    image_prompt: str
    hashtags: list[str]
    cta_text: str
    prompt_version: str
    candidate_id: str
    cover_layout: dict[str, Any] = field(default_factory=dict)
    draft_id: str = field(default_factory=_id)


@dataclass(slots=True)
class ImageAsset:
    draft_id: str
    asset_type: str
    prompt_text: str
    size: str
    local_path: str
    provider: str
    status: str
    asset_id: str = field(default_factory=_id)


@dataclass(slots=True)
class ReviewDraft:
    source_article_id: str
    source_title: str
    source_url: str
    source_site_name: str
    source_category_tag: str
    content_draft: ContentDraft
    image_asset: ImageAsset
    review_status: str
    llm_provider: str
    llm_model: str
    review_notes: str | None = None
    publish_result: dict[str, Any] | None = None
    generated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    review_id: str = field(default_factory=_id)


@dataclass(slots=True)
class PublishPayload:
    title: str
    body_text: str
    hashtags: list[str]
    images: list[str]
    draft_id: str
    extra: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class PublishResult:
    success: bool
    result_status: str
    note_url: str | None
    draft_id: str
    detail: dict[str, Any]
    recorded_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
