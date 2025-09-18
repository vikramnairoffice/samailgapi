# Simple Gmail REST Mailer

## Project Overview

A completely overhauled Python-based email marketing application focused on Gmail REST API integration with personalized invoice generation. The system has been streamlined to use Gmail REST API exclusively, removing SMTP complexity and authentication issues. Features simplified token-based Gmail authentication, intelligent content management, and comprehensive error handling for reliable email delivery.

## 📁 FILE ORGANIZATION RULES

### Core Directory Structure:
- **Core folder**: Only store essential code files (.py, .js, .html, etc.)
- **Test files**: Store in separate `/tests` folder in core directory
- **Cache files**: Store outside core folder (e.g., `__pycache__`, `.gradio`, temp files)

### File Placement Guidelines:
- ✅ **Core directory**: Main application code, modules, utilities
- ✅ **Tests folder**: Unit tests, integration tests, test utilities
- ✅ **Outside core**: Cache files, temporary files, build artifacts, logs

## Current Features

### Core Components

1. **Gmail REST Mailer** (`mailer.py`) - Pure Gmail REST API email sending engine
   - Gmail REST API integration with direct token authentication
   - Multi-threaded campaign execution with intelligent lead distribution
   - Event-driven progress tracking with real-time updates
   - Enhanced error handling with Gmail API-specific error types
   - Token file loading and validation system
   - Campaign management with attachment building and email composition

2. **InvoiceGenerator** (`invoice.py`) - Advanced PDF/image invoice generation
   - Random invoice data generation with professional styling
   - Personalized account names from recipient emails
   - PDF to image conversion support with PyMuPDF (135 DPI)
   - Support for multiple phone numbers and business types
   - Local logos directory functionality for custom branding
   - HEIF/HEIC image format support via pillow_heif
   - Comprehensive error handling with graceful fallbacks

3. **Content Management System** (`content.py`)
   - Extensive default subject lines (40+ professional templates)
   - Multiple default email body templates with professional tone
   - Advanced sender name generation with business/personal types
   - Faker library integration for realistic names
   - Default recipient seed list for testing
   - Configurable attachment directories (PDF/Image)
   - Send delay configuration for rate limiting

4. **Gradio Web Interface** (`ui.py`) - Clean, minimal user interface
   - Gmail token file upload with multi-file support
   - Real-time file statistics and lead count validation
   - Attachment type selection (Invoice, PDF, Image)
   - Campaign configuration with leads per account setting
   - Sender name type selection (Business/Personal)
   - Progress monitoring with detailed status updates

5. **Token Integration Helpers** (`ui_token_helpers.py`)
   - Token file analysis and validation
   - Campaign execution wrapper with error handling
   - UI output formatting and error surface management
   - Progress tracking integration with Gradio interface

6. **Google Colab Setup Automation** (`colab_setup.py`) - One-command deployment
   - Automated package installation and directory creation
   - Simplified Colab workflow for cloud deployment
   - Enhanced accessibility for rapid testing

### File Structure
```
├── mailer.py              # Gmail REST API email sending engine
├── invoice.py             # PDF/image invoice generation with advanced features
├── ui.py                  # Gradio web interface (simplified, clean design)
├── content.py             # Content templates and sender name management
├── ui_token_helpers.py    # Token integration and campaign execution helpers
├── colab_setup.py         # Google Colab deployment automation
├── setup.py               # Package configuration with proper dependencies
├── requirements.txt       # Core dependencies (7 essential packages)
└── logos/                 # Local logos directory for invoice branding

tests/                     # Comprehensive test suite
├── test_content_manager.py        # Content system validation
├── test_file_processing.py        # File handling and processing tests
├── test_gmail_token_consistency.py # Token scope and loading tests
├── test_token_validation.py       # Token file validation tests
├── test_ui_error_handling.py      # UI error management tests
├── test_ui_selection_logic.py     # UI component interaction tests
├── verify_counts.py               # Data validation utilities
└── verify_gmass_changes.py        # Migration verification tests

testing & qa/              # Legacy test directory (being phased out)
specs/                     # Technical specifications and documentation
```

## Core Dependencies

### Essential Packages (requirements.txt)
```
gradio>=3.0.0          # Web interface framework
reportlab>=3.6.0       # PDF generation for invoices
pymupdf>=1.20.0        # PDF to image conversion
faker>=15.0.0          # Realistic name generation
google-auth>=2.0.0     # Gmail API authentication
requests>=2.25.0       # HTTP requests for Gmail REST API
Pillow>=8.0.0          # Image processing and HEIF support
```

## Development Commands

### Running the Application
```python
python ui.py
```

### Google Colab Deployment
```python
# One-command setup in Google Colab
python colab_setup.py
```

### Installing Dependencies
```bash
pip install -r requirements.txt
```

### Running Tests
```bash
# Content management tests
python tests/test_content_manager.py

# Token validation tests
python tests/test_token_validation.py

# UI integration tests
python tests/test_ui_error_handling.py
python tests/test_ui_selection_logic.py

# Gmail token consistency tests
python tests/test_gmail_token_consistency.py
```

## Gmail REST API Configuration

### Authentication System
- **Gmail REST API Only**: Simplified authentication using direct token upload
- **Required Token Scope**: `['https://mail.google.com/']` for full Gmail access
- **Token File Format**: Named as `<email>.json` (e.g., `user@gmail.com.json`)
- **Multi-Account Support**: Upload multiple token files for campaign distribution

### Campaign Modes
- **Lead Distribution**: Distributes leads evenly across all uploaded Gmail accounts
- **Attachment Types**: Invoice (generated), PDF (from directory), Image (from directory)
- **Rate Limiting**: Configurable send delays to prevent API quota issues

### Gmail API Endpoints Used
- **Profile URL**: `https://gmail.googleapis.com/gmail/v1/users/me/profile`
- **Send URL**: `https://gmail.googleapis.com/gmail/v1/users/me/messages/send`
- **Required Scope**: `['https://mail.google.com/']`

## Recent Major Overhaul (September 2025)

### Complete System Redesign
- ✅ **GMAIL REST API EXCLUSIVE**: Removed all SMTP code and dependencies
  - Eliminated complex SMTP connection management and authentication issues
  - Simplified to Gmail REST API only for reliable, consistent email delivery
  - Removed persistent connection complexity in favor of stateless API calls

- ✅ **STREAMLINED CODEBASE**: Massive code reduction and simplification
  - Removed token_manager.py (functionality integrated into mailer.py)
  - Simplified UI to essential functions only
  - Eliminated redundant authentication paths and error handling layers
  - Clean, focused architecture with single responsibility components

- ✅ **ENHANCED TESTING SUITE**: Comprehensive test coverage for new architecture
  - Token validation and scope consistency tests
  - UI error handling and selection logic validation
  - Content management system tests with faker library stubs
  - File processing and attachment generation tests

- ✅ **IMPROVED USER EXPERIENCE**: Simplified interface with better feedback
  - Clean Gradio interface with essential controls only
  - Real-time file statistics and progress updates
  - Intelligent error messaging and troubleshooting guidance
  - Streamlined campaign configuration and execution

## UI Development Guidelines

### Interface Framework Requirements
- **UI Framework**: MUST use Gradio exclusively for all user interface development
- **No HTML/CSS**: Do not create custom HTML, CSS, or other web technologies
- **No Alternative Frameworks**: Do not use Streamlit, Flask, Django, or any other web frameworks
- **Gradio Components**: Use only Gradio's built-in components (gr.Button, gr.Textbox, gr.File, etc.)
- **Styling**: Use Gradio's theming and built-in styling options only

## Technical Architecture

### Gmail REST API Integration
- **Stateless Design**: Each email sent via independent Gmail REST API call
- **Token Management**: Direct token file loading with scope validation
- **Error Handling**: Gmail API-specific error categorization and recovery
- **Multi-Threading**: Campaign workers with independent token file access
- **Progress Tracking**: Event-driven updates with real-time UI feedback

### Content Generation System
- **Template-Based**: Professional subject lines and email bodies from templates
- **Dynamic Invoices**: Generated per recipient with personalized account details
- **Flexible Attachments**: Support for generated invoices, random PDFs, or images
- **Sender Personalization**: Business or personal sender name generation

## Security & Best Practices

- Direct Gmail token file management without OAuth flow complexity
- Isolated token storage per Gmail account with standardized naming
- Gmail REST API rate limiting and quota management
- Comprehensive error handling with actionable debugging information
- Clean codebase without legacy authentication artifacts
- Test-driven development ensuring reliability and maintainability

## Code Standards & Restrictions

### Unicode Character Policy
**STRICTLY PROHIBITED**: No Unicode characters, emojis, or special symbols in code files
- **Banned**: Emojis (🚀, 📧, ✅, ❌, etc.)
- **Banned**: Unicode progress bars (█, ░)
- **Banned**: Unicode bullet points (•)
- **Banned**: Any non-ASCII characters in code
- **Allowed**: Standard ASCII characters only (A-Z, a-z, 0-9, basic punctuation)
- **Allowed**: Essential encoding/decoding functions (base64, UTF-8) for API compatibility

**Rationale**: Unicode characters cause constant compatibility issues across different systems and environments.