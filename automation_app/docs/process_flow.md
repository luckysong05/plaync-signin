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
├── captcha_handler.py        # CAPTCHA detection (vendor iframes + DOM selectors only)
└── lookup.py                 # Excel cross-tab search (with mtime cache)
```

## Full Sign-In Flow (`full_signin.py`)

```
full_signin(page, email, password, carrier, name, birthday, sex, phone, ...)
│
├─ 1. step_navigate()
│     → goto plaync login URL
│
├─ 2. step_fill_email()
│     → click email field, type email (50-150ms/char)
│
├─ 3. step_click_login_button()
│     → click login/next button after email
│
├─ 4. step_fill_password()
│     → click password field, type password
│
├─ 5. step_click_final_login()
│     → click final submit button
│
├─ 6. step_handle_restricted_account()  ← CHECKED FIRST
│     ├─ Detected? → restricted flow (email/phone → Confirm → Complete)
│     │               → return success (skip all)
│     └─ Not detected → continue
│
├─ [CAPTCHA CHECK] ── (inline, no step number)
│     detect_captcha()?
│     ├─ YES → wait_for_captcha_solve()
│     │         → GUI shows CAPTCHA popup
│     │         → user solves in browser
│     │         → user clicks Continue
│     │         → continue
│     └─ NO  → continue
│
├─ 7. identity_check
│     │
│     │  Detect "Identity Verification" + "Phone Number Verification" in page text?
│     │
│     ├─ YES → [IDENTITY PAGE PATH]
│     │   a) [CAPTCHA] manual solve popup
│     │   b) User solves CAPTCHA in browser
│     │   c) User clicks Continue
│     │
│     └─ NO  → [nothing, continue]
│
├─ 8. step_first_pass_verification()
│     → click "본인인증" / "First Pass" button
│
├─ 9. step_dismiss_popups()
│     → dismiss interstitial popups/dialogs
│
├─10. step_select_carrier(carrier)
│     → iterate visible buttons, match normalized text
│     → select carrier button (SKT/KT/LGU+/알뜰폰 variants)
│
├─11. step_sms_verification()
│     → wait up to 7s for certAuthCheck buttons
│     → click "문자(SMS) 인증" button
│     → check terms agreement checkbox
│     → click confirm/Next/red button
│     → wait for identity form transition
│
├─12. step_fill_identity_form(name, birthday, sex, phone)
│     → wait for identity form to load
│     → save debug screenshot + dump visible fields
│     → fill name field (input[name="username"] / #sms_username)
│     → click Next (button.btn_pass / .btnUserName_sms / "다음")
│     → fill birthday (input#myNum1, 6-digit YYMMDD)
│     → Tab → fill sex (input#myNum2, 1-digit RRN gender)
│     → phone field appears dynamically after birthday entry
│     → fill phone
│     → [CAPTCHA] always pause for manual solve
│     → click final Next/Continue (다음/계속/인증번호)
│
└─ return {success: True/False, step: "...", error: "..."}
```

## Error Handling

- Each step wrapped in try/except
- On failure: save screenshot to `screenshots/`, return error with step name
- Restricted account failures are non-fatal (warn and continue to normal flow)
- Browser kept open on error — user can inspect page and click Continue or Stop

## Conditional Behaviors

| Condition | Action |
|-----------|--------|
| Email field not found | Raise error → return failure |
| Password field not found | Raise error → return failure |
| CAPTCHA before login submit | Skip (invisible reCAPTCHA, nothing to solve) |
| CAPTCHA after login submit | Pause, show GUI popup, wait for user solve |
| Identity verification page ("Identity Verification" + "Phone Number Verification") detected | Manual CAPTCHA popup → continue from First Pass |
| Identity verification page NOT detected | Run First Pass → dismiss popups → carrier |
| Restricted account detected | Run restricted flow, skip all identity steps |
| First Pass button not found | Fall through (may already on carrier page) |
| Carrier not found | **Raise RuntimeError** → GUI error popup |
| SMS button not found | Try first certAuthCheck button |
| Terms checkbox not found | Proceed without checking |
| Name field not found | **Raise RuntimeError** → GUI error popup |
| Birthday/sex field not found | **Raise RuntimeError** → GUI error popup |
| Phone field not found | **Raise RuntimeError** → GUI error popup |
| Next button after name not found | **Raise RuntimeError** → GUI error popup |
| SMS request button not found | Warn and continue |
