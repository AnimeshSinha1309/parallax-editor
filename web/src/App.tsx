import { useEffect, useMemo } from 'react';
import { EditorLayout } from './layouts/EditorLayout';
import { FileExplorer } from './components/FileExplorer';
import { PlanEditor } from './components/PlanEditor';
import { AIFeed } from './components/AIFeed';
import { CommandPalette } from './components/CommandPalette';
import { VimCommandBar } from './components/VimCommandBar';
import { Header } from './components/Header';
import { useKeyboardShortcuts } from './hooks/useKeyboardShortcuts';
import { useFulfillment } from './hooks/useFulfillment';
import { useFileSystem } from './hooks/useFileSystem';
import { useUIStore } from './stores/uiStore';
import { useFeedStore } from './stores/feedStore';
import { useFileSystemStore } from './stores/fileSystemStore';
import { CardType } from './types/models';
import { config } from './utils/config';

function App() {
  // Generate or retrieve user ID
  const userId = useMemo(() => {
    const stored = localStorage.getItem('parallax_user_id');
    if (stored) return stored;

    const newId = `user-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
    localStorage.setItem('parallax_user_id', newId);
    return newId;
  }, []);

  // Set up keyboard shortcuts
  useKeyboardShortcuts();

  // Enable backend integration (if configured)
  const { charCount, isProcessing, error } = useFulfillment({
    userId,
    enabled: config.enableBackend,
  });

  // File system operations
  const { loadFileTree, loadFile } = useFileSystem({
    enabled: config.enableBackend,
  });

  const { theme } = useUIStore();
  const { addCards } = useFeedStore();
  const { setScopeRoot, setPlanPath } = useFileSystemStore();

  // Apply theme to document
  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
  }, [theme]);

  // Parse URL parameters and initialize file system
  useEffect(() => {
    if (!config.enableBackend) return;

    const urlParams = new URLSearchParams(window.location.search);
    const scopeParam = urlParams.get('scope');
    const planParam = urlParams.get('plan');

    // Set scope root
    if (scopeParam) {
      console.log(`Initializing with scope: ${scopeParam}`);
      setScopeRoot(scopeParam);

      // Load file tree
      loadFileTree(scopeParam);

      // Load plan file if specified
      if (planParam) {
        console.log(`Loading plan file: ${planParam}`);
        setPlanPath(planParam);
        loadFile(planParam);
      }
    } else {
      console.log('No scope parameter provided, using default scope');
    }
  }, [loadFileTree, loadFile, setScopeRoot, setPlanPath]);

  // Add some demo cards on mount (only if backend is disabled)
  useEffect(() => {
    if (!config.enableBackend) {
      const demoCards = [
        {
          header: 'Welcome to Parallax!',
          text: 'This is a demo card. Start editing your plan document to see AI-powered suggestions here.',
          type: CardType.CONTEXT,
          metadata: { source: 'demo' },
        },
        {
          header: 'What is the project structure?',
          text: 'Consider documenting your project structure in the plan document. This will help with code generation.',
          type: CardType.QUESTION,
          metadata: { source: 'demo' },
        },
      ];

      // Add demo cards after a short delay
      const timer = setTimeout(() => {
        addCards(demoCards);
      }, 500);

      return () => clearTimeout(timer);
    }
  }, [addCards]);

  // Log backend status and errors
  useEffect(() => {
    if (config.enableBackend) {
      console.log('Backend integration enabled');
      console.log(`User ID: ${userId}`);
      console.log(`Char count: ${charCount}, Processing: ${isProcessing}`);
      if (error) {
        console.error('Backend error:', error);
      }
    }
  }, [userId, charCount, isProcessing, error]);

  return (
    <EditorLayout
      header={<Header />}
      leftPanel={<FileExplorer />}
      centerPanel={<PlanEditor />}
      rightPanel={<AIFeed />}
      footer={<VimCommandBar />}
    >
      <CommandPalette />
    </EditorLayout>
  );
}

export default App;
