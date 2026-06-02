# PlayNC Sign-In Process Flow

## Module Structure

```
automation/
├── full_signin.py            # Thin orchestrator (imports from steps/)
├── steps/
│   ├── _helpers.py           # Shared helpers, constants, CAPTCHA utils
│   ├── login.py              # step_navigate → email → password → submit
│   ├── restricted.py         # step_handle_restricted_account
│   └── identity.py           # First Pass → carrier → SMS → identity form
├── runner.py                 # Background thread orchestrator
├── playwright_client.py      # Browser lifecycle
├── captcha_handler.py        # CAPTCHA detection + reCAPTCHA auto-detect
└── lookup.py                 # Excel cross-tab search (with mtime cache)
```

## GUI Layout (`gui/main_window.py`)

```
┌──────────────────────────────────┐
│  Excel File                      │
│  [________________________] Browse│
├──────────────────────────────────┤
│  Email                           │
│  [____________________________]  │
├──────────────────────────────────┤
│  [▶ Start] [↺ Reset] [■ Stop]   │
│  ████████████░░░░░ 75%          │
├──────────────────────────────────┤
│  ⚠ CAPTCHA Detected  (hidden)   │
│  [Continue]                      │
├──────────────────────────────────┤
│  Error — Browser Kept Open (hid) │
│  [Continue]                      │
├──────────────────────────────────┤
│  Log (expandable)                │
│  ┌──────────────────────────┐    │
│  │ 2026-06-02 Looking up... │    │
│  │ Signing in...            │    │
│  │ ...                      │    │
│  └──────────────────────────┘    │
├──────────────────────────────────┤
│  ✓ Success: —  ✗ Failed: —  [Export]│
└──────────────────────────────────┘
```

- **Start**: lookup email → auto-launch browser → run full sign-in
- **Reset**: clear log/results, enable Start for new account
- **Stop**: kill running automation
- No Check button, no data preview, no status label

## Full Sign-In Flow (`full_signin.py`)

```
full_signin(page, email, password, carrier, name, birthday, sex, phone, ...)
│
├─ 1. step_navigate()
│     → goto plaync login URL
│     → dismiss cookie consent banner ("Agree to All")
│     → random scroll
│
├─ 2. step_fill_email()
│     → find email field, click, fill via insert_text
│
├─ 3. step_click_login_button()
│     → click login/next button after email
│     → wait for password field to appear (10s timeout)
│
├─ 4. step_fill_password()
│     → find password field, click, fill
│
├─ 5. step_click_final_login()
│     → click final submit button
│     → wait for navigation away from nclogin/signin (15s timeout)
│     → wait for domcontentloaded (10s timeout)
│
├─ 6. step_handle_restricted_account()
│     ├─ Detect keywords: "temporarily restricted", "보안 확인", etc.
│     ├─ Detected? → CAPTCHA check → email/phone → Confirm → Complete
│     │               → return success (skip all)
│     └─ Not detected → continue
│
├─ [CAPTCHA CHECK after login]
│     detect_captcha()?
│     ├─ YES → wait_for_captcha_solve() with auto-detect
│     │         → GUI shows CAPTCHA popup
│     │         → user solves reCAPTCHA in browser (auto-detected via token)
│     │         → OR user clicks Continue button
│     │         → continue
│     └─ NO  → continue
│
├─ 7. Identity verification page check
│     ├─ Detected "Identity Verification" text?
│     │   ├─ YES → _check_captcha() auto-detect + proceed
│     │   └─ NO  → continue
│
├─ 8. step_first_pass_verification()
│     → click "본인인증" / "First Pass" button
│
├─ 9. step_dismiss_popups()
│     → dismiss interstitial popups/dialogs
│
├─10. step_select_carrier(carrier)
│     → wait for carrier button visible (순서: SKT/KT/LGU+)
│     → iterate visible buttons, match normalized text
│     → select carrier button
│
├─11. step_sms_verification()
│     → wait for cert method buttons (순서: [class*="cert"])
│     → click SMS button ("문자(SMS)")
│     → wait for terms checkbox (5s timeout)
│     → check terms checkbox
│     → click confirm button ("다음")
│     → wait for form transition
│
├─12. step_fill_identity_form(name, birthday, sex, phone)
│     → save debug screenshot
│     → fill name field (순서: input[placeholder*="이름"])
│     → click Next (순서: .btnUserName_sms / button.btn_pass)
│     → fill birthday (순서: input[placeholder*="생년월일"])
│     → Tab → fill sex (순서: input[placeholder*="gender"])
│     → phone appears dynamically after birthday entry
│     → fill phone (순서: input[placeholder*="휴대폰"])
│     → [CAPTCHA] _user_continue blocks until CAPTCHA solved / Continue clicked
│     → click final Next (send SMS request)
│
└─ return {success: True/False, step: "...", error: "..."}
```

## CAPTCHA Auto-Detect (`captcha_handler.py`)

Three detection methods in `wait_for_captcha_solve()`:
1. **GUI Continue clicked** — `solved_event` fires
2. **CAPTCHA DOM disappears** — vendor iframe/selector no longer found
3. **reCAPTCHA token detected** — `#g-recaptcha-response` textarea has value > 50 chars

User can either solve reCAPTCHA in browser (auto) or click GUI Continue (fallback).

## Identity Form Field Detection

All identity form fields live on main page (no iframe). `_find_identity_frame` removed.

| Field | Primary selector | Fallbacks |
|-------|-----------------|-----------|
| Name | `input[placeholder*="이름"]` | username, sms_username, sms_*, class*="userName" |
| Birthday | `input[placeholder*="생년월일"]` | myNum1, Birth, myNum*, name*="birth" |
| Sex | `input[placeholder*="gender"]` | myNum2, myNum2 class, maxlength="1" |
| Phone | `input[placeholder*="휴대폰"]` | sms_mobileno, mobileno, phone, mobile |

Each field search uses 2s timeout per selector (was 5s).

## Timing Optimizations

- Fixed `sleep()` calls reduced from up to 4s to 0.1-1.0s
- Dead selectors removed or moved to end of list
- Working selectors placed first in priority order
- Step 5 now properly waits for redirect (was returning immediately)
- Carrier/cert page detection trimmed from ~30s to ~1s

## Error Handling

- Each step wrapped in try/except
- On failure: save screenshot to `screenshots/`, return error with step name
- Restricted account failures are non-fatal (warn and continue to normal flow)
- Browser kept open on error — user can inspect page and click Continue or Stop

## Conditional Behaviors

| Condition | Action |
|-----------|--------|
| Email not entered | Show warning, block Start |
| Email lookup fails | Log error, re-enable Start |
| CAPTCHA after login | Auto-detect reCAPTCHA solve + GUI popup fallback |
| Identity verification page detected | CAPTCHA check + auto-detect, proceed to First Pass |
| Restricted account detected | Run restricted flow, skip all identity steps |
| First Pass button not found | Fall through (may already on carrier page) |
| Carrier not found | **Raise RuntimeError** → GUI error popup |
| reCAPTCHA solved in browser | Auto-detected via response token, no Continue click needed |
| Name/birthday/sex/phone not found | **Raise RuntimeError** → GUI error popup |
| Next button after name not found | **Raise RuntimeError** → GUI error popup |
| SMS request button not found | Warn and continue |
