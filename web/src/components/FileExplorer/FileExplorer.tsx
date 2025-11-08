import { useFileSystemStore } from '../../stores/fileSystemStore';
import { useUIStore } from '../../stores/uiStore';
import { FileTree } from './FileTree';

export function FileExplorer() {
  const { rootNode, scopeRoot, planPath } = useFileSystemStore();
  const { focusPane } = useUIStore();

  const handleClick = () => {
    focusPane('files');
  };

  return (
    <div
      className="h-full flex flex-col overflow-hidden"
      onClick={handleClick}
    >
      {/* Header */}
      <div className="px-4 py-2 border-b border-vscode-border">
        <h2 className="text-sm font-semibold text-vscode-text-primary uppercase">
          Explorer
        </h2>
      </div>

      {/* Context Info */}
      <div className="px-4 py-2 text-xs text-vscode-text-secondary border-b border-vscode-border">
        <div className="mb-1">
          <span className="font-semibold">Scope:</span>{' '}
          <span className="font-mono">{scopeRoot}</span>
        </div>
        {planPath && (
          <div>
            <span className="font-semibold">Plan:</span>{' '}
            <span className="font-mono">{planPath}</span>
          </div>
        )}
      </div>

      {/* File Tree */}
      <div className="flex-1 overflow-auto px-2 py-2">
        {rootNode ? (
          <FileTree node={rootNode} level={0} />
        ) : (
          <div className="text-vscode-text-secondary text-sm p-4">
            No files to display
          </div>
        )}
      </div>
    </div>
  );
}
