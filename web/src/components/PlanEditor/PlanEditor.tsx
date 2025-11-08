import { MonacoEditor } from './MonacoEditor';

export function PlanEditor() {
  return (
    <div className="h-full flex flex-col">
      {/* Editor Toolbar (optional for now) */}
      {/* <div className="h-10 border-b border-vscode-border px-4 flex items-center">
        <span className="text-sm text-vscode-text-secondary">PLAN.md</span>
      </div> */}

      {/* Monaco Editor */}
      <div className="flex-1 overflow-hidden">
        <MonacoEditor />
      </div>
    </div>
  );
}
