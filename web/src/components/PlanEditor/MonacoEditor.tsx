import Editor, { OnMount } from '@monaco-editor/react';
import { useRef, useEffect } from 'react';
import { useEditorStore } from '../../stores/editorStore';
import { useUIStore } from '../../stores/uiStore';
import * as monaco from 'monaco-editor';

export function MonacoEditor() {
  const editorRef = useRef<monaco.editor.IStandaloneCodeEditor | null>(null);
  const {
    content,
    language,
    setContent,
    setCursorPosition,
  } = useEditorStore();
  const { focusPane, theme } = useUIStore();

  const handleEditorDidMount: OnMount = (editor, monaco) => {
    editorRef.current = editor;

    // Track cursor position changes
    editor.onDidChangeCursorPosition((e) => {
      const position = e.position;
      setCursorPosition([position.lineNumber - 1, position.column - 1]);
    });

    // Focus the editor initially
    editor.focus();
  };

  const handleEditorChange = (value: string | undefined) => {
    if (value !== undefined) {
      setContent(value);
    }
  };

  const handleClick = () => {
    focusPane('editor');
  };

  // Set up Monaco editor theme
  useEffect(() => {
    if (editorRef.current) {
      const monacoTheme = theme === 'dark' ? 'vs-dark' : 'vs-light';
      monaco.editor.setTheme(monacoTheme);
    }
  }, [theme]);

  return (
    <div
      className="h-full w-full"
      onClick={handleClick}
    >
      <Editor
        height="100%"
        language={language}
        value={content}
        theme="vs-dark"
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
