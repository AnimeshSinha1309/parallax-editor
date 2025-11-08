import { useEffect, useRef } from 'react';
import { useUIStore } from '../../stores/uiStore';
import { useFeedStore } from '../../stores/feedStore';
import { useEditorStore } from '../../stores/editorStore';

export function VimCommandBar() {
  const {
    vimCommandMode,
    vimCommand,
    setVimCommand,
    exitVimCommandMode,
    focusPane,
  } = useUIStore();
  const { clearCards } = useFeedStore();
  const { content, setContent } = useEditorStore();
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (vimCommandMode) {
      inputRef.current?.focus();
    }
  }, [vimCommandMode]);

  const executeCommand = (cmd: string) => {
    const parts = cmd.trim().split(/\s+/);
    const command = parts[0].toLowerCase();
    const args = parts.slice(1);

    switch (command) {
      // Navigation commands
      case 'files':
        focusPane('files');
        break;
      case 'editor':
      case 'edit':
      case 'e':
        focusPane('editor');
        // TODO: If args[0] is provided, open that file
        break;
      case 'feed':
        focusPane('feed');
        break;

      // File operations
      case 'w':
      case 'write':
        // TODO: Save file
        console.log('Save file');
        break;
      case 'q':
      case 'quit':
        // TODO: Close/quit
        console.log('Quit');
        break;
      case 'wq':
      case 'x':
        // TODO: Save and close
        console.log('Save and quit');
        break;

      // AI feed operations
      case 'clear':
        clearCards();
        break;

      // Editor operations (basic examples)
      case 'dd':
        // Delete current line
        // This would need cursor position info
        console.log('Delete line');
        break;

      default:
        console.log('Unknown command:', command);
    }

    exitVimCommandMode();
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      executeCommand(vimCommand);
    } else if (e.key === 'Escape') {
      e.preventDefault();
      exitVimCommandMode();
    }
  };

  if (!vimCommandMode) {
    return (
      <div className="h-full flex items-center px-4 text-xs text-vscode-text-secondary">
        <span>Press <kbd className="px-1 py-0.5 bg-vscode-bg-tertiary rounded">:</kbd> for Vim commands</span>
        <span className="mx-4">|</span>
        <span>Press <kbd className="px-1 py-0.5 bg-vscode-bg-tertiary rounded">Ctrl+P</kbd> for command palette</span>
      </div>
    );
  }

  return (
    <div className="h-full flex items-center px-2 bg-vscode-bg-secondary">
      <span className="text-vscode-accent-yellow font-bold mr-1">:</span>
      <input
        ref={inputRef}
        type="text"
        value={vimCommand}
        onChange={(e) => setVimCommand(e.target.value)}
        onKeyDown={handleKeyDown}
        className="flex-1 bg-transparent text-vscode-text-primary outline-none text-sm"
        placeholder="Enter command..."
      />
    </div>
  );
}
