/**
 * Monaco Inline Completions Provider for Ghost Text
 * Provides AI-suggested completions as gray inline text at cursor position
 */

import type { editor, languages, CancellationToken, IDisposable } from 'monaco-editor';
import { useCompletionStore } from '../../stores/completionStore';

export class GhostTextProvider implements languages.InlineCompletionsProvider {
  /**
   * Provide inline completions (ghost text) at the current cursor position
   */
  async provideInlineCompletions(
    model: editor.ITextModel,
    position: languages.Position,
    context: languages.InlineCompletionContext,
    token: CancellationToken
  ): Promise<languages.InlineCompletions | undefined> {
    // Get current completion from store
    const completion = useCompletionStore.getState().currentCompletion;

    if (!completion || token.isCancellationRequested) {
      return undefined;
    }

    // Return the completion as an inline suggestion
    return {
      items: [
        {
          insertText: completion,
          range: {
            startLineNumber: position.lineNumber,
            startColumn: position.column,
            endLineNumber: position.lineNumber,
            endColumn: position.column,
          },
        },
      ],
    };
  }

  /**
   * Free any resources (cleanup)
   */
  freeInlineCompletions(): void {
    // No cleanup needed for now
  }
}

/**
 * Register the ghost text provider with Monaco
 */
export function registerGhostTextProvider(): IDisposable {
  const monaco = (window as any).monaco;

  if (!monaco) {
    console.warn('Monaco not loaded yet');
    return {
      dispose: () => {},
    };
  }

  return monaco.languages.registerInlineCompletionsProvider(
    'markdown',
    new GhostTextProvider()
  );
}
