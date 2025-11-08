# Backend Integration Plan for Parallax Web Editor

## Overview
Integrate the web frontend with the Parallizer backend following the same pattern used by the CLI, including real-time AI suggestions, ghost text completions, and polling for incremental updates.

---

## 1. Current State Analysis

### What We Have (Web Frontend)
- ✅ Monaco Editor with markdown support
- ✅ AI Feed panel with card display
- ✅ State management (Zustand stores)
- ✅ Keyboard shortcuts system
- ✅ Mock data for demo

### What CLI Does (Reference Implementation)
- **Character Threshold**: 20 characters typed triggers debounce
- **Idle Timer**: 4 seconds of inactivity before calling backend
- **POST /fulfill**: Sends document + cursor + context → gets immediate response
- **Poll /cached**: Every 3 seconds until `processing=false`
- **Card Separation**: COMPLETION → ghost text, QUESTION/CONTEXT → sidebar
- **Ghost Text**: Bold magenta, accept with Tab/Right, dismiss with Esc
- **Error Handling**: Retries with exponential backoff, caches last successful response

---

## 2. Architecture Plan

### Data Flow
```
User Types
    ↓
Character Counter (20+ chars)
    ↓
Idle Timer (4 seconds)
    ↓
POST /fulfill
    ├─→ Immediate Response (cached cards + processing=true)
    └─→ Background Processing (4 fulfillers in parallel)
    ↓
Poll /cached (every 3 seconds)
    ├─→ Get incremental updates
    └─→ Stop when processing=false
    ↓
Separate Cards by Type
    ├─→ COMPLETION → Monaco Inline Completions (ghost text)
    └─→ QUESTION/CONTEXT → AI Feed Store
    ↓
Display & Await User Action
    ├─→ Tab/Right Arrow → Accept completion
    └─→ Esc/Any Key → Dismiss completion
```

### New Components/Files to Create

```
web/src/
├── services/
│   ├── api.ts                      # HTTP client (existing - enhance)
│   └── backendService.ts           # NEW: /fulfill & /cached API calls
├── hooks/
│   ├── useFulfillment.ts           # NEW: Debouncing + backend integration
│   └── usePolling.ts               # NEW: Poll /cached endpoint
├── components/PlanEditor/
│   ├── MonacoEditor.tsx            # MODIFY: Add inline completions provider
│   └── GhostTextProvider.ts        # NEW: Monaco inline completions integration
├── stores/
│   ├── completionStore.ts          # NEW: Track current ghost text completion
│   └── feedStore.ts                # MODIFY: Add backend update methods
└── utils/
    ├── config.ts                   # NEW: Backend URL configuration
    └── debounce.ts                 # NEW: Debouncing utility
```

---

## 3. Implementation Steps

### Step 1: Configuration & API Service

**File: `web/src/utils/config.ts`**
```typescript
export const config = {
  backendUrl: import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000',
  fulfillment: {
    charThreshold: 20,      // Same as CLI
    idleTimeout: 4000,      // 4 seconds
    pollInterval: 3000,     // 3 seconds
    maxRetries: 3,
  },
};
```

**File: `web/src/services/backendService.ts`**
```typescript
import type { FulfillRequest, FulfillResponse } from '../types/models';

export class BackendService {
  private baseUrl: string;

  constructor(baseUrl: string) {
    this.baseUrl = baseUrl;
  }

  // POST /fulfill - Initial request
  async fulfill(request: FulfillRequest): Promise<FulfillResponse & { processing: boolean }> {
    const response = await fetch(`${this.baseUrl}/fulfill`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      throw new Error(`Fulfill failed: ${response.status}`);
    }

    return response.json();
  }

  // GET /cached - Poll for updates
  async getCached(userId: string): Promise<FulfillResponse & { processing: boolean }> {
    const response = await fetch(`${this.baseUrl}/user/${userId}/cached`);

    if (!response.ok) {
      throw new Error(`Get cached failed: ${response.status}`);
    }

    return response.json();
  }

  // DELETE /feed - Clear user feed
  async clearFeed(userId: string): Promise<void> {
    await fetch(`${this.baseUrl}/user/${userId}/feed`, {
      method: 'DELETE',
    });
  }
}

export const backendService = new BackendService(config.backendUrl);
```

---

### Step 2: Debouncing Hook

**File: `web/src/hooks/useFulfillment.ts`**
```typescript
import { useEffect, useRef, useState } from 'react';
import { useEditorStore } from '../stores/editorStore';
import { useFileSystemStore } from '../stores/fileSystemStore';
import { backendService } from '../services/backendService';
import { config } from '../utils/config';

export function useFulfillment(userId: string) {
  const [charCount, setCharCount] = useState(0);
  const [isProcessing, setIsProcessing] = useState(false);
  const idleTimerRef = useRef<NodeJS.Timeout | null>(null);
  const pollingIntervalRef = useRef<NodeJS.Timeout | null>(null);

  const { content, cursorPosition } = useEditorStore();
  const { scopeRoot, planPath } = useFileSystemStore();

  const callBackend = async () => {
    try {
      setIsProcessing(true);

      // Call /fulfill
      const response = await backendService.fulfill({
        user_id: userId,
        document_text: content,
        cursor_position: cursorPosition,
        global_context: {
          scope_root: scopeRoot,
          plan_path: planPath || undefined,
        },
      });

      // Handle immediate response
      handleCards(response.cards);

      // Start polling if still processing
      if (response.processing) {
        startPolling(userId);
      } else {
        setIsProcessing(false);
      }
    } catch (error) {
      console.error('Fulfillment failed:', error);
      setIsProcessing(false);
    }
  };

  const startPolling = (userId: string) => {
    // Clear existing poll
    if (pollingIntervalRef.current) {
      clearInterval(pollingIntervalRef.current);
    }

    // Poll every 3 seconds
    pollingIntervalRef.current = setInterval(async () => {
      try {
        const cached = await backendService.getCached(userId);
        handleCards(cached.cards);

        // Stop polling when done
        if (!cached.processing) {
          stopPolling();
          setIsProcessing(false);
        }
      } catch (error) {
        console.error('Polling failed:', error);
        stopPolling();
        setIsProcessing(false);
      }
    }, config.fulfillment.pollInterval);
  };

  const stopPolling = () => {
    if (pollingIntervalRef.current) {
      clearInterval(pollingIntervalRef.current);
      pollingIntervalRef.current = null;
    }
  };

  const handleCards = (cards: Card[]) => {
    // Separate by type
    const completions = cards.filter(c => c.type === CardType.COMPLETION);
    const feedCards = cards.filter(c => c.type !== CardType.COMPLETION);

    // Update stores
    if (completions.length > 0) {
      useCompletionStore.getState().setCompletion(completions[0]);
    }

    if (feedCards.length > 0) {
      useFeedStore.getState().addCards(feedCards);
    }
  };

  // Track character changes
  useEffect(() => {
    const prevContentRef = { current: content };

    return () => {
      // Count characters typed
      const diff = Math.abs(content.length - prevContentRef.current.length);
      setCharCount(prev => prev + diff);
      prevContentRef.current = content;
    };
  }, [content]);

  // Handle debouncing
  useEffect(() => {
    if (charCount >= config.fulfillment.charThreshold && !isProcessing) {
      // Cancel existing timer
      if (idleTimerRef.current) {
        clearTimeout(idleTimerRef.current);
      }

      // Start new idle timer
      idleTimerRef.current = setTimeout(() => {
        callBackend();
        setCharCount(0);
      }, config.fulfillment.idleTimeout);
    }

    return () => {
      if (idleTimerRef.current) {
        clearTimeout(idleTimerRef.current);
      }
    };
  }, [charCount, isProcessing]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      stopPolling();
    };
  }, []);

  return {
    charCount,
    isProcessing,
  };
}
```

---

### Step 3: Completion Store

**File: `web/src/stores/completionStore.ts`**
```typescript
import { create } from 'zustand';

interface CompletionStore {
  // Current completion suggestion
  currentCompletion: string | null;
  completionMetadata: Record<string, any> | null;

  // Actions
  setCompletion: (card: Card) => void;
  clearCompletion: () => void;
  acceptCompletion: () => void;
  rejectCompletion: () => void;
}

export const useCompletionStore = create<CompletionStore>((set, get) => ({
  currentCompletion: null,
  completionMetadata: null,

  setCompletion: (card: Card) =>
    set({
      currentCompletion: card.text,
      completionMetadata: card.metadata || {},
    }),

  clearCompletion: () =>
    set({
      currentCompletion: null,
      completionMetadata: null,
    }),

  acceptCompletion: () => {
    const { currentCompletion } = get();
    if (currentCompletion) {
      // Insert text into editor
      const { content, cursorPosition, setContent, setCursorPosition } = useEditorStore.getState();
      const [line, col] = cursorPosition;

      // Insert completion at cursor
      const lines = content.split('\n');
      const currentLine = lines[line] || '';
      const before = currentLine.slice(0, col);
      const after = currentLine.slice(col);
      lines[line] = before + currentCompletion + after;

      setContent(lines.join('\n'));
      setCursorPosition([line, col + currentCompletion.length]);

      // Clear completion
      set({ currentCompletion: null, completionMetadata: null });
    }
  },

  rejectCompletion: () => {
    set({ currentCompletion: null, completionMetadata: null });
  },
}));
```

---

### Step 4: Monaco Inline Completions

**File: `web/src/components/PlanEditor/GhostTextProvider.ts`**
```typescript
import * as monaco from 'monaco-editor';
import { useCompletionStore } from '../../stores/completionStore';

export class GhostTextProvider implements monaco.languages.InlineCompletionsProvider {
  async provideInlineCompletions(
    model: monaco.editor.ITextModel,
    position: monaco.Position,
    context: monaco.languages.InlineCompletionContext,
    token: monaco.CancellationToken
  ): Promise<monaco.languages.InlineCompletions | undefined> {

    const completion = useCompletionStore.getState().currentCompletion;

    if (!completion) {
      return undefined;
    }

    return {
      items: [
        {
          insertText: completion,
          range: new monaco.Range(
            position.lineNumber,
            position.column,
            position.lineNumber,
            position.column
          ),
          command: undefined,
        },
      ],
    };
  }

  freeInlineCompletions(): void {
    // Cleanup if needed
  }
}
```

**Modify: `web/src/components/PlanEditor/MonacoEditor.tsx`**
```typescript
// Add to handleEditorDidMount
const handleEditorDidMount = (editorInstance: editor.IStandaloneCodeEditor) => {
  editorRef.current = editorInstance;

  // ... existing code ...

  // Register inline completions provider
  const provider = monaco.languages.registerInlineCompletionsProvider('markdown',
    new GhostTextProvider()
  );

  // Store disposable for cleanup
  disposablesRef.current.push(provider);
};
```

---

### Step 5: Keyboard Shortcuts for Completions

**Modify: `web/src/hooks/useKeyboardShortcuts.ts`**
```typescript
// Add to keyboard handler
if (e.key === 'Tab' || e.key === 'ArrowRight') {
  const hasCompletion = useCompletionStore.getState().currentCompletion !== null;

  if (hasCompletion && isMonacoEditor) {
    e.preventDefault();
    useCompletionStore.getState().acceptCompletion();
    return;
  }
}

if (e.key === 'Escape') {
  const hasCompletion = useCompletionStore.getState().currentCompletion !== null;

  if (hasCompletion && isMonacoEditor) {
    e.preventDefault();
    useCompletionStore.getState().rejectCompletion();
    return;
  }

  // ... existing escape handling ...
}
```

---

### Step 6: Integrate with App

**Modify: `web/src/App.tsx`**
```typescript
function App() {
  // ... existing code ...

  // Generate user ID (or get from auth)
  const userId = useMemo(() => {
    return localStorage.getItem('parallax_user_id') ||
           (() => {
             const id = `user-${Date.now()}`;
             localStorage.setItem('parallax_user_id', id);
             return id;
           })();
  }, []);

  // Enable backend integration
  const { charCount, isProcessing } = useFulfillment(userId);

  // ... rest of app ...
}
```

---

## 4. Environment Configuration

**File: `web/.env.example`**
```bash
# Backend API URL
VITE_BACKEND_URL=http://localhost:8000

# Fulfillment settings (optional, has defaults)
VITE_CHAR_THRESHOLD=20
VITE_IDLE_TIMEOUT=4000
VITE_POLL_INTERVAL=3000
```

**File: `web/.env.development`**
```bash
VITE_BACKEND_URL=http://localhost:8000
```

---

## 5. Testing Plan

### Unit Tests
- ✅ Test `useFulfillment` hook debouncing logic
- ✅ Test `backendService` API calls
- ✅ Test `completionStore` accept/reject logic
- ✅ Test character counting threshold

### Integration Tests
- ✅ Test full flow: type → debounce → API call → display
- ✅ Test polling mechanism starts and stops correctly
- ✅ Test ghost text appears and can be accepted/rejected
- ✅ Test feed cards appear in sidebar

### Manual Testing Checklist
```
[ ] Start backend: uv run python -m parallizer.backend_handler
[ ] Start frontend: npm run dev
[ ] Type 20+ characters in editor
[ ] Wait 4 seconds (idle timeout)
[ ] Verify network request to /fulfill
[ ] Verify polling requests to /cached every 3 seconds
[ ] Verify ghost text appears in editor (if COMPLETION card)
[ ] Press Tab/Right → completion accepted
[ ] Type again, wait for new completion
[ ] Press Esc → completion dismissed
[ ] Verify QUESTION/CONTEXT cards in sidebar
```

---

## 6. Rollout Strategy

### Phase 1: Foundation (Backend Off by Default)
- Add configuration with feature flag
- Implement API service
- Add `useFulfillment` hook
- Can be enabled with env var: `VITE_ENABLE_BACKEND=true`

### Phase 2: Ghost Text
- Implement Monaco inline completions
- Add keyboard handlers
- Test acceptance/rejection

### Phase 3: Polling & Feed
- Implement polling mechanism
- Connect to feed store
- Display cards in sidebar

### Phase 4: Production Ready
- Add error handling & retry logic
- Add loading indicators
- Add user preferences (enable/disable AI)
- Enable by default

---

## 7. Open Questions

1. **User Authentication**:
   - How should we generate/manage user IDs?
   - Options: localStorage, session ID, auth system?

2. **Ghost Text Styling**:
   - Monaco uses default gray for inline suggestions
   - Can we customize to match CLI's "bold magenta"?
   - May need CSS overrides

3. **Offline Mode**:
   - Should editor work without backend?
   - Fall back to mock data if backend unavailable?

4. **Performance**:
   - Should we cancel in-flight requests if user keeps typing?
   - How to handle rapid polling (rate limiting)?

5. **Configuration UI**:
   - Should users be able to adjust thresholds?
   - Settings panel for char count, idle timeout, etc.?

---

## 8. Success Criteria

- ✅ Editor sends requests to backend after 20 chars + 4 sec idle
- ✅ Backend responses appear as ghost text (completions) or sidebar cards
- ✅ Ghost text can be accepted with Tab/Right
- ✅ Ghost text can be dismissed with Esc
- ✅ Polling continues until all fulfillers complete
- ✅ No performance degradation (no UI blocking)
- ✅ Graceful error handling (network failures, timeouts)
- ✅ Works with existing features (command palette, vim mode, etc.)

---

## 9. Timeline Estimate

| Phase | Tasks | Estimate |
|-------|-------|----------|
| Config & API | Setup, backendService.ts | 2 hours |
| Debouncing | useFulfillment hook | 3 hours |
| Polling | usePolling hook | 2 hours |
| Ghost Text | Monaco inline completions | 4 hours |
| Keyboard | Accept/reject handlers | 2 hours |
| Feed Updates | Connect to stores | 2 hours |
| Testing | Unit + integration tests | 4 hours |
| Polish | Error handling, UX | 3 hours |
| **Total** | | **22 hours (~3 days)** |

---

## 10. Dependencies

- Backend must be running: `uv run python -m parallizer.backend_handler`
- Backend endpoints: `/fulfill`, `/user/{id}/cached`, `/user/{id}/feed`
- Environment variables configured
- Monaco Editor (already installed)
- Zustand stores (already implemented)

---

## Next Steps

1. **Review this plan** - Approve or request changes
2. **Create feature branch** - `git checkout -b feat/backend-integration`
3. **Implement in order** - Step 1 → 2 → 3 → 4 → 5 → 6
4. **Test incrementally** - Test each step before moving to next
5. **Commit frequently** - Clear commit messages
6. **Create PR** - When complete and tested

---

Ready to proceed? Please review and let me know if you'd like any changes to the plan!
