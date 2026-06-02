"""Playwright browser lifecycle management.

Launches Chromium with extra args to reduce automation detection
(headers, navigator.webdriver flag). Fresh context per run avoids
stale session state corrupting subsequent runs.

Auto-detects bundled Playwright browser (from PyInstaller build)
and sets PLAYWRIGHT_BROWSERS_PATH before launching.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Optional

from playwright.sync_api import sync_playwright, Browser, BrowserContext, Page


def _setup_bundled_browser():
    """If running from PyInstaller build, find bundled Playwright browsers
    and set PLAYWRIGHT_BROWSERS_PATH so Playwright can find them."""
    if not getattr(sys, "frozen", False):
        return

    # --onedir: browsers live next to the executable
    exe_dir = Path(sys.executable).parent
    browsers = exe_dir / "playwright-browsers"
    if not browsers.is_dir():
        # --onefile: browsers bundled inside the temp extraction dir
        meipass = getattr(sys, "_MEIPASS", None)
        if meipass:
            browsers = Path(meipass) / "playwright-browsers"

    if browsers.is_dir():
        os.environ.setdefault("PLAYWRIGHT_BROWSERS_PATH", str(browsers))


class PlaywrightClient:
    """Manages Playwright browser instance. Fresh context each time."""

    def __init__(self, headless: bool = False, window_width: int = 700, window_height: int = 780,
                 instance_id: int | None = None):
        self.headless = headless
        self.window_width = window_width
        self.window_height = window_height
        self.instance_id = instance_id
        self._playwright = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None

    def start(self) -> Page:
        """Launch browser with anti-detection args, create context and page."""
        _setup_bundled_browser()
        self._playwright = sync_playwright().start()
        self.browser = self._playwright.chromium.launch(
            headless=self.headless,
            args=[
                f"--window-size={self.window_width},{self.window_height}",
                "--disable-blink-features=AutomationControlled",
            ],
        )
        self.context = self.browser.new_context(
            no_viewport=True,
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/126.0.0.0 Safari/537.36"
            ),
        )
        self.page = self.context.new_page()
        self.page.set_default_timeout(30000)

        # Hide webdriver automation flag
        self.page.add_init_script(
            "Object.defineProperty(navigator, 'webdriver', {get: () => undefined});"
        )

        if self.instance_id is not None:
            self.page.on("load", lambda: self.page.evaluate(
                f"document.title = '[{self.instance_id}] ' + document.title"
            ))

        return self.page

    def close(self):
        """Close context, browser, and stop playwright."""
        try:
            if self.context:
                self.context.close()
            if self.browser:
                self.browser.close()
        finally:
            if self._playwright:
                self._playwright.stop()
