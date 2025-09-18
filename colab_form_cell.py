#@title Simple Gmail REST Mailer - Colab Form (Single Cell)
# This cell is designed for Google Colab only. It keeps all logic intact
# and only changes the UI/flow to Colab-native uploads + form parameters.

import os, sys, glob, time, traceback

# Ensure we are running in Colab
IN_COLAB = 'google.colab' in sys.modules
if not IN_COLAB:
    print("This cell is intended for Google Colab. It may not function outside Colab.")

# Optional: install requirements if missing (Colab session)
try:
    import reportlab  # noqa: F401
    import fitz       # PyMuPDF  # noqa: F401
    from PIL import Image  # noqa: F401
    import google  # noqa: F401
except Exception:
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", "-r", "requirements.txt"])  # noqa: E702

from mailer import (
    campaign_events,
    update_file_stats,
)
from content import (
    SENDER_NAME_TYPES,
    DEFAULT_SENDER_NAME_TYPE,
)

if IN_COLAB:
    from google.colab import files as colab_files
    from IPython.display import clear_output


# Storage locations in Colab
TOKEN_DIR = "/content/gmail_tokens"
DATA_DIR = "/content/data"
os.makedirs(TOKEN_DIR, exist_ok=True)
os.makedirs(DATA_DIR, exist_ok=True)


def _upload_with_filter(accept_exts, dest_dir, description):
    print(description)
    uploaded = colab_files.upload()
    saved = []
    for name, data in (uploaded or {}).items():
        lower = name.lower()
        if not any(lower.endswith(ext) for ext in accept_exts):
            continue
        path = os.path.join(dest_dir, os.path.basename(name))
        with open(path, "wb") as f:
            f.write(data)
        saved.append(path)
    print(f"Saved {len(saved)} file(s) to {dest_dir}")
    return saved


def _attachment_folder_status(path: str) -> str:
    if not path:
        return "No attachment folder configured."

    folder = os.path.abspath(os.path.expanduser(path.strip()))
    if not os.path.exists(folder):
        return f"Folder not found: {folder}"
    if not os.path.isdir(folder):
        return f"Not a folder: {folder}"

    try:
        files = [entry.path for entry in os.scandir(folder) if entry.is_file()]
    except Exception as exc:
        return f"Folder error: {exc}"

    if not files:
        return f"No files in {folder}"

    return f"{len(files)} file(s) detected in {folder}"


# === Step 1 - Gmail token upload (refresh token JSON files) ===
token_files = sorted(glob.glob(os.path.join(TOKEN_DIR, "*.json")))
if IN_COLAB and not token_files:
    token_files = _upload_with_filter([".json"], TOKEN_DIR, "Step 1 - Upload Gmail token JSON files")

token_status, _ = update_file_stats(token_files, None)
print(token_status)


# === Step 2 - Leads .txt upload ===
leads_path = os.path.join(DATA_DIR, "leads.txt")
if IN_COLAB and not os.path.exists(leads_path):
    leads_uploaded = _upload_with_filter([".txt"], DATA_DIR, "Step 2 - Upload leads .txt (one email per line)")
    if leads_uploaded:
        # Use the first uploaded .txt as leads file
        leads_path = leads_uploaded[0]

_leads_msg = update_file_stats([], leads_path)[1] if os.path.exists(leads_path) else "No leads uploaded yet"
print(_leads_msg)


# === Colab Form Parameters ===
# The following #@param annotations define the Colab form controls.

content_template = "own_proven"  #@param ["own_proven", "gmass_inboxed"]
sender_name_type = "business"  #@param ["business", "personal"]
email_content_mode = "Attachment"  #@param ["Attachment", "Invoice"]
attachment_folder = ""  #@param {type:"string"}
invoice_format = "pdf"  #@param ["pdf", "image", "heic"]
leads_per_account = 10  #@param {type:"integer"}
send_delay_seconds = 4.5  #@param {type:"number"}
mode = "gmass"  #@param ["gmass", "leads"]
start_sending = False  #@param {type:"boolean"}

# Optional developer field (kept empty by default)
support_number = ""  # Optional: one or two numbers separated by newline

print(_attachment_folder_status(attachment_folder))


def _run_campaign_colab():
    # Preconditions
    if not token_files:
        print("No Gmail token files found. Re-run and upload token JSON files.")
        return
    if (mode or "gmass").lower() == "leads" and not os.path.exists(leads_path):
        print("Leads mode selected but no leads file uploaded. Re-run and upload a leads .txt file.")
        return

    folder_hint = (attachment_folder or "").strip()
    if (email_content_mode or "Attachment").lower() == "attachment":
        status = _attachment_folder_status(folder_hint)
        if status.startswith("Folder not found") or status.startswith("Not a folder") or status.startswith("Folder error") or status.startswith("No files"):
            print(status)
            return

    print("Starting campaign...\n")

    # Stream events
    events = campaign_events(
        token_files=token_files,
        leads_file=leads_path if (mode or "gmass").lower() == "leads" else None,
        leads_per_account=leads_per_account,
        send_delay_seconds=send_delay_seconds,
        mode=mode,
        content_template=content_template,
        email_content_mode=email_content_mode,
        attachment_format='pdf',
        attachment_folder=attachment_folder,
        invoice_format=invoice_format,
        support_number=support_number,
        sender_name_type=sender_name_type,
    )

    total = 0
    successes = 0
    try:
        for event in events:
            kind = event.get('kind')
            if kind == 'token_error':
                print(f"Token issue: {event.get('message')}")
            elif kind == 'fatal':
                print(event.get('message', 'Fatal error'))
                return
            elif kind == 'progress':
                total = event.get('total', total)
                successes = event.get('successes', successes)
                account = event.get('account', 'unknown')
                lead = event.get('lead', 'unknown')
                if event.get('success'):
                    print(f"OK Sent to {lead} using {account} ({successes}/{total})")
                else:
                    print(f"FAIL for {lead} using {account}: {event.get('message')} ({successes}/{total})")
            elif kind == 'done':
                print(event.get('message', 'Done'))
            else:
                print(str(event))
    except Exception:
        print("Unexpected error while running campaign:\n")
        traceback.print_exc()


if start_sending:
    _run_campaign_colab()
else:
    print("Ready. Set parameters and enable 'start_sending' to run.")
