import Editor, { BeforeMount } from '@monaco-editor/react';
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

  const handleBeforeMount: BeforeMount = (monaco) => {
    // Define Monokai Pro theme
    monaco.editor.defineTheme('monokai-pro', {
      base: 'vs-dark',
      inherit: true,
      rules: [
        { token: '', foreground: 'FCFCFA', background: '2D2A2E' },
        { token: 'comment', foreground: '727072', fontStyle: 'italic' },
        { token: 'keyword', foreground: 'FF6188' },
        { token: 'keyword.control', foreground: 'FF6188' },
        { token: 'keyword.operator', foreground: 'FF6188' },
        { token: 'string', foreground: 'FFD866' },
        { token: 'number', foreground: 'AB9DF2' },
        { token: 'constant', foreground: 'AB9DF2' },
        { token: 'type', foreground: '78DCE8', fontStyle: 'italic' },
        { token: 'class', foreground: 'A9DC76' },
        { token: 'function', foreground: 'A9DC76' },
        { token: 'variable', foreground: 'FCFCFA' },
        { token: 'variable.parameter', foreground: 'FC9867' },
        { token: 'operator', foreground: 'FF6188' },
        { token: 'delimiter', foreground: 'FCFCFA' },
      ],
      colors: {
        'editor.background': '#2D2A2E',
        'editor.foreground': '#FCFCFA',
        'editorLineNumber.foreground': '#5B595C',
        'editorLineNumber.activeForeground': '#C1C0C0',
        'editor.selectionBackground': '#5B595C80',
        'editor.inactiveSelectionBackground': '#5B595C40',
        'editor.lineHighlightBackground': '#3E3B3F',
        'editorCursor.foreground': '#FCFCFA',
        'editorWhitespace.foreground': '#5B595C',
        'editorIndentGuide.background': '#3E3B3F',
        'editorIndentGuide.activeBackground': '#5B595C',
        'editorRuler.foreground': '#3E3B3F',
        'editorBracketMatch.background': '#5B595C',
        'editorBracketMatch.border': '#727072',
        'scrollbarSlider.background': '#5B595C80',
        'scrollbarSlider.hoverBackground': '#5B595CA0',
        'scrollbarSlider.activeBackground': '#5B595CC0',
      },
    });
  };

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

  // Use Monokai Pro theme for the editor
  const monacoTheme = 'monokai-pro';

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
        beforeMount={handleBeforeMount}
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
