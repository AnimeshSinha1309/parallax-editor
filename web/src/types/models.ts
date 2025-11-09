/**
 * TypeScript types mirroring Python models from shared/models.py and shared/context.py
 */

export enum CardType {
  QUESTION = 'question',
  CONTEXT = 'context',
  COMPLETION = 'completion',
  MATH = 'math',
  EMAIL = 'email',
}

export interface Card {
  header: string;
  text: string;
  type: CardType;
  metadata?: Record<string, any>;
  // Internal UI fields
  id?: string;  // Generated on client side
}

export interface GlobalPreferenceContext {
  scope_root: string;
  plan_path?: string;
}

export interface FulfillRequest {
  user_id: string;
  document_text: string;
  cursor_position: [number, number]; // [line, column]
  global_context: GlobalPreferenceContext;
}

export interface FulfillResponse {
  cards: Card[];
}

// File system types
export interface FileNode {
  name: string;
  path: string;
  type: 'file' | 'directory';
  children?: FileNode[];
}

// Command types
export interface Command {
  id: string;
  label: string;
  category?: string;
  shortcut?: string;
  icon?: string;
  action: () => void | Promise<void>;
}

// Editor state types
export interface EditorState {
  content: string;
  cursorPosition: [number, number];
  language: string;
  filePath?: string;
}
