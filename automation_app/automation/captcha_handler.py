"""CAPTCHA detection and human-in-the-loop handling.

Only flags known CAPTCHA vendors (reCAPTCHA, hCaptcha, Turnstile).
Excludes generic iframes with "challenge" — too many false positives.
"""

from __future__ import annotations

import logging
import time
from typing import Callable, Optional

from playwright.sync_api import Page

logger = logging.getLogger(__name__)

# Only flag established CAPTCHA vendors
CAPTCHA_VENDOR_DOMAINS = [
    "recaptcha",
    "hcaptcha",
    "cf-turnstile",
    "turnstile",
    "arkoselabs",
    "funcaptcha",
    "geetest",
]

CAPTCHA_SELECTORS = [
    'iframe[src*="recaptcha/api"]',
    'iframe[src*="hcaptcha"]',
    'iframe[src*="turnstile"]',
    'iframe[src*="arkoselabs"]',
    'iframe[src*="funcaptcha"]',
    '.g-recaptcha',
    '.h-captcha',
    '.cf-turnstile',
    '[class*="cf-turnstile"]',
]


def detect_captcha(page: Page) -> bool:
    """Check for actual CAPTCHA widgets. Returns True if found.

    Checks:
    1. Known CAPTCHA vendor iframes (reCAPTCHA, hCaptcha, Turnstile)
    2. Known CAPTCHA DOM selectors
    """
    # Check 1: vendor iframes — skip invisible widgets
    for frame in page.frames:
        src = (frame.url or "").lower()
        if "size=invisible" in src:
            continue
        if any(vendor in src for vendor in CAPTCHA_VENDOR_DOMAINS):
            logger.info("Visible CAPTCHA frame detected")
            return True

    # Check 2: DOM selectors
    for sel in CAPTCHA_SELECTORS:
        try:
            count = page.locator(sel).count()
            if count > 0:
                logger.info("CAPTCHA selector match: '%s' (%d found)", sel, count)
                return True
        except Exception:
            continue

    return False


def _is_recaptcha_solved(page: Page) -> bool:
    """Check if reCAPTCHA has a response token (user solved it)."""
    try:
        token = page.evaluate(
            "() => document.querySelector('#g-recaptcha-response')?.value "
            "|| document.querySelector('[name=\"g-recaptcha-response\"]')?.value "
            "|| ''"
        )
        return bool(token and len(token) > 50)
    except Exception:
        return False


def wait_for_captcha_solve(
    page: Page,
    timeout: int = 120,
    on_detected: Optional[Callable] = None,
    solved_event=None,
) -> bool:
    """Block until CAPTCHA solved or timeout. Returns True if solved."""
    if on_detected:
        on_detected()

    deadline = time.time() + timeout
    while time.time() < deadline:
        if solved_event and solved_event.is_set():
            solved_event.clear()
            logger.info("CAPTCHA: user clicked Continue")
            return True

        if not detect_captcha(page):
            logger.info("CAPTCHA: disappeared from page")
            return True

        if _is_recaptcha_solved(page):
            logger.info("CAPTCHA: reCAPTCHA response token detected — user solved it")
            return True

        time.sleep(1)

    logger.warning("CAPTCHA timeout (%ds)", timeout)
    return False
