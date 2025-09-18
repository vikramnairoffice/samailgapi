# Tasks — Implement Inline UI Error Panel (Issue No. 3)

Status: To do. Do not implement beyond this task list.

## Scope
Implement a single inline UI error panel with full diagnostics, wrapped around UI entrypoints only, with minimal, targeted edits. No new modules/files. No filesystem writes. Keep all existing prints. Present diagnostics as plain text (no HTML/JS clipboard).

## Checklist
- [ ] Add `ui_error_wrapper` decorator and `TeeIO` stream mirror inside `ui_token_helpers.py` (no new files)
  - [ ] Capture `stdout`/`stderr` via `io.StringIO` and mirror to original streams
  - [ ] Support `output_type` parameter: `"generator"` and `"selection"`
  - [ ] Build plain-text diagnostics: type, message, full traceback, captured stdout/stderr, args/kwargs, environment context, attachment dir counts, token/account context
- [ ] Decorate `unified_send_handler_with_selection` with `@ui_error_wrapper(output_type="generator")` in `ui_token_helpers.py`
- [ ] Import and decorate `validate_and_show_selection` in `ui.py` with `@ui_error_wrapper(output_type="selection")`
- [ ] Replace print-and-return error exits with minimal re-raises so the wrapper can surface failures
  - [ ] `ui_token_helpers.py`: after yielding error for invalid selection, raise `ValueError("Invalid account selection")`
  - [ ] `ui_token_helpers.py`: after yielding error for no selection, raise suitable exception
  - [ ] `ui.py` (`validate_and_show_selection`): in `except` blocks, re-raise after existing prints
- [ ] Switch UI components used for diagnostics to plain-text components
  - [ ] In `ui.py`, change `selection_status` from `gr.HTML` to `gr.Textbox` (multiline, `interactive=False`)
  - [ ] In `ui.py`, change `log_box` from `gr.HTML` to `gr.Textbox` (multiline, `interactive=False`)
- [ ] Ensure output shapes match Gradio expectations on error
  - [ ] Send flow: yield one final tuple with plain-text diagnostics in `log_box` and placeholders for others
  - [ ] Selection flow: return `(gr.update(visible=False), placeholder table, plain-text diagnostics)`
- [ ] Keep all existing debug prints; verify they appear both in console and in captured output
- [ ] Manual tests
  - [ ] Selection flow errors (malformed accounts file, invalid token JSON) show diagnostics in `selection_status`
  - [ ] Send flow errors (empty selection, bad config) show diagnostics in `log_box`
  - [ ] Manual copy works (text is fully selectable)

## Acceptance Criteria
- On any unhandled exception in `validate_and_show_selection` or `unified_send_handler_with_selection`, the UI displays a single inline error panel as plain text with:
  - Error type, message, and full traceback
  - Captured stdout/stderr including existing prints
  - Function args/kwargs and relevant context (auth files, token paths, dirs) without redaction
  - No clipboard button or downloads; manual copy is sufficient
- No deep refactors; only small, targeted changes in the specified files/functions
- No filesystem writes for logs or bundles; everything appears inline
- Existing prints are preserved

## Notes
- Colab-friendly requirements apply: avoid file I/O; keep diagnostics inline.
- Prefer monospaced display via `gr.Textbox` or `gr.Code`; ensure multi-line visibility (set `lines` appropriately).
