# G4-T1 Integrated Parity Runbook

## Execution
- Date: 2025-10-05
- Environment: Windows 11 (local), Python 3.13.1
- Command: python -m pytest
- Result: 170 passed in 13.90s with 10 warnings

## Coverage
- Email adapters: tests/test_mailer_parity.py, tests/test_senders_gmail_rest.py, tests/test_senders_gmail_smtp.py
- Orchestrator email modes: tests/test_orchestrator_email_manual.py, tests/test_orchestrator_email_automatic.py, tests/test_orchestrator_multi_mode.py
- Drive adapters: tests/test_orchestrator_drive_share.py
- UI shell + preview: tests/test_orchestrator_ui_shell.py, tests/test_ui_gmass_preview.py

## Warnings
- reportlab emits Python 3.14 ast.NameConstant deprecation
- websockets.legacy import path deprecated after 2024-11-09
- mailer.py still calls datetime.utcnow(); captured in Known_Issues

## Next Steps
- Hold for G4-T2 live token smoke once implemented
- Re-run parity suite after datetime.utcnow migration
