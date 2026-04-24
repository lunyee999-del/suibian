from __future__ import annotations

import json
import re
from pathlib import Path

from social_crawl_skill.materials import MaterialIndexer


DEFAULT_SEEDS = [
    "Umlink",
    "俄区电商",
    "俄罗斯电商",
    "俄语区卖家",
    "跨境电商",
    "Ozon",
    "Wildberries",
    "Yandex Market",
    "一键上架",
    "AI优化标题",
    "AI关键词",
    "比价采购",
    "选品分析",
    "店铺智能运营",
]


class QueryPlanner:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.output_dir = root / "outputs" / "query_plan"
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def _find_material_dir(self) -> Path:
        plan_dir = self.root / "planDOC"
        candidates = [path for path in plan_dir.iterdir() if path.is_dir() and "资料" in path.name]
        if candidates:
            return candidates[0]
        raise FileNotFoundError("No material directory found under planDOC.")

    def generate(self) -> dict:
        material_dir = self._find_material_dir()
        index = MaterialIndexer(self.root).build_index(material_dir, self.output_dir / "material_index.json")
        corpus = "\n".join(chunk.get("excerpt", "") for chunk in index.get("text_chunks", []))
        selected = [seed for seed in DEFAULT_SEEDS if seed in corpus]
        if "Umlink" not in selected:
            selected.insert(0, "Umlink")
        query_groups = {
            "product_core": [
                "Umlink 一键上架",
                "Umlink AI优化标题",
                "Umlink 比价采购",
            ],
            "market_scene": [
                "俄区电商 Ozon 一键上架",
                "Wildberries 上架工具",
                "Yandex Market 选品",
            ],
            "pain_points": [
                "跨境电商 上架太慢",
                "俄区电商 选品 难",
                "跨境电商 AI标题",
            ],
            "competitor_style": [
                "Ozon 运营技巧",
                "Wildberries 卖家 效率工具",
                "跨境电商 自动化 工具",
            ],
        }
        payload = {
            "material_dir": str(material_dir),
            "selected_keywords": selected,
            "query_groups": query_groups,
        }
        (self.output_dir / "queries.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        return payload
