import { useEffect, useRef } from 'react';

export type SwipeDirection = 'left' | 'right' | 'up' | 'down';

interface SwipeGestureOptions {
  onSwipeLeft?: () => void;
  onSwipeRight?: () => void;
  onSwipeUp?: () => void;
  onSwipeDown?: () => void;
  minSwipeDistance?: number;
  maxSwipeTime?: number;
}

/**
 * Hook to detect swipe gestures on touch devices
 * @param elementRef - Ref to the element to attach swipe listeners to
 * @param options - Swipe gesture options including callbacks and thresholds
 */
export function useSwipeGesture(
  elementRef: React.RefObject<HTMLElement | null>,
  options: SwipeGestureOptions
) {
  const {
    onSwipeLeft,
    onSwipeRight,
    onSwipeUp,
    onSwipeDown,
    minSwipeDistance = 50,
    maxSwipeTime = 500,
  } = options;

  const touchStartRef = useRef<{ x: number; y: number; time: number } | null>(
    null
  );

  useEffect(() => {
    const element = elementRef.current;
    if (!element) return;

    const handleTouchStart = (e: TouchEvent) => {
      const touch = e.touches[0];
      touchStartRef.current = {
        x: touch.clientX,
        y: touch.clientY,
        time: Date.now(),
      };
    };

    const handleTouchEnd = (e: TouchEvent) => {
      if (!touchStartRef.current) return;

      const touch = e.changedTouches[0];
      const touchEnd = {
        x: touch.clientX,
        y: touch.clientY,
        time: Date.now(),
      };

      const deltaX = touchEnd.x - touchStartRef.current.x;
      const deltaY = touchEnd.y - touchStartRef.current.y;
      const deltaTime = touchEnd.time - touchStartRef.current.time;

      // Reset touch start
      touchStartRef.current = null;

      // Check if swipe was too slow
      if (deltaTime > maxSwipeTime) return;

      // Determine if swipe is primarily horizontal or vertical
      const absX = Math.abs(deltaX);
      const absY = Math.abs(deltaY);

      // Require minimum distance
      if (absX < minSwipeDistance && absY < minSwipeDistance) return;

      // Horizontal swipe
      if (absX > absY) {
        if (deltaX > 0 && onSwipeRight) {
          onSwipeRight();
        } else if (deltaX < 0 && onSwipeLeft) {
          onSwipeLeft();
        }
      }
      // Vertical swipe
      else {
        if (deltaY > 0 && onSwipeDown) {
          onSwipeDown();
        } else if (deltaY < 0 && onSwipeUp) {
          onSwipeUp();
        }
      }
    };

    element.addEventListener('touchstart', handleTouchStart);
    element.addEventListener('touchend', handleTouchEnd);

    return () => {
      element.removeEventListener('touchstart', handleTouchStart);
      element.removeEventListener('touchend', handleTouchEnd);
    };
  }, [
    elementRef,
    onSwipeLeft,
    onSwipeRight,
    onSwipeUp,
    onSwipeDown,
    minSwipeDistance,
    maxSwipeTime,
  ]);
}
