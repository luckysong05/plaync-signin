"""Complete PlayNC sign-in orchestrator.

Delegates to step modules:
  - steps/login.py       → navigate, email, password, submit
  - steps/restricted.py  → restricted account flow
  - steps/identity.py    → first pass, carrier, SMS, identity form
"""

from __future__ import annotations

import logging
import threading
from typing import Callable, Optional

from playwright.sync_api import Page

from .steps._helpers import (
    LOGIN_URL, save_debug_screenshot, _dump_fields, _check_captcha, _user_continue,
)
from .steps.login import (
    step_navigate, step_fill_email, step_click_login_button,
    step_fill_password, step_click_final_login,
)
from .steps.restricted import step_handle_restricted_account
from .steps.identity import (
    step_first_pass_verification, step_dismiss_popups,
    step_select_carrier, step_sms_verification, step_fill_identity_form,
)

logger = logging.getLogger(__name__)


def full_signin(
    page: Page,
    email: str,
    password: str,
    carrier: str = "SKT",
    name: str = "",
    birthday: str = "",
    sex: int = 0,
    phone: str = "",
    on_captcha: Optional[Callable] = None,
    captcha_solved: Optional[threading.Event] = None,
    debug: bool = False,
) -> dict:
    """Run complete multi-step PlayNC sign-in with human-like behavior.

    Returns {'success': bool, 'step': str, 'error': str | None}.
    """
    page._plaync_debug = debug

    try:
        step_navigate(page)
    except Exception as e:
        save_debug_screenshot(page, "01_navigate_error")
        return {"success": False, "step": "navigate", "error": str(e)}

    try:
        step_fill_email(page, email)
    except Exception as e:
        save_debug_screenshot(page, "02_email_error")
        return {"success": False, "step": "fill_email", "error": str(e)}

    try:
        step_click_login_button(page)
    except Exception as e:
        save_debug_screenshot(page, "03_login_btn_error")
        return {"success": False, "step": "click_login_button", "error": str(e)}

    try:
        step_fill_password(page, password)
    except Exception as e:
        save_debug_screenshot(page, "04_password_error")
        return {"success": False, "step": "fill_password", "error": str(e)}

    try:
        step_click_final_login(page)
    except Exception as e:
        save_debug_screenshot(page, "05_final_login_error")
        return {"success": False, "step": "click_final_login", "error": str(e)}
    _dump_fields(page, None, "after_login")

    # Restricted account check
    try:
        restricted_detected = step_handle_restricted_account(
            page, email, phone, on_captcha=on_captcha, captcha_solved=captcha_solved
        )
    except Exception as e:
        logger.warning("Restricted account handler failed (non-fatal): %s", e)
        restricted_detected = False

    if restricted_detected:
        logger.info("Restricted account flow completed — skipping all remaining steps")
        return {"success": True, "step": "restricted_resolved", "error": None}

    # CAPTCHA after login
    if not _check_captcha(page, on_captcha, captcha_solved, "after login"):
        return {"success": False, "step": "captcha_after_login", "error": "CAPTCHA timeout"}
    _dump_fields(page, None, "after_captcha")

    # Identity verification page detection (English variant)
    identity_detected = False
    try:
        identity_detected = page.locator(
            "text=Identity Verification"
        ).first.is_visible(timeout=2000)
    except Exception:
        pass

    if identity_detected:
        logger.info("[Step 7] Identity verification page detected — manual CAPTCHA popup")
        save_debug_screenshot(page, "06_identity_verify")
        _dump_fields(page, None, "identity_verify")
        _user_continue(on_captcha, captcha_solved, "identity verification")
        _dump_fields(page, None, "after_identity_verify")

    # First Pass → dismiss popups → carrier → SMS → identity form
    try:
        step_first_pass_verification(page)
    except Exception as e:
        save_debug_screenshot(page, "06_firstpass_error")
        return {"success": False, "step": "first_pass", "error": str(e)}
    _dump_fields(page, None, "after_firstpass")

    try:
        step_dismiss_popups(page)
    except Exception as e:
        logger.warning("Popup dismissal failed (non-fatal): %s", e)

    try:
        step_select_carrier(page, carrier)
    except Exception as e:
        save_debug_screenshot(page, "07_carrier_error")
        return {"success": False, "step": "select_carrier", "error": str(e)}
    _dump_fields(page, None, "after_carrier")

    try:
        step_sms_verification(page)
    except Exception as e:
        save_debug_screenshot(page, "08_sms_setup_error")
        return {"success": False, "step": "sms_verification", "error": str(e)}
    _dump_fields(page, None, "after_sms")

    try:
        step_fill_identity_form(page, name, birthday, sex, phone,
                                 on_captcha=on_captcha, captcha_solved=captcha_solved)
    except Exception as e:
        save_debug_screenshot(page, "09_identity_error")
        return {"success": False, "step": "identity_form", "error": str(e)}

    logger.info("Full sign-in flow completed")
    return {"success": True, "step": "complete", "error": None}
