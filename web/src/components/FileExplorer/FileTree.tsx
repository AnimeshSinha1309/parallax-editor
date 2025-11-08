import { ChevronRight, ChevronDown, File, Folder } from 'lucide-react';
import { useFileSystemStore } from '../../stores/fileSystemStore';
import { useFileSystem } from '../../hooks/useFileSystem';
import { config } from '../../utils/config';
import type { FileNode } from '../../types/models';
import clsx from 'clsx';

interface FileTreeProps {
  node: FileNode;
  level: number;
}

export function FileTree({ node, level }: FileTreeProps) {
  const {
    expandedPaths,
    selectedPath,
    toggleExpanded,
    selectFile,
  } = useFileSystemStore();

  const { loadFile } = useFileSystem({
    enabled: config.enableBackend,
  });

  const isExpanded = expandedPaths.has(node.path);
  const isSelected = selectedPath === node.path;
  const isDirectory = node.type === 'directory';

  const handleClick = (e: React.MouseEvent) => {
    e.stopPropagation();

    if (isDirectory) {
      toggleExpanded(node.path);
    } else {
      selectFile(node.path);
      // Load file content into editor
      if (config.enableBackend) {
        loadFile(node.path);
      }
    }
  };

  return (
    <div>
      {/* Node Item */}
      <div
        className={clsx(
          'flex items-center gap-1 px-2 py-1 cursor-pointer hover:bg-vscode-bg-tertiary rounded text-sm transition-all',
          isSelected && 'bg-vscode-accent-blue text-white'
        )}
        style={{ paddingLeft: `${level * 12 + 8}px` }}
        onClick={handleClick}
      >
        {/* Chevron for directories */}
        {isDirectory && (
          <span className="flex-shrink-0">
            {isExpanded ? (
              <ChevronDown size={16} />
            ) : (
              <ChevronRight size={16} />
            )}
          </span>
        )}

        {/* Icon */}
        <span className="flex-shrink-0">
          {isDirectory ? (
            <Folder size={16} className="text-vscode-accent-blue" />
          ) : (
            <File size={16} className="text-vscode-text-secondary" />
          )}
        </span>

        {/* Name */}
        <span className="truncate">{node.name}</span>
      </div>

      {/* Children (if directory and expanded) */}
      {isDirectory && isExpanded && node.children && (
        <div>
          {node.children.map((child) => (
            <FileTree key={child.path} node={child} level={level + 1} />
          ))}
        </div>
      )}
    </div>
  );
}
