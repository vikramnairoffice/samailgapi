# Google Colab Setup Guide - Simple Mailer with Personalized Attachments

## 🚀 Quick Setup (Copy-Paste Ready)

### Step 1: Install the Package
Copy and paste this cell into your Google Colab notebook:

```python
# Install the Simple Mailer package directly from GitHub
!pip install git+https://github.com/vikramnairoffice/Simple-mailer-with-personlization.git

# Or install all dependencies manually if the above doesn't work
!pip install gradio>=3.0.0 reportlab>=3.6.0 pymupdf>=1.20.0 faker>=15.0.0
!pip install google-auth-oauthlib>=0.8.0 google-api-python-client>=2.70.0
!pip install requests>=2.25.0 beautifulsoup4>=4.9.0 Pillow>=8.0.0
```

### Step 2: Import and Launch the Application
Copy and paste this cell:

```python
# Import the UI module
from ui import main

# Launch the Gradio interface
main()
```

### Step 3: Alternative Launch Method
If the above doesn't work, try this alternative approach:

```python
# Download the core files directly
import subprocess
import os

# No need to create core directory - files are now in root

# Download main files (replace with your actual raw GitHub URLs)
files_to_download = [
    'ui.py',
    'mailer.py', 
    'invoice.py',
    'content.py',
    'token_manager.py',
    'ui_token_helpers.py',
    'requirements.txt'
]

# Download each file
for file_name in files_to_download:
    !wget -O {file_name} https://raw.githubusercontent.com/vikramnairoffice/Simple-mailer-with-personlization/main/{file_name}

# Install dependencies
!pip install -r requirements.txt

# Launch the application
exec(open('ui.py').read())
```

## 📁 File Upload Instructions

### Required Files:
1. **Accounts File** (format: `email@domain.com,password`)
2. **Leads File** (one email per line)
3. **Gmail Token Files** (JSON format from Google Cloud Console)

### Upload Process:
1. Use the file upload widgets in the Gradio interface
2. For Gmail API: Upload your OAuth2 credential JSON files
3. Follow the simplified token-based authentication process

## 🔧 Google Colab Optimizations

### Token-Based Authentication
- **No browser automation required** - perfect for Colab environment
- **Direct token file upload** instead of complex OAuth flows
- **Simplified authentication process** designed for Colab constraints

### File Management
- All generated files (invoices, tokens) are stored in Colab's temporary storage
- Download generated reports and invoices before session ends
- Token files persist during the Colab session

### Performance Features
- **Persistent SMTP connections** (84% performance improvement)
- **Multi-threaded sending** optimized for Colab resources
- **Real-time progress tracking** in the web interface

## 📊 Usage in Google Colab

### Basic Workflow:
1. **Run Installation Cell** → Install packages
2. **Run Launch Cell** → Start the web interface
3. **Upload Files** → Accounts, leads, and token files via the UI
4. **Configure Settings** → Email content, attachments, delays
5. **Send Emails** → Monitor progress in real-time

### Advanced Features:
- **Invoice Generation**: Personalized PDF/image invoices
- **Multiple SMTP Providers**: Gmail, Yahoo, Outlook, AOL
- **Attachment Support**: PDF, images, or generated invoices
- **Progress Monitoring**: Real-time status and error tracking

## 🔒 Security in Colab

### Token Management:
- Tokens are stored temporarily in the Colab session
- No persistent storage of sensitive credentials
- Isolated authentication per account

### Best Practices:
- Upload credential files only when needed
- Clear sensitive data before sharing notebooks
- Use app passwords for SMTP when possible

## 🐛 Troubleshooting

### Common Issues:

**Installation Problems:**
```python
# If pip install fails, try installing dependencies individually:
!pip install gradio --upgrade
!pip install reportlab pymupdf faker
!pip install google-auth-oauthlib google-api-python-client
```

**Import Errors:**
```python
# Try restarting runtime and running installation again
# Runtime → Restart Runtime
```

**File Access Issues:**
```python
# Ensure files are in the correct directory
import os
print("Current directory:", os.getcwd())
print("Python files:", [f for f in os.listdir('.') if f.endswith('.py')])
```

**Authentication Issues:**
- Use the simplified token upload method
- Ensure JSON credential files are valid
- Check token file format and permissions

## 📞 Support

For issues specific to Google Colab setup:
1. Check that all dependencies are installed correctly
2. Verify file paths and permissions
3. Use the simplified authentication methods designed for Colab
4. Restart runtime if you encounter import issues

## 🎯 Quick Test

Test the installation with this simple verification:

```python
# Quick verification script
try:
    from ui import main
    print("✅ Installation successful! Ready to launch.")
    print("Run main() to start the application.")
except ImportError as e:
    print(f"❌ Installation issue: {e}")
    print("Please run the installation steps again.")
```

---

**Note**: This application is optimized for Google Colab with token-based authentication and simplified file management. All complex OAuth flows have been replaced with direct token upload methods for maximum Colab compatibility.