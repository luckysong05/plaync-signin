"""Identity verification steps: carrier, SMS, identity form."""

from __future__ import annotations

import logging
import random
import threading
from typing import Callable, Optional

from playwright.sync_api import Page

from ._helpers import (
    DELAY_MEDIUM, DELAY_LONG,
    sleep, paste_text, human_click, _click_el, _find_first,
    _dump_fields, _user_continue, save_debug_screenshot,
)

logger = logging.getLogger(__name__)


def step_first_pass_verification(page: Page):
    """Click 'First Pass' / identity verification button."""
    logger.info("[Step 7] Click First Pass / identity verification")
    first_pass_selectors = [
        'button:has-text("First Pass")', 'button:has-text("본인인증")',
        'button:has-text("인증")', 'a:has-text("First Pass")',
        'a:has-text("본인인증")', 'img[alt*="firstpass"]',
        'img[alt*="본인인증"]', 'button:has-text("휴대폰 인증")',
        'button:has-text("phone")', 'button:has-text("인증하기")',
        '[class*="firstpass"]', '[class*="btn"]:has-text("인증")',
    ]
    for sel in first_pass_selectors:
        try:
            el = page.locator(sel).first
            if el.is_visible(timeout=2000):
                box = el.bounding_box()
                if box:
                    cx = int(box["x"] + box["width"] / 2 + random.uniform(-2, 2))
                    cy = int(box["y"] + box["height"] / 2 + random.uniform(-2, 2))
                    human_click(page, cx, cy)
                else:
                    el.click()
                logger.info("First Pass button found and clicked: '%s'", sel)
                sleep(*DELAY_MEDIUM)
                return
        except Exception:
            continue

    logger.warning("First Pass button not found — may already be on carrier page")


def step_dismiss_popups(page: Page):
    """Dismiss interstitial popups/dialogs before carrier selection."""
    logger.info("[Step 8] Dismissing popups...")
    dismiss_selectors = [
        'button:has-text("닫기")', 'button:has-text("Close")',
        'button:has-text("close")', 'button:has-text("확인")',
        'button:has-text("OK")', 'button:has-text("동의")',
        'button:has-text("동의함")', 'button:has-text("Agree")',
        'button:has-text("agree")', 'button:has-text("취소")',
        'button:has-text("Cancel")', 'button:has-text("cancel")',
        'button:has-text("X")', '[class*="close"]', '[class*="dimiss"]',
        '[class*="popup"] button:first-child',
        '[class*="modal"] button:first-child',
        '[class*="layer"] button:first-child',
        '[class*="overlay"] button:first-child',
        '[class*="alert"] button:first-child',
    ]
    dismissed = False
    for sel in dismiss_selectors:
        try:
            el = page.locator(sel).first
            if not el.is_visible(timeout=800):
                continue
            txt = (el.inner_text() or "")[:30]
            if "알뜰폰" in txt or "btn_check" in (el.get_attribute("class") or ""):
                continue
            box = el.bounding_box()
            if box:
                cx = int(box["x"] + box["width"] / 2 + random.uniform(-3, 3))
                cy = int(box["y"] + box["height"] / 2 + random.uniform(-3, 3))
                human_click(page, cx, cy)
            else:
                el.click()
            logger.info("Popup dismissed via '%s' (text='%s')", sel, txt)
            dismissed = True
            sleep(0.5, 1.5)
            break
        except Exception:
            continue

    if dismissed:
        for sel in dismiss_selectors:
            try:
                el = page.locator(sel).first
                if el.is_visible(timeout=500):
                    el.click()
                    logger.info("Secondary popup dismissed")
                    sleep(0.3, 0.8)
                    break
            except Exception:
                continue
    else:
        logger.info("No popups detected, proceeding")


def step_select_carrier(page: Page, carrier: str):
    """Select carrier: SKT, KT, LGU+ (or LG U+), MVNO."""
    logger.info("[Step 9] Select carrier: %s", carrier)

    carrier_page_selectors = [
        'button:has-text("SKT")', 'button:has-text("KT")',
        'button:has-text("LGU+")', 'button:has-text("SK")',
        'input[type="radio"]',
    ]
    carrier_found = False
    for sel in carrier_page_selectors:
        try:
            page.locator(sel).first.wait_for(state="visible", timeout=3000)
            carrier_found = True
            logger.info("Carrier page loaded — element visible: '%s'", sel)
            break
        except Exception:
            continue
    if not carrier_found:
        logger.warning("Carrier elements not found — proceeding anyway")
    else:
        sleep(0.5, 1.0)

    carrier_map = {
        "skt": "SKT", "kt": "KT",
        "lgu": "LG U+", "lgu+": "LG U+", "lg u+": "LG U+", "lg": "LG U+",
        "mvno": "MVNO", "알뜰폰": "MVNO",
        "skt알뜰폰": "SKT알뜰폰", "kt알뜰폰": "KT알뜰폰",
        "lgu+알뜰폰": "LG U+알뜰폰", "lg u+알뜰폰": "LG U+알뜰폰",
        "lg알뜰폰": "LGU+알뜰폰",
    }
    target = carrier_map.get(carrier.strip().lower().replace(" ", ""), carrier)

    for btn in page.locator("button:visible").all():
        try:
            btn_txt = btn.inner_text().replace("\n", "").replace("\r", "").strip()
            if btn_txt == target:
                _click_el(page, btn)
                logger.info("Carrier '%s' selected", target)
                sleep(*DELAY_MEDIUM)
                return
        except Exception:
            continue

    raise RuntimeError(f"Could not select carrier '{target}'")


def step_sms_verification(page: Page):
    """Select SMS → check terms → click confirm button."""
    logger.info("[Step 10] SMS verification: select SMS → checkbox → confirm")

    # Wait for cert method page
    logger.info("Waiting for certification method page...")
    cert_found = False
    for sel in ['[class*="cert"]', 'button:has-text("문자")', 'button:has-text("SMS")']:
        try:
            page.locator(sel).first.wait_for(state="visible", timeout=3000)
            cert_found = True
            logger.info("Cert method page loaded — '%s' visible", sel)
            break
        except Exception:
            continue
    if not cert_found:
        logger.warning("Cert method page not found — may already be past this step")

    sms_selectors = [
        'button:has-text("문자(SMS)")', 'button:has-text("문자")',
        'button:has-text("SMS")', 'button.certAuthCheck:has-text("SMS")',
        'button.certAuthCheck:has-text("문자")', 'button.certAuthCheck',
        '[class*="certAuth"]:has-text("SMS")', 'button.certAuthCheck:nth-child(1)',
    ]
    sms_clicked = False
    for sel in sms_selectors:
        try:
            el = page.locator(sel).first
            if el.is_visible(timeout=1500):
                box = el.bounding_box()
                if box:
                    cx = int(box["x"] + box["width"] / 2 + random.uniform(-3, 3))
                    cy = int(box["y"] + box["height"] / 2 + random.uniform(-3, 3))
                    human_click(page, cx, cy)
                else:
                    el.click()
                logger.info("SMS cert method selected via '%s'", sel)
                sms_clicked = True
                break
        except Exception:
            continue

    if not sms_clicked:
        try:
            el = page.locator('button.certAuthCheck').first
            el.wait_for(state="visible", timeout=3000)
            box = el.bounding_box()
            if box:
                cx = int(box["x"] + box["width"] / 2 + random.uniform(-3, 3))
                cy = int(box["y"] + box["height"] / 2 + random.uniform(-3, 3))
                human_click(page, cx, cy)
            else:
                el.click()
            logger.info("SMS cert method selected via first certAuthCheck button")
            sms_clicked = True
        except Exception:
            pass

    if not sms_clicked:
        logger.warning("Could not click SMS cert method button")
    else:
        sleep(0.3, 0.6)
        # Wait for terms section
        try:
            page.locator('input[type="checkbox"]').first.wait_for(state="visible", timeout=5000)
        except Exception:
            pass

    # Check terms agreement checkbox
    logger.info("Looking for terms checkbox")
    terms_selectors = [
        'input[type="checkbox"]', 'input[id*="agree"]', 'input[id*="terms"]',
        'input[id*="동의"]', 'label:has-text("동의")', 'span:has-text("동의")',
        'input[name*="agree"]', '[class*="agree"]', '[class*="terms"]',
        'input[id*="chk"]',
    ]
    for sel in terms_selectors:
        try:
            el = page.locator(sel).first
            if el.is_visible(timeout=1000):
                if el.is_checked():
                    logger.info("Terms already checked")
                else:
                    box = el.bounding_box()
                    if box:
                        cx = int(box["x"] + box["width"] / 2 + random.uniform(-2, 2))
                        cy = int(box["y"] + box["height"] / 2 + random.uniform(-2, 2))
                        human_click(page, cx, cy)
                    else:
                        el.click()
                    logger.info("Terms checkbox checked via '%s'", sel)
                sleep(0.3, 0.6)
                break
        except Exception:
            continue
    else:
        logger.warning("Terms checkbox not found — proceeding")

    # Click confirm button
    logger.info("Looking for confirm button after terms")
    confirm_selectors = [
        'button:has-text("다음")', 'button:has-text("Next")',
        'button:has-text("next")', 'button:has-text("확인")',
        'button:has-text("Continue")', 'button:has-text("본인확인")',
        'button:has-text("인증하기")', 'button[type="submit"]',
        'button:has-text("동의")',
    ]
    for sel in confirm_selectors:
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
                logger.info("Confirm button clicked via '%s'", sel)
                break
        except Exception:
            continue
    else:
        logger.warning("Confirm button not found after terms — proceeding")

    # Wait for identity iframe to appear
    sleep(0.3, 0.6)
    save_debug_screenshot(page, "11_after_sms_confirm")


def step_fill_identity_form(
    page: Page,
    name: str,
    birthday: str,
    sex: int,
    phone: str,
    on_captcha: Optional[Callable] = None,
    captcha_solved: Optional[threading.Event] = None,
):
    """Fill identity form popup: name, birthday, gender, phone, request SMS."""
    logger.info("[Step 11] Fill identity form: %s, %s, sex=%d, %s", name, birthday, sex, phone)

    save_debug_screenshot(page, "13_identity_form")

    _dump_fields(page, None, "identity_form_initial")

    def _fill_and_next(field_name, value, selectors, has_next=True):
        el = _find_first(page, None, selectors, timeout=5000)
        if not el:
            logger.warning("%s field not found", field_name)
            return False
        sleep(0.2, 0.5)
        _click_el(page, el)
        sleep(0.1, 0.3)
        el.fill("")
        sleep(0.1, 0.2)
        paste_text(page, value)
        logger.info("%s filled: %s", field_name, value)
        if has_next:
            sleep(0.3, 0.6)
            next_el = None
            next_selectors = [
                '.btnUserName_sms', 'button.btn_pass',
                'button:has-text("다음")', 'button:has-text("Next")',
                'button:has-text("next")', 'button:has-text("확인")',
                'button:has-text("Confirm")',
                '[class*="btn_pass"]',
            ]
            ctx = page
            for sel in next_selectors:
                try:
                    el = ctx.locator(sel).first
                    el.wait_for(state="attached", timeout=2000)
                    if el.is_visible(timeout=1000):
                        next_el = el
                        logger.info("Next button found via '%s'", sel)
                        break
                except Exception:
                    continue
            if not next_el:
                try:
                    el = ctx.locator('button.btn_pass').first
                    if el.is_visible(timeout=800):
                        next_el = el
                        logger.info("Next button found via btn_pass class")
                except Exception:
                    pass
            if next_el:
                _click_el(page, next_el)
                logger.info("Next clicked after %s", field_name)
                sleep(0.5, 1.0)
                # Wait for next field
                try:
                    page.locator('#myNum1, #myNum2, #sms_mobileno').first.wait_for(
                        state="visible", timeout=5000
                    )
                except Exception:
                    pass
                _dump_fields(page, None)
            else:
                raise RuntimeError(f"Next button not found after {field_name}")
        return True

    # Name (page 1 → Next to page 2)
    if not _fill_and_next("name", name, [
        'input[name="username"]', '#sms_username', 'input[id*="sms_"]',
        'input[placeholder*="이름"]', 'input[class*="userName"]',
        'input[name="name"]', 'input[id*="name"]',
    ]):
        raise RuntimeError("Name field not found in identity form")

    # Birthday → Tab → sex → phone (same page)
    bday_ok = _fill_and_next("birthday", birthday, [
        '#myNum1', 'input.myNum1', 'input[placeholder*="생년월일"]',
        'input[placeholder*="Birth"]', 'input[id*="myNum"]',
        'input[name*="birth"]', 'input[maxlength="8"]', 'input[maxlength="10"]',
    ], has_next=False)
    if not bday_ok:
        raise RuntimeError("Birthday field not found in identity form")

    sleep(0.2, 0.3)
    page.keyboard.press("Tab")
    sleep(0.2, 0.3)

    sex_ok = _fill_and_next("sex", str(sex), [
        '#myNum2', 'input.myNum2', 'input[class*="myNum2"]',
        'input[placeholder*="gender"]', 'input[maxlength="1"]',
        'input[type="tel"]:not(#myNum1)',
    ], has_next=False)
    if not sex_ok:
        raise RuntimeError("Sex field not found in identity form")

    # Phone appears dynamically after birthday/sex
    sleep(0.5, 1.0)
    _dump_fields(page, None, "after_birthday_sex")
    phone_ok = _fill_and_next("phone", phone, [
        '#sms_mobileno', 'input[name="mobileno"]',
        'input[placeholder*="휴대폰"]',
        'input[id*="phone"]', 'input[name*="phone"]',
        'input[placeholder*="Phone"]', 'input[name*="mobile"]',
        'input[type="tel"]:not(#myNum1):not(#myNum2)',
        'input:not(#myNum1):not(#myNum2):not(#sms_username)',
    ], has_next=False)

    if not phone_ok:
        raise RuntimeError("Phone field not found in identity form")

    # Always pause for manual CAPTCHA check after phone
    _user_continue(on_captcha, captcha_solved, "after phone entry")

    # Click Next/Continue after CAPTCHA
    logger.info("Clicking Next/Continue after CAPTCHA")
    next_sel = [
        'button:has-text("다음")', 'button:has-text("Next")', 'button:has-text("next")',
        'button:has-text("계속")', 'button:has-text("Continue")', 'button:has-text("continue")',
        'button:has-text("확인")',
        'button:has-text("인증번호")', 'button:has-text("인증")', 'button:has-text("Request")',
        'button:has-text("Send")', 'button:has-text("전송")', 'button:has-text("본인인증")',
        'button:has-text("sms")', 'button:has-text("SMS")',
        'button:has-text("인증번호 요청")', 'button:has-text("인증번호 전송")',
    ]
    final_el = _find_first(page, None, next_sel, timeout=2000)
    if final_el:
        _click_el(page, final_el)
        logger.info("Final Next/Continue clicked after CAPTCHA")
    else:
        logger.warning("Final button after CAPTCHA not found")

    return True
