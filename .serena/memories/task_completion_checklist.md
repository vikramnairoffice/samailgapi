# Task Completion Checklist

## When Code Changes Are Made

### 1. Testing Requirements
- Run relevant test files from `/tests` directory
- Verify no regressions in core functionality
- Test Gmail token validation if authentication code is modified
- Test UI components if interface code is changed

### 2. Code Quality Checks
- Ensure no Unicode characters are introduced
- Verify Gradio-only UI components (no HTML/CSS)
- Check that all functions follow snake_case naming
- Validate error handling uses RuntimeError with descriptive messages

### 3. File Organization
- Keep core application files in root directory
- Store new test files in `/tests` folder
- Avoid creating unnecessary documentation files unless explicitly requested

### 4. Gmail API Compliance
- Verify token scope remains `['https://mail.google.com/']`
- Test token loading and validation functionality
- Ensure Gmail REST API endpoints are correctly used

### 5. Pre-deployment Testing
```bash
# Run key test suites
python tests/test_content_manager.py
python tests/test_token_validation.py
python tests/test_ui_error_handling.py
```

### 6. Functional Verification
- Test application startup: `python ui.py`
- Verify Gradio interface loads correctly
- Check token upload functionality works