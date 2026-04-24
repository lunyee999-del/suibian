from __future__ import annotations

import json
import os
import platform as sys_platform
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from playwright.sync_api import BrowserContext, Page, Playwright, sync_playwright


PlatformName = Literal["xiaohongshu", "douyin", "kuaishou"]


@dataclass
class PlatformRuntimeConfig:
    platform: PlatformName
    home_url: str
    login_url: str
    profile_dir: Path
    downloads_dir: Path
    cdp_port: int


class BrowserRuntime:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.runtime_dir = root / "runtime"
        self.browser_dir = self.runtime_dir / "browser_profiles"
        self.browser_dir.mkdir(parents=True, exist_ok=True)

    def platform_config(self, platform: PlatformName) -> PlatformRuntimeConfig:
        mapping = {
            "xiaohongshu": ("https://www.xiaohongshu.com/explore", "https://www.xiaohongshu.com/"),
            "douyin": ("https://www.douyin.com/", "https://www.douyin.com/"),
            "kuaishou": ("https://www.kuaishou.com/new-reco", "https://www.kuaishou.com/"),
        }
        port_map = {
            "xiaohongshu": 9333,
            "douyin": 9334,
            "kuaishou": 9335,
        }
        home_url, login_url = mapping[platform]
        profile_dir = self.browser_dir / platform
        downloads_dir = profile_dir / "downloads"
        profile_dir.mkdir(parents=True, exist_ok=True)
        downloads_dir.mkdir(parents=True, exist_ok=True)
        return PlatformRuntimeConfig(
            platform=platform,
            home_url=home_url,
            login_url=login_url,
            profile_dir=profile_dir,
            downloads_dir=downloads_dir,
            cdp_port=port_map[platform],
        )

    def profile_status(self, platform: PlatformName) -> dict:
        config = self.platform_config(platform)
        return {
            "platform": platform,
            "profile_dir": str(config.profile_dir),
            "downloads_dir": str(config.downloads_dir),
            "cdp_port": config.cdp_port,
            "exists": config.profile_dir.exists(),
            "files": [str(path.relative_to(config.profile_dir)) for path in config.profile_dir.rglob("*") if path.is_file()][:50],
        }

    def launch_persistent(self, playwright: Playwright, platform: PlatformName, headless: bool = True) -> BrowserContext:
        config = self.platform_config(platform)
        self._cleanup_profile_locks(config.profile_dir)
        channel = os.environ.get("AGENT_TEAM_BROWSER_CHANNEL")
        executable_path = os.environ.get("AGENT_TEAM_BROWSER_EXECUTABLE")
        launch_args = {
            "user_data_dir": str(config.profile_dir),
            "headless": headless,
            "accept_downloads": True,
            "downloads_path": str(config.downloads_dir),
            "args": [
                "--disable-blink-features=AutomationControlled",
                "--no-default-browser-check",
                "--disable-dev-shm-usage",
            ],
        }
        if executable_path:
            launch_args["executable_path"] = executable_path
        elif channel:
            launch_args["channel"] = channel
        elif sys_platform.system().lower() == "windows":
            launch_args["channel"] = "msedge"
        return playwright.chromium.launch_persistent_context(**launch_args)

    def _cleanup_profile_locks(self, profile_dir: Path) -> None:
        lock_candidates = [
            profile_dir / "SingletonLock",
            profile_dir / "SingletonCookie",
            profile_dir / "SingletonSocket",
            profile_dir / "lockfile",
            profile_dir / "Default" / "LOCK",
        ]
        for path in lock_candidates:
            try:
                if path.exists():
                    path.unlink()
            except Exception:
                continue

    def write_runtime_manifest(self) -> Path:
        payload = {
            "runtime_dir": str(self.runtime_dir),
            "browser_profiles_dir": str(self.browser_dir),
            "docker_note": "Mount runtime/browser_profiles as a persistent volume to preserve login state across container restarts.",
            "environment": {
                "AGENT_TEAM_BROWSER_CHANNEL": "Optional local browser channel, e.g. msedge or chrome.",
                "AGENT_TEAM_BROWSER_EXECUTABLE": "Optional browser executable path for containerized deployment.",
            },
        }
        path = self.runtime_dir / "runtime_manifest.json"
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        return path

    def open_page(self, platform: PlatformName, headless: bool = True) -> tuple[Playwright, BrowserContext, Page]:
        playwright = sync_playwright().start()
        try:
            context = self.launch_persistent(playwright, platform=platform, headless=headless)
            page = context.pages[0] if context.pages else context.new_page()
            return playwright, context, page
        except Exception:
            playwright.stop()
            raise

    def launch_manual_browser(self, platform: PlatformName) -> dict:
        config = self.platform_config(platform)
        executable = os.environ.get("AGENT_TEAM_BROWSER_EXECUTABLE")
        if not executable and sys_platform.system().lower() == "windows":
            candidates = [
                Path(r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"),
                Path(r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"),
                Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe"),
            ]
            for candidate in candidates:
                if candidate.exists():
                    executable = str(candidate)
                    break
        if not executable:
            raise RuntimeError("No browser executable found. Set AGENT_TEAM_BROWSER_EXECUTABLE.")
        self._cleanup_profile_locks(config.profile_dir)
        args = [
            executable,
            f"--user-data-dir={config.profile_dir}",
            "--no-first-run",
            "--disable-default-browser-check",
            f"--remote-debugging-port={config.cdp_port}",
            config.login_url,
        ]
        subprocess.Popen(args)
        return {
            "platform": platform,
            "browser_executable": executable,
            "profile_dir": str(config.profile_dir),
            "login_url": config.login_url,
            "cdp_url": f"http://127.0.0.1:{config.cdp_port}",
        }

    def connect_existing(self, platform: PlatformName) -> tuple[Playwright, BrowserContext, Page]:
        config = self.platform_config(platform)
        playwright = sync_playwright().start()
        try:
            browser = playwright.chromium.connect_over_cdp(f"http://127.0.0.1:{config.cdp_port}")
            context = browser.contexts[0] if browser.contexts else browser.new_context()
            page = context.pages[0] if context.pages else context.new_page()
            return playwright, context, page
        except Exception:
            playwright.stop()
            raise
