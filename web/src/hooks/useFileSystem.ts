/**
 * File system operations hook for loading/saving files
 */

import { useEffect, useState, useCallback } from 'react';
import { backendService } from '../services/backendService';
import { useFileSystemStore } from '../stores/fileSystemStore';
import { useEditorStore } from '../stores/editorStore';
import type { FileNode } from '../types/models';

interface UseFileSystemOptions {
  enabled?: boolean;
}

interface UseFileSystemReturn {
  loading: boolean;
  error: string | null;
  loadFileTree: (scopeRoot: string) => Promise<void>;
  loadFile: (path: string) => Promise<void>;
  saveFile: (path: string, content: string) => Promise<void>;
}

export function useFileSystem(options: UseFileSystemOptions = {}): UseFileSystemReturn {
  const { enabled = true } = options;
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const { scopeRoot, setRootNode } = useFileSystemStore();
  const { setContent, setFilePath, setLanguage } = useEditorStore();

  /**
   * Load file tree from backend
   */
  const loadFileTree = useCallback(async (scope: string) => {
    if (!enabled) return;

    setLoading(true);
    setError(null);

    try {
      console.log(`Loading file tree for scope: ${scope}`);
      const tree = await backendService.getFileTree(scope, 10);
      setRootNode(tree);
      console.log(`File tree loaded successfully`);
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : 'Unknown error loading file tree';
      setError(errorMsg);
      console.error('Error loading file tree:', errorMsg);
    } finally {
      setLoading(false);
    }
  }, [enabled, setRootNode]);

  /**
   * Load file content from backend
   */
  const loadFile = useCallback(async (path: string) => {
    if (!enabled) return;

    setLoading(true);
    setError(null);

    try {
      console.log(`Loading file: ${path}`);
      const result = await backendService.getFileContent(path, scopeRoot);

      setContent(result.content);
      setFilePath(path);
      setLanguage(result.language);

      console.log(`File loaded: ${path} (${result.language}, ${result.content.length} chars)`);
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : 'Unknown error loading file';
      setError(errorMsg);
      console.error('Error loading file:', errorMsg);

      // Show error in editor
      setContent(`# Error Loading File\n\nFailed to load ${path}:\n${errorMsg}`);
      setFilePath(path);
      setLanguage('markdown');
    } finally {
      setLoading(false);
    }
  }, [enabled, scopeRoot, setContent, setFilePath, setLanguage]);

  /**
   * Save file content to backend
   */
  const saveFile = useCallback(async (path: string, content: string) => {
    if (!enabled) return;

    setLoading(true);
    setError(null);

    try {
      console.log(`Saving file: ${path} (${content.length} bytes)`);
      const result = await backendService.saveFile(path, content, scopeRoot);
      console.log(`File saved successfully: ${result.message}`);
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : 'Unknown error saving file';
      setError(errorMsg);
      console.error('Error saving file:', errorMsg);
      throw err; // Re-throw so caller can handle
    } finally {
      setLoading(false);
    }
  }, [enabled, scopeRoot]);

  return {
    loading,
    error,
    loadFileTree,
    loadFile,
    saveFile,
  };
}
