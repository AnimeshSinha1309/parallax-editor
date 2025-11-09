import { describe, it, expect, beforeEach } from 'vitest';
import { useEditorStore } from '../editorStore';

describe('EditorStore', () => {
  beforeEach(() => {
    // Reset store state before each test
    useEditorStore.getState().reset();
  });

  it('should initialize with empty content', () => {
    const { content, language, cursorPosition } = useEditorStore.getState();

    expect(content).toBe('');
    expect(language).toBe('markdown');
    expect(cursorPosition).toEqual([0, 0]);
  });

  it('should update content', () => {
    const { setContent } = useEditorStore.getState();

    setContent('New content');

    expect(useEditorStore.getState().content).toBe('New content');
  });

  it('should update cursor position', () => {
    const { setCursorPosition } = useEditorStore.getState();

    setCursorPosition([10, 5]);

    expect(useEditorStore.getState().cursorPosition).toEqual([10, 5]);
  });

  it('should update file path', () => {
    const { setFilePath } = useEditorStore.getState();

    setFilePath('/test/path.md');

    expect(useEditorStore.getState().filePath).toBe('/test/path.md');
  });

  it('should update language', () => {
    const { setLanguage } = useEditorStore.getState();

    setLanguage('javascript');

    expect(useEditorStore.getState().language).toBe('javascript');
  });

  it('should reset to initial state', () => {
    const { setContent, setCursorPosition, setFilePath, reset } = useEditorStore.getState();

    // Make some changes
    setContent('Modified');
    setCursorPosition([5, 10]);
    setFilePath('/test.md');

    // Reset
    reset();

    const state = useEditorStore.getState();
    expect(state.content).toBe('');
    expect(state.cursorPosition).toEqual([0, 0]);
    expect(state.filePath).toBeUndefined();
  });
});
