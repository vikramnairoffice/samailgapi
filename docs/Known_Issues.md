# Known Issues (as of 2025-10-05)

- [G4-T1] reportlab dependency emits ast.NameConstant deprecation under Python 3.13; monitor upstream release.
- [G4-T1] websockets.legacy import shows pending removal after 2024-11-09; keep adapter tests ready for module swap.
- [G4-T1] mailer.py still calls datetime.utcnow(); migrate to timezone-aware datetime when touching that module.
