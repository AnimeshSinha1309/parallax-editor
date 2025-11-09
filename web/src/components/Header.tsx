import { FileCode2, Moon, Sun } from 'lucide-react';
import { useUIStore } from '../stores/uiStore';

export function Header() {
  const { theme, toggleTheme } = useUIStore();

  return (
    <div className="h-full flex items-center justify-between px-3 bg-vscode-bg-primary">
      <div className="flex items-center gap-2">
        <FileCode2 size={16} className="text-vscode-accent-green" />
        <span className="text-base font-light text-vscode-text-primary tracking-tight">
          parallax.
        </span>
      </div>

      <button
        onClick={toggleTheme}
        className="p-1.5 hover:bg-vscode-bg-tertiary transition-colors text-vscode-text-secondary hover:text-vscode-text-primary"
        aria-label="Toggle theme"
      >
        {theme === 'dark' ? <Sun size={14} /> : <Moon size={14} />}
      </button>
    </div>
  );
}
