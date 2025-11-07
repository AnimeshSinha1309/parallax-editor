# Ghost Text Implementation Guide

## Overview

Ghost text completions are inline code suggestions that appear as greyed-out text at the cursor position. This document outlines what's been prepared and what needs to be implemented.

## Current Status

### ✅ Completed Foundation

1. **Card Model Enhancement** (`fulfillers/models.py`)
   - Added `CardType` enum with values: QUESTION, CONTEXT, COMPLETION
   - Updated `Card` dataclass to include `type` field
   - All cards now categorized by type

2. **Fulfiller Architecture**
   - Created `DummyFulfiller` (`fulfillers/dummy.py`) for placeholder completions
   - Returns mix of CONTEXT, QUESTION, and COMPLETION cards
   - All fulfillers implement async `invoke()` method

3. **FeedHandler Refactoring** (`parallax/core/feed_handler.py`)
   - Now uses `List[Card]` instead of `list[dict]`
   - Registers multiple fulfillers via `register_fulfiller()`
   - Invokes all fulfillers concurrently using `asyncio.gather()`
   - Separates cards by type:
     - COMPLETION → Ghost text
     - QUESTION/CONTEXT → Sidebar cards
   - Added `set_text_editor()` method for ghost text reference
   - Calls `text_editor.set_ghost_text()` when COMPLETION cards received

4. **TextEditor Preparation** (`parallax/widgets/text_editor.py`)
   - Added `ghost_text` and `ghost_text_visible` state fields
   - Created placeholder methods:
     - `set_ghost_text(completion)` - Store and display ghost text
     - `clear_ghost_text()` - Remove ghost text
     - `accept_ghost_text()` - Insert ghost text at cursor
   - Added comprehensive TODO comments with implementation notes

5. **AIFeed Updates** (`parallax/widgets/ai_feed.py`)
   - Updated `update_content()` to accept `List[Card]`
   - Removed backward compatibility with dict format
   - All cards now use `card.header` and `card.text`

6. **ParallaxApp Integration** (`parallax/app.py`)
   - Registers `DummyFulfiller` on startup
   - Sets both AI feed and text editor references in FeedHandler
   - Passes cursor position to FeedHandler on text changes

## 🚧 TODO: Ghost Text Rendering

The core challenge is **rendering grey text inline** within Textual's TextArea widget.

### Challenge

Textual's `TextArea` doesn't natively support inline overlays or styled ghost text. We need to choose an implementation approach:

### Option A: Rich Text Overlay (Recommended)

Create a transparent overlay widget that renders ghost text using Rich styling.

**Implementation Steps:**

1. Create `GhostTextOverlay` widget:
```python
class GhostTextOverlay(Widget):
    """Overlay widget that renders ghost text at cursor position."""

    def __init__(self, text_area: TextArea):
        super().__init__()
        self.text_area = text_area
        self.ghost_text = ""

    def render(self) -> RenderableType:
        if not self.ghost_text:
            return Text("")

        # Calculate cursor screen position
        cursor_row, cursor_col = self.text_area.cursor_location

        # Create Rich Text with dim styling
        from rich.text import Text
        ghost = Text(self.ghost_text, style="dim")

        # Position at cursor (requires coordinate mapping)
        # TODO: Map (row, col) to screen coordinates
        return ghost
```

2. Update `TextEditor.compose()`:
```python
def compose(self):
    with Container():
        yield TextArea(id="text-area", ...)
        yield GhostTextOverlay(id="ghost-overlay")
```

3. Update `set_ghost_text()` to refresh overlay:
```python
def set_ghost_text(self, completion: str):
    self.ghost_text = completion
    overlay = self.query_one("#ghost-overlay", GhostTextOverlay)
    overlay.ghost_text = completion
    overlay.refresh()
```

**Pros:**
- Clean separation of concerns
- Doesn't modify TextArea internals
- Easy to style with Rich

**Cons:**
- Coordinate mapping complexity (cursor position → screen coordinates)
- May have z-index/layering issues

### Option B: Extend TextArea

Subclass TextArea and override rendering to inject ghost text.

**Implementation Steps:**

1. Create `GhostTextArea(TextArea)`:
```python
class GhostTextArea(TextArea):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.ghost_text = ""

    def render_line(self, y: int) -> Strip:
        # Get normal line rendering
        strip = super().render_line(y)

        # If this is cursor line, append ghost text
        cursor_row, cursor_col = self.cursor_location
        if y == cursor_row and self.ghost_text:
            # Inject dimmed ghost text after cursor
            # TODO: Modify Strip to include ghost text
            pass

        return strip
```

2. Replace TextArea with GhostTextArea in `TextEditor.compose()`

**Pros:**
- Direct access to rendering pipeline
- Precise cursor positioning
- No coordinate mapping needed

**Cons:**
- Tightly coupled to TextArea internals
- May break with Textual updates
- More complex rendering logic

### Option C: Temporary Text Insertion

Insert ghost text directly into TextArea with special markers, remove on keystroke.

**Implementation Steps:**

1. Insert completion text with markers:
```python
def set_ghost_text(self, completion: str):
    text_area = self.query_one("#text-area", TextArea)
    cursor_row, cursor_col = text_area.cursor_location

    lines = text_area.text.split('\n')
    line = lines[cursor_row]

    # Insert with markers: ⟪completion⟫
    new_line = line[:cursor_col] + "⟪" + completion + "⟫" + line[cursor_col:]
    lines[cursor_row] = new_line
    text_area.load_text('\n'.join(lines))
```

2. Remove markers on keystroke

**Pros:**
- Simplest implementation
- No custom rendering needed

**Cons:**
- Pollutes actual text content
- Can't style text as "dim" easily
- Marker characters may conflict with actual content
- Not a true "ghost" text (user sees markers)

## 🎯 Recommended Approach

**Start with Option A (Rich Text Overlay)** for cleaner architecture:

1. Create `GhostTextOverlay` widget in `parallax/widgets/ghost_text_overlay.py`
2. Solve coordinate mapping (cursor position → screen position)
3. Handle Tab key to accept completion
4. Handle any keystroke to dismiss completion
5. Add visual styling (dim grey text, subtle background)

If coordinate mapping proves too difficult, **fall back to Option B** (extend TextArea).

## 🔑 Key Features to Implement

### 1. Tab Key Acceptance

Add to `ParallaxApp`:

```python
def on_key(self, event: events.Key) -> None:
    if event.key == "tab":
        editor = self.query_one("#text-editor", TextEditor)
        if editor.accept_ghost_text():
            event.prevent_default()
            return
```

### 2. Auto-Dismiss on Keystroke

Clear ghost text on any non-Tab keystroke:

```python
def on_text_area_changed(self, event: TextArea.Changed):
    # Clear ghost text when user types
    editor = self.query_one("#text-editor", TextEditor)
    editor.clear_ghost_text()

    # Then proceed with normal handling
    self.feed_handler.on_text_change(...)
```

### 3. Debouncing (300ms)

Add debounce to avoid triggering on every keystroke:

```python
import asyncio

class FeedHandler:
    def __init__(self, ...):
        self._debounce_task = None

    def on_text_change(self, new_content: str, ...):
        # Cancel previous debounce
        if self._debounce_task:
            self._debounce_task.cancel()

        # Schedule new update after 300ms
        self._debounce_task = asyncio.create_task(
            self._debounced_update(new_content)
        )

    async def _debounced_update(self, text_buffer: str):
        await asyncio.sleep(0.3)  # 300ms debounce
        await self._trigger_update_async(text_buffer)
```

### 4. Multi-line Completions

Currently only single-line completions supported. For multi-line:

- Detect newlines in completion text
- Render across multiple lines
- Update acceptance logic to handle multi-line insertion

## 📁 File Locations

- **Card Model**: `fulfillers/models.py` (CardType enum, Card dataclass)
- **Dummy Fulfiller**: `fulfillers/dummy.py` (placeholder completions)
- **Feed Handler**: `parallax/core/feed_handler.py` (orchestration)
- **Text Editor**: `parallax/widgets/text_editor.py` (ghost text state, TODO methods)
- **AI Feed**: `parallax/widgets/ai_feed.py` (sidebar cards)
- **Main App**: `parallax/app.py` (integration, event handling)

## 🧪 Testing Strategy

1. **Unit Tests**:
   - Test Card model serialization
   - Test DummyFulfiller returns correct card types
   - Test FeedHandler separates cards by type

2. **Integration Tests**:
   - Type 20 characters → verify fulfiller invoked
   - Verify COMPLETION cards trigger ghost text
   - Verify CONTEXT/QUESTION cards update sidebar

3. **Manual Testing**:
   - Open file, type code
   - After 20 chars, see ghost text appear (dim grey)
   - Press Tab → ghost text inserted
   - Press any key → ghost text dismissed
   - Check sidebar cards update

## 🔄 Future Enhancements

1. **LLM Integration**: Replace DummyFulfiller with actual K2 Think API
2. **Semantic Context**: Pass surrounding code context to fulfillers
3. **Multi-Agent**: Add separate agents for questions, context, completion
4. **Smart Filtering**: Don't re-surface dismissed completions
5. **Ranking**: Use relevance scoring for multiple completions
6. **Inline Documentation**: Show function signatures in ghost text

## 📝 Summary

The architecture is **ready for ghost text**:
- ✅ Cards are properly typed (COMPLETION for ghost text)
- ✅ Fulfillers return COMPLETION cards
- ✅ FeedHandler routes COMPLETION cards to TextEditor
- ✅ TextEditor has placeholder methods ready

**What's missing**: The actual rendering of grey text in the editor. This is a Textual-specific UI challenge that requires either custom overlay widgets or extending TextArea's render method.

The recommendation is to start with **Option A (Rich Text Overlay)** as it's cleaner and more maintainable, even though it requires solving the coordinate mapping problem.
