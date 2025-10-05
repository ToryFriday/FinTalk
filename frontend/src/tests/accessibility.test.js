import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import '@testing-library/jest-dom';

// Import components to test
import Button from '../components/common/Button';
import FormField from '../components/common/FormField';
import Alert from '../components/common/Alert';
import Modal from '../components/common/Modal';
import Layout from '../components/layout/Layout';

// Mock hooks
jest.mock('../hooks/useAccessibility', () => ({
  useAccessibility: () => ({
    announce: jest.fn(),
    manageFocus: jest.fn(),
    trapFocus: jest.fn(() => jest.fn()),
    useEscapeKey: jest.fn()
  })
}));

jest.mock('../hooks/useResponsive', () => ({
  useResponsive: () => ({
    isMobile: false,
    isTablet: false,
    isDesktop: true,
    currentBreakpoint: 'lg'
  })
}));

// Test wrapper component
const TestWrapper = ({ children }) => (
  <BrowserRouter>
    {children}
  </BrowserRouter>
);

describe('Accessibility Tests', () => {
  describe('Button Component', () => {
    test('has proper ARIA attributes', () => {
      render(
        <Button ariaLabel="Test button" ariaDescribedBy="help-text">
          Click me
        </Button>
      );
      
      const button = screen.getByRole('button');
      expect(button).toHaveAttribute('aria-label', 'Test button');
      expect(button).toHaveAttribute('aria-describedby', 'help-text');
    });

    test('shows loading state with proper ARIA', () => {
      render(
        <Button loading loadingText="Saving...">
          Save
        </Button>
      );
      
      const button = screen.getByRole('button');
      expect(button).toHaveAttribute('aria-busy', 'true');
      expect(button).toBeDisabled();
      expect(screen.getByText('Saving...')).toBeInTheDocument();
    });

    test('meets minimum touch target size', () => {
      render(<Button>Test</Button>);
      
      const button = screen.getByRole('button');
      const styles = window.getComputedStyle(button);
      const minHeight = parseInt(styles.minHeight);
      
      expect(minHeight).toBeGreaterThanOrEqual(44);
    });

    test('is keyboard accessible', () => {
      const handleClick = jest.fn();
      render(<Button onClick={handleClick}>Test</Button>);
      
      const button = screen.getByRole('button');
      button.focus();
      fireEvent.keyDown(button, { key: 'Enter' });
      fireEvent.keyUp(button, { key: 'Enter' });
      
      expect(handleClick).toHaveBeenCalled();
    });
  });

  describe('FormField Component', () => {
    test('has proper label association', () => {
      render(
        <FormField
          label="Email Address"
          type="email"
          value=""
          onChange={() => {}}
        />
      );
      
      const input = screen.getByLabelText('Email Address');
      expect(input).toBeInTheDocument();
      expect(input).toHaveAttribute('type', 'email');
    });

    test('shows required indicator', () => {
      render(
        <FormField
          label="Required Field"
          required
          value=""
          onChange={() => {}}
        />
      );
      
      expect(screen.getByText('*')).toBeInTheDocument();
      expect(screen.getByLabelText(/required/i)).toBeInTheDocument();
    });

    test('displays error with proper ARIA', () => {
      render(
        <FormField
          label="Test Field"
          value=""
          onChange={() => {}}
          error="This field is required"
        />
      );
      
      const input = screen.getByLabelText('Test Field');
      const errorMessage = screen.getByRole('alert');
      
      expect(input).toHaveAttribute('aria-invalid', 'true');
      expect(errorMessage).toHaveTextContent('This field is required');
      expect(errorMessage).toHaveAttribute('aria-live', 'polite');
    });

    test('has help text properly associated', () => {
      render(
        <FormField
          label="Password"
          type="password"
          value=""
          onChange={() => {}}
          helpText="Must be at least 8 characters"
        />
      );
      
      const input = screen.getByLabelText('Password');
      const helpText = screen.getByText('Must be at least 8 characters');
      
      expect(input).toHaveAttribute('aria-describedby');
      expect(helpText).toBeInTheDocument();
    });
  });

  describe('Alert Component', () => {
    test('has proper role and ARIA attributes', () => {
      render(
        <Alert type="danger" title="Error">
          Something went wrong
        </Alert>
      );
      
      const alert = screen.getByRole('alert');
      expect(alert).toHaveAttribute('aria-live', 'assertive');
      expect(alert).toHaveTextContent('Something went wrong');
    });

    test('is dismissible with keyboard', () => {
      const handleDismiss = jest.fn();
      render(
        <Alert dismissible onDismiss={handleDismiss}>
          Dismissible alert
        </Alert>
      );
      
      const alert = screen.getByRole('status');
      fireEvent.keyDown(alert, { key: 'Escape' });
      
      expect(handleDismiss).toHaveBeenCalled();
    });

    test('has proper focus management', () => {
      render(
        <Alert dismissible onDismiss={() => {}}>
          Focusable alert
        </Alert>
      );
      
      const alert = screen.getByRole('status');
      expect(alert).toHaveAttribute('tabIndex', '0');
    });
  });

  describe('Modal Component', () => {
    test('has proper dialog role and ARIA attributes', () => {
      render(
        <Modal isOpen title="Test Modal" onClose={() => {}}>
          Modal content
        </Modal>
      );
      
      const modal = screen.getByRole('dialog');
      expect(modal).toHaveAttribute('aria-modal', 'true');
      expect(modal).toHaveAttribute('aria-labelledby');
      expect(modal).toHaveAttribute('aria-describedby');
    });

    test('closes on Escape key', () => {
      const handleClose = jest.fn();
      render(
        <Modal isOpen onClose={handleClose} closeOnEscape>
          Modal content
        </Modal>
      );
      
      fireEvent.keyDown(document, { key: 'Escape' });
      expect(handleClose).toHaveBeenCalled();
    });

    test('has accessible close button', () => {
      const handleClose = jest.fn();
      render(
        <Modal isOpen onClose={handleClose} title="Test Modal">
          Modal content
        </Modal>
      );
      
      const closeButton = screen.getByLabelText('Close modal');
      expect(closeButton).toBeInTheDocument();
      
      fireEvent.click(closeButton);
      expect(handleClose).toHaveBeenCalled();
    });
  });

  describe('Layout Component', () => {
    test('has proper landmark roles', () => {
      render(
        <TestWrapper>
          <Layout>
            <div>Content</div>
          </Layout>
        </TestWrapper>
      );
      
      expect(screen.getByRole('banner')).toBeInTheDocument(); // header
      expect(screen.getByRole('main')).toBeInTheDocument(); // main
      expect(screen.getByRole('contentinfo')).toBeInTheDocument(); // footer
      expect(screen.getByRole('navigation')).toBeInTheDocument(); // nav
    });

    test('has skip link for keyboard users', () => {
      render(
        <TestWrapper>
          <Layout>
            <div>Content</div>
          </Layout>
        </TestWrapper>
      );
      
      const skipLink = screen.getByText('Skip to main content');
      expect(skipLink).toBeInTheDocument();
      expect(skipLink).toHaveAttribute('href', '#main-content');
    });

    test('navigation has proper ARIA labels', () => {
      render(
        <TestWrapper>
          <Layout>
            <div>Content</div>
          </Layout>
        </TestWrapper>
      );
      
      const nav = screen.getByRole('navigation');
      expect(nav).toHaveAttribute('aria-label', 'Main navigation');
      
      const menubar = screen.getByRole('menubar');
      expect(menubar).toBeInTheDocument();
    });

    test('mobile menu is accessible', async () => {
      // Mock mobile viewport
      jest.mocked(require('../hooks/useResponsive').useResponsive).mockReturnValue({
        isMobile: true,
        isTablet: false,
        isDesktop: false,
        currentBreakpoint: 'sm'
      });

      render(
        <TestWrapper>
          <Layout>
            <div>Content</div>
          </Layout>
        </TestWrapper>
      );
      
      const menuButton = screen.getByLabelText(/navigation menu/i);
      expect(menuButton).toHaveAttribute('aria-expanded', 'false');
      expect(menuButton).toHaveAttribute('aria-controls', 'main-navigation');
      
      fireEvent.click(menuButton);
      
      await waitFor(() => {
        expect(menuButton).toHaveAttribute('aria-expanded', 'true');
      });
    });
  });

  describe('Focus Management', () => {
    test('focus is properly managed in modals', () => {
      render(
        <Modal isOpen title="Focus Test" onClose={() => {}}>
          <button>First button</button>
          <button>Second button</button>
        </Modal>
      );
      
      // Modal should be focused when opened
      const modal = screen.getByRole('dialog');
      expect(document.activeElement).toBe(modal);
    });

    test('focus returns to trigger after modal closes', async () => {
      const TestComponent = () => {
        const [isOpen, setIsOpen] = React.useState(false);
        
        return (
          <>
            <button onClick={() => setIsOpen(true)}>Open Modal</button>
            <Modal isOpen={isOpen} onClose={() => setIsOpen(false)}>
              Modal content
            </Modal>
          </>
        );
      };
      
      render(<TestComponent />);
      
      const trigger = screen.getByText('Open Modal');
      fireEvent.click(trigger);
      
      const closeButton = screen.getByLabelText('Close modal');
      fireEvent.click(closeButton);
      
      await waitFor(() => {
        expect(document.activeElement).toBe(trigger);
      });
    });
  });

  describe('Screen Reader Support', () => {
    test('has proper heading hierarchy', () => {
      render(
        <TestWrapper>
          <Layout>
            <div>
              <h2>Section Title</h2>
              <h3>Subsection</h3>
            </div>
          </Layout>
        </TestWrapper>
      );
      
      const headings = screen.getAllByRole('heading');
      expect(headings[0]).toHaveProperty('tagName', 'H1'); // Logo
      expect(headings[1]).toHaveProperty('tagName', 'H2');
      expect(headings[2]).toHaveProperty('tagName', 'H3');
    });

    test('has proper live regions', () => {
      render(
        <Alert type="success">
          Operation completed successfully
        </Alert>
      );
      
      const alert = screen.getByRole('status');
      expect(alert).toHaveAttribute('aria-live', 'polite');
    });
  });

  describe('Color Contrast and Visual Accessibility', () => {
    test('focus indicators are visible', () => {
      render(<Button>Test Button</Button>);
      
      const button = screen.getByRole('button');
      button.focus();
      
      const styles = window.getComputedStyle(button);
      expect(styles.outline).toBeTruthy();
    });

    test('supports high contrast mode', () => {
      // Mock high contrast media query
      Object.defineProperty(window, 'matchMedia', {
        writable: true,
        value: jest.fn().mockImplementation(query => ({
          matches: query === '(prefers-contrast: high)',
          media: query,
          onchange: null,
          addListener: jest.fn(),
          removeListener: jest.fn(),
          addEventListener: jest.fn(),
          removeEventListener: jest.fn(),
          dispatchEvent: jest.fn(),
        })),
      });

      render(<Button>High Contrast Button</Button>);
      
      const button = screen.getByRole('button');
      expect(button).toBeInTheDocument();
    });
  });

  describe('Reduced Motion Support', () => {
    test('respects prefers-reduced-motion', () => {
      // Mock reduce;
}); });
  })ment();
   Docu).toBeInThealertect(     exp
 status');e('yRoltBcreen.ge srt = const ale   
   
     );
      rt>       </Ale
 d be reducedion shoul  Animat     fo">
   "inpe=ty<Alert 
        der(ren       });


     })),      n(),
  nt: jest.fispatchEve       dfn(),
   tener: jest.ntLiseEve       remov  ),
  jest.fn(r:enetListddEven  a,
        jest.fn()er: removeListen
          (),: jest.fntenerddLis    a     ge: null,
 han     oncy,
     quera:         medie)',
  ducion: reced-motefers-redury === '(pres: que      match ({
    uery =>ion(qentat).mockImplemjest.fn(: ueal     v: true,
   table    wri', {
    Mediatch'ma(window, nePropertyject.defiry
      Obuemedia qd motion 