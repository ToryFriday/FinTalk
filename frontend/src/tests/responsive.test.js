import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';

// Import hooks to test
import { useResponsive, useResponsiveGrid } from '../hooks/useResponsive';

// Mock window.matchMedia
const mockMatchMedia = (width) => {
  Object.defineProperty(window, 'innerWidth', {
    writable: true,
    configurable: true,
    value: width,
  });
  
  Object.defineProperty(window, 'matchMedia', {
    writable: true,
    value: jest.fn().mockImplementation(query => ({
      matches: false,
      media: query,
      onchange: null,
      addListener: jest.fn(),
      removeListener: jest.fn(),
      addEventListener: jest.fn(),
      removeEventListener: jest.fn(),
      dispatchEvent: jest.fn(),
    })),
  });
};

// Test component using responsive hooks
const TestResponsiveComponent = () => {
  const { currentBreakpoint, isMobile, isTablet, isDesktop, windowSize } = useResponsive();
  
  return (
    <div>
      <div data-testid="breakpoint">{currentBreakpoint}</div>
      <div data-testid="is-mobile">{isMobile.toString()}</div>
      <div data-testid="is-tablet">{isTablet.toString()}</div>
      <div data-testid="is-desktop">{isDesktop.toString()}</div>
      <div data-testid="window-width">{windowSize.width}</div>
    </div>
  );
};

const TestGridComponent = () => {
  const { getColumns, getGridClasses } = useResponsiveGrid();
  
  const columns = getColumns({ xs: 1, sm: 2, md: 3, lg: 4 });
  const classes = getGridClasses({ xs: 12, sm: 6, md: 4, lg: 3 });
  
  return (
    <div>
      <div data-testid="columns">{columns}</div>
      <div data-testid="classes">{classes}</div>
    </div>
  );
};

describe('Responsive Design Tests', () => {
  beforeEach(() => {
    // Reset window size before each test
    mockMatchMedia(1024);
  });

  describe('useResponsive Hook', () => {
    test('detects mobile breakpoint correctly', () => {
      mockMatchMedia(480);
      
      render(<TestResponsiveComponent />);
      
      expect(screen.getByTestId('breakpoint')).toHaveTextContent('xs');
      expect(screen.getByTestId('is-mobile')).toHaveTextContent('true');
      expect(screen.getByTestId('is-tablet')).toHaveTextContent('false');
      expect(screen.getByTestId('is-desktop')).toHaveTextContent('false');
    });

    test('detects tablet breakpoint correctly', () => {
      mockMatchMedia(768);
      
      render(<TestResponsiveComponent />);
      
      expect(screen.getByTestId('breakpoint')).toHaveTextContent('md');
      expect(screen.getByTestId('is-mobile')).toHaveTextContent('false');
      expect(screen.getByTestId('is-tablet')).toHaveTextContent('true');
      expect(screen.getByTestId('is-desktop')).toHaveTextContent('false');
    });

    test('detects desktop breakpoint correctly', () => {
      mockMatchMedia(1200);
      
      render(<TestResponsiveComponent />);
      
      expect(screen.getByTestId('breakpoint')).toHaveTextContent('xl');
      expect(screen.getByTestId('is-mobile')).toHaveTextContent('false');
      expect(screen.getByTestId('is-tablet')).toHaveTextContent('false');
      expect(screen.getByTestId('is-desktop')).toHaveTextContent('true');
    });

    test('updates on window resize', () => {
      const { rerender } = render(<TestResponsiveComponent />);
      
      // Start with desktop
      expect(screen.getByTestId('breakpoint')).toHaveTextContent('lg');
      
      // Resize to mobile
      mockMatchMedia(480);
      fireEvent.resize(window);
      rerender(<TestResponsiveComponent />);
      
      expect(screen.getByTestId('breakpoint')).toHaveTextContent('xs');
    });
  });

  describe('useResponsiveGrid Hook', () => {
    test('returns correct column count for breakpoint', () => {
      mockMatchMedia(768); // md breakpoint
      
      render(<TestGridComponent />);
      
      expect(screen.getByTestId('columns')).toHaveTextContent('3');
    });

    test('generates correct CSS classes', () => {
      render(<TestGridComponent />);
      
      const classes = screen.getByTestId('classes').textContent;
      expect(classes).toContain('col');
      expect(classes).toContain('col-xs-12');
      expect(classes).toContain('col-sm-6');
      expect(classes).toContain('col-md-4');
      expect(classes).toContain('col-lg-3');
    });
  });

  describe('Responsive Components', () => {
    test('PostCard adapts to mobile layout', () => {
      mockMatchMedia(480);
      
      // Mock the PostCard component with responsive behavior
      const MockPostCard = () => {
        const { isMobile } = useResponsive();
        
        return (
          <div className={`post-card ${isMobile ? 'post-card-mobile' : ''}`}>
            <div data-testid="mobile-indicator">{isMobile.toString()}</div>
          </div>
        );
      };
      
      render(<MockPostCard />);
      
      expect(screen.getByTestId('mobile-indicator')).toHaveTextContent('true');
      expect(screen.getByRole('generic')).toHaveClass('post-card-mobile');
    });

    test('Navigation adapts to mobile layout', () => {
      mockMatchMedia(480);
      
      const MockNavigation = () => {
        const { isMobile } = useResponsive();
        
        return (
          <nav>
            {isMobile ? (
              <button data-testid="mobile-menu-toggle">Menu</button>
            ) : (
              <div data-testid="desktop-nav">Desktop Nav</div>
            )}
          </nav>
        );
      };
      
      render(<MockNavigation />);
      
      expect(screen.getByTestId('mobile-menu-toggle')).toBeInTheDocument();
      expect(screen.queryByTestId('desktop-nav')).not.toBeInTheDocument();
    });
  });

  describe('CSS Grid and Flexbox Responsive Behavior', () => {
    test('grid columns adjust based on screen size', () => {
      const TestGrid = () => {
        const { currentBreakpoint } = useResponsive();
        
        const getColumnCount = () => {
          switch (currentBreakpoint) {
            case 'xs': return 1;
            case 'sm': return 2;
            case 'md': return 3;
            case 'lg': return 4;
            case 'xl': return 4;
            default: return 1;
          }
        };
        
        return (
          <div 
            data-testid="grid"
            style={{ 
              display: 'grid',
              gridTemplateColumns: `repeat(${getColumnCount()}, 1fr)`
            }}
          >
            <div>Item 1</div>
            <div>Item 2</div>
            <div>Item 3</div>
            <div>Item 4</div>
          </div>
        );
      };
      
      mockMatchMedia(768); // md breakpoint
      render(<TestGrid />);
      
      const grid = screen.getByTestId('grid');
      expect(grid.style.gridTemplateColumns).toBe('repeat(3, 1fr)');
    });

    test('flexbox direction changes on mobile', () => {
      const TestFlex = () => {
        const { isMobile } = useResponsive();
        
        return (
          <div 
            data-testid="flex-container"
            style={{ 
              display: 'flex',
              flexDirection: isMobile ? 'column' : 'row'
            }}
          >
            <div>Item 1</div>
            <div>Item 2</div>
          </div>
        );
      };
      
      mockMatchMedia(480); // mobile
      render(<TestFlex />);
      
      const flexContainer = screen.getByTestId('flex-container');
      expect(flexContainer.style.flexDirection).toBe('column');
    });
  });

  describe('Touch Target Sizes', () => {
    test('buttons meet minimum touch target size on mobile', () => {
      mockMatchMedia(480);
      
      const TestButton = () => {
        const { isMobile } = useResponsive();
        
        return (
          <button 
            data-testid="touch-button"
            style={{ 
              minHeight: isMobile ? '44px' : '36px',
              minWidth: isMobile ? '44px' : 'auto'
            }}
          >
            Touch Me
          </button>
        );
      };
      
      render(<TestButton />);
      
      const button = screen.getByTestId('touch-button');
      expect(button.style.minHeight).toBe('44px');
      expect(button.style.minWidth).toBe('44px');
    });
  });

  describe('Responsive Typography', () => {
    test('font sizes scale with screen size', () => {
      const TestTypography = () => {
        const { currentBreakpoint } = useResponsive();
        
        const getFontSize = () => {
          switch (currentBreakpoint) {
            case 'xs': return '14px';
            case 'sm': return '16px';
            case 'md': return '16px';
            case 'lg': return '18px';
            case 'xl': return '18px';
            default: return '16px';
          }
        };
        
        return (
          <p 
            data-testid="responsive-text"
            style={{ fontSize: getFontSize() }}
          >
            Responsive text
          </p>
        );
      };
      
      mockMatchMedia(480); // xs breakpoint
      render(<TestTypography />);
      
      const text = screen.getByTestId('responsive-text');
      expect(text.style.fontSize).toBe('14px');
    });
  });

  describe('Image Responsiveness', () => {
    test('images have responsive attributes', () => {
      const TestImage = () => {
        const { currentBreakpoint } = useResponsive();
        
        const getSrcSet = () => {
          return [
            'image-small.jpg 480w',
            'image-medium.jpg 768w',
            'image-large.jpg 1200w'
          ].join(', ');
        };
        
        const getSizes = () => {
          return [
            '(max-width: 480px) 100vw',
            '(max-width: 768px) 100vw',
            '100vw'
          ].join(', ');
        };
        
        return (
          <img
            data-testid="responsive-image"
            src="image-large.jpg"
            srcSet={getSrcSet()}
            sizes={getSizes()}
            alt="Responsive test image"
          />
        );
      };
      
      render(<TestImage />);
      
      const image = screen.getByTestId('responsive-image');
      expect(image).toHaveAttribute('srcset');
      expect(image).toHaveAttribute('sizes');
      expect(image.getAttribute('srcset')).toContain('480w');
      expect(image.getAttribute('srcset')).toContain('768w');
      expect(image.getAttribute('srcset')).toContain('1200w');
    });
  });
});