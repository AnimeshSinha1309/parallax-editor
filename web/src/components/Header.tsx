import { FileCode2, Moon, Sun } from 'lucide-react';
import { useUIStore } from '../stores/uiStore';

export function Header() {
  const { theme, toggleTheme } = useUIStore();

  return (
    <div className="h-full flex items-center justify-between px-4 bg-vscode-bg-secondary">
      <div className="flex items-center gap-3">
        <FileCode2 size={20} className="text-vscode-accent-blue" />
        <span className="text-sm font-semibold text-vscode-text-primary">
          Parallax Editor
        </span>
      </div>

      <div className="flex items-center gap-2">
        <button
          onClick={toggleTheme}
          className="p-2 rounded hover:bg-vscode-bg-tertiary transition-colors text-vscode-text-primary"
          aria-label="Toggle theme"
        >
          {theme === 'dark' ? <Sun size={16} /> : <Moon size={16} />}
        </button>
      </div>
    </div>
  );
}
