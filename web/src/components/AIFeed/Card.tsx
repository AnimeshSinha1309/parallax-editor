import { X, HelpCircle, Info, Lightbulb, Sigma, Mail } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import remarkMath from 'remark-math';
import rehypeKatex from 'rehype-katex';
import 'katex/dist/katex.min.css';
import { useFeedStore } from '../../stores/feedStore';
import type { Card as CardModel } from '../../types/models';
import { CardType } from '../../types/models';
import clsx from 'clsx';

interface CardProps {
  card: CardModel;
}

const CARD_ICONS = {
  [CardType.QUESTION]: HelpCircle,
  [CardType.CONTEXT]: Info,
  [CardType.COMPLETION]: Lightbulb,
  [CardType.MATH]: Sigma,
  [CardType.EMAIL]: Mail,
};

const CARD_COLORS = {
  [CardType.QUESTION]: 'text-vscode-accent-yellow',
  [CardType.CONTEXT]: 'text-vscode-accent-blue',
  [CardType.COMPLETION]: 'text-vscode-accent-green',
  [CardType.MATH]: 'text-vscode-accent-purple',
  [CardType.EMAIL]: 'text-vscode-accent-orange',
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
        'mb-2 bg-vscode-bg-tertiary border border-vscode-border overflow-hidden transition-all cursor-pointer',
        isSelected && 'border-vscode-focus-border',
        `card-${card.type}`
      )}
      onClick={handleClick}
    >
      {/* Card Header */}
      <div className="px-2.5 py-1.5 border-b border-vscode-border flex items-start justify-between">
        <div className="flex items-center gap-1.5 flex-1 min-w-0">
          <Icon size={14} className={clsx('flex-shrink-0', iconColor)} />
          <span className="text-xs font-medium text-vscode-text-primary truncate">
            {card.header}
          </span>
        </div>
        <button
          onClick={handleDelete}
          className="flex-shrink-0 ml-2 text-vscode-text-secondary hover:text-vscode-accent-red transition-colors"
          aria-label="Delete card"
        >
          <X size={12} />
        </button>
      </div>

      {/* Card Body */}
      <div className="px-2.5 py-2 text-xs text-vscode-text-primary">
        <ReactMarkdown
          className="markdown-content"
          remarkPlugins={[remarkMath]}
          rehypePlugins={[rehypeKatex]}
          components={{
            p: ({ children }) => <p className="mb-1.5 last:mb-0">{children}</p>,
            code: ({ children }) => (
              <code className="px-1 py-0.5 bg-vscode-bg-primary text-xs font-mono">
                {children}
              </code>
            ),
            a: ({ href, children }) => (
              <a
                href={href}
                target="_blank"
                rel="noopener noreferrer"
                className="text-vscode-accent-blue hover:underline"
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
          <div className="mt-1.5 pt-1.5 border-t border-vscode-border text-xs text-vscode-text-secondary">
            {card.metadata.source && (
              <div className="text-xs">Source: {card.metadata.source}</div>
            )}
            {card.metadata.confidence && (
              <div className="text-xs">Confidence: {(card.metadata.confidence * 100).toFixed(0)}%</div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
