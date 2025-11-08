# Parallax Web Editor

A modern, VS Code-like web interface for the Parallax AI-assisted plan editor.

## Features

- **3-Pane Layout**: Resizable panes for file explorer, editor, and AI feed
- **Monaco Editor**: Full-featured markdown editor with syntax highlighting
- **AI Feed Panel**: Real-time display of AI suggestions, questions, and context
- **Command Palette** (Ctrl+P): Quick command access VS Code-style
- **Vim Command Bar**: Vim-style commands with `:` prefix
- **Keyboard Shortcuts**: Comprehensive keyboard navigation

## Commands

### Command Palette (Ctrl+P)
- Focus: File Explorer (Ctrl+1)
- Focus: Editor (Ctrl+2)
- Focus: AI Feed (Ctrl+3)
- Toggle Sidebar (Ctrl+B)

### Vim Commands (Press `:`)
- `:files` - Focus file explorer
- `:edit` - Focus editor
- `:feed` - Focus AI feed
- `:clear` - Clear AI feed

## Development

```bash
npm install
npm run dev      # Start dev server at http://localhost:5173/
npm test         # Run unit tests (29 passing)
npm run build    # Build for production
```

## Technology Stack

- React 19 + TypeScript
- Monaco Editor (VS Code's editor)
- Zustand (state management)
- Tailwind CSS + Allotment (resizable panes)
- Vitest + Testing Library

## Status

✅ All core features implemented
✅ 29 unit tests passing
✅ Dev server running
⏳ Backend integration pending
