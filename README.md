# Parallax

A modern terminal-based text editor with integrated AI assistance capabilities, built with Python and Textual.

## Overview

Parallax is a vim-inspired terminal text editor featuring a three-pane interface:
- **Left Pane**: File explorer for navigating your project structure
- **Center Pane**: Text editor with syntax highlighting and line numbers
- **Right Pane**: AI information feed (placeholder for future AI integration)
- **Bottom**: Command mode for executing editor commands (vim-style with `:` prefix)

## Features

- 🎨 **Syntax Highlighting**: Currently supports Markdown with extensible architecture
- 🔢 **Line Numbers**: Clear line numbering in the editor
- 📁 **File Explorer**: Full directory tree navigation
- 🤖 **AI Integration Ready**: Modular design for easy AI endpoint integration
- ⌨️ **Command Mode**: Vim-style command interface (`:command`)
- 🧩 **Modular Architecture**: Clean separation of concerns for easy maintenance

## Requirements

- Python 3.11 or higher
- Textual TUI framework

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd parallax
```

2. Create a virtual environment (recommended):
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

Run Parallax from the command line:

```bash
python -m parallax.main
```

Or with a specific file:

```bash
python -m parallax.main /path/to/file.md
```

### Command Mode

Press `:` to enter command mode at the bottom of the screen. Type your command and press Enter.

*Note: Command handlers are placeholders and will be implemented in future versions.*

## Project Structure

```
parallax/
├── README.md
├── requirements.txt
├── parallax/
│   ├── __init__.py
│   ├── main.py                 # Main application entry point
│   ├── app.py                  # Textual app with 3-pane layout
│   ├── widgets/
│   │   ├── __init__.py
│   │   ├── file_explorer.py   # File tree navigation
│   │   ├── text_editor.py     # Editor with line numbers
│   │   ├── ai_feed.py          # AI information boxes
│   │   └── command_input.py   # Command mode input
│   ├── core/
│   │   ├── __init__.py
│   │   ├── command_handler.py # Command processing logic
│   │   └── syntax_highlighter.py # Syntax highlighting
│   └── config/
│       ├── __init__.py
│       └── ai_config.py        # AI feed configuration
└── tests/
    ├── __init__.py
    ├── test_command_handler.py
    ├── test_syntax_highlighter.py
    └── test_ai_feed.py
```

## Development

### Running Tests

Make sure your virtual environment is activated, then run:

```bash
pytest tests/ -v
```

All tests should pass successfully. The test suite includes 44+ unit tests covering:
- Command handler functionality
- Syntax highlighting for multiple file types
- AI feed configuration management

### Adding New Syntax Highlighting

Extend the `SyntaxHighlighter` class in `parallax/core/syntax_highlighter.py`:

```python
def highlight_python(self, content: str) -> str:
    # Add your highlighting logic
    pass
```

### Configuring AI Feed

Modify `parallax/config/ai_config.py` to customize the information boxes:

```python
AI_FEED_CONFIG = [
    {"header": "Your Header", "content": "Your content"},
    # Add more boxes
]
```

### Implementing Commands

Add command handlers in `parallax/core/command_handler.py`:

```python
def handle_save(self, args: list[str]) -> str:
    # Implement save logic
    pass
```

## Roadmap

- [ ] Command implementation (`:w`, `:q`, `:open`, etc.)
- [ ] AI endpoint integration
- [ ] Multiple syntax highlighting support (Python, JavaScript, etc.)
- [ ] File creation/deletion in explorer
- [ ] Search and replace
- [ ] Multiple buffer support
- [ ] Configuration file support
- [ ] Plugin system

## Contributing

Contributions are welcome! Please ensure all tests pass before submitting a pull request.

## License

MIT License (or your preferred license)

## Acknowledgments

Built with [Textual](https://github.com/Textualize/textual) - the modern TUI framework for Python.
