import { useEffect, useRef, useState, RefObject } from 'react';

interface UseIntersectionObserverOptions {
  threshold?: number;
  root?: Element | null;
  rootMargin?: string;
  enabled?: boolean;
}

/**
 * Hook for observing when an element enters or leaves the viewport
 * Useful for lazy loading images, components, or triggering data fetches
 */
export function useIntersectionObserver<T extends HTMLElement = HTMLDivElement>(
  options: UseIntersectionObserverOptions = {}
): [RefObject<T | null>, boolean] {
  const {
    threshold = 0.1,
    root = null,
    rootMargin = '50px', // Start loading 50px before element enters viewport
    enabled = true,
  } = options;

  const elementRef = useRef<T | null>(null);
  const [isIntersecting, setIsIntersecting] = useState(false);

  useEffect(() => {
    if (!enabled || !elementRef.current) {
      return;
    }

    const element = elementRef.current;
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          setIsIntersecting(entry.isIntersecting);
        });
      },
      {
        threshold,
        root,
        rootMargin,
      }
    );

    observer.observe(element);

    return () => {
      observer.disconnect();
    };
  }, [threshold, root, rootMargin, enabled]);

  return [elementRef, isIntersecting];
}

/**
 * Hook for observing multiple elements at once
 * Returns a map of element refs to their intersection state
 */
export function useMultipleIntersectionObserver<T extends HTMLElement = HTMLDivElement>(
  count: number,
  options: UseIntersectionObserverOptions = {}
): [RefObject<T | null>[], Map<number, boolean>] {
  const {
    threshold = 0.1,
    root = null,
    rootMargin = '50px',
    enabled = true,
  } = options;

  const refs = useRef<RefObject<T | null>[]>([]);
  const [intersectionMap, setIntersectionMap] = useState<Map<number, boolean>>(new Map());

  useEffect(() => {
    // Initialize refs when count changes
    if (refs.current.length !== count) {
      refs.current = Array.from({ length: count }, () => ({ current: null } as RefObject<T | null>));
    }
  }, [count]);

  useEffect(() => {
    if (!enabled || count === 0) {
      return;
    }

    const observer = new IntersectionObserver(
      (entries) => {
        setIntersectionMap((prev) => {
          const next = new Map(prev);
          entries.forEach((entry) => {
            const index = refs.current.findIndex((ref) => ref.current === entry.target);
            if (index !== -1) {
              next.set(index, entry.isIntersecting);
            }
          });
          return next;
        });
      },
      {
        threshold,
        root,
        rootMargin,
      }
    );

    refs.current.forEach((ref) => {
      if (ref.current) {
        observer.observe(ref.current);
      }
    });

    return () => {
      observer.disconnect();
    };
  }, [count, threshold, root, rootMargin, enabled]);

  return [refs.current, intersectionMap];
}

