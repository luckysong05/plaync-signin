"""PlayNC Sign-In Automation — Entry point.

Usage:
    python app.py              # prompts for instance count
    python app.py 3            # three instances, no prompt
"""

from __future__ import annotations

import json
import logging
import multiprocessing
import sys
from pathlib import Path

from gui.main_window import MainWindow


def _prompt_instance_count() -> int:
    """Show popup asking how many GUIs to open. Falls back to 1 if cancelled."""
    try:
        import tkinter
        from tkinter import simpledialog

        root = tkinter.Tk()
        root.withdraw()
        root.attributes("-topmost", True)
        count = simpledialog.askinteger(
            "PlayNC Instances",
            "How many windows to open?",
            initialvalue=1,
            minvalue=1,
            maxvalue=20,
            parent=root,
        )
        root.destroy()
        return count if count is not None else 1
    except Exception:
        return 1


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


def _run_instance(instance_id: int, config: dict):
    """Run one GUI instance in its own process."""
    log_dir = Path(__file__).parent / "logs"
    log_dir.mkdir(exist_ok=True)

    handler = logging.FileHandler(log_dir / f"automation_{instance_id}.log", encoding="utf-8")
    handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s"))

    root = logging.getLogger()
    root.addHandler(handler)

    # Offset each window so they don't stack
    cols = 4
    col = (instance_id - 1) % cols
    row = (instance_id - 1) // cols
    window_x = col * 420
    window_y = row * 620

    config = {**config, "instance_id": instance_id, "window_x": window_x, "window_y": window_y}
    app = MainWindow(config)
    app.title(f"PlayNC Sign-In Automation [{instance_id}]")
    app.mainloop()


def main():
    setup_logging()
    config = load_config()

    app = MainWindow(config)
    app.mainloop()


if __name__ == "__main__":
    multiprocessing.freeze_support()
    count = int(sys.argv[1]) if len(sys.argv) > 1 else _prompt_instance_count()

    if count == 1:
        main()
    else:
        procs = []
        for i in range(1, count + 1):
            p = multiprocessing.Process(target=_run_instance, args=(i, load_config()))
            p.start()
            procs.append(p)
        for p in procs:
            p.join()
