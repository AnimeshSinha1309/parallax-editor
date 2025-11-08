import { useEffect } from 'react';
import { EditorLayout } from './layouts/EditorLayout';
import { FileExplorer } from './components/FileExplorer';
import { PlanEditor } from './components/PlanEditor';
import { AIFeed } from './components/AIFeed';
import { CommandPalette } from './components/CommandPalette';
import { VimCommandBar } from './components/VimCommandBar';
import { Header } from './components/Header';
import { useKeyboardShortcuts } from './hooks/useKeyboardShortcuts';
import { useUIStore } from './stores/uiStore';
import { useFeedStore } from './stores/feedStore';
import { CardType } from './types/models';

function App() {
  // Set up keyboard shortcuts
  useKeyboardShortcuts();

  const { theme } = useUIStore();
  const { addCards } = useFeedStore();

  // Apply theme to document
  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
  }, [theme]);

  // Add some demo cards on mount
  useEffect(() => {
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
  }, [addCards]);

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
