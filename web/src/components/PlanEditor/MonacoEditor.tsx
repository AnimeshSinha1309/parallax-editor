import Editor from '@monaco-editor/react';
import { useRef, useEffect } from 'react';
import { useEditorStore } from '../../stores/editorStore';
import { useUIStore } from '../../stores/uiStore';
import { useCompletionStore } from '../../stores/completionStore';
import { registerGhostTextProvider } from './GhostTextProvider';
import type { editor, IDisposable } from 'monaco-editor';

export function MonacoEditor() {
  const editorRef = useRef<editor.IStandaloneCodeEditor | null>(null);
  const disposablesRef = useRef<IDisposable[]>([]);

  const {
    content,
    language,
    setContent,
    setCursorPosition,
  } = useEditorStore();
  const { focusPane, theme } = useUIStore();
  const { currentCompletion } = useCompletionStore();

  const handleEditorDidMount = (editorInstance: editor.IStandaloneCodeEditor) => {
    editorRef.current = editorInstance;

    // Track cursor position changes
    const cursorListener = editorInstance.onDidChangeCursorPosition((e) => {
      const position = e.position;
      setCursorPosition([position.lineNumber - 1, position.column - 1]);
    });
    disposablesRef.current.push(cursorListener);

    // Register ghost text provider
    const providerDisposable = registerGhostTextProvider();
    disposablesRef.current.push(providerDisposable);

    // Focus the editor initially
    editorInstance.focus();
  };

  const handleEditorChange = (value: string | undefined) => {
    if (value !== undefined) {
      setContent(value);
    }
  };

  const handleClick = () => {
    focusPane('editor');
  };

  // Trigger inline suggestions when completion changes
  useEffect(() => {
    if (editorRef.current && currentCompletion) {
      // Trigger Monaco's inline suggestions
      editorRef.current.trigger('ghost-text', 'editor.action.inlineSuggest.trigger', {});
    }
  }, [currentCompletion]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      disposablesRef.current.forEach((d) => d.dispose());
    };
  }, []);

  // Determine Monaco theme based on UI theme
  const monacoTheme = theme === 'dark' ? 'vs-dark' : 'vs-light';

  return (
    <div
      className="h-full w-full"
      onClick={handleClick}
    >
      <Editor
        height="100%"
        language={language}
        value={content}
        theme={monacoTheme}
        onChange={handleEditorChange}
        onMount={handleEditorDidMount}
        options={{
          fontSize: 14,
          fontFamily: 'Cascadia Code, Fira Code, Consolas, Monaco, monospace',
          minimap: { enabled: true },
          lineNumbers: 'on',
          rulers: [80],
          wordWrap: 'on',
          automaticLayout: true,
          scrollBeyondLastLine: false,
          renderWhitespace: 'selection',
          suggest: {
            preview: true,
            showInlineDetails: true,
          },
          quickSuggestions: {
            other: true,
            comments: false,
            strings: false,
          },
          // Enable inline suggestions (ghost text)
          inlineSuggest: {
            enabled: true,
          },
          padding: {
            top: 16,
            bottom: 16,
          },
        }}
      />
    </div>
  );
}
