"""Shared helpers, constants, and CAPTCHA utilities for all step modules."""

from __future__ import annotations

import logging
import random
import time
from pathlib import Path
from typing import Callable, Optional

from playwright.sync_api import Page

from ..captcha_handler import detect_captcha, wait_for_captcha_solve

logger = logging.getLogger(__name__)

# --- Constants ---
LOGIN_URL = "https://login.plaync.com/nclogin/signin?return_url=https%3A%2F%2Fid.plaync.com%2Funban%2Fp0004%2Fintro%3Ffrom%3Dpurple"
SCREENSHOT_DIR = Path(__file__).resolve().parent.parent.parent / "screenshots"

DELAY_SHORT = (0.5, 1.5)
DELAY_MEDIUM = (1.0, 3.0)
DELAY_LONG = (2.0, 4.0)

TYPING_MIN_MS = 50
TYPING_MAX_MS = 150


# --- Core helpers ---


def _rand(a: float, b: float) -> float:
    return random.uniform(a, b)


def sleep(a: float = 0.5, b: float = 1.5):
    time.sleep(_rand(a, b))


def human_type(page: Page, text: str, delay_ms: tuple[int, int] = (TYPING_MIN_MS, TYPING_MAX_MS)):
    for char in text:
        page.keyboard.type(char, delay=random.randint(*delay_ms))


def _get_mouse_pos(page: Page) -> tuple[int, int]:
    try:
        pos = page.evaluate("({x: window.mouseX || 0, y: window.mouseY || 0})")
        return int(pos["x"]), int(pos["y"])
    except Exception:
        return 0, 0


def human_click(page: Page, x: int, y: int, steps: int = 10):
    bx, by = _get_mouse_pos(page)
    mid_x = (bx + x) / 2 + random.randint(-20, 20)
    mid_y = (by + y) / 2 + random.randint(-20, 20)
    page.mouse.move(mid_x, mid_y, steps=steps // 2)
    page.mouse.move(x, y, steps=steps // 2)
    sleep(0.1, 0.3)
    page.mouse.click(x, y)


def click_element(page: Page, selector: str, timeout: int = 15000):
    el = page.locator(selector).first
    el.wait_for(state="visible", timeout=timeout)
    box = el.bounding_box()
    if not box:
        raise RuntimeError(f"Cannot get bounding box for '{selector}'")
    cx = box["x"] + box["width"] / 2 + random.uniform(-3, 3)
    cy = box["y"] + box["height"] / 2 + random.uniform(-3, 3)
    human_click(page, int(cx), int(cy))
    return el


def _click_el(page: Page, el):
    try:
        box = el.bounding_box()
        if box:
            cx = int(box["x"] + box["width"] / 2 + random.uniform(-3, 3))
            cy = int(box["y"] + box["height"] / 2 + random.uniform(-3, 3))
            human_click(page, cx, cy)
        else:
            el.click()
    except Exception:
        try:
            el.click()
        except Exception:
            logger.warning("Could not click element")


def _find_first(page: Page, ctx_frame, selectors, timeout=1000):
    """Find first matching visible element in page or iframe context."""
    ctx = ctx_frame if ctx_frame else page
    for sel in selectors:
        try:
            el = ctx.locator(sel).first
            el.wait_for(state="attached", timeout=timeout)
            if el.is_visible():
                box = el.bounding_box()
                if box and box["width"] > 0 and box["height"] > 0:
                    return el
        except Exception:
            continue
    return None


def _random_scroll(page: Page):
    delta = random.randint(-80, 80)
    page.evaluate(f"window.scrollBy(0, {delta})")
    sleep(0.3, 0.8)


# --- Debug ---


def save_debug_screenshot(page: Page, label: str):
    if not getattr(page, "_plaync_debug", False):
        return
    SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)
    ts = time.strftime("%Y%m%d-%H%M%S")
    path = SCREENSHOT_DIR / f"{label}_{ts}.png"
    try:
        page.screenshot(path=str(path), full_page=True)
        logger.info("Screenshot saved: %s", path)
    except Exception as e:
        logger.warning("Failed screenshot: %s", e)


def _dump_fields(page: Page, ctx_frame, label: str = ""):
    if not getattr(page, "_plaync_debug", False):
        return
    ctx = ctx_frame if ctx_frame else page
    tag = f" [{label}]" if label else ""
    try:
        logger.info("--- Page dump%s ---", tag)
        try:
            body_text = (ctx.locator("body").inner_text(timeout=2000) or "")[:500]
            logger.info("  BODY TEXT: %s", body_text.replace("\n", " | "))
        except Exception:
            pass
        for h_tag in ["h1", "h2", "h3", "h4"]:
            for h in ctx.locator(f"{h_tag}:visible").all():
                txt = (h.inner_text() or "")[:80]
                if txt.strip():
                    logger.info("  <%s> %s", h_tag, txt)
        for lb in ctx.locator("label:visible, span:visible, p:visible, strong:visible").all():
            txt = (lb.inner_text() or "")[:60]
            if txt.strip():
                logger.info("  <label> %s", txt)
        logger.info("--- Inputs ---")
        for inp in ctx.locator("input:visible, select:visible, textarea:visible").all():
            tag_name = inp.evaluate("el => el.tagName")
            n = inp.get_attribute("name") or ""
            i = inp.get_attribute("id") or ""
            t = inp.get_attribute("type") or ""
            p = inp.get_attribute("placeholder") or ""
            c = inp.get_attribute("class") or ""
            v = inp.get_attribute("value") or ""
            logger.info("  <%s> name='%s' id='%s' type='%s' placeholder='%s' class='%s' value='%s'",
                        tag_name.lower(), n, i, t, p, c[:60], v[:20])
        logger.info("--- Buttons ---")
        for btn in ctx.locator("button:visible, a:visible, [role='button']:visible").all():
            txt = (btn.inner_text() or "")[:60]
            i = btn.get_attribute("id") or ""
            c = btn.get_attribute("class") or ""
            logger.info("  <button> text='%s' id='%s' class='%s'", txt, i, c[:60])
        logger.info("--- Page dump end%s ---", tag)
    except Exception as e:
        logger.warning("Page dump failed: %s", e)


# --- CAPTCHA utilities ---


def _user_continue(on_captcha, captcha_solved, label=""):
    """Show manual CAPTCHA popup, block until user clicks Continue."""
    logger.info("Manual CAPTCHA popup shown%s", f" — {label}" if label else "")
    if on_captcha:
        on_captcha()
    if captcha_solved:
        captcha_solved.wait()
        captcha_solved.clear()
        logger.info("CAPTCHA confirmed by user")


def _check_captcha(page: Page, on_captcha, captcha_solved, label="") -> bool:
    """Detect CAPTCHA and wait for user solve. Returns False only on timeout."""
    if not detect_captcha(page):
        return True
    logger.info("CAPTCHA detected%s", f" — {label}" if label else "")
    return wait_for_captcha_solve(page, on_detected=on_captcha, solved_event=captcha_solved)
