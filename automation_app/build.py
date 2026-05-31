"""Build PlayNC into standalone executable with bundled Playwright browser.

Usage:
    python build.py                 # build for current platform
    python build.py --clean         # remove previous build artifacts
    python build.py --onefile       # single exe (slower startup, larger)

Output: dist/PlayNC/

  Mac:  dist/PlayNC/PlayNC          (run.sh launcher sets browser path)
  Win:  dist/PlayNC/PlayNC.exe      (run.bat launcher sets browser path)

The Playwright Chromium browser (~350MB) is copied next to the
executable so the app auto-detects it at launch — no Python/npm needed.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent
DIST_DIR = PROJECT_DIR / "dist" / "PlayNC"


def clean():
    for p in [PROJECT_DIR / "build", PROJECT_DIR / "dist", PROJECT_DIR / "PlayNC.spec"]:
        if p.exists():
            shutil.rmtree(p) if p.is_dir() else p.unlink()
            print(f"  Removed {p}")


def find_playwright_browser() -> Path | None:
    candidates = [
        Path.home() / "Library" / "Caches" / "ms-playwright",
        Path.home() / "AppData" / "Local" / "ms-playwright",
        Path(os.environ.get("PLAYWRIGHT_BROWSERS_PATH", "")),
    ]
    for base in candidates:
        if not base.is_dir():
            continue
        for entry in sorted(base.iterdir()):
            if entry.name.startswith("chromium-") and entry.is_dir():
                return entry
    return None


def bundle_browser(target_dir: Path):
    """Copy Playwright Chromium browser alongside the executable."""
    browser_dir = find_playwright_browser()
    if browser_dir is None:
        print("\n  [WARN] Playwright Chromium browser not found locally.")
        print("  App will use default Playwright browser location at runtime.")
        print("  To bundle: run 'playwright install chromium' in your venv.\n")
        return

    dest = target_dir / "playwright-browsers"
    if dest.exists():
        print("  Playwright browsers already bundled, skipping copy.")
        return

    print(f"  Bundling: {browser_dir.name} (~{sum(f.stat().st_size for f in browser_dir.rglob('*') if f.is_file()) // 1024 // 1024}MB)")
    print(f"  Copying to: {dest}")
    shutil.copytree(browser_dir, dest / browser_dir.name, symlinks=True)
    print("  Browser bundled.")


def build():
    print("=" * 60)
    print("  PlayNC Build")
    print("=" * 60)

    venv_python = PROJECT_DIR / ".venv" / "bin" / "python"
    if not venv_python.exists():
        venv_python = PROJECT_DIR / ".venv" / "Scripts" / "python.exe"
    python_exe = str(venv_python) if venv_python.exists() else sys.executable
    print(f"  Python: {python_exe}\n")

    # Determine output mode
    onefile = "--onefile" in sys.argv

    # Build PyInstaller command
    print(f"[1/3] Running PyInstaller ({'onefile' if onefile else 'onedir'})...")

    cmd = [
        python_exe, "-m", "PyInstaller",
        str(PROJECT_DIR / "app.py"),
        "--name", "PlayNC",
        "--distpath", str(DIST_DIR.parent),
        "--workpath", str(PROJECT_DIR / "build"),
        "--add-data", f"config{os.pathsep}config",
        "--hidden-import", "automation.steps._helpers",
        "--hidden-import", "automation.steps.login",
        "--hidden-import", "automation.steps.restricted",
        "--hidden-import", "automation.steps.identity",
        "--hidden-import", "customtkinter",
        "--hidden-import", "pandas",
        "--hidden-import", "openpyxl",
        "--exclude-module", "tkinter.test",
        "--exclude-module", "unittest",
        "--exclude-module", "pydoc",
        "--exclude-module", "test",
        "--noconfirm",
    ]

    if onefile:
        cmd.append("--onefile")
    else:
        cmd.append("--onedir")

    result = subprocess.run(cmd, cwd=str(PROJECT_DIR))
    if result.returncode != 0:
        print(f"\n[ERROR] PyInstaller failed (code {result.returncode})")
        sys.exit(1)

    # Determine output path
    if onefile:
        exe_name = "PlayNC.exe" if sys.platform == "win32" else "PlayNC"
        output_exe = DIST_DIR.parent / exe_name  # --distpath puts exe in parent
    else:
        output_dir = DIST_DIR.parent / "PlayNC"
        # Rename to PlayNC if needed — but PyInstaller already named it
        DIST_DIR.mkdir(parents=True, exist_ok=True)

    # Step 2: Bundle Playwright browser
    print("\n[2/3] Bundling Playwright browser...")
    bundle_browser(DIST_DIR)

    # Step 3: Launcher scripts + README
    print("\n[3/3] Creating launcher scripts and README...")
    create_launchers(DIST_DIR)
    create_readme(DIST_DIR)

    print("\n" + "=" * 60)
    print("  Done!")
    print(f"  Output: {DIST_DIR}")
    if sys.platform == "win32":
        print("  Run: double-click dist\\PlayNC\\run.bat")
    else:
        print("  Run: ./dist/PlayNC/run.sh")
    print("=" * 60)


def create_launchers(target: Path):
    """Create launcher script for current platform only."""
    target.mkdir(parents=True, exist_ok=True)

    if sys.platform == "win32":
        bat = """@echo off
set "PLAYWRIGHT_BROWSERS_PATH=%~dp0playwright-browsers"
"%~dp0PlayNC.exe" %*
"""
        target.joinpath("run.bat").write_text(bat)
    else:
        sh = """#!/usr/bin/env bash
DIR="$(cd "$(dirname "$0")" && pwd)"
export PLAYWRIGHT_BROWSERS_PATH="$DIR/playwright-browsers"
exec "$DIR/PlayNC" "$@"
"""
        p = target / "run.sh"
        p.write_text(sh)
        p.chmod(0o755)


def create_readme(target: Path):
    """Write platform-specific end-user README."""
    if sys.platform == "win32":
        start_cmd = "double-click run.bat"
    else:
        start_cmd = "right-click run.sh → Open with Terminal"

    readme = f"""PlayNC Sign-In Automation
===========================

Start: {start_cmd}

1. Put your Excel file (游戏验证.xlsx) somewhere on your computer
2. Launch the app
3. Click Browse to select your Excel file
4. Enter an email address and click Check
5. Review looked-up data
6. Click Start to begin automated sign-in
7. If CAPTCHA appears, solve it in the browser window
8. App handles the rest

Need help? Contact the developer.
"""

    readme_path = target / "README.txt"
    readme_path.write_text(readme)


if __name__ == "__main__":
    if "--clean" in sys.argv:
        clean()
    build()
