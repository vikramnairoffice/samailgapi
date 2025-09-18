# Tech Stack and Dependencies

## Core Dependencies (requirements.txt)
```
gradio>=3.0.0          # Web interface framework
reportlab>=3.6.0       # PDF generation for invoices
pymupdf>=1.20.0        # PDF to image conversion
faker>=15.0.0          # Realistic name generation
google-auth>=2.0.0     # Gmail API authentication
requests>=2.25.0       # HTTP requests for Gmail REST API
Pillow>=8.0.0          # Image processing and HEIF support
```

## Runtime Environment
- **Language**: Python 3.x
- **Platform**: Windows (PowerShell environment)
- **UI Framework**: Gradio exclusively (no HTML/CSS/other frameworks allowed)
- **API**: Gmail REST API only (no SMTP)

## Gmail API Configuration
- **Required Scope**: `['https://mail.google.com/']`
- **Token Format**: Named as `<email>.json` (e.g., `user@gmail.com.json`)
- **Endpoints Used**:
  - Profile: `https://gmail.googleapis.com/gmail/v1/users/me/profile`
  - Send: `https://gmail.googleapis.com/gmail/v1/users/me/messages/send`

## Testing Framework
- Primary: `unittest` (Python standard library)
- Additional: `pytest` (for some tests)
- Mocking: `unittest.mock`