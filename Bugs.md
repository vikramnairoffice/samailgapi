# Bugs & Regressions (Post‑Refactor)

This list reflects the current codebase after the Gmail‑only refactor. All previous/obsolete issues have been removed.

## Critical

- Token extractor GUI is broken
  - Location: `Simple Gmail Token Extractor/generate_token.py:1`
  - Issues:
    - Corrupted enum strings and a syntax error in `AuthStatus` (e.g., invalid comma in `IN_PROGRESS`).
    - Mis-typed Gmail service name in `build('gma   il', 'v1', ...)`.
    - Mixed non‑ASCII glyphs in button/status labels likely from an encoding mishap.
  - Impact: Script fails to start; token generation cannot be used.

- Packaging/dependency mismatches
  - Location: `requirements.txt`, `setup.py:1`
  - Issues:
    - Missing runtime deps for the extractor and test sender: `google-auth-oauthlib`, `google-api-python-client`, `pillow-heif` (used in `invoice.py`).
    - `setup.py` fallback requirements embed literal `\r\n` escapes in a couple entries.
  - Impact: Fresh installs miss required packages; packaging fallback may break if `requirements.txt` is absent.

- Test suite out of sync with refactor
  - Location: `tests/`
  - Issues:
    - Multiple tests reference deleted modules/APIs (e.g., `token_manager.py`, `parse_file_lines`, selection‑table flows).
    - Example files: `tests/test_gmail_token_consistency.py`, `tests/test_file_processing.py`.
  - Impact: Tests fail to import or assert expectations from the pre‑refactor architecture.

## High

- Subject generation mismatch for GMass template
  - Location: `content.py: get_subject_and_body`
  - Issue: Always uses `generate_subject_with_prefix_pattern()` even for `gmass_inboxed`; tests and earlier behavior expect a plain subject (no prefix) for that template.
  - Impact: Inconsistent subject lines; related tests cannot be made to pass without aligning behavior.

- UI progress markers show replacement glyphs
  - Location: `ui_token_helpers.py: _format_progress`
  - Issue: Emits "? Sent" / "? Failed" instead of ASCII or valid emoji (likely encoding loss).
  - Impact: Poor UX/readability in the Gradio log textbox.

- Headless‑unsafe token extractor
  - Location: `Simple Gmail Token Extractor/generate_token.py`
  - Issue: Uses `tkinter` GUI for batch auth; this fails in headless/server environments.
  - Impact: Token generation unavailable in common deployment targets.

## Medium

- Residual dev/test code in content module
  - Location: `content.py: __main__` block at file end
  - Issue: Prints sample subjects/bodies when executed directly.
  - Impact: Noise and accidental execution risk when invoked as a script.

- Very large, repetitive content lists
  - Location: `content.py: body_parts['part1']`
  - Issue: Significant duplication; increases memory and repetition in outputs.
  - Impact: Minor performance/quality concerns.

- Noisy debug prints in invoice utilities
  - Location: `invoice.py`
  - Issue: Logs conversion steps, warnings, and logo selection to stdout.
  - Impact: Clutters logs; better as optional logging.

- Token/credential folder naming divergence
  - Locations: Extractor uses `Credentials/` and `Tokens/`; main app relies on uploaded tokens (no fixed folder).
  - Impact: User confusion about where tokens should live; docs/UI and extractor disagree.

## Low

- Minor packaging metadata issues
  - Location: `setup.py`
  - Issue: Fallback requirements contain literal CRLF escapes; classifiers include many Python versions not guaranteed by CI.
  - Impact: Cosmetic/robustness.

- Repository hygiene
  - Locations: multiple
  - Issues: Leftover prints across modules, empty `Plan.md`, and various large images/docs in root inflate the repo.
  - Impact: Cosmetic.

## Suggested Fixes (Prioritized)

- Repair the token extractor
  - Replace corrupted `AuthStatus` strings; fix `build('gmail', 'v1', ...)`.
  - Add explicit `requirements` for the extractor (or include the missing deps in root `requirements.txt`).
  - Provide a CLI (headless) flow as an alternative to `tkinter`.

- Align content subject generation
  - For `gmass_inboxed`, select plain `DEFAULT_SUBJECTS` (no prefix) or update tests/docs to reflect the new prefixed scheme consistently.

- Refresh the test suite
  - Delete or rewrite tests that depend on `token_manager.py`, `parse_file_lines`, selection tables, and SMTP paths that no longer exist.
  - Add tests for the current Gmail REST flow: `load_gmail_token`, `campaign_events`, and invoice attachment modes.

- Tidy packaging and logs
  - Add `google-auth-oauthlib`, `google-api-python-client`, and `pillow-heif` to `requirements.txt` (or gate features with optional extras).
  - Remove noisy prints or guard them behind a debug flag; drop the `__main__` block from `content.py`.

