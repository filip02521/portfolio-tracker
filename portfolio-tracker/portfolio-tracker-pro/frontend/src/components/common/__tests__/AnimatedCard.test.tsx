import React from 'react';
import { render, screen } from '@testing-library/react';
import { AnimatedCard } from '../AnimatedCard';
import '@testing-library/jest-dom';

describe('AnimatedCard', () => {
  beforeEach(() => {
    jest.useFakeTimers();
  });

  afterEach(() => {
    jest.runOnlyPendingTimers();
    jest.useRealTimers();
  });

  it('renders children correctly', () => {
    render(
      <AnimatedCard>
        <div>Test Content</div>
      </AnimatedCard>
    );

    expect(screen.getByText('Test Content')).toBeInTheDocument();
  });

  it('applies animation after delay', () => {
    const { container, rerender } = render(
      <AnimatedCard delay={100}>
        <div>Test</div>
      </AnimatedCard>
    );

    const card = container.firstChild as HTMLElement;
    expect(card).toHaveStyle({ opacity: '0' });
    expect(card).toHaveStyle({ transform: 'translateY(10px)' });

    jest.advanceTimersByTime(100);
    
    // Force rerender to apply state changes
    rerender(
      <AnimatedCard delay={100}>
        <div>Test</div>
      </AnimatedCard>
    );
    
    expect(card).toHaveStyle({ opacity: '1' });
    expect(card).toHaveStyle({ transform: 'translateY(0)' });
  });

  it('caps delay at 300ms', () => {
    const { container, rerender } = render(
      <AnimatedCard delay={500}>
        <div>Test</div>
      </AnimatedCard>
    );

    const card = container.firstChild as HTMLElement;
    expect(card).toHaveStyle({ opacity: '0' });

    // After capped delay (300ms), should be visible
    jest.advanceTimersByTime(300);
    rerender(
      <AnimatedCard delay={500}>
        <div>Test</div>
      </AnimatedCard>
    );
    expect(card).toHaveStyle({ opacity: '1' });
  });

  it('cleans up timer on unmount', () => {
    const { unmount } = render(
      <AnimatedCard delay={100}>
        <div>Test</div>
      </AnimatedCard>
    );

    expect(jest.getTimerCount()).toBe(1);
    unmount();
    expect(jest.getTimerCount()).toBe(0);
  });
});

