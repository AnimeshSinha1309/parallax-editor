import { create } from 'zustand';
import type { Card } from '../types/models';
import { useEditorStore } from './editorStore';

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
      // Get editor state
      const { content, cursorPosition, setContent, setCursorPosition } =
        useEditorStore.getState();
      const [line, col] = cursorPosition;

      // Split content into lines
      const lines = content.split('\n');

      // Ensure line exists
      if (line < 0 || line >= lines.length) {
        console.error('Invalid cursor position');
        return;
      }

      // Insert completion at cursor position
      const currentLine = lines[line];
      const before = currentLine.slice(0, col);
      const after = currentLine.slice(col);
      lines[line] = before + currentCompletion + after;

      // Update editor content
      setContent(lines.join('\n'));

      // Move cursor to end of completion
      setCursorPosition([line, col + currentCompletion.length]);

      // Clear completion
      set({ currentCompletion: null, completionMetadata: null });
    }
  },

  rejectCompletion: () => {
    // Simply clear the completion
    set({ currentCompletion: null, completionMetadata: null });
  },
}));
