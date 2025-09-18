# Tech Stack

## Core Technologies
- **Language**: Python 3.7+
- **Web UI**: Gradio
- **API Interaction**: Google API Client Library for Python (`google-auth-oauthlib`, `google-api-python-client`) for interacting with the Gmail REST API.

## Key Dependencies
- **`gradio`**: For building the web-based user interface.
- **`google-auth` & `google-api-python-client`**: For authenticating with and using the Gmail API.
- **`requests`**: For making HTTP requests to the Gmail API endpoints.
- **`reportlab`**: For generating personalized invoices in PDF format.
- **`faker`**: For generating placeholder data (company names, addresses) for invoices.
- **`PyMuPDF`**: For converting generated PDFs into images (PNG).
- **`Pillow` & `pillow-heif`**: For handling image conversions, including to HEIC format.

## Development & Setup
- **Virtual Environment**: It is recommended to use a virtual environment to manage dependencies.
  ```bash
  python -m venv .venv
  # On Windows
  .venv\Scripts\activate
  # On macOS/Linux
  source .venv/bin/activate
  ```
- **Installation**: Dependencies are listed in `requirements.txt` and can be installed via pip:
  ```bash
  pip install -r requirements.txt
  ```
- **Running the Application**: The application is launched through the `ui.py` script or the console entry point:
  ```bash
  python ui.py
  # or, if installed as a package
  simple-mailer
  ```

## Configuration
- All configuration is managed through the Gradio web interface at runtime.
- There are no on-disk configuration files or environment variables required for the application to run, aside from the necessary `token.json` files for Gmail authentication.