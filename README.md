# Simple Gmail REST Mailer

Token-first Gmail sender with a Gradio dashboard, personalized invoice generation, and a Colab-friendly workflow. Upload OAuth token JSON files, tune email content, and monitor progress from the browser or a notebook.

## Highlights
- **Gmail REST only** – no SMTP passwords; each token is verified via the Gmail profile endpoint before sends.
- **Colab form cell** – copy `colab_form_cell.py` into a notebook cell for an all-in-one upload + send experience.
- **Invoice/attachment workflow** – generate PDFs/HEIF images on the fly or re-use assets stored under `pdfs/`, `images/`, and `logos/`.
- **Seed + leads modes** – blast the bundled GMass seed list or distribute uploaded leads across accounts.
- **Console entry point** – install the package and launch the Gradio UI with `simple-mailer`.

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
pip install -q -U git+https://github.com/<owner>/<repo>.git@main
```
Replace `<owner>/<repo>` with the repository slug. For private repos, include a PAT: `https://<token>@github.com/...`.

After installation you can:
```python
from mailer import campaign_events
from ui import main  # launches the Gradio dashboard
```

## Google Colab quick start

1. **Install the package**
   ```python
   # Cell 1 – install from GitHub
   !pip install -q -U git+https://github.com/<owner>/<repo>.git@main
   ```
2. **Launch a UI**
   - Option A – run the packaged Gradio app:
     ```python
     from ui import main
     main()  # opens Gradio in Colab output
     ```
   - Option B – paste the contents of `colab_form_cell.py` into a Colab cell. The form handles token/leads uploads and streams campaign progress inside the notebook.

If you prefer an imperative helper, execute:
```python
import colab_setup
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
ui.py               # Gradio dashboard
ui_token_helpers.py # Bridges UI events to the mailer generator
mailer.py           # Gmail REST workflow + token/lead orchestration
invoice.py          # Invoice generator (PDF, PNG, HEIF)
content.py          # Subject/body templates and sender name helpers
colab_form_cell.py  # Copy-paste Colab cell with upload form
colab_setup.py      # Bootstrap helper for Colab/notebook runs
requirements.txt    # Runtime dependencies
setup.py            # Packaging configuration
```

## Development tips
- `python colab_setup.py` on a workstation installs notebook extras and launches the UI.
- Use the console script after installation: `simple-mailer`.
- Keep runtime assets (logos, prebuilt attachments, tokens) out of version control; they are covered in `.gitignore`.

## License
MIT – for educational and legitimate outreach workflows only. Review Google policies before sending bulk email.
