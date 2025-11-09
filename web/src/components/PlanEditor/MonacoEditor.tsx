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

  const handleBeforeMount = (monaco: any) => {
    // Define Noctis Minimus theme
    monaco.editor.defineTheme('noctis-minimus', {
      base: 'vs-dark',
      inherit: true,
      rules: [
        { token: '', foreground: 'c5cdd3' },
        { token: 'comment', foreground: '5e7887', fontStyle: 'italic' },
        { token: 'keyword', foreground: 'c88da2' },
        { token: 'keyword.control', foreground: 'c88da2' },
        { token: 'keyword.operator', foreground: 'c88da2' },
        { token: 'string', foreground: '72c09f' },
        { token: 'string.interpolated', foreground: '3f8d6c' },
        { token: 'number', foreground: '7068b1' },
        { token: 'constant', foreground: 'a88c00' },
        { token: 'type', foreground: 'be856f' },
        { token: 'type.identifier', foreground: 'be856f' },
        { token: 'class', foreground: '3f848d' },
        { token: 'function', foreground: '3f848d' },
        { token: 'variable', foreground: 'd3b692' },
        { token: 'variable.parameter', foreground: 'd3b692' },
        { token: 'operator', foreground: 'c88da2' },
        { token: 'delimiter', foreground: 'c5cdd3' },
        { token: 'tag', foreground: 'c37455' },
        { token: 'support', foreground: '72b7c0' },
        { token: 'invalid', foreground: 'b16a4e' },
      ],
      colors: {
        'editor.background': '#1b2932',
        'editor.foreground': '#c5cdd3',
        'editorLineNumber.foreground': '#5d6e79',
        'editorLineNumber.activeForeground': '#6496b4',
        'editor.selectionBackground': '#496d8355',
        'editor.inactiveSelectionBackground': '#496d8320',
        'editor.lineHighlightBackground': '#1f3240',
        'editorCursor.foreground': '#b3d2e6',
        'editorWhitespace.foreground': '#5d6e7944',
        'editorIndentGuide.background': '#2e4554',
        'editorIndentGuide.activeBackground': '#5d6e79',
        'editorRuler.foreground': '#2e4554',
        'editorBracketMatch.background': '#496d8366',
        'editorBracketMatch.border': '#5998c0',
        'scrollbarSlider.background': '#5d6e7966',
        'scrollbarSlider.hoverBackground': '#5d6e7999',
        'scrollbarSlider.activeBackground': '#5998c0bb',
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

  // Use Noctis Minimus theme
  const monacoTheme = 'noctis-minimus';

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
          fontFamily: 'Fira Code, Cascadia Code, Consolas, Monaco, monospace',
          fontLigatures: true,
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
