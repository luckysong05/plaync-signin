"""Theme and style constants for the application."""

import customtkinter as ctk

# ── Color palette ──────────────────────────────────────────────────
PRIMARY = "#2B5EA7"
SECONDARY = "#1F1F1F"
BG = "#2B2B2B"
FG = "#333333"
TEXT = "#E0E0E0"
SUCCESS = "#2E7D32"
DANGER = "#C62828"
WARNING = "#F9A825"
CAPTCHA_BG = "#3E2723"

# ── Fonts ──────────────────────────────────────────────────────────
FONT_LABEL = ("Segoe UI", 12)
FONT_VALUE = ("Segoe UI", 12, "bold")
FONT_BUTTON = ("Segoe UI", 13)
FONT_HEADER = ("Segoe UI", 14, "bold")
FONT_LOG = ("Consolas", 11)
FONT_TITLE = ("Segoe UI", 18, "bold")


def setup_theme():
    """Configure CustomTkinter appearance."""
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("dark-blue")


def section_label(master, text: str) -> ctk.CTkLabel:
    """Create a section header label."""
    return ctk.CTkLabel(master, text=text, font=FONT_HEADER, anchor="w")
