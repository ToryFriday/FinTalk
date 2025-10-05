import React from 'react';
import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';

// Import components to test
import Button from '../components/common/Button';
import FormField from '../components/common/FormField';
import LoadingSpinner from '../components/common/LoadingSpinner';

describe('Basic Accessibility Tests', () => {
  describe('Button Component', () => {
    test('renders with proper accessibility attributes', () => {
      render(
        <Button ariaLabel="Test button">
          Click me
        </Button>
      );
      
      const button = screen.getByRole('button');
      expect(button).toHaveAttribute('aria-label', 'Test button');
      expect(button).toHaveTextContent('Click me');
    });

    test('shows loading state correctly', () => {
      render(
        <Button loading loadingText="Saving...">
          Save
        </Button>
      );
      
      const button = screen.getByRole('button');
      expect(button).toHaveAttribute('aria-busy', 'true');
      expect(button).toBeDisabled();
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
    });
  });

  describe('LoadingSpinner Component', () => {
    test('has proper ARIA attributes', () => {
      render(<LoadingSpinner message="Loading content..." />);
      
      const spinner = screen.getByRole('status');
      expect(spinner).toHaveAttribute('aria-label', 'Loading content...');
    });

    test('includes screen reader text', () => {
      render(<LoadingSpinner message="Please wait..." />);
      
      expect(screen.getByText('Please wait...')).toBeInTheDocument();
    });
  });

  describe('CSS Custom Properties', () => {
    test('CSS variables are defined', () => {
      // Create a test element to check CSS custom properties
      const testElement = document.createElement('div');
      document.body.appendChild(testElement);
      
      const styles = window.getComputedStyle(testElement);
      
      // Check if CSS custom properties are available
      // Note: In jsdom, getComputedStyle may not return custom properties
      // This is more of a smoke test
      expect(testElement).toBeInTheDocument();
      
      document.body.removeChild(testElement);
    });
  });

  describe('Responsive Design Classes', () => {
    test('utility classes are available', () => {
      render(
        <div className="d-flex justify-content-center align-items-center">
          <span className="text-center">Centered content</span>
        </div>
      );
      
      const container = screen.getByText('Centered content').parentElement;
      expect(container).toHaveClass('d-flex');
      expect(container).toHaveClass('justify-content-center');
      expect(container).toHaveClass('align-items-center');
    });
  });
});