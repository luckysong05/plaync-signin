"""Login page steps: navigate, email, password, submit."""

from __future__ import annotations

import logging
import random

from playwright.sync_api import Page

from ._helpers import (
    LOGIN_URL, DELAY_MEDIUM, DELAY_LONG,
    sleep, paste_text, human_click, save_debug_screenshot, _random_scroll,
)

logger = logging.getLogger(__name__)


def step_navigate(page: Page):
    logger.info("[Step 1] Navigate to login page")
    page.goto(LOGIN_URL, wait_until="domcontentloaded", timeout=30000)
    _random_scroll(page)
    sleep(*DELAY_MEDIUM)


def step_fill_email(page: Page, email: str):
    logger.info("[Step 2] Fill email field")
    email_selectors = [
        'input[name="id"]', 'input[type="email"]', 'input[name="email"]',
        'input[placeholder*="이메일"]', 'input[placeholder*="아이디"]',
        'input[placeholder*="Email"]', "#id", 'input[id*="id"]',
    ]
    email_el = None
    for sel in email_selectors:
        try:
            el = page.locator(sel).first
            if el.is_visible(timeout=2000):
                email_el = el
                break
        except Exception:
            continue

    if not email_el:
        raise RuntimeError("Email input field not found")

    box = email_el.bounding_box()
    if box:
        cx = int(box["x"] + box["width"] / 2 + random.uniform(-3, 3))
        cy = int(box["y"] + box["height"] / 2 + random.uniform(-3, 3))
        human_click(page, cx, cy)
    else:
        email_el.click()

    sleep(0.3, 0.8)
    email_el.fill("")
    sleep(0.1, 0.2)
    paste_text(page, email)
    sleep(*DELAY_MEDIUM)


def step_click_login_button(page: Page):
    logger.info("[Step 3] Click Login button")
    login_btns = [
        'button[type="submit"]', 'button:has-text("Log In")',
        'button:has-text("로그인")', 'button:has-text("Login")',
        'button:has-text("Next")', 'button:has-text("다음")',
        'a:has-text("로그인")',
    ]
    clicked = False
    for sel in login_btns:
        try:
            el = page.locator(sel).first
            if el.is_visible(timeout=2000):
                box = el.bounding_box()
                if box:
                    cx = int(box["x"] + box["width"] / 2 + random.uniform(-3, 3))
                    cy = int(box["y"] + box["height"] / 2 + random.uniform(-3, 3))
                    human_click(page, cx, cy)
                else:
                    el.click()
                clicked = True
                break
        except Exception:
            continue

    if not clicked:
        page.keyboard.press("Enter")

    # Wait for password field instead of networkidle
    try:
        page.locator('input[type="password"]').first.wait_for(state="visible", timeout=15000)
    except Exception:
        logger.warning("Password field not visible after login button — continuing")
    sleep(*DELAY_MEDIUM)


def step_fill_password(page: Page, password: str):
    logger.info("[Step 4] Fill password field")
    pw_selectors = [
        'input[type="password"]', 'input[name="password"]', 'input[name="pw"]',
        "#pw", 'input[id*="pw"]', 'input[id*="password"]',
        'input[placeholder*="비밀번호"]',
    ]
    pw_el = None
    for sel in pw_selectors:
        try:
            el = page.locator(sel).first
            el.wait_for(state="visible", timeout=3000)
            pw_el = el
            break
        except Exception:
            continue

    if not pw_el:
        raise RuntimeError("Password field not found after email step")

    box = pw_el.bounding_box()
    if box:
        cx = int(box["x"] + box["width"] / 2 + random.uniform(-3, 3))
        cy = int(box["y"] + box["height"] / 2 + random.uniform(-3, 3))
        human_click(page, cx, cy)
    else:
        pw_el.click()

    sleep(0.3, 0.8)
    pw_el.fill("")
    sleep(0.1, 0.2)
    paste_text(page, password)
    sleep(*DELAY_MEDIUM)


def step_click_final_login(page: Page):
    logger.info("[Step 5] Click final login button")
    login_btns = [
        'button[type="submit"]', 'button:has-text("Log In")',
        'button:has-text("로그인")', 'button:has-text("Login")',
        'button:has-text("Sign In")',
    ]
    clicked = False
    for sel in login_btns:
        try:
            el = page.locator(sel).first
            if el.is_visible(timeout=2000):
                box = el.bounding_box()
                if box:
                    cx = int(box["x"] + box["width"] / 2 + random.uniform(-3, 3))
                    cy = int(box["y"] + box["height"] / 2 + random.uniform(-3, 3))
                    human_click(page, cx, cy)
                else:
                    el.click()
                clicked = True
                break
        except Exception:
            continue

    if not clicked:
        page.keyboard.press("Enter")

    # Wait for navigation away from login page or any post-login element
    try:
        page.wait_for_url(f"**/*", timeout=15000)
    except Exception:
        pass
    sleep(*DELAY_LONG)
