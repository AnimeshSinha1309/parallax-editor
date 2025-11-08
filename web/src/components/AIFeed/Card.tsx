import { X, HelpCircle, Info, Lightbulb } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import { useFeedStore } from '../../stores/feedStore';
import { Card as CardType, CardType as CardTypeEnum } from '../../types/models';
import clsx from 'clsx';

interface CardProps {
  card: CardType;
}

const CARD_ICONS = {
  [CardTypeEnum.QUESTION]: HelpCircle,
  [CardTypeEnum.CONTEXT]: Info,
  [CardTypeEnum.COMPLETION]: Lightbulb,
};

const CARD_COLORS = {
  [CardTypeEnum.QUESTION]: 'text-vscode-accent-yellow',
  [CardTypeEnum.CONTEXT]: 'text-vscode-accent-blue',
  [CardTypeEnum.COMPLETION]: 'text-vscode-accent-green',
};

export function Card({ card }: CardProps) {
  const { removeCard, selectedCardId, selectCard } = useFeedStore();
  const Icon = CARD_ICONS[card.type];
  const iconColor = CARD_COLORS[card.type];
  const isSelected = selectedCardId === card.id;

  const handleDelete = (e: React.MouseEvent) => {
    e.stopPropagation();
    if (card.id) {
      removeCard(card.id);
    }
  };

  const handleClick = () => {
    selectCard(card.id || null);
  };

  return (
    <div
      className={clsx(
        'mb-3 rounded bg-vscode-bg-tertiary border border-vscode-border overflow-hidden transition-all cursor-pointer',
        isSelected && 'ring-2 ring-vscode-focus-border',
        `card-${card.type}`
      )}
      onClick={handleClick}
    >
      {/* Card Header */}
      <div className="px-3 py-2 border-b border-vscode-border flex items-start justify-between">
        <div className="flex items-center gap-2 flex-1 min-w-0">
          <Icon size={16} className={clsx('flex-shrink-0', iconColor)} />
          <span className="text-sm font-semibold text-vscode-text-primary truncate">
            {card.header}
          </span>
        </div>
        <button
          onClick={handleDelete}
          className="flex-shrink-0 ml-2 text-vscode-text-secondary hover:text-vscode-accent-red transition-colors"
          aria-label="Delete card"
        >
          <X size={16} />
        </button>
      </div>

      {/* Card Body */}
      <div className="px-3 py-2 text-sm text-vscode-text-primary">
        <ReactMarkdown
          className="markdown-content"
          components={{
            p: ({ children }) => <p className="mb-2 last:mb-0">{children}</p>,
            code: ({ children }) => (
              <code className="px-1 py-0.5 bg-vscode-bg-primary rounded text-xs font-mono">
                {children}
              </code>
            ),
            a: ({ href, children }) => (
              <a
                href={href}
                target="_blank"
                rel="noopener noreferrer"
                className="text-vscode-accent-blue underline hover:text-vscode-accent-green"
              >
                {children}
              </a>
            ),
          }}
        >
          {card.text}
        </ReactMarkdown>

        {/* Metadata (if any) */}
        {card.metadata && Object.keys(card.metadata).length > 0 && (
          <div className="mt-2 pt-2 border-t border-vscode-border text-xs text-vscode-text-secondary">
            {card.metadata.source && (
              <div>Source: {card.metadata.source}</div>
            )}
            {card.metadata.confidence && (
              <div>Confidence: {(card.metadata.confidence * 100).toFixed(0)}%</div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
