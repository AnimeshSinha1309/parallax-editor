import { create } from 'zustand';

export type PaneType = 'files' | 'editor' | 'feed';

interface UIStore {
  // Focus management
  activePane: PaneType;
  focusPane: (pane: PaneType) => void;

  // Panel visibility
  leftPanelVisible: boolean;
  rightPanelVisible: boolean;
  toggleLeftPanel: () => void;
  toggleRightPanel: () => void;

  // Command systems
  commandPaletteOpen: boolean;
  vimCommandMode: boolean;
  vimCommand: string;
  openCommandPalette: () => void;
  closeCommandPalette: () => void;
  enterVimCommandMode: () => void;
  exitVimCommandMode: () => void;
  setVimCommand: (command: string) => void;

  // Theme
  theme: 'dark' | 'light';
  toggleTheme: () => void;
}

export const useUIStore = create<UIStore>((set) => ({
  // Focus management
  activePane: 'editor',
  focusPane: (pane: PaneType) => set({ activePane: pane }),

  // Panel visibility
  leftPanelVisible: true,
  rightPanelVisible: true,
  toggleLeftPanel: () =>
    set((state) => ({ leftPanelVisible: !state.leftPanelVisible })),
  toggleRightPanel: () =>
    set((state) => ({ rightPanelVisible: !state.rightPanelVisible })),

  // Command systems
  commandPaletteOpen: false,
  vimCommandMode: false,
  vimCommand: '',
  openCommandPalette: () =>
    set({ commandPaletteOpen: true, vimCommandMode: false }),
  closeCommandPalette: () => set({ commandPaletteOpen: false }),
  enterVimCommandMode: () =>
    set({ vimCommandMode: true, commandPaletteOpen: false, vimCommand: '' }),
  exitVimCommandMode: () => set({ vimCommandMode: false, vimCommand: '' }),
  setVimCommand: (command: string) => set({ vimCommand: command }),

  // Theme
  theme: 'light',
  toggleTheme: () =>
    set((state) => ({ theme: state.theme === 'dark' ? 'light' : 'dark' })),
}));
