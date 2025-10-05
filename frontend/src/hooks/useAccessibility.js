import { useEffect, useRef, useState } from 'react';

/**
 * Custom hook for managing focus and accessibility features
 */
export const useAccessibility = () => {
  const [announcements, setAnnouncements] = useState([]);
  const announcementRef = useRef(null);

  /**
   * Announce message to screen readers
   * @param {string} message - Message to announce
   * @param {string} priority - Priority level ('polite' or 'assertive')
   */
  const announce = (message, priority = 'polite') => {
    const announcement = {
      id: Date.now(),
      message,
      priority,
      timestamp: new Date().toISOString()
    };
    
    setAnnouncements(prev => [...prev, announcement]);
    
    // Remove announcement after it's been read
    setTimeout(() => {
      setAnnouncements(prev => prev.filter(a => a.id !== announcement.id));
    }, 1000);
  };

  /**
   * Focus management for modals and dynamic content
   * @param {HTMLElement} element - Element to focus
   * @param {Object} options - Focus options
   */
  const manageFocus = (element, options = {}) => {
    if (!element) return;
    
    const { preventScroll = false, selectText = false } = options;
    
    element.focus({ preventScroll });
    
    if (selectText && element.select) {
      element.select();
    }
  };

  /**
   * Trap focus within a container (useful for modals)
   * @param {HTMLElement} container - Container element
   * @returns {Function} Cleanup function
   */
  const trapFocus = (container) => {
    if (!container) return () => {};

    const focusableElements = container.querySelectorAll(
      'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
    );
    
    const firstElement = focusableElements[0];
    const lastElement = focusableElements[focusableElements.length - 1];

    const handleTabKey = (e) => {
      if (e.key !== 'Tab') return;

      if (e.shiftKey) {
        if (document.activeElement === firstElement) {
          lastElement.focus();
          e.preventDefault();
        }
      } else {
        if (document.activeElement === lastElement) {
          firstElement.focus();
          e.preventDefault();
        }
      }
    };

    container.addEventListener('keydown', handleTabKey);
    
    // Focus first element
    if (firstElement) {
      firstElement.focus();
    }

    return () => {
      container.removeEventListener('keydown', handleTabKey);
    };
  };

  /**
   * Handle escape key for closing modals/dropdowns
   * @param {Function} callback - Function to call on escape
   * @returns {Function} Cleanup function
   */
  const useEscapeKey = (callback) => {
    useEffect(() => {
      const handleEscape = (e) => {
        if (e.key === 'Escape') {
          callback();
        }
      };

      document.addEventListener('keydown', handleEscape);
      return () => document.removeEventListener('keydown', handleEscape);
    }, [callback]);
  };

  return {
    announce,
    manageFocus,
    trapFocus,
    useEscapeKey,
    announcements,
    announcementRef
  };
};

/**
 * Hook for managing keyboard navigation
 */
export const useKeyboardNavigation = (items, onSelect) => {
  const [activeIndex, setActiveIndex] = useState(-1);

  const handleKeyDown = (e) => {
    switch (e.key) {
      case 'ArrowDown':
        e.preventDefault();
        setActiveIndex(prev => 
          prev < items.length - 1 ? prev + 1 : 0
        );
        break;
      case 'ArrowUp':
        e.preventDefault();
        setActiveIndex(prev => 
          prev > 0 ? prev - 1 : items.length - 1
        );
        break;
      case 'Enter':
      case ' ':
        e.preventDefault();
        if (activeIndex >= 0 && onSelect) {
          onSelect(items[activeIndex], activeIndex);
        }
        break;
      case 'Escape':
        setActiveIndex(-1);
        break;
      default:
        break;
    }
  };

  const resetNavigation = () => {
    setActiveIndex(-1);
  };

  return {
    activeIndex,
    handleKeyDown,
    resetNavigation,
    setActiveIndex
  };
};

/**
 * Hook for managing ARIA live regions
 */
export const useLiveRegion = () => {
  const [liveMessage, setLiveMessage] = useState('');
  const [politeness, setPoliteness] = useState('polite');

  const announce = (message, level = 'polite') => {
    setPoliteness(level);
    setLiveMessage(message);
    
    // Clear message after announcement
    setTimeout(() => {
      setLiveMessage('');
    }, 1000);
  };

  return {
    liveMessage,
    politeness,
    announce
  };
};

/**
 * Hook for detecting reduced motion preference
 */
export const useReducedMotion = () => {
  const [prefersReducedMotion, setPrefersReducedMotion] = useState(false);

  useEffect(() => {
    const mediaQuery = window.matchMedia('(prefers-reduced-motion: reduce)');
    setPrefersReducedMotion(mediaQuery.matches);

    const handleChange = (e) => {
      setPrefersReducedMotion(e.matches);
    };

    mediaQuery.addEventListener('change', handleChange);
    return () => mediaQuery.removeEventListener('change', handleChange);
  }, []);

  return prefersReducedMotion;
};

/**
 * Hook for detecting high contrast preference
 */
export const useHighContrast = () => {
  const [prefersHighContrast, setPrefersHighContrast] = useState(false);

  useEffect(() => {
    const mediaQuery = window.matchMedia('(prefers-contrast: high)');
    setPrefersHighContrast(mediaQuery.matches);

    const handleChange = (e) => {
      setPrefersHighContrast(e.matches);
    };

    mediaQuery.addEventListener('change', handleChange);
    return () => mediaQuery.removeEventListener('change', handleChange);
  }, []);

  return prefersHighContrast;
};