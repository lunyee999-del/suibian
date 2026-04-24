from __future__ import annotations

from collections import defaultdict

from app.domain.models import RawItem, TopicCandidate, TrendTopic


COLUMN_TYPES = (
    "hot_keyword",
    "ranking_analysis",
    "product_selection",
    "operation_tips",
)


class TopicService:
    def build_topics(self, raw_items: list[RawItem]) -> list[TrendTopic]:
        grouped: dict[str, list[RawItem]] = defaultdict(list)
        for item in raw_items:
            key = item.keywords[0] if item.keywords else item.title
            grouped[key].append(item)

        topics: list[TrendTopic] = []
        for key, items in grouped.items():
            topics.append(
                TrendTopic(
                    topic_name=key,
                    topic_type="keyword",
                    keywords=sorted({kw for item in items for kw in item.keywords}),
                    source_names=[item.source_name for item in items],
                    summary="；".join(item.summary for item in items[:2]),
                    heat_score=float(len(items) * 10),
                )
            )
        return topics

    def build_candidates(self, topics: list[TrendTopic]) -> list[TopicCandidate]:
        candidates: list[TopicCandidate] = []
        for index, topic in enumerate(topics):
            column_type = COLUMN_TYPES[index % len(COLUMN_TYPES)]
            title_map = {
                "hot_keyword": f"最近 Ozon 的“{topic.topic_name}”明显在升温",
                "ranking_analysis": f"Ozon 榜单里关于{topic.topic_name}的信号",
                "product_selection": f"{topic.topic_name} 现在适不适合做 Ozon",
                "operation_tips": f"做 {topic.topic_name} 内容前先看这几个点",
            }
            angle_map = {
                "hot_keyword": "解释关键词热度变化和卖家关注点",
                "ranking_analysis": "从榜单变化中提炼判断",
                "product_selection": "给出是否入场和观察重点",
                "operation_tips": "总结运营动作和避坑点",
            }
            candidates.append(
                TopicCandidate(
                    column_type=column_type,
                    topic_title=title_map[column_type],
                    topic_angle=angle_map[column_type],
                    topic_brief=topic.summary,
                    priority_score=topic.heat_score,
                    trend_topic_id=topic.topic_id,
                )
            )
        return candidates

