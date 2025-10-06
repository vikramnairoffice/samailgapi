# Gardio Blueprint Audit (2025-10-06)

This report locks the final Gardio blueprint baselines for the refactor. Update the hashes whenever a blueprint fixture changes and re-run `python -m pytest tests/test_docs_blueprint_audit.py` to confirm parity.

| Layout | SHA256 | Status |
| --- | --- | --- |
| drive_share | 92419bab39e958fef16d1f61351c81a7c99cbf2c3ba8c458ef14e74d645578f6 | Match |
| email_automatic | 6db36e052983f4a039f7b22903c59a3fd5340c34a094364eb495e2c78ab32e12 | Match |
| email_manual | e9526e1f3123d7cb14c6443d1de7a6b6d10de8c77638b8ac4dd16f3fdc0e9fed | Match |
| multi_mode | 89e16ecb390fc9cd744ee15df7c34bf36398deae48fcbf10d4b9a779174e0841 | Match |

Notes
- Fixtures live in `tests/fixtures/gardio_blueprints/` and are consumed by `gardio_ui.create_blueprint`.
- Regenerate snapshots only after validating layout changes inside Colab; rerun the audit test before shipping.
