import { useState, useEffect, useRef } from 'react';
import { useUIStore } from '../../stores/uiStore';
import { useFeedStore } from '../../stores/feedStore';
import { Command } from '../../types/models';
import { Search, File, Folder, Settings, Save, X } from 'lucide-react';
import clsx from 'clsx';

// Define available commands
const useCommands = (): Command[] => {
  const { focusPane, toggleLeftPanel, toggleRightPanel, closeCommandPalette } = useUIStore();
  const { clearCards } = useFeedStore();

  return [
    {
      id: 'focus-files',
      label: 'Focus: File Explorer',
      category: 'Navigation',
      shortcut: 'Ctrl+1',
      icon: 'Folder',
      action: () => {
        focusPane('files');
        closeCommandPalette();
      },
    },
    {
      id: 'focus-editor',
      label: 'Focus: Editor',
      category: 'Navigation',
      shortcut: 'Ctrl+2',
      icon: 'File',
      action: () => {
        focusPane('editor');
        closeCommandPalette();
      },
    },
    {
      id: 'focus-feed',
      label: 'Focus: AI Feed',
      category: 'Navigation',
      shortcut: 'Ctrl+3',
      icon: 'Settings',
      action: () => {
        focusPane('feed');
        closeCommandPalette();
      },
    },
    {
      id: 'toggle-sidebar',
      label: 'Toggle Sidebar',
      category: 'View',
      shortcut: 'Ctrl+B',
      icon: 'Folder',
      action: () => {
        toggleLeftPanel();
        closeCommandPalette();
      },
    },
    {
      id: 'toggle-ai-feed',
      label: 'Toggle AI Feed',
      category: 'View',
      shortcut: 'Ctrl+Alt+F',
      icon: 'Settings',
      action: () => {
        toggleRightPanel();
        closeCommandPalette();
      },
    },
    {
      id: 'clear-feed',
      label: 'Clear AI Feed',
      category: 'AI',
      icon: 'X',
      action: () => {
        clearCards();
        closeCommandPalette();
      },
    },
  ];
};

export function CommandPalette() {
  const { commandPaletteOpen, closeCommandPalette } = useUIStore();
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedIndex, setSelectedIndex] = useState(0);
  const inputRef = useRef<HTMLInputElement>(null);
  const commands = useCommands();

  // Filter commands based on search query
  const filteredCommands = commands.filter((cmd) =>
    cmd.label.toLowerCase().includes(searchQuery.toLowerCase())
  );

  useEffect(() => {
    if (commandPaletteOpen) {
      setSearchQuery('');
      setSelectedIndex(0);
      inputRef.current?.focus();
    }
  }, [commandPaletteOpen]);

  useEffect(() => {
    setSelectedIndex(0);
  }, [searchQuery]);

  const handleKeyDown = (e: React.KeyboardEvent) => {
    switch (e.key) {
      case 'Escape':
        e.preventDefault();
        closeCommandPalette();
        break;
      case 'ArrowDown':
        e.preventDefault();
        setSelectedIndex((prev) =>
          prev < filteredCommands.length - 1 ? prev + 1 : prev
        );
        break;
      case 'ArrowUp':
        e.preventDefault();
        setSelectedIndex((prev) => (prev > 0 ? prev - 1 : prev));
        break;
      case 'Enter':
        e.preventDefault();
        if (filteredCommands[selectedIndex]) {
          filteredCommands[selectedIndex].action();
        }
        break;
    }
  };

  if (!commandPaletteOpen) return null;

  return (
    <div
      className="fixed inset-0 bg-black bg-opacity-50 flex items-start justify-center pt-24 z-50"
      onClick={closeCommandPalette}
    >
      <div
        className="bg-vscode-bg-secondary border border-vscode-border rounded-lg shadow-2xl w-full max-w-2xl slide-down"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Search Input */}
        <div className="flex items-center gap-3 px-4 py-3 border-b border-vscode-border">
          <Search size={18} className="text-vscode-text-secondary" />
          <input
            ref={inputRef}
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Type a command or search..."
            className="flex-1 bg-transparent text-vscode-text-primary placeholder-vscode-text-secondary outline-none text-sm"
          />
        </div>

        {/* Command List */}
        <div className="max-h-96 overflow-y-auto">
          {filteredCommands.length === 0 ? (
            <div className="px-4 py-8 text-center text-vscode-text-secondary text-sm">
              No commands found
            </div>
          ) : (
            filteredCommands.map((cmd, index) => (
              <button
                key={cmd.id}
                onClick={() => cmd.action()}
                className={clsx(
                  'w-full flex items-center gap-3 px-4 py-3 text-left transition-colors',
                  index === selectedIndex
                    ? 'bg-vscode-accent-blue text-white'
                    : 'hover:bg-vscode-bg-tertiary text-vscode-text-primary'
                )}
              >
                <span className="text-sm flex-1">{cmd.label}</span>
                {cmd.shortcut && (
                  <span
                    className={clsx(
                      'text-xs px-2 py-1 rounded',
                      index === selectedIndex
                        ? 'bg-white bg-opacity-20'
                        : 'bg-vscode-bg-primary'
                    )}
                  >
                    {cmd.shortcut}
                  </span>
                )}
              </button>
            ))
          )}
        </div>

        {/* Footer */}
        <div className="px-4 py-2 border-t border-vscode-border text-xs text-vscode-text-secondary flex items-center justify-between">
          <span>↑↓ to navigate</span>
          <span>↵ to select</span>
          <span>Esc to close</span>
        </div>
      </div>
    </div>
  );
}
