import { Allotment } from 'allotment';
import 'allotment/dist/style.css';
import { useUIStore } from '../stores/uiStore';
import clsx from 'clsx';

interface EditorLayoutProps {
  leftPanel: React.ReactNode;
  centerPanel: React.ReactNode;
  rightPanel: React.ReactNode;
  header: React.ReactNode;
  footer: React.ReactNode;
}

export function EditorLayout({
  leftPanel,
  centerPanel,
  rightPanel,
  header,
  footer,
}: EditorLayoutProps) {
  const {
    leftPanelVisible,
    rightPanelVisible,
    activePane,
  } = useUIStore();

  return (
    <div className="flex flex-col h-full w-full bg-vscode-bg-primary">
      {/* Header */}
      <div className="h-12 border-b border-vscode-border flex-shrink-0">
        {header}
      </div>

      {/* Main content area with 3 panes */}
      <div className="flex-1 overflow-hidden">
        <Allotment>
          {/* Left Panel - File Explorer */}
          {leftPanelVisible && (
            <Allotment.Pane
              minSize={200}
              preferredSize={250}
              maxSize={600}
            >
              <div
                className={clsx(
                  'h-full bg-vscode-bg-secondary border-r border-vscode-border',
                  activePane === 'files' && 'pane-focused'
                )}
                data-pane="files"
              >
                {leftPanel}
              </div>
            </Allotment.Pane>
          )}

          {/* Center Panel - Editor */}
          <Allotment.Pane minSize={400}>
            <div
              className={clsx(
                'h-full bg-vscode-bg-primary',
                activePane === 'editor' && 'pane-focused'
              )}
              data-pane="editor"
            >
              {centerPanel}
            </div>
          </Allotment.Pane>

          {/* Right Panel - AI Feed */}
          {rightPanelVisible && (
            <Allotment.Pane
              minSize={300}
              preferredSize={350}
              maxSize={800}
            >
              <div
                className={clsx(
                  'h-full bg-vscode-bg-secondary border-l border-vscode-border',
                  activePane === 'feed' && 'pane-focused'
                )}
                data-pane="feed"
              >
                {rightPanel}
              </div>
            </Allotment.Pane>
          )}
        </Allotment>
      </div>

      {/* Footer - Command bar */}
      <div className="h-8 border-t border-vscode-border flex-shrink-0">
        {footer}
      </div>
    </div>
  );
}
