import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { useFulfillment } from '../useFulfillment';
import { useEditorStore } from '../../stores/editorStore';
import { useFeedStore } from '../../stores/feedStore';
import { useCompletionStore } from '../../stores/completionStore';
import { backendService } from '../../services/backendService';
import { CardType } from '../../types/models';

// Mock the backend service
vi.mock('../../services/backendService', () => ({
  backendService: {
    fulfill: vi.fn(),
    getCached: vi.fn(),
  },
}));

describe('useFulfillment', () => {
  beforeEach(() => {
    vi.useFakeTimers();
    // Reset stores
    useEditorStore.getState().reset();
    useFeedStore.setState({ cards: [], selectedCardId: null, isLoading: false });
    useCompletionStore.setState({ currentCompletion: null, completionMetadata: null });
  });

  afterEach(() => {
    vi.restoreAllMocks();
    vi.useRealTimers();
  });

  it('should initialize with zero char count', () => {
    const { result } = renderHook(() =>
      useFulfillment({ userId: 'test-user', enabled: true })
    );

    expect(result.current.charCount).toBe(0);
    expect(result.current.isProcessing).toBe(false);
  });

  it('should count characters as content changes', async () => {
    const { result } = renderHook(() =>
      useFulfillment({ userId: 'test-user', enabled: true })
    );

    // Change content
    useEditorStore.getState().setContent('Hello');

    await waitFor(() => {
      expect(result.current.charCount).toBeGreaterThan(0);
    });
  });

  it('should not trigger backend if below threshold', async () => {
    const fulfillMock = vi.mocked(backendService.fulfill);
    fulfillMock.mockResolvedValue({
      cards: [],
      processing: false,
    });

    renderHook(() => useFulfillment({ userId: 'test-user', enabled: true }));

    // Type less than 20 characters
    useEditorStore.getState().setContent('Hello');

    // Wait for idle timeout
    vi.advanceTimersByTime(5000);

    // Should not call backend
    expect(fulfillMock).not.toHaveBeenCalled();
  });

  it('should trigger backend after threshold + idle timeout', async () => {
    const fulfillMock = vi.mocked(backendService.fulfill);
    fulfillMock.mockResolvedValue({
      cards: [
        {
          header: 'Test',
          text: 'Test completion',
          type: CardType.COMPLETION,
        },
      ],
      processing: false,
    });

    const { result } = renderHook(() =>
      useFulfillment({ userId: 'test-user', enabled: true })
    );

    // Type 20+ characters
    useEditorStore.getState().setContent('12345678901234567890');

    // Wait for idle timeout (4 seconds)
    await waitFor(() => {
      vi.advanceTimersByTime(4000);
    });

    // Should call backend
    await waitFor(() => {
      expect(fulfillMock).toHaveBeenCalled();
    });
  });

  it('should handle completion cards', async () => {
    const fulfillMock = vi.mocked(backendService.fulfill);
    fulfillMock.mockResolvedValue({
      cards: [
        {
          header: 'Completion',
          text: 'suggested text',
          type: CardType.COMPLETION,
        },
      ],
      processing: false,
    });

    renderHook(() => useFulfillment({ userId: 'test-user', enabled: true }));

    // Type and wait
    useEditorStore.getState().setContent('12345678901234567890');
    vi.advanceTimersByTime(4000);

    await waitFor(() => {
      const completion = useCompletionStore.getState().currentCompletion;
      expect(completion).toBe('suggested text');
    });
  });

  it('should handle feed cards', async () => {
    const fulfillMock = vi.mocked(backendService.fulfill);
    fulfillMock.mockResolvedValue({
      cards: [
        {
          header: 'Question',
          text: 'What is this?',
          type: CardType.QUESTION,
        },
        {
          header: 'Context',
          text: 'Some context',
          type: CardType.CONTEXT,
        },
      ],
      processing: false,
    });

    renderHook(() => useFulfillment({ userId: 'test-user', enabled: true }));

    // Trigger
    useEditorStore.getState().setContent('12345678901234567890');
    vi.advanceTimersByTime(4000);

    await waitFor(() => {
      const cards = useFeedStore.getState().cards;
      expect(cards.length).toBe(2);
      expect(cards[0].type).toBe(CardType.QUESTION);
      expect(cards[1].type).toBe(CardType.CONTEXT);
    });
  });

  it('should not call backend when disabled', async () => {
    const fulfillMock = vi.mocked(backendService.fulfill);

    renderHook(() => useFulfillment({ userId: 'test-user', enabled: false }));

    // Type and wait
    useEditorStore.getState().setContent('12345678901234567890');
    vi.advanceTimersByTime(4000);

    expect(fulfillMock).not.toHaveBeenCalled();
  });

  it('should handle errors gracefully', async () => {
    const fulfillMock = vi.mocked(backendService.fulfill);
    fulfillMock.mockRejectedValue(new Error('Network error'));

    const { result } = renderHook(() =>
      useFulfillment({ userId: 'test-user', enabled: true })
    );

    // Trigger
    useEditorStore.getState().setContent('12345678901234567890');
    vi.advanceTimersByTime(4000);

    await waitFor(() => {
      expect(result.current.error).toBeTruthy();
      expect(result.current.isProcessing).toBe(false);
    });
  });
});
