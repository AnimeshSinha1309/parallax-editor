import { describe, it, expect, beforeEach } from 'vitest';
import { useCompletionStore } from '../completionStore';
import { useEditorStore } from '../editorStore';
import { CardType } from '../../types/models';

describe('CompletionStore', () => {
  beforeEach(() => {
    // Reset stores
    useCompletionStore.setState({
      currentCompletion: null,
      completionMetadata: null,
    });

    useEditorStore.getState().reset();
  });

  describe('setCompletion', () => {
    it('should set completion from card', () => {
      const card = {
        header: 'Completion',
        text: 'suggested text',
        type: CardType.COMPLETION,
        metadata: { confidence: 0.9 },
      };

      useCompletionStore.getState().setCompletion(card);

      const state = useCompletionStore.getState();
      expect(state.currentCompletion).toBe('suggested text');
      expect(state.completionMetadata).toEqual({ confidence: 0.9 });
    });

    it('should handle card without metadata', () => {
      const card = {
        header: 'Completion',
        text: 'suggested text',
        type: CardType.COMPLETION,
      };

      useCompletionStore.getState().setCompletion(card);

      const state = useCompletionStore.getState();
      expect(state.currentCompletion).toBe('suggested text');
      expect(state.completionMetadata).toEqual({});
    });
  });

  describe('clearCompletion', () => {
    it('should clear completion', () => {
      // Set a completion first
      const card = {
        header: 'Completion',
        text: 'suggested text',
        type: CardType.COMPLETION,
      };
      useCompletionStore.getState().setCompletion(card);

      // Clear it
      useCompletionStore.getState().clearCompletion();

      const state = useCompletionStore.getState();
      expect(state.currentCompletion).toBeNull();
      expect(state.completionMetadata).toBeNull();
    });
  });

  describe('acceptCompletion', () => {
    it('should insert completion at cursor position', () => {
      // Set up editor state
      useEditorStore.getState().setContent('Hello world');
      useEditorStore.getState().setCursorPosition([0, 6]); // After "Hello "

      // Set a completion
      const card = {
        header: 'Completion',
        text: 'beautiful ',
        type: CardType.COMPLETION,
      };
      useCompletionStore.getState().setCompletion(card);

      // Accept completion
      useCompletionStore.getState().acceptCompletion();

      // Check editor state
      const editorState = useEditorStore.getState();
      expect(editorState.content).toBe('Hello beautiful world');
      expect(editorState.cursorPosition).toEqual([0, 16]); // After "Hello beautiful "

      // Check completion cleared
      const completionState = useCompletionStore.getState();
      expect(completionState.currentCompletion).toBeNull();
    });

    it('should handle multiline documents', () => {
      // Set up multiline content
      useEditorStore.getState().setContent('Line 1\nLine 2\nLine 3');
      useEditorStore.getState().setCursorPosition([1, 5]); // End of "Line "

      // Set a completion
      const card = {
        header: 'Completion',
        text: 'Two',
        type: CardType.COMPLETION,
      };
      useCompletionStore.getState().setCompletion(card);

      // Accept completion
      useCompletionStore.getState().acceptCompletion();

      // Check result
      const editorState = useEditorStore.getState();
      expect(editorState.content).toBe('Line 1\nLine Two2\nLine 3');
      expect(editorState.cursorPosition).toEqual([1, 8]); // After "Line Two"
    });

    it('should do nothing if no completion', () => {
      useEditorStore.getState().setContent('Hello');
      useEditorStore.getState().setCursorPosition([0, 5]);

      // Accept with no completion set
      useCompletionStore.getState().acceptCompletion();

      // Content unchanged
      expect(useEditorStore.getState().content).toBe('Hello');
    });
  });

  describe('rejectCompletion', () => {
    it('should clear completion without modifying editor', () => {
      // Set up editor and completion
      useEditorStore.getState().setContent('Hello');
      useEditorStore.getState().setCursorPosition([0, 5]);

      const card = {
        header: 'Completion',
        text: ' world',
        type: CardType.COMPLETION,
      };
      useCompletionStore.getState().setCompletion(card);

      // Reject completion
      useCompletionStore.getState().rejectCompletion();

      // Editor unchanged
      expect(useEditorStore.getState().content).toBe('Hello');
      expect(useEditorStore.getState().cursorPosition).toEqual([0, 5]);

      // Completion cleared
      expect(useCompletionStore.getState().currentCompletion).toBeNull();
    });
  });
});
