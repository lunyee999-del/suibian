from __future__ import annotations

from pathlib import Path


class PromptLoader:
    def __init__(self, prompts_dir: Path) -> None:
        self.prompts_dir = prompts_dir

    def load(self, name: str) -> str:
        return (self.prompts_dir / name).read_text(encoding="utf-8")

