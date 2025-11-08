import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { Card } from '../Card';
import { CardType } from '../../../types/models';

describe('Card Component', () => {
  it('should render question card', () => {
    const card = {
      id: 'test-1',
      header: 'Test Question',
      text: 'This is a test question',
      type: CardType.QUESTION,
    };

    render(<Card card={card} />);

    expect(screen.getByText('Test Question')).toBeInTheDocument();
    expect(screen.getByText('This is a test question')).toBeInTheDocument();
  });

  it('should render context card', () => {
    const card = {
      id: 'test-2',
      header: 'Test Context',
      text: 'This is context information',
      type: CardType.CONTEXT,
    };

    render(<Card card={card} />);

    expect(screen.getByText('Test Context')).toBeInTheDocument();
    expect(screen.getByText('This is context information')).toBeInTheDocument();
  });

  it('should render completion card', () => {
    const card = {
      id: 'test-3',
      header: 'Test Completion',
      text: 'This is a completion suggestion',
      type: CardType.COMPLETION,
    };

    render(<Card card={card} />);

    expect(screen.getByText('Test Completion')).toBeInTheDocument();
    expect(screen.getByText('This is a completion suggestion')).toBeInTheDocument();
  });

  it('should render markdown content', () => {
    const card = {
      id: 'test-4',
      header: 'Markdown Test',
      text: 'This has **bold** and *italic* text',
      type: CardType.CONTEXT,
    };

    render(<Card card={card} />);

    const boldText = screen.getByText('bold');
    expect(boldText.tagName).toBe('STRONG');

    const italicText = screen.getByText('italic');
    expect(italicText.tagName).toBe('EM');
  });

  it('should render metadata if provided', () => {
    const card = {
      id: 'test-5',
      header: 'Test with Metadata',
      text: 'Content',
      type: CardType.CONTEXT,
      metadata: {
        source: 'test-source',
        confidence: 0.95,
      },
    };

    render(<Card card={card} />);

    expect(screen.getByText(/Source: test-source/)).toBeInTheDocument();
    expect(screen.getByText(/Confidence: 95%/)).toBeInTheDocument();
  });

  it('should have delete button', () => {
    const card = {
      id: 'test-6',
      header: 'Test',
      text: 'Content',
      type: CardType.QUESTION,
    };

    render(<Card card={card} />);

    const deleteButton = screen.getByLabelText('Delete card');
    expect(deleteButton).toBeInTheDocument();
  });
});
