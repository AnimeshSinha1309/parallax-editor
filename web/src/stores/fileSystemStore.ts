import { create } from 'zustand';
import type { FileNode } from '../types/models';

interface FileSystemStore {
  // File tree
  rootNode: FileNode | null;
  expandedPaths: Set<string>;
  selectedPath: string | null;

  // Context
  scopeRoot: string;
  planPath: string | null;

  // Actions
  setRootNode: (node: FileNode) => void;
  toggleExpanded: (path: string) => void;
  selectFile: (path: string) => void;
  setScopeRoot: (path: string) => void;
  setPlanPath: (path: string | null) => void;
}

// Mock file tree data for development
const mockFileTree: FileNode = {
  name: 'project',
  path: '/project',
  type: 'directory',
  children: [
    {
      name: 'src',
      path: '/project/src',
      type: 'directory',
      children: [
        { name: 'main.py', path: '/project/src/main.py', type: 'file' },
        { name: 'utils.py', path: '/project/src/utils.py', type: 'file' },
      ],
    },
    {
      name: 'docs',
      path: '/project/docs',
      type: 'directory',
      children: [
        { name: 'README.md', path: '/project/docs/README.md', type: 'file' },
        { name: 'API.md', path: '/project/docs/API.md', type: 'file' },
      ],
    },
    { name: 'PLAN.md', path: '/project/PLAN.md', type: 'file' },
    { name: 'package.json', path: '/project/package.json', type: 'file' },
  ],
};

export const useFileSystemStore = create<FileSystemStore>((set) => ({
  rootNode: mockFileTree,
  expandedPaths: new Set(['/project', '/project/src']),
  selectedPath: '/project/PLAN.md',
  scopeRoot: '/project',
  planPath: '/project/PLAN.md',

  setRootNode: (node: FileNode) =>
    set({ rootNode: node }),

  toggleExpanded: (path: string) =>
    set((state) => {
      const newExpanded = new Set(state.expandedPaths);
      if (newExpanded.has(path)) {
        newExpanded.delete(path);
      } else {
        newExpanded.add(path);
      }
      return { expandedPaths: newExpanded };
    }),

  selectFile: (path: string) =>
    set({ selectedPath: path }),

  setScopeRoot: (path: string) =>
    set({ scopeRoot: path }),

  setPlanPath: (path: string | null) =>
    set({ planPath: path }),
}));
