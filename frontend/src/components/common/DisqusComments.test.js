import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import DisqusComments from './DisqusComments';

// Mock environment variables
const originalEnv = process.env;

beforeEach(() => {
  jest.resetModules();
  process.env = { ...originalEnv };
  
  // Clear any existing Disqus scripts
  const existingScripts = document.querySelectorAll('script[src*="disqus.com"]');
  existingScripts.forEach(script => script.remove());
  
  // Clear Disqus global variables
  delete window.DISQUS;
  delete window.disqus_config;
});

afterEach(() => {
  process.env = originalEnv;
});

describe('DisqusComments', () => {
  const defaultProps = {
    postId: '123',
    postTitle: 'Test Post Title',
    postUrl: 'https://example.com/posts/123'
  };

  test('renders fallback message when Disqus shortname is not configured', () => {
    // Don't set REACT_APP_DISQUS_SHORTNAME
    render(<DisqusComments {...defaultProps} />);
    
    expect(screen.getByText('Comments')).toBeInTheDocument();
    expect(screen.getByText('Comments are currently unavailable. Please check back later.')).toBeInTheDocument();
  });

  test('renders loading state initially when Disqus is configured', () => {
    process.env.REACT_APP_DISQUS_SHORTNAME = 'test-shortname';
    
    render(<DisqusComments {...defaultProps} />);
    
    expect(screen.getByText('Loading comments...')).toBeInTheDocument();
    expect(screen.getByTestId('loading-spinner')).toBeInTheDocument();
  });

  test('creates Disqus script with correct shortname', async () => {
    process.env.REACT_APP_DISQUS_SHORTNAME = 'test-shortname';
    
    render(<DisqusComments {...defaultProps} />);
    
    await waitFor(() => {
      const script = document.querySelector('script[src*="test-shortname.disqus.com/embed.js"]');
      expect(script).toBeInTheDocument();
    });
  });

  test('sets up disqus_config correctly', async () => {
    process.env.REACT_APP_DISQUS_SHORTNAME = 'test-shortname';
    
    render(<DisqusComments {...defaultProps} />);
    
    await waitFor(() => {
      expect(window.disqus_config).toBeDefined();
    });
    
    // Mock the disqus_config function call
    const mockThis = {
      page: {},
      callbacks: { onReady: [], onError: [] }
    };
    
    window.disqus_config.call(mockThis);
    
    expect(mockThis.page.url).toBe('https://example.com/posts/123');
    expect(mockThis.page.identifier).toBe('post-123');
    expect(mockThis.page.title).toBe('Test Post Title');
  });

  test('uses custom postSlug when provided', async () => {
    process.env.REACT_APP_DISQUS_SHORTNAME = 'test-shortname';
    
    render(<DisqusComments {...defaultProps} postSlug="custom-slug" />);
    
    await waitFor(() => {
      expect(window.disqus_config).toBeDefined();
    });
    
    const mockThis = {
      page: {},
      callbacks: { onReady: [], onError: [] }
    };
    
    window.disqus_config.call(mockThis);
    
    expect(mockThis.page.identifier).toBe('custom-slug');
  });

  test('generates correct URL when postUrl is not provided', async () => {
    process.env.REACT_APP_DISQUS_SHORTNAME = 'test-shortname';
    process.env.REACT_APP_SITE_URL = 'https://mysite.com';
    
    const propsWithoutUrl = {
      postId: '123',
      postTitle: 'Test Post Title'
    };
    
    render(<DisqusComments {...propsWithoutUrl} />);
    
    await waitFor(() => {
      expect(window.disqus_config).toBeDefined();
    });
    
    const mockThis = {
      page: {},
      callbacks: { onReady: [], onError: [] }
    };
    
    window.disqus_config.call(mockThis);
    
    expect(mockThis.page.url).toBe('https://mysite.com/posts/123');
  });

  test('shows error fallback when script fails to load', async () => {
    process.env.REACT_APP_DISQUS_SHORTNAME = 'test-shortname';
    
    render(<DisqusComments {...defaultProps} />);
    
    // Simulate script error
    await waitFor(() => {
      const script = document.querySelector('script[src*="disqus.com"]');
      expect(script).toBeInTheDocument();
      
      // Trigger error event
      const errorEvent = new Event('error');
      script.dispatchEvent(errorEvent);
    });
    
    await waitFor(() => {
      expect(screen.getByText('Comments are temporarily unavailable. Please try refreshing the page or check back later.')).toBeInTheDocument();
      expect(screen.getByText('Retry')).toBeInTheDocument();
    });
  });

  test('renders noscript fallback when loaded', async () => {
    process.env.REACT_APP_DISQUS_SHORTNAME = 'test-shortname';
    
    render(<DisqusComments {...defaultProps} />);
    
    // Mock successful load
    await waitFor(() => {
      const script = document.querySelector('script[src*="disqus.com"]');
      expect(script).toBeInTheDocument();
    });
    
    // Simulate onReady callback
    if (window.disqus_config) {
      const mockThis = {
        page: {},
        callbacks: { onReady: [jest.fn()], onError: [] }
      };
      window.disqus_config.call(mockThis);
      mockThis.callbacks.onReady[0]();
    }
    
    await waitFor(() => {
      expect(screen.getByTestId('noscript-message')).toBeInTheDocument();
    });
  });

  test('handles missing required props gracefully', () => {
    process.env.REACT_APP_DISQUS_SHORTNAME = 'test-shortname';
    
    // Missing postTitle
    render(<DisqusComments postId="123" />);
    
    expect(screen.getByText('Comments are temporarily unavailable. Please try refreshing the page or check back later.')).toBeInTheDocument();
  });

  test('resets Disqus when props change', async () => {
    process.env.REACT_APP_DISQUS_SHORTNAME = 'test-shortname';
    
    const { rerender } = render(<DisqusComments {...defaultProps} />);
    
    // Mock DISQUS object
    window.DISQUS = {
      reset: jest.fn()
    };
    
    // Change props
    rerender(<DisqusComments {...defaultProps} postId="456" postTitle="New Title" />);
    
    await waitFor(() => {
      expect(window.DISQUS.reset).toHaveBeenCalledWith({
        reload: true,
        config: expect.any(Function)
      });
    });
  });
});