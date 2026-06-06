"""Main application window."""

from __future__ import annotations

import logging
import threading
from tkinter import filedialog, messagebox
from typing import Optional

import customtkinter as ctk

from .styles import setup_theme, section_label, FONT_LOG, FONT_BUTTON, CAPTCHA_BG, SUCCESS, DANGER, WARNING
from automation.runner import Runner
from automation.lookup import lookup, LookupResult

logger = logging.getLogger(__name__)


class MainWindow(ctk.CTk):
    """Application main window with all control sections."""

    def __init__(self, config: dict):
        super().__init__()
        self.config = config
        self.runner: Optional[Runner] = None
        self._last_result: Optional[LookupResult] = None

        self._setup_window()
        self._build_ui()
        self._bind_callbacks()

    # ── Window setup ───────────────────────────────────────────────

    def _setup_window(self):
        setup_theme()
        self.title("PlayNC Sign-In Automation")
        x = self.config.get("window_x")
        y = self.config.get("window_y")
        geom = f"400x600" + (f"+{x}+{y}" if x is not None and y is not None else "")
        self.geometry(geom)
        self.minsize(400, 600)

    # ── Build UI sections ──────────────────────────────────────────

    def _build_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(5, weight=1)  # log area expands

        row = 0
        self._build_excel_section(row)
        row += 1
        self._build_email_section(row)
        row += 1
        self._build_controls_section(row)
        row += 1
        self._build_captcha_section(row)
        row += 1
        self._build_error_section(row)
        row += 1
        self._build_log_section(row)
        row += 1
        self._build_summary_section(row)

    def _build_excel_section(self, row: int):
        frame = ctk.CTkFrame(self)
        frame.grid(row=row, column=0, sticky="ew", padx=10, pady=(10, 2))
        frame.grid_columnconfigure(1, weight=1)

        section_label(frame, "Excel File").grid(row=0, column=0, columnspan=3, sticky="w", padx=10, pady=(8, 4))

        default_path = self.config.get("excel_path", "data/游戏验证.xlsx")
        self.excel_path_var = ctk.StringVar(value=default_path)

        ctk.CTkEntry(frame, textvariable=self.excel_path_var).grid(row=1, column=0, columnspan=2, sticky="ew", padx=10, pady=(0, 8))
        ctk.CTkButton(frame, text="Browse", width=80, command=self._browse_excel).grid(row=1, column=2, padx=(0, 10), pady=(0, 8))

    def _build_email_section(self, row: int):
        frame = ctk.CTkFrame(self)
        frame.grid(row=row, column=0, sticky="ew", padx=10, pady=2)
        frame.grid_columnconfigure(0, weight=1)

        section_label(frame, "Email").grid(row=0, column=0, sticky="w", padx=10, pady=(8, 4))

        self.email_var = ctk.StringVar()
        ctk.CTkEntry(frame, textvariable=self.email_var, placeholder_text="Enter email address").grid(
            row=1, column=0, sticky="ew", padx=10, pady=(0, 8)
        )

    def _build_controls_section(self, row: int):
        frame = ctk.CTkFrame(self)
        frame.grid(row=row, column=0, sticky="ew", padx=10, pady=2)
        frame.grid_columnconfigure(1, weight=1)

        btn_frame = ctk.CTkFrame(frame, fg_color="transparent")
        btn_frame.grid(row=0, column=0, padx=10, pady=8)

        self.start_btn = ctk.CTkButton(btn_frame, text="▶  Start", command=self._on_start, font=FONT_BUTTON,
                                        fg_color=SUCCESS, hover_color="#1B5E20", width=100)
        self.start_btn.pack(side="left", padx=(0, 6))

        self.reset_btn = ctk.CTkButton(btn_frame, text="↺  Reset", command=self._on_reset, font=FONT_BUTTON,
                                        fg_color=WARNING, text_color="#000", width=100)
        self.reset_btn.pack(side="left", padx=6)
        self.reset_btn.pack_forget()

        self.stop_btn = ctk.CTkButton(btn_frame, text="■  Stop", command=self._on_stop, font=FONT_BUTTON,
                                       fg_color=DANGER, hover_color="#B71C1C", width=100, state="disabled")
        self.stop_btn.pack(side="left", padx=6)

    def _build_captcha_section(self, row: int):
        self.captcha_frame = ctk.CTkFrame(self, fg_color=CAPTCHA_BG)
        self.captcha_frame.grid(row=row, column=0, sticky="ew", padx=10, pady=2)
        self.captcha_frame.grid_columnconfigure(0, weight=1)
        self.captcha_frame.grid_remove()

        ctk.CTkLabel(self.captcha_frame, text="⚠ CAPTCHA Detected",
                      font=("Segoe UI", 14, "bold"), text_color="#FFB74D").grid(row=0, column=0, pady=(8, 2))
        ctk.CTkLabel(self.captcha_frame, text="Please solve the CAPTCHA in the browser window.\n"
                                               "Then click Continue below.",
                      font=("Segoe UI", 12)).grid(row=1, column=0, pady=2)
        self.continue_btn = ctk.CTkButton(self.captcha_frame, text="Continue", command=self._on_captcha_continue,
                                           font=FONT_BUTTON, fg_color=WARNING, text_color="#000",
                                           width=120)
        self.continue_btn.grid(row=2, column=0, pady=(4, 8))
        self.captcha_timeout_label = ctk.CTkLabel(self.captcha_frame, text="", font=("Segoe UI", 10))
        self.captcha_timeout_label.grid(row=3, column=0, pady=(0, 4))

    def _build_error_section(self, row: int):
        self.error_frame = ctk.CTkFrame(self, fg_color="#4A0000")
        self.error_frame.grid(row=row, column=0, sticky="ew", padx=10, pady=2)
        self.error_frame.grid_columnconfigure(0, weight=1)
        self.error_frame.grid_remove()

        ctk.CTkLabel(self.error_frame, text="Error — Browser Kept Open",
                      font=("Segoe UI", 14, "bold"), text_color="#EF9A9A").grid(row=0, column=0, pady=(8, 2))
        self.error_msg_label = ctk.CTkLabel(self.error_frame, text="",
                                            font=("Segoe UI", 11), wraplength=600)
        self.error_msg_label.grid(row=1, column=0, pady=2, padx=10)
        ctk.CTkLabel(self.error_frame, text="Fix the issue in the browser, then click Continue.\n"
                                             "Or click Stop to cancel.",
                      font=("Segoe UI", 12)).grid(row=2, column=0, pady=2)
        self.error_continue_btn = ctk.CTkButton(self.error_frame, text="Continue",
                                                command=self._on_error_continue,
                                                font=FONT_BUTTON, fg_color=DANGER, width=120)
        self.error_continue_btn.grid(row=3, column=0, pady=(4, 8))

    def _build_log_section(self, row: int):
        frame = ctk.CTkFrame(self)
        frame.grid(row=row, column=0, sticky="nsew", padx=10, pady=2)
        frame.grid_rowconfigure(1, weight=1)
        frame.grid_columnconfigure(0, weight=1)

        section_label(frame, "Log").grid(row=0, column=0, sticky="w", padx=10, pady=(8, 4))

        self.log_text = ctk.CTkTextbox(frame, font=FONT_LOG, wrap="none", state="disabled")
        self.log_text.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 8))

    def _build_summary_section(self, row: int):
        frame = ctk.CTkFrame(self)
        frame.grid(row=row, column=0, sticky="ew", padx=10, pady=(2, 10))
        frame.grid_columnconfigure(2, weight=1)

        self.success_label = ctk.CTkLabel(frame, text="✓ Success: —", font=("Segoe UI", 12), text_color="#81C784")
        self.success_label.grid(row=0, column=0, padx=10, pady=8)

        self.fail_label = ctk.CTkLabel(frame, text="✗ Failed: —", font=("Segoe UI", 12), text_color="#EF9A9A")
        self.fail_label.grid(row=0, column=1, padx=10, pady=8)

        self.export_btn = ctk.CTkButton(frame, text="Export Results", command=self._on_export,
                                         font=FONT_BUTTON, state="disabled")
        self.export_btn.grid(row=0, column=2, padx=(0, 10), pady=8, sticky="e")

    # ── Event binding ──────────────────────────────────────────────

    def _bind_callbacks(self):
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    # ── Actions ────────────────────────────────────────────────────

    def _browse_excel(self):
        path = filedialog.askopenfilename(
            title="Select Excel File",
            filetypes=[("Excel files", "*.xlsx *.xls"), ("All files", "*.*")]
        )
        if path:
            self.excel_path_var.set(path)

    def _on_start(self):
        email = self.email_var.get().strip()
        if not email:
            messagebox.showwarning("Input Required", "Please enter an email address.")
            return

        if self.runner and self.runner.running:
            messagebox.showinfo("Already Running", "Automation is already in progress.")
            return

        # Reset UI for run
        self.log_text.configure(state="normal")
        self.log_text.delete("0.0", "end")
        self.log_text.configure(state="disabled")
        self.success_label.configure(text="✓ Success: —")
        self.fail_label.configure(text="✗ Failed: —")
        self.export_btn.configure(state="disabled")
        self.start_btn.configure(state="disabled")
        self.reset_btn.pack_forget()
        self.stop_btn.configure(state="normal")
        self.captcha_frame.grid_remove()
        self.error_frame.grid_remove()

        self._log(f"Looking up: {email}")
        self._log("Looking up...")
        self.runner = None
        self._last_result = None

        threading.Thread(target=self._do_start, args=(email,), daemon=True).start()

    def _do_start(self, email: str):
        try:
            excel_path = self.excel_path_var.get()
            result = lookup(email, excel_path)
            self.after(0, self._on_lookup_result, result)
        except Exception as e:
            self.after(0, self._on_lookup_error, str(e))

    def _on_lookup_result(self, result: LookupResult):
        if not result.success:
            self._log(f"Lookup failed: {result.error}")
            self._log("Lookup failed")
            self._enable_controls()
            return

        missing = []
        if not result.name:
            missing.append("name")
        if not result.birthday:
            missing.append("birthday")
        if missing:
            msg = f"Identity data incomplete: {', '.join(missing)} not found for this account"
            self._log(f"Lookup failed: {msg}")
            self._log("Lookup failed")
            self._enable_controls()
            return

        self._last_result = result
        self._log(f"Found: {result.name} | {result.phone} | {result.email}")
        self._log("Signing in...")

        self._start_runner(result)

    def _on_lookup_error(self, error: str):
        self._log(f"Lookup error: {error}")
        self._log("Error")
        self._enable_controls()

    def _start_runner(self, result: LookupResult):
        self.runner = Runner(
            config={
                **self.config,
                "excel_path": self.excel_path_var.get(),
                "window_width": 600,
                "window_height": 800,
            },
            callbacks={
                "on_log": self._log,
                "on_status": self._log,
                "on_data": lambda _: None,
                "on_captcha": self._show_captcha,
                "on_error": self._show_error,
                "on_complete": self._on_complete,
            },
        )
        self.runner.start(result)

    def _on_stop(self):
        if self.runner:
            self.runner.stop()
            self._log("User requested stop.")
            self._log("Stopped")
            self._enable_controls()
            self.runner = None

    def _on_reset(self):
        self.log_text.configure(state="normal")
        self.log_text.delete("0.0", "end")
        self.log_text.configure(state="disabled")
        self.success_label.configure(text="✓ Success: —")
        self.fail_label.configure(text="✗ Failed: —")
        self.export_btn.configure(state="disabled")
        self._log("Ready")
        self.reset_btn.pack_forget()
        self.start_btn.configure(state="normal")
        self.captcha_frame.grid_remove()
        self.error_frame.grid_remove()
        self.runner = None
        self._last_result = None

    def _on_captcha_continue(self):
        if self.runner:
            self.runner.captcha_continue()
        self.captcha_frame.grid_remove()

    def _on_export(self):
        path = filedialog.asksaveasfilename(
            title="Export Results",
            defaultextension=".xlsx",
            filetypes=[("Excel files", "*.xlsx")]
        )
        if path:
            self._log(f"Results exported to {path}")

    def _on_close(self):
        if self.runner and self.runner.running:
            self.runner.stop()
        self.destroy()

    # ── GUI updates (thread-safe via after) ────────────────────────

    def _log(self, message: str):
        self.after(0, self._do_log, message)

    def _do_log(self, message: str):
        self.log_text.configure(state="normal")
        self.log_text.insert("end", f"{message}\n")
        self.log_text.see("end")
        self.log_text.configure(state="disabled")

    def _show_captcha(self):
        self.after(0, self.captcha_frame.grid)

    def _show_error(self, msg: str):
        def show():
            self.error_msg_label.configure(text=msg)
            self.error_frame.grid()
        self.after(0, show)

    def _on_error_continue(self):
        if self.runner:
            self.runner.error_continue()
        self.error_frame.grid_remove()

    def _on_complete(self, result: dict):
        self.after(0, self._do_complete, result)

    def _do_complete(self, result: dict):
        if result.get("success"):
            self.success_label.configure(text=f'✓ Success: {result.get("email", "")}')
        else:
            self.fail_label.configure(text=f'✗ Failed: {result.get("error", "Unknown error")}')
        self.stop_btn.configure(state="disabled")
        self.reset_btn.pack(before=self.stop_btn, side="left", padx=6)
        self.runner = None

    def _enable_controls(self):
        self.start_btn.configure(state="normal")
        self.stop_btn.configure(state="disabled")
        self.captcha_frame.grid_remove()
        self.error_frame.grid_remove()
