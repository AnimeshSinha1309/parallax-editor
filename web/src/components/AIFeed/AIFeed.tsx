import { useEffect } from 'react';
import { useFeedStore } from '../../stores/feedStore';
import { useUIStore } from '../../stores/uiStore';
import { Card } from './Card';
import { Loader2, Sparkles } from 'lucide-react';
import { CardType } from '../../types/models';

export function AIFeed() {
  const { cards, isLoading, clearCards } = useFeedStore();
  const { focusPane } = useUIStore();

  const handleClick = () => {
    focusPane('feed');
  };

  // Add some mock cards for demo purposes
  useEffect(() => {
    // Mock cards will be added here for testing
    // In production, these will come from the backend
  }, []);

  const questionCards = cards.filter((c) => c.type === CardType.QUESTION);
  const contextCards = cards.filter((c) => c.type === CardType.CONTEXT);
  const completionCards = cards.filter((c) => c.type === CardType.COMPLETION);
  const mathCards = cards.filter((c) => c.type === CardType.MATH);
  const emailCards = cards.filter((c) => c.type === CardType.EMAIL);

  return (
    <div
      className="h-full flex flex-col overflow-hidden"
      onClick={handleClick}
    >
      {/* Header */}
      <div className="px-3 py-2 border-b border-vscode-border flex items-center justify-between">
        <h2 className="text-xs font-medium text-vscode-text-secondary flex items-center gap-1.5">
          <Sparkles size={12} />
          AI Feed
        </h2>
        {cards.length > 0 && (
          <button
            onClick={(e) => {
              e.stopPropagation();
              clearCards();
            }}
            className="text-xs text-vscode-text-secondary hover:text-vscode-text-primary transition-colors"
          >
            Clear
          </button>
        )}
      </div>

      {/* Feed Content */}
      <div className="flex-1 overflow-y-auto px-2 py-2">
        {isLoading && (
          <div className="flex items-center justify-center gap-2 py-8 text-vscode-text-secondary">
            <Loader2 size={20} className="animate-spin" />
            <span className="text-sm">Loading suggestions...</span>
          </div>
        )}

        {!isLoading && cards.length === 0 && (
          <div className="text-center py-8 text-vscode-text-secondary">
            <Sparkles size={32} className="mx-auto mb-2 opacity-50" />
            <p className="text-sm">No suggestions yet</p>
            <p className="text-xs mt-1">
              Start editing to see AI-powered suggestions
            </p>
          </div>
        )}

        {/* Questions Section */}
        {questionCards.length > 0 && (
          <div className="mb-3">
            <h3 className="text-xs font-medium text-vscode-text-secondary mb-1.5 px-1">
              Questions
            </h3>
            {questionCards.map((card) => (
              <Card key={card.id} card={card} />
            ))}
          </div>
        )}

        {/* Context Section */}
        {contextCards.length > 0 && (
          <div className="mb-3">
            <h3 className="text-xs font-medium text-vscode-text-secondary mb-1.5 px-1">
              Context
            </h3>
            {contextCards.map((card) => (
              <Card key={card.id} card={card} />
            ))}
          </div>
        )}

        {/* Math Section */}
        {mathCards.length > 0 && (
          <div className="mb-3">
            <h3 className="text-xs font-medium text-vscode-text-secondary mb-1.5 px-1">
              Math
            </h3>
            {mathCards.map((card) => (
              <Card key={card.id} card={card} />
            ))}
          </div>
        )}

        {/* Email Section */}
        {emailCards.length > 0 && (
          <div className="mb-3">
            <h3 className="text-xs font-medium text-vscode-text-secondary mb-1.5 px-1">
              Emails
            </h3>
            {emailCards.map((card) => (
              <Card key={card.id} card={card} />
            ))}
          </div>
        )}

        {/* Completions Section */}
        {completionCards.length > 0 && (
          <div className="mb-3">
            <h3 className="text-xs font-medium text-vscode-text-secondary mb-1.5 px-1">
              Completions
            </h3>
            {completionCards.map((card) => (
              <Card key={card.id} card={card} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
