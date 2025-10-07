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
python ui.py
```

### Pip install the Git repo
Once the project is published to GitHub, a single command installs the package and its runtime dependencies:
```bash
pip install -q -U git+https://github.com/vikramnairoffice/samailgapi.git@main
```
Replace `vikramnairoffice/samailgapi` with the repository slug. For private repos, include a PAT: `https://<token>@github.com/vikramnairoffice/samailgapi.git`.

After installation you can:
```python
from mailer import campaign_events
from ui import main  # launches the Gradio dashboard
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
     from ui import main
     main()  # opens Gradio in Colab output
     ```
     - Option B - call the bootstrap helper:
       ```python
       import colab_setup
       colab_setup.install_packages()
       colab_setup.ensure_playwright_browsers()
       colab_setup.create_directories()
       colab_setup.launch_app()
       ```
       This installs notebook extras (`google-auth-oauthlib`, `google-api-python-client`), downloads the Playwright Chromium browser bundle, prepares `gmail_tokens/`, `pdfs/`, `images/`, and launches the UI.

## Gmail token requirements
- Generate OAuth2 refresh tokens with scope `https://mail.google.com/` (e.g., via Google Cloud Console or OAuth playground).
- Each token JSON must include `client_id`, `client_secret`, and `refresh_token`.
- Store tokens under `gmail_tokens/` locally or upload them in Colab. The app refreshes and validates every token before sending.

## Project layout
```
ui.py               # Gradio dashboard
ui_token_helpers.py # Bridges UI events to the mailer generator
mailer.py           # Gmail REST workflow + token/lead orchestration
invoice.py          # Invoice generator (PDF, PNG, HEIF)
content.py          # Subject/body templates and sender name helpers
colab_setup.py      # Bootstrap helper for Colab/notebook runs
requirements.txt    # Runtime dependencies
setup.py            # Packaging configuration
```

## Development tips
- `python colab_setup.py` on a workstation installs notebook extras and launches the UI.
- Use the console script after installation: `simple-mailer`.
- Keep runtime assets (logos, prebuilt attachments, tokens) out of version control; they are covered in `.gitignore`.

## Troubleshooting

### Playwright errors inside asyncio environments

If you see the message `It looks like you are using Playwright Sync API inside the asyncio loop`,
the renderer is being driven from an environment that already has an event loop (for example
Google Colab notebooks). The project now routes every Playwright job through a dedicated
background thread with its own event loop, so the async API can run safely without colliding with
the caller's loop. Make sure you are running the refactored renderer located in
`html_renderer.py`, which creates a worker thread and awaits all Playwright calls on that thread's
event loop.【F:html_renderer.py†L43-L110】

### Missing Chromium executable

When you run the project in a fresh environment (such as a new Colab session) Playwright may log
`BrowserType.launch: Executable doesn't exist at .../chromium_headless_shell...` followed by a hint
to run `playwright install`. This simply means the chromium binary has not been downloaded in that
runtime yet. Install the browser bundle with `playwright install chromium --with-deps` (or run the
bootstrap helper which now tries that command automatically and falls back to `playwright install
chromium`). After the browser downloads you can confirm every dependency is present with
`playwright install --check`, which the helper also runs for you. The renderer will raise a
`PlaywrightUnavailable` error explaining the same requirement if the module cannot start because the
browser payload is missing.【F:html_renderer.py†L132-L144】【F:colab_setup.py†L45-L126】

## License
MIT - for educational and legitimate outreach workflows only. Review Google policies before sending bulk email.

