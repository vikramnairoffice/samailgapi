# Essential Development Commands

## Running the Application
```bash
python ui.py
```

## Installing Dependencies
```bash
pip install -r requirements.txt
```

## Testing Commands
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

# File processing tests
python tests/test_file_processing.py
```

## Google Colab Deployment
```bash
python colab_setup.py
```

## PowerShell Utilities (Windows Environment)
- Use PowerShell commands over Git Bash when possible
- Standard Windows file operations and navigation

## File Structure Validation
```bash
# Verify test counts and data validation
python tests/verify_counts.py
python tests/verify_gmass_changes.py
```