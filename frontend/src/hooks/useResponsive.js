import { useState, useEffect } from 'react';

/**
 * Breakpoint values matching CSS custom properties
 */
const BREAKPOINTS = {
  xs: 0,
  sm: 576,
  md: 768,
  lg: 992,
  xl: 1200
};

/**
 * Hook for responsive design utilities
 */
export const useResponsive = () => {
  const [windowSize, setWindowSize] = useState({
    width: typeof window !== 'undefined' ? window.innerWidth : 0,
    height: typeof window !== 'undefined' ? window.innerHeight : 0
  });

  const [currentBreakpoint, setCurrentBreakpoint] = useState('xs');

  useEffect(() => {
    const handleResize = () => {
      const width = window.innerWidth;
      const height = window.innerHeight;
      
      setWindowSize({ width, height });

      // Determine current breakpoint
      if (width >= BREAKPOINTS.xl) {
        setCurrentBreakpoint('xl');
      } else if (width >= BREAKPOINTS.lg) {
        setCurrentBreakpoint('lg');
      } else if (width >= BREAKPOINTS.md) {
        setCurrentBreakpoint('md');
      } else if (width >= BREAKPOINTS.sm) {
        setCurrentBreakpoint('sm');
      } else {
        setCurrentBreakpoint('xs');
      }
    };

    // Set initial values
    handleResize();

    // Add event listener
    window.addEventListener('resize', handleResize);

    // Cleanup
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  /**
   * Check if current screen size is at or above specified breakpoint
   * @param {string} breakpoint - Breakpoint name (xs, sm, md, lg, xl)
   * @returns {boolean}
   */
  const isAbove = (breakpoint) => {
    return windowSize.width >= BREAKPOINTS[breakpoint];
  };

  /**
   * Check if current screen size is below specified breakpoint
   * @param {string} breakpoint - Breakpoint name (xs, sm, md, lg, xl)
   * @returns {boolean}
   */
  const isBelow = (breakpoint) => {
    return windowSize.width < BREAKPOINTS[breakpoint];
  };

  /**
   * Check if current screen size is between two breakpoints
   * @param {string} min - Minimum breakpoint
   * @param {string} max - Maximum breakpoint
   * @returns {boolean}
   */
  const isBetween = (min, max) => {
    return windowSize.width >= BREAKPOINTS[min] && windowSize.width < BREAKPOINTS[max];
  };

  /**
   * Get responsive value based on current breakpoint
   * @param {Object} values - Object with breakpoint keys and values
   * @returns {*} Value for current breakpoint
   */
  const getResponsiveValue = (values) => {
    const breakpoints = ['xl', 'lg', 'md', 'sm', 'xs'];
    
    for (const bp of breakpoints) {
      if (values[bp] !== undefined && isAbove(bp)) {
        return values[bp];
      }
    }
    
    // Fallback to xs or first available value
    return values.xs || values[Object.keys(values)[0]];
  };

  return {
    windowSize,
    currentBreakpoint,
    isAbove,
    isBelow,
    isBetween,
    getResponsiveValue,
    isMobile: isBelow('md'),
    isTablet: isBetween('md', 'lg'),
    isDesktop: isAbove('lg')
  };
};

/**
 * Hook for managing responsive grid columns
 */
export const useResponsiveGrid = (defaultCols = 1) => {
  const { currentBreakpoint, getResponsiveValue } = useResponsive();

  /**
   * Calculate responsive columns
   * @param {Object|number} columns - Column configuration or number
   * @returns {number} Number of columns for current breakpoint
   */
  const getColumns = (columns) => {
    if (typeof columns === 'number') {
      return columns;
    }

    return getResponsiveValue({
      xs: 1,
      sm: 2,
      md: 3,
      lg: 4,
      xl: 4,
      ...columns
    });
  };

  /**
   * Generate responsive grid classes
   * @param {Object} config - Grid configuration
   * @returns {string} CSS classes
   */
  const getGridClasses = (config = {}) => {
    const classes = ['col'];
    
    Object.entries(config).forEach(([breakpoint, value]) => {
      if (BREAKPOINTS[breakpoint] !== undefined) {
        classes.push(`col-${breakpoint}-${value}`);
      }
    });

    return classes.join(' ');
  };

  return {
    currentBreakpoint,
    getColumns,
    getGridClasses
  };
};

/**
 * Hook for responsive image loading
 */
export const useResponsiveImage = () => {
  const { windowSize, currentBreakpoint } = useResponsive();

  /**
   * Generate responsive image sources
   * @param {Object} sources - Image sources by breakpoint
   * @returns {Object} Responsive image configuration
   */
  const getResponsiveImage = (sources) => {
    const { xs, sm, md, lg, xl, alt = '', ...props } = sources;

    const srcSet = [];
    const sizes = [];

    if (xs) {
      srcSet.push(`${xs} 576w`);
      sizes.push('(max-width: 576px) 100vw');
    }
    if (sm) {
      srcSet.push(`${sm} 768w`);
      sizes.push('(max-width: 768px) 100vw');
    }
    if (md) {
      srcSet.push(`${md} 992w`);
      sizes.push('(max-width: 992px) 100vw');
    }
    if (lg) {
      srcSet.push(`${lg} 1200w`);
      sizes.push('(max-width: 1200px) 100vw');
    }
    if (xl) {
      srcSet.push(`${xl} 1400w`);
      sizes.push('100vw');
    }

    return {
      src: xl || lg || md || sm || xs,
      srcSet: srcSet.join(', '),
      sizes: sizes.join(', '),
      alt,
      ...props
    };
  };

  return {
    getResponsiveImage,
    currentBreakpoint
  };
};

/**
 * Hook for responsive text sizing
 */
export const useResponsiveText = () => {
  const { getResponsiveValue } = useResponsive();

  /**
   * Get responsive font size
   * @param {Object} sizes - Font sizes by breakpoint
   * @returns {string} CSS font size
   */
  const getFontSize = (sizes) => {
    return getResponsiveValue({
      xs: '0.875rem',
      sm: '1rem',
      md: '1rem',
      lg: '1.125rem',
      xl: '1.125rem',
      ...sizes
    });
  };

  /**
   * Get responsive line height
   * @param {Object} heights - Line heights by breakpoint
   * @returns {string} CSS line height
   */
  const getLineHeight = (heights) => {
    return getResponsiveValue({
      xs: '1.4',
      sm: '1.5',
      md: '1.6',
      lg: '1.6',
      xl: '1.6',
      ...heights
    });
  };

  return {
    getFontSize,
    getLineHeight
  };
};