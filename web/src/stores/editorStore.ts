import { create } from 'zustand';
import type { EditorState } from '../types/models';

interface EditorStore extends EditorState {
  // Actions
  setContent: (content: string) => void;
  setCursorPosition: (position: [number, number]) => void;
  setFilePath: (path: string) => void;
  setLanguage: (language: string) => void;
  reset: () => void;
}

const initialState: EditorState = {
  content: '',
  cursorPosition: [0, 0],
  language: 'markdown',
  filePath: undefined,
};

export const useEditorStore = create<EditorStore>((set) => ({
  ...initialState,

  setContent: (content: string) =>
    set({ content }),

  setCursorPosition: (position: [number, number]) =>
    set({ cursorPosition: position }),

  setFilePath: (path: string) =>
    set({ filePath: path }),

  setLanguage: (language: string) =>
    set({ language }),

  reset: () =>
    set(initialState),
}));
