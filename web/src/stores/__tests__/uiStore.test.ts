import { describe, it, expect, beforeEach } from 'vitest';
import { useUIStore } from '../uiStore';

describe('UIStore', () => {
  beforeEach(() => {
    // Reset to initial state
    useUIStore.setState({
      activePane: 'editor',
      leftPanelVisible: true,
      rightPanelVisible: true,
      commandPaletteOpen: false,
      vimCommandMode: false,
      vimCommand: '',
      theme: 'dark',
    });
  });

  describe('Focus management', () => {
    it('should change active pane', () => {
      const { focusPane } = useUIStore.getState();

      focusPane('files');
      expect(useUIStore.getState().activePane).toBe('files');

      focusPane('feed');
      expect(useUIStore.getState().activePane).toBe('feed');
    });
  });

  describe('Panel visibility', () => {
    it('should toggle left panel', () => {
      const { toggleLeftPanel } = useUIStore.getState();

      expect(useUIStore.getState().leftPanelVisible).toBe(true);

      toggleLeftPanel();
      expect(useUIStore.getState().leftPanelVisible).toBe(false);

      toggleLeftPanel();
      expect(useUIStore.getState().leftPanelVisible).toBe(true);
    });

    it('should toggle right panel', () => {
      const { toggleRightPanel } = useUIStore.getState();

      expect(useUIStore.getState().rightPanelVisible).toBe(true);

      toggleRightPanel();
      expect(useUIStore.getState().rightPanelVisible).toBe(false);

      toggleRightPanel();
      expect(useUIStore.getState().rightPanelVisible).toBe(true);
    });
  });

  describe('Command palette', () => {
    it('should open and close command palette', () => {
      const { openCommandPalette, closeCommandPalette } = useUIStore.getState();

      openCommandPalette();
      expect(useUIStore.getState().commandPaletteOpen).toBe(true);

      closeCommandPalette();
      expect(useUIStore.getState().commandPaletteOpen).toBe(false);
    });

    it('should close vim command mode when opening command palette', () => {
      const { enterVimCommandMode, openCommandPalette } = useUIStore.getState();

      enterVimCommandMode();
      expect(useUIStore.getState().vimCommandMode).toBe(true);

      openCommandPalette();
      expect(useUIStore.getState().vimCommandMode).toBe(false);
      expect(useUIStore.getState().commandPaletteOpen).toBe(true);
    });
  });

  describe('Vim command mode', () => {
    it('should enter and exit vim command mode', () => {
      const { enterVimCommandMode, exitVimCommandMode } = useUIStore.getState();

      enterVimCommandMode();
      expect(useUIStore.getState().vimCommandMode).toBe(true);
      expect(useUIStore.getState().vimCommand).toBe('');

      exitVimCommandMode();
      expect(useUIStore.getState().vimCommandMode).toBe(false);
    });

    it('should set vim command', () => {
      const { enterVimCommandMode, setVimCommand } = useUIStore.getState();

      enterVimCommandMode();
      setVimCommand('files');

      expect(useUIStore.getState().vimCommand).toBe('files');
    });

    it('should close command palette when entering vim mode', () => {
      const { openCommandPalette, enterVimCommandMode } = useUIStore.getState();

      openCommandPalette();
      expect(useUIStore.getState().commandPaletteOpen).toBe(true);

      enterVimCommandMode();
      expect(useUIStore.getState().commandPaletteOpen).toBe(false);
      expect(useUIStore.getState().vimCommandMode).toBe(true);
    });
  });

  describe('Theme', () => {
    it('should toggle theme', () => {
      const { toggleTheme } = useUIStore.getState();

      expect(useUIStore.getState().theme).toBe('dark');

      toggleTheme();
      expect(useUIStore.getState().theme).toBe('light');

      toggleTheme();
      expect(useUIStore.getState().theme).toBe('dark');
    });
  });
});
