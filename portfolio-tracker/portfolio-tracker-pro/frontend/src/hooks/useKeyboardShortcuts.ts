import { useEffect, useCallback, useRef } from 'react';
import { logger } from '../utils/logger';

export interface KeyboardShortcut {
  key: string;
  ctrlKey?: boolean;
  metaKey?: boolean;
  shiftKey?: boolean;
  altKey?: boolean;
  action: () => void;
  description: string;
  category: 'navigation' | 'actions' | 'modals' | 'search';
}

interface UseKeyboardShortcutsOptions {
  enabled?: boolean;
  shortcuts: KeyboardShortcut[];
}

/**
 * Hook for managing keyboard shortcuts
 * 
 * @param options - Configuration options
 * @param options.enabled - Whether shortcuts are enabled (default: true)
 * @param options.shortcuts - Array of keyboard shortcuts to register
 * 
 * @example
 * ```tsx
 * useKeyboardShortcuts({
 *   enabled: true,
 *   shortcuts: [
 *     {
 *       key: 'r',
 *       action: () => handleRefresh(),
 *       description: 'Refresh dashboard',
 *       category: 'actions'
 *     }
 *   ]
 * });
 * ```
 */
export const useKeyboardShortcuts = ({ enabled = true, shortcuts }: UseKeyboardShortcutsOptions) => {
  const shortcutsRef = useRef(shortcuts);
  const enabledRef = useRef(enabled);

  // Update refs when props change
  useEffect(() => {
    shortcutsRef.current = shortcuts;
    enabledRef.current = enabled;
  }, [shortcuts, enabled]);

  const handleKeyDown = useCallback((event: KeyboardEvent) => {
    // Don't handle shortcuts if disabled
    if (!enabledRef.current) {
      return;
    }

    // Don't handle shortcuts when user is typing in input/textarea/contenteditable
    const target = event.target as HTMLElement;
    if (
      target.tagName === 'INPUT' ||
      target.tagName === 'TEXTAREA' ||
      target.isContentEditable
    ) {
      // Allow Escape to close modals even when typing
      if (event.key === 'Escape') {
        // Continue to check for Escape shortcuts
      } else {
        return;
      }
    }

    // Check each shortcut
    for (const shortcut of shortcutsRef.current) {
      const keyMatches = event.key.toLowerCase() === shortcut.key.toLowerCase();
      const ctrlMatches = shortcut.ctrlKey === undefined ? !event.ctrlKey : shortcut.ctrlKey === event.ctrlKey;
      const metaMatches = shortcut.metaKey === undefined ? !event.metaKey : shortcut.metaKey === event.metaKey;
      const shiftMatches = shortcut.shiftKey === undefined ? !event.shiftKey : shortcut.shiftKey === event.shiftKey;
      const altMatches = shortcut.altKey === undefined ? !event.altKey : shortcut.altKey === event.altKey;

      if (keyMatches && ctrlMatches && metaMatches && shiftMatches && altMatches) {
        event.preventDefault();
        event.stopPropagation();
        
        logger.debug(`Keyboard shortcut triggered: ${shortcut.key}`, { shortcut });
        shortcut.action();
        return;
      }
    }
  }, []);

  useEffect(() => {
    if (!enabled) {
      return;
    }

    window.addEventListener('keydown', handleKeyDown);
    
    return () => {
      window.removeEventListener('keydown', handleKeyDown);
    };
  }, [enabled, handleKeyDown]);
};

/**
 * Helper to create a keyboard shortcut
 */
export const createShortcut = (
  key: string,
  action: () => void,
  description: string,
  category: KeyboardShortcut['category'],
  options?: {
    ctrlKey?: boolean;
    metaKey?: boolean;
    shiftKey?: boolean;
    altKey?: boolean;
  }
): KeyboardShortcut => ({
  key,
  action,
  description,
  category,
  ...options,
});

/**
 * Common keyboard shortcuts configuration
 */
export const COMMON_SHORTCUTS = {
  SEARCH: (action: () => void) => createShortcut('/', action, 'Open search / command palette', 'search'),
  REFRESH: (action: () => void) => createShortcut('r', action, 'Refresh current page', 'actions'),
  GOALS: (action: () => void) => createShortcut('g', action, 'Go to Goals page', 'navigation'),
  HELP: (action: () => void) => createShortcut('?', action, 'Show keyboard shortcuts help', 'modals'),
  ESCAPE: (action: () => void) => createShortcut('Escape', action, 'Close modal / drawer', 'modals'),
  COMMAND_PALETTE: (action: () => void) => createShortcut('k', action, 'Open command palette', 'search', { ctrlKey: true, metaKey: true }),
};

