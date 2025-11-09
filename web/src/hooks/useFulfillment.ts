import { useEffect, useRef, useState } from 'react';
import { useEditorStore } from '../stores/editorStore';
import { useFileSystemStore } from '../stores/fileSystemStore';
import { useFeedStore } from '../stores/feedStore';
import { useCompletionStore } from '../stores/completionStore';
import { backendService } from '../services/backendService';
import { config } from '../utils/config';
import { CardType } from '../types/models';
import type { Card } from '../types/models';

interface UseFulfillmentOptions {
  userId: string;
  enabled?: boolean;
}

export function useFulfillment({ userId, enabled = true }: UseFulfillmentOptions) {
  const [charCount, setCharCount] = useState(0);
  const [isProcessing, setIsProcessing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const idleTimerRef = useRef<NodeJS.Timeout | null>(null);
  const pollingIntervalRef = useRef<NodeJS.Timeout | null>(null);
  const previousContentRef = useRef('');

  const { content, cursorPosition } = useEditorStore();
  const { scopeRoot, planPath } = useFileSystemStore();

  /**
   * Handle cards from backend response
   */
  const handleCards = (cards: Card[]) => {
    // Separate cards by type
    const completions = cards.filter((c) => c.type === CardType.COMPLETION);
    const feedCards = cards.filter(
      (c) => c.type === CardType.QUESTION || c.type === CardType.CONTEXT || c.type === CardType.MATH || c.type === CardType.EMAIL
    );

    // Update completion store (only first completion)
    if (completions.length > 0) {
      useCompletionStore.getState().setCompletion(completions[0]);
    }

    // Update feed store (replace existing cards)
    if (feedCards.length > 0) {
      // Clear existing cards and add new ones
      useFeedStore.getState().clearCards();
      useFeedStore.getState().addCards(feedCards);
    }
  };

  /**
   * Start polling /cached endpoint
   */
  const startPolling = () => {
    // Clear existing poll
    if (pollingIntervalRef.current) {
      clearInterval(pollingIntervalRef.current);
    }

    // Poll every 3 seconds
    pollingIntervalRef.current = setInterval(async () => {
      try {
        const cached = await backendService.getCached(userId);
        handleCards(cached.cards);

        // Stop polling when done
        if (!cached.processing) {
          stopPolling();
          setIsProcessing(false);
        }
      } catch (err) {
        console.error('Polling failed:', err);
        setError(err instanceof Error ? err.message : 'Polling failed');
        stopPolling();
        setIsProcessing(false);
      }
    }, config.fulfillment.pollInterval);
  };

  /**
   * Stop polling
   */
  const stopPolling = () => {
    if (pollingIntervalRef.current) {
      clearInterval(pollingIntervalRef.current);
      pollingIntervalRef.current = null;
    }
  };

  /**
   * Call backend /fulfill endpoint
   */
  const callBackend = async () => {
    if (!enabled) return;

    try {
      setIsProcessing(true);
      setError(null);

      // Call /fulfill
      const response = await backendService.fulfill({
        user_id: userId,
        document_text: content,
        cursor_position: cursorPosition,
        global_context: {
          scope_root: scopeRoot,
          plan_path: planPath || undefined,
        },
      });

      // Handle immediate response
      handleCards(response.cards);

      // Start polling if still processing
      if (response.processing) {
        startPolling();
      } else {
        setIsProcessing(false);
      }
    } catch (err) {
      console.error('Fulfillment failed:', err);
      setError(err instanceof Error ? err.message : 'Fulfillment failed');
      setIsProcessing(false);
    }
  };

  /**
   * Track content changes and count characters
   */
  useEffect(() => {
    if (!enabled) return;

    const previousContent = previousContentRef.current;
    const diff = Math.abs(content.length - previousContent.length);

    if (diff > 0) {
      setCharCount((prev) => prev + diff);
    }

    previousContentRef.current = content;
  }, [content, enabled]);

  /**
   * Handle debouncing with character threshold and idle timer
   */
  useEffect(() => {
    if (!enabled) return;

    if (charCount >= config.fulfillment.charThreshold && !isProcessing) {
      // Cancel existing timer
      if (idleTimerRef.current) {
        clearTimeout(idleTimerRef.current);
      }

      // Start new idle timer (4 seconds)
      idleTimerRef.current = setTimeout(() => {
        callBackend();
        setCharCount(0);
      }, config.fulfillment.idleTimeout);
    }

    return () => {
      if (idleTimerRef.current) {
        clearTimeout(idleTimerRef.current);
      }
    };
  }, [charCount, isProcessing, enabled]);

  /**
   * Cleanup on unmount
   */
  useEffect(() => {
    return () => {
      stopPolling();
      if (idleTimerRef.current) {
        clearTimeout(idleTimerRef.current);
      }
    };
  }, []);

  /**
   * Manual trigger for fulfillment
   */
  const trigger = () => {
    if (enabled && !isProcessing) {
      callBackend();
      setCharCount(0);
    }
  };

  return {
    charCount,
    isProcessing,
    error,
    trigger,
  };
}
