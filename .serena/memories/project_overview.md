# Simple Gmail REST Mailer - Project Overview

## Purpose
A Python-based email marketing application that uses Gmail REST API exclusively for sending personalized emails with generated invoice attachments. The system has been completely overhauled to eliminate SMTP complexity and focus on reliability through Gmail's REST API.

## Core Architecture
- **Gmail REST API Only**: Stateless email sending using OAuth tokens
- **Multi-threaded Campaign Execution**: Lead distribution across multiple Gmail accounts
- **Real-time Progress Tracking**: Event-driven updates with Gradio UI integration
- **Dynamic Content Generation**: Invoice generation with personalized details
- **Token-based Authentication**: Direct token file upload and validation

## Key Components
1. **mailer.py**: Core Gmail REST API engine with multi-threading
2. **invoice.py**: PDF/image invoice generation with branding support
3. **ui.py**: Gradio web interface for campaign management
4. **content.py**: Template management for subjects, bodies, and sender names
5. **ui_token_helpers.py**: UI integration and campaign execution wrapper

## Recent Major Overhaul (September 2025)
- Removed all SMTP code and dependencies
- Streamlined to Gmail REST API exclusive operation
- Eliminated token_manager.py (functionality moved to mailer.py)
- Enhanced testing suite with comprehensive coverage
- Simplified UI to essential functions only