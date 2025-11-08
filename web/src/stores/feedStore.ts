import { create } from 'zustand';
import type { Card, CardType } from '../types/models';

interface FeedStore {
  cards: Card[];
  selectedCardId: string | null;
  isLoading: boolean;

  // Actions
  addCard: (card: Card) => void;
  addCards: (cards: Card[]) => void;
  removeCard: (cardId: string) => void;
  clearCards: () => void;
  clearCardsByType: (type: CardType) => void;
  selectCard: (cardId: string | null) => void;
  setLoading: (loading: boolean) => void;
}

// Generate unique ID for cards
const generateId = () => `card-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;

export const useFeedStore = create<FeedStore>((set) => ({
  cards: [],
  selectedCardId: null,
  isLoading: false,

  addCard: (card: Card) =>
    set((state) => ({
      cards: [...state.cards, { ...card, id: card.id || generateId() }],
    })),

  addCards: (cards: Card[]) =>
    set((state) => ({
      cards: [
        ...state.cards,
        ...cards.map((card) => ({ ...card, id: card.id || generateId() })),
      ],
    })),

  removeCard: (cardId: string) =>
    set((state) => ({
      cards: state.cards.filter((card) => card.id !== cardId),
      selectedCardId: state.selectedCardId === cardId ? null : state.selectedCardId,
    })),

  clearCards: () =>
    set({ cards: [], selectedCardId: null }),

  clearCardsByType: (type: CardType) =>
    set((state) => ({
      cards: state.cards.filter((card) => card.type !== type),
    })),

  selectCard: (cardId: string | null) =>
    set({ selectedCardId: cardId }),

  setLoading: (loading: boolean) =>
    set({ isLoading: loading }),
}));
