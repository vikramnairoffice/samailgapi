import os
import subprocess
import sys
from pathlib import Path

import pkg_resources

ROOT = Path(__file__).parent
REQUIREMENTS_FILE = ROOT / "requirements.txt"

BASE_REQUIREMENTS = [
    "gradio>=3.0.0",
    "reportlab>=3.6.0",
    "pymupdf>=1.20.0",
    "faker>=15.0.0",
    "google-auth>=2.0.0",
    "requests>=2.25.0",
    "Pillow>=8.0.0",
    "pillow-heif>=0.9.0",
    "python-docx>=0.8.11",
    "playwright>=1.45.0",
]

COLAB_EXTRAS = [
    "google-auth-oauthlib>=0.8.0",
    "google-api-python-client>=2.70.0",
]

DIRECTORIES = ["pdfs", "images", "logos", "gmail_tokens"]


def _load_requirements():
    """Return the combined list of requirements for installation."""
    if REQUIREMENTS_FILE.exists():
        lines = REQUIREMENTS_FILE.read_text(encoding="utf-8").splitlines()
        reqs = [line.strip() for line in lines if line.strip() and not line.lstrip().startswith("#")]
        return reqs + COLAB_EXTRAS
    return BASE_REQUIREMENTS + COLAB_EXTRAS


def install_packages():
    """Install all required packages using pip."""
    desired = _load_requirements()
    installed = {pkg.key for pkg in pkg_resources.working_set}

    missing = []
    for spec in desired:
        pkg_name = pkg_resources.Requirement.parse(spec).key
        if pkg_name not in installed:
            missing.append(spec)

    if missing:
        print(f"Installing missing packages: {', '.join(missing)}")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", *missing, "-q"])
            print("All packages installed successfully.")
        except subprocess.CalledProcessError as exc:
            print(f"Error installing packages: {exc}")
            sys.exit(1)
    else:
        print("All required packages are already installed.")


def create_directories():
    """Create the directories the application expects at runtime."""
    print("\nPreparing local directories...")
    for directory in DIRECTORIES:
        try:
            os.makedirs(directory, exist_ok=True)
            print(f"  - {directory} ready")
        except OSError as exc:
            print(f"Error creating {directory}: {exc}")
            sys.exit(1)


def launch_app():
    """Launch the Gradio UI."""
    print("\nLaunching the Simple Gmail REST Mailer UI...")
    print("=" * 50)
    try:
        import ui

        ui.main()
    except ImportError:
        print("Error: Could not import the 'ui' module. Ensure the package is installed or on sys.path.")
        sys.exit(1)
    except Exception as exc:
        print(f"An error occurred while launching the application: {exc}")
        sys.exit(1)


if __name__ == "__main__":
    print("--- Simple Gmail REST Mailer: Colab/bootstrap helper ---")
    install_packages()
    create_directories()
    print("\nUpload Gmail OAuth token JSON files into 'gmail_tokens/' before sending campaigns.")
    launch_app()
