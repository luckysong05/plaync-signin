"""Restricted account verification flow after login."""

from __future__ import annotations

import logging
import random
import threading
import time
from typing import Callable, Optional

from playwright.sync_api import Page

from ..captcha_handler import detect_captcha, wait_for_captcha_solve
from ._helpers import sleep, human_click, human_type, save_debug_screenshot

logger = logging.getLogger(__name__)


def step_handle_restricted_account(
    page: Page,
    email: str,
    phone: str = "",
    on_captcha: Optional[Callable] = None,
    captcha_solved: Optional[threading.Event] = None,
):
    """Handle 'account temporarily restricted' flow if it appears after login.

    If not found, returns immediately (no-op).
    """
    logger.info("[Step 6] Checking for restricted account flow...")

    restrict_indicators = [
        "temporarily restricted", "보안 확인", "계정 보호",
        "제한된", "본인 확인",
    ]
    is_restricted = False
    # Check specific text locators first (faster than full body.inner_text)
    for indicator in restrict_indicators:
        try:
            if page.locator(f"text={indicator}").first.is_visible(timeout=1000):
                logger.info("Restricted account indicator found: '%s'", indicator)
                is_restricted = True
                break
        except Exception:
            continue

    # Fallback: full body scan if text locators missed
    if not is_restricted:
        try:
            body = page.locator("body").inner_text(timeout=1000)
            for indicator in restrict_indicators:
                if indicator.lower() in body.lower():
                    logger.info("Restricted account indicator found (body scan): '%s'", indicator)
                    is_restricted = True
                    break
        except Exception:
            pass

    if not is_restricted:
        logger.info("No restricted account flow detected — continuing")
        return False

    sleep(1.0, 2.0)

    # CAPTCHA challenge (if present)
    if detect_captcha(page):
        logger.info("CAPTCHA challenge in restricted account flow")
        save_debug_screenshot(page, "09a_restrict_captcha")
        solved = wait_for_captcha_solve(page, on_detected=on_captcha, solved_event=captcha_solved)
        if not solved:
            logger.warning("CAPTCHA timeout in restricted account flow — continuing anyway")

    sleep(0.5, 1.5)

    # Fill email or phone form
    logger.info("Looking for email/phone confirmation form")
    sleep(1.0, 2.0)

    email_filled = False
    email_sel = [
        'input[name="email"]', 'input[type="email"]',
        'input[placeholder*="email"]', 'input[placeholder*="Email"]',
        'input[placeholder*="이메일"]',
    ]
    for sel in email_sel:
        try:
            el = page.locator(sel).first
            if el.is_visible(timeout=1000):
                box = el.bounding_box()
                if box:
                    cx = int(box["x"] + box["width"] / 2 + random.uniform(-3, 3))
                    cy = int(box["y"] + box["height"] / 2 + random.uniform(-3, 3))
                    human_click(page, cx, cy)
                else:
                    el.click()
                sleep(0.2, 0.5)
                el.fill("")
                sleep(0.1, 0.3)
                human_type(page, email)
                logger.info("Email filled for restricted account verification")
                email_filled = True
                break
        except Exception:
            continue

    if not email_filled:
        phone_sel = [
            'input[name="phone"]', 'input[id*="phone"]',
            'input[placeholder*="phone"]', 'input[placeholder*="Phone"]',
            'input[type="tel"]', 'input[name*="mobile"]',
            'input[placeholder*="휴대폰"]',
        ]
        for sel in phone_sel:
            try:
                el = page.locator(sel).first
                if el.is_visible(timeout=1000):
                    box = el.bounding_box()
                    if box:
                        cx = int(box["x"] + box["width"] / 2 + random.uniform(-3, 3))
                        cy = int(box["y"] + box["height"] / 2 + random.uniform(-3, 3))
                        human_click(page, cx, cy)
                    else:
                        el.click()
                    sleep(0.2, 0.5)
                    el.fill("")
                    sleep(0.1, 0.3)
                    human_type(page, phone if phone else email)
                    logger.info("Phone filled for restricted account verification")
                    email_filled = True
                    break
            except Exception:
                continue

    if not email_filled:
        logger.warning("Could not find email or phone field for restricted account")

    # Click Confirm/Submit
    sleep(0.5, 1.5)
    confirm_selectors = [
        'button:has-text("Confirm")', 'button:has-text("confirm")',
        'button:has-text("Submit")', 'button:has-text("submit")',
        'button:has-text("확인")', 'button:has-text("전송")',
        'button:has-text("Send")', 'button[type="submit"]',
    ]
    for sel in confirm_selectors:
        try:
            el = page.locator(sel).first
            if el.is_visible(timeout=1000):
                box = el.bounding_box()
                if box:
                    cx = int(box["x"] + box["width"] / 2 + random.uniform(-3, 3))
                    cy = int(box["y"] + box["height"] / 2 + random.uniform(-3, 3))
                    human_click(page, cx, cy)
                else:
                    el.click()
                logger.info("Confirm button clicked via '%s'", sel)
                break
        except Exception:
            continue
    else:
        logger.warning("Confirm/Submit button not found for restricted account")

    # Click Complete button
    sleep(1.0, 2.0)
    complete_selectors = [
        'button:has-text("Complete")', 'button:has-text("complete")',
        'button:has-text("Confirm")', 'button:has-text("confirm")',
        'button:has-text("완료")', 'button:has-text("확인")',
        'button:has-text("Done")', 'button:has-text("done")',
        'button:has-text("완성")',
    ]
    for sel in complete_selectors:
        try:
            el = page.locator(sel).first
            if el.is_visible(timeout=1000):
                box = el.bounding_box()
                if box:
                    cx = int(box["x"] + box["width"] / 2 + random.uniform(-3, 3))
                    cy = int(box["y"] + box["height"] / 2 + random.uniform(-3, 3))
                    human_click(page, cx, cy)
                else:
                    el.click()
                logger.info("Complete button clicked via '%s'", sel)
                break
        except Exception:
            continue
    else:
        logger.warning("Complete button not found — may not be needed")

    sleep(2.0, 4.0)
    logger.info("Restricted account flow completed")
    return True
