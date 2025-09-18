# Code Style and Conventions

## Unicode Character Policy (CRITICAL)
**STRICTLY PROHIBITED**: No Unicode characters, emojis, or special symbols in code files
- **Banned**: Emojis (🚀, 📧, ✅, ❌, etc.)
- **Banned**: Unicode progress bars (█, ░)
- **Banned**: Unicode bullet points (•)
- **Banned**: Any non-ASCII characters in code
- **Allowed**: Standard ASCII characters only (A-Z, a-z, 0-9, basic punctuation)
- **Allowed**: Essential encoding/decoding functions (base64, UTF-8) for API compatibility

**Rationale**: Unicode characters cause constant compatibility issues across different systems and environments.

## UI Framework Requirements
- **MUST use Gradio exclusively** for all user interface development
- **No HTML/CSS**: Do not create custom HTML, CSS, or other web technologies
- **No Alternative Frameworks**: Do not use Streamlit, Flask, Django, or any other web frameworks
- **Gradio Components**: Use only Gradio's built-in components (gr.Button, gr.Textbox, gr.File, etc.)
- **Styling**: Use Gradio's theming and built-in styling options only

## Python Conventions
- Function names: snake_case (e.g., `send_gmail_message`, `load_token_files`)
- Docstrings: Simple descriptive strings for function purposes
- Error handling: Raise RuntimeError with descriptive messages
- Testing: Use unittest.TestCase for test classes

## File Organization
- **Core files**: Main application code in root directory
- **Tests**: Stored in `/tests` folder
- **Legacy**: `testing & qa/` directory being phased out
- **Specs**: Technical documentation in `/specs` folder