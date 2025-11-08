import { useEffect } from 'react';
import { useUIStore } from '../stores/uiStore';
import { useCompletionStore } from '../stores/completionStore';

export function useKeyboardShortcuts() {
  const {
    openCommandPalette,
    enterVimCommandMode,
    exitVimCommandMode,
    vimCommandMode,
    focusPane,
    toggleLeftPanel,
    toggleRightPanel,
  } = useUIStore();

  const { currentCompletion, acceptCompletion, rejectCompletion } = useCompletionStore();

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Ignore shortcuts when typing in inputs (except our vim command bar)
      const target = e.target as HTMLElement;
      const isInput = target.tagName === 'INPUT' || target.tagName === 'TEXTAREA';
      const isMonacoEditor = target.closest('.monaco-editor') !== null;

      // Completion shortcuts - HIGHEST PRIORITY (when completion is active in Monaco)
      if (currentCompletion && isMonacoEditor) {
        // Accept completion with Tab or Right Arrow
        if (e.key === 'Tab' || e.key === 'ArrowRight') {
          // Only accept on Right Arrow if at end of line
          if (e.key === 'ArrowRight') {
            const selection = window.getSelection();
            const range = selection?.getRangeAt(0);
            // Let Monaco handle if not at end - this is a simple check
            // Monaco will handle the actual inline suggestion acceptance
          }

          if (e.key === 'Tab') {
            e.preventDefault();
            acceptCompletion();
            return;
          }
        }

        // Reject completion with Escape
        if (e.key === 'Escape') {
          e.preventDefault();
          rejectCompletion();
          return;
        }
      }

      // Vim command mode activation (only when not in an input)
      if (e.key === ':' && !isInput && !vimCommandMode && !isMonacoEditor) {
        e.preventDefault();
        enterVimCommandMode();
        return;
      }

      // Escape key - exit vim command mode (if not handling completion)
      if (e.key === 'Escape' && vimCommandMode && !currentCompletion) {
        e.preventDefault();
        exitVimCommandMode();
        return;
      }

      // Command Palette (Ctrl+P or Cmd+P)
      if ((e.ctrlKey || e.metaKey) && e.key === 'p') {
        e.preventDefault();
        openCommandPalette();
        return;
      }

      // Focus shortcuts (Ctrl+1, 2, 3)
      if ((e.ctrlKey || e.metaKey) && !e.shiftKey && !e.altKey) {
        switch (e.key) {
          case '1':
            e.preventDefault();
            focusPane('files');
            break;
          case '2':
            e.preventDefault();
            focusPane('editor');
            break;
          case '3':
            e.preventDefault();
            focusPane('feed');
            break;
        }
      }

      // Toggle panels
      if ((e.ctrlKey || e.metaKey) && e.key === 'b') {
        e.preventDefault();
        toggleLeftPanel();
      }

      // Toggle AI feed (Ctrl+Alt+F)
      if ((e.ctrlKey || e.metaKey) && e.altKey && e.key === 'f') {
        e.preventDefault();
        toggleRightPanel();
      }

      // Save (Ctrl+S) - prevent default browser save
      if ((e.ctrlKey || e.metaKey) && e.key === 's') {
        e.preventDefault();
        // TODO: Implement save functionality
        console.log('Save triggered');
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [
    openCommandPalette,
    enterVimCommandMode,
    exitVimCommandMode,
    vimCommandMode,
    focusPane,
    toggleLeftPanel,
    toggleRightPanel,
    currentCompletion,
    acceptCompletion,
    rejectCompletion,
  ]);
}
