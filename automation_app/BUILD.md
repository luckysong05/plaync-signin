# Building PlayNC Executable

Package into standalone app — no Python needed on target machines.

## Requirements

- **Mac**: Apple Silicon (M1/M2/M3) or Intel. macOS 12+ recommended.
- **Windows**: Windows 10/11, 64-bit.
- ~2GB free disk space (includes Chromium browser).
- Build on each target platform separately (no cross-compile).

---

## Mac Build

### 1. Prerequisites

```bash
# Open Terminal in automation_app/
cd automation_app

# Create virtual environment (one-time)
python3 -m venv .venv

# Activate it
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Install Playwright Chromium browser
playwright install chromium
```

### 2. Build

```bash
python build.py --clean
```

Output: `dist/PlayNC/`

### 3. Share

```bash
cd dist
zip -r PlayNC-mac.zip PlayNC
```

Send `PlayNC-mac.zip` to users.

### 4. Run (end user)

- Unzip
- Right-click `run.sh` → Open → "Open" in dialog (Gatekeeper warning — first time only)
- Or in Terminal: `./run.sh`

---

## Windows Build

### 1. Install Python

Download Python 3.14 from [python.org](https://www.python.org/downloads/).
**During install: check "Add Python to PATH".**

### 2. Prerequisites

```cmd
:: Open Command Prompt (cmd.exe) in automation_app\
cd automation_app

:: Create virtual environment (one-time)
python -m venv .venv

:: Activate it
.venv\Scripts\activate

:: Install dependencies
pip install -r requirements.txt

:: Install Playwright Chromium browser
playwright install chromium
```

### 3. Build

```cmd
python build.py --clean
```

Output: `dist\PlayNC\`

### 4. Share

```cmd
:: Right-click dist\PlayNC folder → Send to → Compressed (zipped) folder
```

Send `PlayNC.zip` to users.

### 5. Run (end user)

- Unzip
- Double-click `run.bat`
- No warnings, no extra steps

---

## Build Script Options

```bash
python build.py           # normal build (onedir, fastest startup)
python build.py --clean   # remove previous artifacts before building
python build.py --onefile # single executable (slower to start, larger)
```

Default mode (`--onedir`) produces a folder with the exe and supporting files. `--onefile` produces a single .exe/.app but takes longer to extract on first launch.

## Notes

- The Playwright Chromium browser (~530MB) is bundled automatically into `playwright-browsers/`.
- On Mac, the first launch shows a Gatekeeper warning because the app isn't codesigned. Right-click → Open bypasses this.
- On Windows, Windows Defender may briefly scan the executable on first run (normal).
- The `data/` folder (Excel files) is **not** bundled. Users must provide their own `游戏验证.xlsx` or browse to it in the app.
