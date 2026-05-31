"""Reusable GUI widgets."""

from __future__ import annotations

import customtkinter as ctk


class LabeledValue(ctk.CTkFrame):
    """A label: value pair displayed side-by-side."""

    def __init__(self, master, label: str, value: str = "—", **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.label_widget = ctk.CTkLabel(self, text=f"{label}:", font=("Segoe UI", 12), width=80, anchor="e")
        self.label_widget.pack(side="left", padx=(0, 8))

        self.value_widget = ctk.CTkLabel(self, text=value, font=("Segoe UI", 12, "bold"), anchor="w")
        self.value_widget.pack(side="left", fill="x", expand=True)

    def set(self, value: str):
        self.value_widget.configure(text=value or "—")


class PasswordField(ctk.CTkFrame):
    """Password display — plain text, no mask."""

    def __init__(self, master, label: str = "Password:", **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)

        ctk.CTkLabel(self, text=label, font=("Segoe UI", 12), width=80, anchor="e").pack(side="left", padx=(0, 8))

        self.entry = ctk.CTkEntry(self, font=("Segoe UI", 12), width=200, state="readonly")
        self.entry.pack(side="left", fill="x", expand=True, padx=(0, 4))

    def set(self, value: str):
        self.entry.configure(state="normal")
        self.entry.delete(0, "end")
        self.entry.insert(0, value)
        self.entry.configure(state="readonly")
