from __future__ import annotations

from html import escape
from pathlib import Path
import json
import re
import time
from urllib import request
from urllib.parse import urlparse

from app.domain.models import ContentDraft, ImageAsset


class ImageService:
    def __init__(
        self,
        storage_dir: Path,
        wanx_model: str,
        dry_run: bool,
        api_key: str = "",
        base_url: str = "https://dashscope.aliyuncs.com/compatible-mode/v1",
        provider: str = "dashscope",
        ark_api_key: str = "",
        ark_base_url: str = "https://ark.cn-beijing.volces.com/api/v3",
        ark_model: str = "doubao-seedream-5-0-260128",
    ) -> None:
        self.images_dir = storage_dir / "images"
        self.images_dir.mkdir(parents=True, exist_ok=True)
        self.wanx_model = wanx_model
        self.dry_run = dry_run
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.provider = provider.lower().strip()
        self.ark_api_key = ark_api_key
        self.ark_base_url = ark_base_url.rstrip("/")
        self.ark_model = ark_model

    def generate_cover(self, draft: ContentDraft) -> ImageAsset:
        if self.provider == "ark" and self.ark_api_key:
            try:
                return self._generate_via_ark(draft)
            except Exception:
                pass
        if self.api_key:
            try:
                return self._generate_via_dashscope(draft)
            except Exception:
                pass
        return self._generate_placeholder(draft)

    def _generate_via_ark(self, draft: ContentDraft) -> ImageAsset:
        payload = {
            "model": self.ark_model,
            "prompt": draft.image_prompt,
            "sequential_image_generation": "disabled",
            "response_format": "url",
            "size": "2K",
            "stream": False,
            "watermark": True,
        }
        req = request.Request(
            f"{self.ark_base_url}/images/generations",
            data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self.ark_api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        with request.urlopen(req, timeout=180) as response:
            result = json.loads(response.read().decode("utf-8"))

        image_url = self._extract_ark_image_url(result)
        suffix = Path(urlparse(image_url).path).suffix or ".png"
        file_path = self.images_dir / f"{draft.draft_id}_cover{suffix}"
        with request.urlopen(image_url, timeout=180) as response:
            file_path.write_bytes(response.read())

        return ImageAsset(
            draft_id=draft.draft_id,
            asset_type="cover",
            prompt_text=draft.image_prompt,
            size="2K",
            local_path=str(file_path),
            provider="ark-seedream",
            status="generated",
        )

    def _extract_ark_image_url(self, payload: dict) -> str:
        data = payload.get("data")
        if isinstance(data, list) and data:
            first = data[0]
            if isinstance(first, dict) and first.get("url"):
                return str(first["url"])
        if payload.get("url"):
            return str(payload["url"])
        raise RuntimeError(f"Ark image response missing url: {payload}")

    def _generate_via_dashscope(self, draft: ContentDraft) -> ImageAsset:
        create_payload = {
            "model": self.wanx_model.lower(),
            "input": {"prompt": draft.image_prompt},
            "parameters": {"size": "720*1280", "n": 1},
        }
        create_req = request.Request(
            f"{self._dashscope_origin()}/api/v1/services/aigc/text2image/image-synthesis",
            data=json.dumps(create_payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "X-DashScope-Async": "enable",
            },
            method="POST",
        )
        with request.urlopen(create_req, timeout=90) as response:
            created = json.loads(response.read().decode("utf-8"))

        task_id = created["output"]["task_id"]
        result = self._poll_task(task_id)
        image_url = result["output"]["results"][0]["url"]
        suffix = Path(urlparse(image_url).path).suffix or ".png"
        file_path = self.images_dir / f"{draft.draft_id}_cover{suffix}"
        with request.urlopen(image_url, timeout=120) as response:
            file_path.write_bytes(response.read())

        return ImageAsset(
            draft_id=draft.draft_id,
            asset_type="cover",
            prompt_text=draft.image_prompt,
            size="720*1280",
            local_path=str(file_path),
            provider="dashscope-wan",
            status="generated",
        )

    def _poll_task(self, task_id: str) -> dict:
        task_url = f"{self._dashscope_origin()}/api/v1/tasks/{task_id}"
        for _ in range(30):
            poll_req = request.Request(
                task_url,
                headers={"Authorization": f"Bearer {self.api_key}"},
                method="GET",
            )
            with request.urlopen(poll_req, timeout=90) as response:
                payload = json.loads(response.read().decode("utf-8"))
            status = payload["output"]["task_status"]
            if status == "SUCCEEDED":
                return payload
            if status in {"FAILED", "CANCELED", "UNKNOWN"}:
                raise RuntimeError(payload.get("message") or f"image task failed: {status}")
            time.sleep(4)
        raise TimeoutError(f"image task timed out: {task_id}")

    def _dashscope_origin(self) -> str:
        if "/compatible-mode/" in self.base_url:
            return self.base_url.split("/compatible-mode/", 1)[0]
        parsed = urlparse(self.base_url)
        return f"{parsed.scheme}://{parsed.netloc}"

    def _generate_placeholder(self, draft: ContentDraft) -> ImageAsset:
        file_path = self.images_dir / f"{draft.draft_id}_cover.svg"
        accent = self._accent_from_text(draft.title)
        cards = draft.cover_layout.get("cards", []) if draft.cover_layout else []
        svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="1080" height="1440">
  <defs>
    <linearGradient id="bg" x1="0" x2="1" y1="0" y2="1">
      <stop offset="0%" stop-color="#FBF4EA"/>
      <stop offset="100%" stop-color="{accent}"/>
    </linearGradient>
  </defs>
  <rect width="1080" height="1440" fill="url(#bg)"/>
  <rect x="70" y="70" width="940" height="1300" rx="38" fill="#fffdf9"/>
  <rect x="120" y="120" width="200" height="54" rx="27" fill="#14213D"/>
  <text x="160" y="156" font-size="26" font-family="Arial, sans-serif" fill="#FFFFFF">{escape(str(draft.cover_layout.get('eyebrow', 'OZON 干货')))}</text>
  <text x="120" y="260" font-size="64" font-weight="700" font-family="Arial, sans-serif" fill="#10213C">{escape(str(draft.cover_layout.get('main_title', draft.cover_text)))}</text>
  <text x="120" y="330" font-size="32" font-family="Arial, sans-serif" fill="#5B6473">{escape(str(draft.cover_layout.get('sub_title', draft.title[:18])))}</text>
  <rect x="760" y="120" width="160" height="54" rx="27" fill="#F77F00"/>
  <text x="802" y="156" font-size="24" font-family="Arial, sans-serif" fill="#FFFFFF">{escape(str(draft.cover_layout.get('badge', '干货')))}</text>
  <rect x="120" y="430" width="840" height="180" rx="30" fill="#FFF3E6"/>
  <rect x="120" y="650" width="840" height="180" rx="30" fill="#EAF4FF"/>
  <rect x="120" y="870" width="840" height="180" rx="30" fill="#FFF1F6"/>
  <text x="160" y="535" font-size="42" font-weight="700" font-family="Arial, sans-serif" fill="#14213D">{escape(str(cards[0] if len(cards) > 0 else '核心信息'))}</text>
  <text x="160" y="755" font-size="42" font-weight="700" font-family="Arial, sans-serif" fill="#14213D">{escape(str(cards[1] if len(cards) > 1 else '执行要点'))}</text>
  <text x="160" y="975" font-size="42" font-weight="700" font-family="Arial, sans-serif" fill="#14213D">{escape(str(cards[2] if len(cards) > 2 else '避坑提醒'))}</text>
  <text x="120" y="1240" font-size="28" font-family="Arial, sans-serif" fill="#6B7280">{escape(str(draft.cover_layout.get('footer', '跨境卖家内容笔记')))}</text>
  <text x="120" y="1290" font-size="24" font-family="Arial, sans-serif" fill="#94A3B8">fallback cover</text>
</svg>
"""
        file_path.write_text(svg, encoding="utf-8")
        return ImageAsset(
            draft_id=draft.draft_id,
            asset_type="cover",
            prompt_text=draft.image_prompt,
            size="1080*1440",
            local_path=str(file_path),
            provider="fallback-cover",
            status="generated",
        )

    def _accent_from_text(self, text: str) -> str:
        score = sum(ord(char) for char in re.sub(r"\s+", "", text))
        palette = ["#FDECCE", "#E7F0FF", "#FCE7F3", "#E8FFF1", "#FFF1D6"]
        return palette[score % len(palette)]
