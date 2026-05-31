# PlayNC Sign-In Automation

## Project Status
Nothing built yet. Spec in README.md.

## User Profile
- Intermediate Python
- Prefer terse responses, minimal stdlib explanation
- Review before creating >3 files or adding dependencies
- Windows primary target

## My Role
- Write complete working files, no stubs
- Add type hints on all functions
- Don't add features beyond spec
- Ask before installing new dependencies
- Prefer sync Playwright API

## Dev Workflow
- venv: `.venv/` at project root
- Run: `python app.py`
- Tests: pytest for lookup, captcha_handler, signin modules
- Skip GUI tests (CustomTkinter hard to automate)
- Debug: screenshots dump to `screenshots/`
- Logs: `logs/` directory, structured

## Communication
- Terse mode preferred
- Use README.md as source of truth for spec
- Flag deviations from spec
- Confirm before destructive operations

## Conventions
- Type hints on all defs
- Docstrings only when logic non-obvious
- Config over constants — use config.json
- No premature abstraction — three similar lines > one generic helper
