"""Orchestrates full automation flow in background thread.

Flow: email lookup → display data → launch browser → full sign-in
       (login + First Pass + carrier + SMS + identity form + OTP pause).
On error: keeps browser open, shows error dialog, waits for user
acknowledgment before closing.
"""

from __future__ import annotations

import logging
import threading
import time
from typing import Callable, Optional

from .lookup import LookupResult
from .playwright_client import PlaywrightClient
from .full_signin import full_signin as do_full_signin

logger = logging.getLogger(__name__)


class Runner:
    """Runs automation in a daemon thread. Communicates via callbacks."""

    def __init__(self, config: dict, callbacks: dict[str, Callable]):
        self.config = config
        self.on_log = callbacks.get("on_log", print)
        self.on_status = callbacks.get("on_status", print)
        self.on_data = callbacks.get("on_data", lambda _: None)
        self.on_captcha = callbacks.get("on_captcha", lambda: None)
        self.on_error = callbacks.get("on_error", lambda _: None)
        self.on_complete = callbacks.get("on_complete", lambda _: None)

        self._stop = threading.Event()
        self._paused = threading.Event()
        self._paused.set()
        self._captcha_done = threading.Event()
        self._error_acknowledged = threading.Event()
        self._thread: Optional[threading.Thread] = None

    def start(self, result: LookupResult):
        """Launch worker thread with pre-looked-up data."""
        self._stop.clear()
        self._paused.set()
        self._captcha_done.clear()
        self._error_acknowledged.clear()
        self._thread = threading.Thread(target=self._run, args=(result,), daemon=True)
        self._thread.start()

    def stop(self):
        self._stop.set()
        self._captcha_done.set()
        self._error_acknowledged.set()

    def pause(self):
        self._paused.clear()

    def resume(self):
        self._paused.set()

    def captcha_continue(self):
        self._captcha_done.set()

    def error_continue(self):
        """User acknowledged error — allow browser close and completion."""
        self._error_acknowledged.set()

    @property
    def running(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    def _wait_continue(self):
        while not self._paused.is_set():
            if self._stop.is_set():
                return False
            time.sleep(0.1)
        return not self._stop.is_set()

    def _wait_error_ack(self, msg: str):
        """Show error popup, keep browser open, wait for user OK."""
        self.on_log(f"ERROR: {msg}")
        self.on_status("Error — check browser")
        self.on_error(msg)
        self._error_acknowledged.wait()
        self._error_acknowledged.clear()

    def _run(self, result: LookupResult):
        """Main automation sequence."""
        client = None
        try:
            if not self._wait_continue():
                return

            self.on_data(result)

            if not self._wait_continue():
                return

            # --- Step 1: Launch browser ---
            self.on_status("Launching browser...")
            client = PlaywrightClient(
                headless=self.config.get("headless", False),
            )
            page = client.start()
            self.on_log("Browser ready")

            if not self._wait_continue():
                return

            # Clear cookies so login page isn't redirected by old session
            page.context.clear_cookies()
            self.on_log("Session cleared for fresh login")

            # --- Step 2: Full sign-in ---
            self.on_status("Signing in...")

            cap_cb = lambda: self.on_captcha()
            signin_result = do_full_signin(
                page,
                email=result.email,
                password=result.password,
                carrier=result.carrier,
                name=result.name,
                birthday=result.birthday,
                sex=result.sex,
                phone=result.phone,
                on_captcha=cap_cb,
                captcha_solved=self._captcha_done,
                debug=self.config.get("debug", False),
            )

            if signin_result["success"]:
                self.on_log("Sign-in complete! OTP pending manual entry.")
                self.on_status("Waiting for OTP...")
                self.on_log("OTP confirmed by user — process finished.")
                self.on_status("Done")
                client.close()
                client = None
                self.on_complete({
                    "success": True,
                    "email": result.email,
                    "name": result.name,
                    "step": signin_result.get("step", ""),
                })
            else:
                step = signin_result.get("step", "?")
                err = signin_result["error"]
                self._wait_error_ack(f"Step '{step}' failed: {err}")
                client.close()
                client = None
                self.on_complete({
                    "success": False,
                    "error": err,
                    "step": step,
                })

        except Exception as e:
            logger.exception("Runner error")
            if client:
                self._wait_error_ack(str(e))
                client.close()
                client = None
            else:
                self.on_log(f"Error before browser launch: {e}")
                self.on_status("Error")
            self.on_complete({"success": False, "error": str(e)})
