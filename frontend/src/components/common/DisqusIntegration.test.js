import React from 'react';
import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import DisqusComments from './DisqusComments';
import CommentCount from './CommentCount';

// Clear any existing mocks
jest.unmock('../../services/disqusService');

// Mock environment variables for integration test
const originalEnv = process.env;

beforeEach(() => {
  process.env = { ...originalEnv };
  process.env.REACT_APP_DISQUS_SHORTNAME = 'fintalk-dev';
  process.env.REACT_APP_SITE_URL = 'http://localhost:3000';
});

afterEach(() => {
  process.env = originalEnv;
});

describe('Disqus Integration', () => {
  test('DisqusComments renders with proper configuration', () => {
    const props = {
      postId: '123',
      postTitle: 'Test Blog Post',
      postUrl: 'http://localhost:3000/posts/123'
    };

    render(<DisqusComments {...props} />);
    
    // Should show loading state initially
    expect(screen.getByText('Loading comments...')).toBeInTheDocument();
    expect(screen.getByTestId('loading-spinner')).toBeInTheDocument();
    
    // Should have the disqus_thread div
    expect(document.getElementById('disqus_thread')).toBeInTheDocument();
  });

  test('CommentCount renders with proper configuration', () => {
    render(<CommentCount postId="123" showZero={true} />);
    
    // Should show loading state initially
    expect(screen.getByTestId('comment-count-spinner')).toBeInTheDocument();
  });

  test('DisqusComments handles missing configuration gracefully', () => {
    delete process.env.REACT_APP_DISQUS_SHORTNAME;
    
    const props = {
      postId: '123',
      postTitle: 'Test Blog Post'
    };

    render(<DisqusComments {...props} />);
    
    // Should show fallback message
    expect(screen.getByText('Comments')).toBeInTheDocument();
    expect(screen.getByText('Comments are currently unavailable. Please check back later.')).toBeInTheDocument();
  });

  test('CommentCount handles missing configuration gracefully', () => {
    delete process.env.REACT_APP_DISQUS_SHORTNAME;
    
    const { container } = render(<CommentCount postId="123" />);
    
    // Should render nothing when not configured
    expect(container.firstChild).toBeNull();
  });
});