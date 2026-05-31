"""PlayNC Sign-In Automation — Entry point.

Usage:
    python app.py
"""

from __future__ import annotations

import json
import logging
import sys
from pathlib import Path

from gui.main_window import MainWindow


def load_config() -> dict:
    """Load config.json, return dict with defaults."""
    default = {
        "excel_path": "data/游戏验证.xlsx",
        "headless": False,
        "captcha_timeout_seconds": 120,
        "typing_delay_ms": 50,
        "navigation_timeout_ms": 30000,
        "debug": False,
    }

    config_path = Path(__file__).parent / "config" / "config.json"
    if config_path.exists():
        try:
            with open(config_path) as f:
                return {**default, **json.load(f)}
        except Exception as e:
            print(f"Warning: failed to load config: {e}")

    return default


def setup_logging():
    """Configure logging to both file and stdout."""
    log_dir = Path(__file__).parent / "logs"
    log_dir.mkdir(exist_ok=True)

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.FileHandler(log_dir / "automation.log", encoding="utf-8"),
            logging.StreamHandler(sys.stdout),
        ],
    )


def main():
    setup_logging()
    config = load_config()

    app = MainWindow(config)
    app.mainloop()


if __name__ == "__main__":
    main()
