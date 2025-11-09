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
      <div className="px-3 py-2 border-b border-vscode-border">
        <h2 className="text-xs font-medium text-vscode-text-secondary">
          Explorer
        </h2>
      </div>

      {/* File Tree */}
      <div className="flex-1 overflow-auto px-2 py-2">
        {rootNode ? (
          <FileTree node={rootNode} level={0} />
        ) : (
          <div className="text-vscode-text-secondary text-xs px-2 py-4">
            No files to display
          </div>
        )}
      </div>
    </div>
  );
}
