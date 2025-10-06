# Simple Gmail REST Mailer

Token-first Gmail sender with a Gradio dashboard, personalized invoice generation, and a Colab-friendly workflow. Upload OAuth token JSON files, tune email content, and monitor progress from the browser or a notebook.

## Highlights
- **Gmail REST only** - no SMTP passwords; each token is verified via the Gmail profile endpoint before sends.
- **Colab bootstrap helper** - run `colab_setup` to prep a notebook and launch the Gradio UI.
- **Invoice/attachment workflow** - generate PDFs/HEIF images on the fly or re-use assets stored under `pdfs/`, `images/`, and `logos/`.
- **Seed + leads modes** - blast the bundled GMass seed list or distribute uploaded leads across accounts.
- **Console entry point** - install the package and launch the Gradio UI with `simple-mailer`.

## Installation

### Install from source
```bash
# clone or download the repository, then
pip install -r requirements.txt
python -m simple_mailer.ui
```

### Pip install the Git repo
Once the project is published to GitHub, a single command installs the package and its runtime dependencies:
```bash
pip install -q -U git+https://github.com/vikramnairoffice/samailgapi.git@main
```
Replace `vikramnairoffice/samailgapi` with the repository slug. For private repos, include a PAT: `https://<token>@github.com/vikramnairoffice/samailgapi.git`.

After installation you can:
```python
from simple_mailer import mailer
from simple_mailer import ui  # launches the Gradio dashboard
```

## Google Colab quick start

1. **Install the package**
   ```python
   # Cell 1 - install from GitHub
   !pip install -q -U git+https://github.com/vikramnairoffice/samailgapi.git@main
   ```
2. **Launch a UI**
   - Option A - run the packaged Gradio app:
     ```python
     from simple_mailer import ui
     ui.main()  # opens Gradio in Colab output
     ```
   - Option B - call the bootstrap helper:
     ```python
     from simple_mailer import colab_setup
     colab_setup.install_packages()
     colab_setup.create_directories()
     colab_setup.launch_app()
     ```
     This installs notebook extras (`google-auth-oauthlib`, `google-api-python-client`), prepares `gmail_tokens/`, `pdfs/`, `images/`, and launches the UI.

## Gmail token requirements
- Generate OAuth2 refresh tokens with scope `https://mail.google.com/` (e.g., via Google Cloud Console or OAuth playground).
- Each token JSON must include `client_id`, `client_secret`, and `refresh_token`.
- Store tokens under `gmail_tokens/` locally or upload them in Colab. The app refreshes and validates every token before sending.

## Project layout
```
simple_mailer/
  ui.py               # Gradio dashboard entry point
  ui_token_helpers.py # Bridges UI events to the mailer generator
  mailer.py           # Gmail REST workflow + token/lead orchestration
  invoice.py          # Invoice generator (PDF, PNG, HEIF)
  content.py          # Subject/body templates and sender name helpers
  colab_setup.py      # Bootstrap helper for Colab/notebook runs
requirements.txt      # Runtime dependencies
setup.py              # Packaging configuration
```

## Snapshot Baselines
- `tests/fixtures/gardio_blueprints/` keeps PNG baselines for manual, automatic, drive share, and multi mode Gardio layouts.
- `tests/fixtures/ui_snapshots/` holds JSON snapshots of the Gradio UI modes so structural changes surface in tests.
- Run `python -m pytest tests/test_gardio_ui.py tests/test_ui_snapshots.py` after UI tweaks to confirm the guardrails stay green.

## Development tips
- `python -m simple_mailer.colab_setup` on a workstation installs notebook extras and launches the UI.
- Use the console script after installation: `simple-mailer`.
- Keep runtime assets (logos, prebuilt attachments, tokens) out of version control; they are covered in `.gitignore`.


## Live token smoke harness
- Set `LIVE_TOKEN_SMOKE=1` in the environment before invoking the harness.
- Provide an OAuth token JSON seeded with Gmail send/read and Drive scopes; store it under `gmail_tokens/` or load it in Colab.
- Run `python -m pytest tests/test_live_token_smoke.py` to execute the mocked guardrails; add `-k live_smoke_integration` after setting the flag to exercise the real token flow.
- The harness sends a single invoice email, polls the inbox, and shares the generated invoice via Drive.
- Only run this in a controlled Colab or staging mailbox because it performs live network calls.

## License
MIT - for educational and legitimate outreach workflows only. Review Google policies before sending bulk email.



