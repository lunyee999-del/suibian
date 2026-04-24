from __future__ import annotations

import re


TOKEN_PATTERN = re.compile(
    r"[\u4e00-\u9fff]{2,8}|[A-Za-z][A-Za-z0-9\-]{2,20}|[А-Яа-яЁё]{3,24}"
)

STOPWORDS = {
    "ozon",
    "https",
    "http",
    "www",
    "для",
    "что",
    "this",
    "with",
    "from",
    "and",
    "the",
    "运营",
    "内容",
}


def extract_keywords(text: str, preferred: list[str] | None = None, limit: int = 6) -> list[str]:
    preferred = preferred or []
    counts: dict[str, int] = {}
    for token in TOKEN_PATTERN.findall(text):
        normalized = token.strip()
        if not normalized:
            continue
        lowered = normalized.lower()
        if lowered in STOPWORDS:
            continue
        counts[normalized] = counts.get(normalized, 0) + 1

    ranked = [item for item, _ in sorted(counts.items(), key=lambda kv: (-kv[1], len(kv[0])))]
    merged: list[str] = []
    for token in preferred + ranked:
        if token not in merged:
            merged.append(token)
        if len(merged) >= limit:
            break

    if not merged:
        return ["Ozon", "热点"]
    return merged
