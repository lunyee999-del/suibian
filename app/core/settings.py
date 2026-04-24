from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import os


def _load_dotenv(dotenv_path: Path) -> None:
    if not dotenv_path.exists():
        return

    for line in dotenv_path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip())


def _to_bool(value: str | None, default: bool) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(slots=True)
class Settings:
    base_dir: Path
    storage_dir: Path
    prompts_dir: Path
    dry_run: bool
    storage_backend: str
    publisher_url: str
    browser_fetcher_url: str
    llm_api_key: str
    llm_base_url: str
    llm_model: str
    image_provider: str
    wanx_api_key: str
    wanx_model: str
    ark_api_key: str
    ark_image_base_url: str
    ark_image_model: str

    @classmethod
    def load(cls) -> "Settings":
        base_dir = Path(__file__).resolve().parents[2]
        _load_dotenv(base_dir / ".env")
        storage_dir = base_dir / os.environ.get("STORAGE_DIR", "storage")
        prompts_dir = base_dir / "config" / "prompts"
        return cls(
            base_dir=base_dir,
            storage_dir=storage_dir,
            prompts_dir=prompts_dir,
            dry_run=_to_bool(os.environ.get("DRY_RUN"), True),
            storage_backend=os.environ.get("STORAGE_BACKEND", "local_json"),
            publisher_url=os.environ.get("PUBLISHER_URL", "http://127.0.0.1:3010"),
            browser_fetcher_url=os.environ.get("BROWSER_FETCHER_URL", "http://127.0.0.1:3010"),
            llm_api_key=os.environ.get("DASHSCOPE_API_KEY") or os.environ.get("OPENAI_API_KEY", ""),
            llm_base_url=os.environ.get("OPENAI_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1"),
            llm_model=os.environ.get("OPENAI_MODEL", "qwen-plus"),
            image_provider=os.environ.get("IMAGE_PROVIDER", "ark"),
            wanx_api_key=os.environ.get("DASHSCOPE_API_KEY") or os.environ.get("WANX_API_KEY", ""),
            wanx_model=os.environ.get("WANX_MODEL", "Wan2.2-T2I-Flash"),
            ark_api_key=os.environ.get("ARK_API_KEY", ""),
            ark_image_base_url=os.environ.get("ARK_IMAGE_BASE_URL", "https://ark.cn-beijing.volces.com/api/v3"),
            ark_image_model=os.environ.get("ARK_IMAGE_MODEL", "doubao-seedream-5-0-260128"),
        )
