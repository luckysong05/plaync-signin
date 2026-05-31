# PlayNC Sign-In Automation

## Goal

Desktop app for automated sign-in at plaync.com using pre-registered account data from Excel.

### Workflow

1. User enters email address
2. App looks up email in Excel Tab 2 (账号密码) to find password, phone, machine number
3. App uses phone number to look up Tab 1 (身份信息) for name, birthday, sex, carrier
4. Displays all found info on screen for user to review
5. User confirms → app navigates to plaync.com sign-in page and fills credentials
6. Handles CAPTCHA if detected

### User Experience

Users only need to:
1. Make sure Excel file is in the data folder
2. Launch app
3. Enter email
4. Click Start
5. Solve CAPTCHA if prompted

No Python knowledge required. Packaged as EXE for Windows.

---

# Technical Stack

## Core

- Python 3.12+
- Playwright (sync API)
- pandas
- openpyxl

## GUI

- CustomTkinter

## Packaging

- PyInstaller (single-folder distribution)

---

# Project Structure

```text
automation_app/
│
├── app.py                    # Entry point
├── gui/
│   ├── main_window.py        # Main window layout
│   ├── components.py         # Reusable widgets
│   └── styles.py             # Theme constants
│
├── automation/
│   ├── runner.py             # Orchestrates lookup + signin flow
│   ├── full_signin.py        # Step orchestrator
│   ├── playwright_client.py  # Browser lifecycle management
│   ├── captcha_handler.py    # Human-in-the-loop CAPTCHA handling
│   ├── lookup.py             # Excel cross-tab search logic
│   └── steps/
│       ├── _helpers.py       # Shared helpers and constants
│       ├── login.py          # Login page steps
│       ├── restricted.py     # Restricted account flow
│       └── identity.py       # Identity verification steps
│   └── signin.py             # PlayNC sign-in page automation
│
├── data/
│   ├── 游戏验证.xlsx
│   └── results.xlsx
│
├── logs/
├── screenshots/
├── config/
│   └── config.json
│
├── requirements.txt
├── README.md
```

---

# Excel Structure

File: `data/游戏验证.xlsx`

## Tab 1: 身份信息 (Identity)

Used for cross-reference lookup by phone number.

| Column | Header | Description |
|--------|--------|-------------|
| A | 机器号 | Machine number |
| B | 名字 | Name |
| C | 电话号 | Phone number (lookup key) |
| D | 生日 | Birthday |
| E | 性别 | Sex |
| F | 通讯台 | Carrier (SK/KT/LG) |

## Tab 2: 账号密码 (Accounts)

Primary search target by email.

| Column | Header | Description |
|--------|--------|-------------|
| A | 电话 | Phone number |
| B | 机器号 | Machine number |
| C | 账号 | Account / Email (search key) |
| D | 密码 | Password |
| E | Comment | Registration status notes |

## Lookup Logic

```
email → search Tab2.Column C → get (password, phone, machine)
phone → search Tab1.Column C → get (name, birthday, sex, carrier)
```

---

# GUI Layout

## Main Window Sections

1. **Excel File Path**
   - Browse button
   - Selected file path display

2. **Email Input**
   - Text input field
   - Lookup button (optional — or part of Start)

3. **Data Preview**
   - Table or labeled fields displaying looked-up info before automation
   - Fields: Name, Birthday, Sex, Carrier, Phone, Machine, Account, Password

4. **Runtime Controls**
   - Start button
   - Stop button
   - Pause button

5. **Progress Section**
   - Status label
   - Progress bar

6. **Log Window**
   - Scrollable live logs

7. **CAPTCHA Section**
   - "Please solve CAPTCHA in browser, then click Continue" popup

8. **Completion Summary**
   - Success / Failure count
   - Export results button

---

# Automation Flow

## Browser Behavior

- Launch Chromium in visible (non-headless) mode
- Persistent browser context with user data directory
- Save and reuse cookies between runs

## Sign-In Steps (plaync.com)

1. Navigate to `https://login.plaync.com/nclogin/signin`
2. Fill email field
3. Fill password field
4. Click sign-in button
5. Wait for navigation / CAPTCHA
6. Handle CAPTCHA if present

## CAPTCHA Handling

Human-in-the-loop only — no bypass attempts.

**Detection:**
- reCAPTCHA / hCaptcha iframes
- Text: "I am not a robot", "Verify you are human"

**Behavior:**
1. Pause automation
2. Show popup: "Please solve CAPTCHA manually"
3. Wait for user to solve and click Continue (or auto-detect disappearance)
4. Configurable timeout — on timeout, mark row failed, continue

---

# Error Handling

- Timeout errors
- Missing selectors
- Network interruption
- CAPTCHA timeout
- Browser crash

**On error:**
- Save screenshot to `screenshots/`
- Save HTML snapshot
- Log with timestamp, action, error message
- Mark row as failed, continue to next

---

# Logging

Structured logging to both GUI and file.

Fields:
- timestamp
- account email
- action
- success/failure
- error message

---

# Results Output

`data/results.xlsx`

| Column | Description |
|--------|-------------|
| RowNumber | Row index in source |
| Email | Account email |
| Name | Name from identity tab |
| Status | Success / Failed / CAPTCHA Timeout / Validation Error |
| Message | Detail |
| Timestamp | When processed |

---

# Config

`config/config.json`

```json
{
  "excel_path": "data/游戏验证.xlsx",
  "headless": false,
  "captcha_timeout_seconds": 120,
  "typing_delay_ms": 50,
  "navigation_timeout_ms": 30000
}
```

---

# Deliverables

- All source code
- requirements.txt
- README.md
- PyInstaller spec
- Sample config.json
- Sample Excel file schema

---

# Building Executables

Bundle app into standalone executable (no Python required):

```bash
cd automation_app
python build.py --clean
```

Output: `dist/PlayNC/`

- **Mac**: `dist/PlayNC/run.sh` — run from terminal
- **Windows**: `dist/PlayNC/run.bat` — double-click

The Playwright Chromium browser (~500MB) is bundled automatically if you've ran `playwright install chromium`. Build on each target platform (Mac build = Mac app, Windows build = Windows app).

## Distribution

Zip the entire `dist/PlayNC/` folder. Users unzip and run the launcher script — no Python, no dependencies.

---

# Future Extensibility

Architecture should allow future:
- Multiple websites (different sign-in pages)
- Multiple account types
- Scheduling / batch processing
- Cloud execution
- OCR-based flow automation
- Email notifications
