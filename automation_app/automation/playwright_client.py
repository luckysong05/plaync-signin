"""Playwright browser lifecycle management.

Launches Chromium with comprehensive anti-detection:
- Persistent user data dir (cookies/localStorage survive restarts)
- Korean locale & timezone (matching target site)
- Stealth JS patches for navigator, WebGL, plugins, screen, etc.
- Human-like viewport and window management
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Optional

from playwright.sync_api import sync_playwright, BrowserContext, Page
from playwright_stealth import Stealth


def _setup_bundled_browser():
    """If running from PyInstaller build, find bundled Playwright browsers
    and set PLAYWRIGHT_BROWSERS_PATH so Playwright can find them."""
    if not getattr(sys, "frozen", False):
        return

    exe_dir = Path(sys.executable).parent
    browsers = exe_dir / "playwright-browsers"
    if not browsers.is_dir():
        meipass = getattr(sys, "_MEIPASS", None)
        if meipass:
            browsers = Path(meipass) / "playwright-browsers"

    if browsers.is_dir():
        os.environ.setdefault("PLAYWRIGHT_BROWSERS_PATH", str(browsers))


def _load_stealth_script() -> str:
    stealth_path = Path(__file__).resolve().parent / "stealth.js"
    if not stealth_path.exists():
        return ""
    return stealth_path.read_text(encoding="utf-8")


def _user_data_dir(instance_id: int | None) -> str:
    """Persistent browser data dir so sessions survive restarts.

    PyInstaller build: next to executable.
    Dev: under project root's user_data/ (already in .gitignore).
    """
    if getattr(sys, "frozen", False):
        base = Path(sys.executable).parent / "user_data"
    else:
        repo_root = Path(__file__).resolve().parent.parent.parent
        base = repo_root / "user_data"
    name = f"instance_{instance_id}" if instance_id is not None else "default"
    path = base / "browser" / name
    path.mkdir(parents=True, exist_ok=True)
    return str(path)


class PlaywrightClient:
    """Manages Playwright browser with persistent context. Fresh page per run."""

    def __init__(self, headless: bool = False, window_width: int = 700, window_height: int = 780,
                 window_x: int | None = None, window_y: int | None = None,
                 instance_id: int | None = None):
        self.headless = headless
        self.window_width = window_width
        self.window_height = window_height
        self.window_x = window_x
        self.window_y = window_y
        self.instance_id = instance_id
        self._playwright = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None

    def start(self) -> Page:
        """Launch browser with anti-detection, create persistent context and page."""
        _setup_bundled_browser()
        self._playwright = sync_playwright().start()

        args = [
            "--disable-blink-features=AutomationControlled",
            f"--window-size={self.window_width},{self.window_height}",
        ]
        if self.window_x is not None and self.window_y is not None:
            args.append(f"--window-position={self.window_x},{self.window_y}")

        self.context = self._playwright.chromium.launch_persistent_context(
            _user_data_dir(self.instance_id),
            headless=self.headless,
            args=args,
            no_viewport=True,
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/132.0.0.0 Safari/537.36"
            ),
            locale="ko-KR",
            timezone_id="Asia/Seoul",
            geolocation={"latitude": 37.5665, "longitude": 126.9780},
            permissions=["geolocation"],
            color_scheme="light",
        )

        # launch_persistent_context creates first tab automatically
        self.page = self.context.pages[0] if self.context.pages else self.context.new_page()
        self.page.set_default_timeout(30000)

        # Layer 1: playwright-stealth (40+ generic patches)
        Stealth(
            navigator_languages_override=("ko-KR", "ko", "en-US", "en"),
            webgl_vendor_override="Intel Inc.",
            webgl_renderer_override="Intel(R) Iris(R) Xe Graphics",
        ).apply_stealth_sync(self.page)

        # Layer 2: custom stealth.js (Korean-specific overrides on top)
        stealth_js = _load_stealth_script()
        if stealth_js:
            self.context.add_init_script(stealth_js)

        if self.instance_id is not None:
            self.page.on("load", lambda: self.page.evaluate(
                f"document.title = '[{self.instance_id}] ' + document.title"
            ))

        return self.page

    def close(self):
        """Close context (browser) and stop playwright."""
        try:
            if self.context:
                self.context.close()
        finally:
            if self._playwright:
                self._playwright.stop()
