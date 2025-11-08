import { describe, it, expect, beforeEach } from 'vitest';
import { useFeedStore } from '../feedStore';
import { CardType } from '../../types/models';

describe('FeedStore', () => {
  beforeEach(() => {
    // Reset store state before each test
    useFeedStore.setState({ cards: [], selectedCardId: null, isLoading: false });
  });

  it('should initialize with empty cards', () => {
    const { cards } = useFeedStore.getState();
    expect(cards).toEqual([]);
  });

  it('should add a single card', () => {
    const { addCard } = useFeedStore.getState();

    addCard({
      header: 'Test Card',
      text: 'Test content',
      type: CardType.QUESTION,
    });

    const { cards } = useFeedStore.getState();
    expect(cards).toHaveLength(1);
    expect(cards[0].header).toBe('Test Card');
    expect(cards[0].id).toBeDefined();
  });

  it('should add multiple cards', () => {
    const { addCards } = useFeedStore.getState();

    addCards([
      { header: 'Card 1', text: 'Content 1', type: CardType.QUESTION },
      { header: 'Card 2', text: 'Content 2', type: CardType.CONTEXT },
    ]);

    const { cards } = useFeedStore.getState();
    expect(cards).toHaveLength(2);
    expect(cards[0].header).toBe('Card 1');
    expect(cards[1].header).toBe('Card 2');
  });

  it('should remove a card by id', () => {
    const { addCards, removeCard } = useFeedStore.getState();

    addCards([
      { header: 'Card 1', text: 'Content 1', type: CardType.QUESTION },
      { header: 'Card 2', text: 'Content 2', type: CardType.CONTEXT },
    ]);

    const cards = useFeedStore.getState().cards;
    const firstCardId = cards[0].id!;

    removeCard(firstCardId);

    const remainingCards = useFeedStore.getState().cards;
    expect(remainingCards).toHaveLength(1);
    expect(remainingCards[0].header).toBe('Card 2');
  });

  it('should clear all cards', () => {
    const { addCards, clearCards } = useFeedStore.getState();

    addCards([
      { header: 'Card 1', text: 'Content 1', type: CardType.QUESTION },
      { header: 'Card 2', text: 'Content 2', type: CardType.CONTEXT },
    ]);

    clearCards();

    const { cards } = useFeedStore.getState();
    expect(cards).toEqual([]);
  });

  it('should clear cards by type', () => {
    const { addCards, clearCardsByType } = useFeedStore.getState();

    addCards([
      { header: 'Question 1', text: 'Content', type: CardType.QUESTION },
      { header: 'Context 1', text: 'Content', type: CardType.CONTEXT },
      { header: 'Question 2', text: 'Content', type: CardType.QUESTION },
    ]);

    clearCardsByType(CardType.QUESTION);

    const { cards } = useFeedStore.getState();
    expect(cards).toHaveLength(1);
    expect(cards[0].type).toBe(CardType.CONTEXT);
  });

  it('should select and deselect cards', () => {
    const { addCard, selectCard } = useFeedStore.getState();

    addCard({ header: 'Test', text: 'Content', type: CardType.CONTEXT });

    const cards = useFeedStore.getState().cards;
    const cardId = cards[0].id!;

    selectCard(cardId);
    expect(useFeedStore.getState().selectedCardId).toBe(cardId);

    selectCard(null);
    expect(useFeedStore.getState().selectedCardId).toBeNull();
  });

  it('should set loading state', () => {
    const { setLoading } = useFeedStore.getState();

    setLoading(true);
    expect(useFeedStore.getState().isLoading).toBe(true);

    setLoading(false);
    expect(useFeedStore.getState().isLoading).toBe(false);
  });
});
