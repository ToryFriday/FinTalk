import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import CommentCount from './CommentCount';
import disqusService from '../../services/disqusService';

// Mock the disqusService
jest.mock('../../services/disqusService', () => ({
  isConfigured: jest.fn(),
  getCommentCount: jest.fn(),
  getPostIdentifier: jest.fn()
}));

describe('CommentCount', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    disqusService.getPostIdentifier.mockImplementation((postId, slug) => slug || `post-${postId}`);
  });

  test('renders nothing when Disqus is not configured', () => {
    disqusService.isConfigured.mockReturnValue(false);
    
    const { container } = render(<CommentCount postId="123" />);
    
    expect(container.firstChild).toBeNull();
  });

  test('shows loading spinner initially when configured', () => {
    disqusService.isConfigured.mockReturnValue(true);
    disqusService.getCommentCount.mockReturnValue(new Promise(() => {})); // Never resolves
    
    render(<CommentCount postId="123" />);
    
    expect(screen.getByRole('generic')).toHaveClass('comment-count-spinner');
  });

  test('displays comment count when loaded', async () => {
    disqusService.isConfigured.mockReturnValue(true);
    disqusService.getCommentCount.mockResolvedValue(5);
    
    render(<CommentCount postId="123" />);
    
    await waitFor(() => {
      expect(screen.getByText('5')).toBeInTheDocument();
      expect(screen.getByText('comments')).toBeInTheDocument();
    });
  });

  test('displays singular "comment" for count of 1', async () => {
    disqusService.isConfigured.mockReturnValue(true);
    disqusService.getCommentCount.mockResolvedValue(1);
    
    render(<CommentCount postId="123" />);
    
    await waitFor(() => {
      expect(screen.getByText('1')).toBeInTheDocument();
      expect(screen.getByText('comment')).toBeInTheDocument();
    });
  });

  test('displays "0 comments" when showZero is true', async () => {
    disqusService.isConfigured.mockReturnValue(true);
    disqusService.getCommentCount.mockResolvedValue(0);
    
    render(<CommentCount postId="123" showZero={true} />);
    
    await waitFor(() => {
      expect(screen.getByText('0')).toBeInTheDocument();
      expect(screen.getByText('comments')).toBeInTheDocument();
    });
  });

  test('renders nothing when count is 0 and showZero is false', async () => {
    disqusService.isConfigured.mockReturnValue(true);
    disqusService.getCommentCount.mockResolvedValue(0);
    
    const { container } = render(<CommentCount postId="123" showZero={false} />);
    
    await waitFor(() => {
      expect(container.firstChild).toBeNull();
    });
  });

  test('applies custom className', async () => {
    disqusService.isConfigured.mockReturnValue(true);
    disqusService.getCommentCount.mockResolvedValue(3);
    
    render(<CommentCount postId="123" className="custom-class" />);
    
    await waitFor(() => {
      expect(screen.getByText('3').closest('.comment-count')).toHaveClass('custom-class');
    });
  });

  test('uses custom postSlug when provided', async () => {
    disqusService.isConfigured.mockReturnValue(true);
    disqusService.getCommentCount.mockResolvedValue(2);
    
    render(<CommentCount postId="123" postSlug="custom-slug" />);
    
    await waitFor(() => {
      expect(disqusService.getCommentCount).toHaveBeenCalledWith("123", "custom-slug");
    });
  });

  test('handles error gracefully', async () => {
    disqusService.isConfigured.mockReturnValue(true);
    disqusService.getCommentCount.mockRejectedValue(new Error('Network error'));
    
    render(<CommentCount postId="123" />);
    
    await waitFor(() => {
      expect(screen.getByText('0')).toBeInTheDocument();
      expect(screen.getByText('comments')).toBeInTheDocument();
    });
  });

  test('sets correct data-disqus-identifier attribute', async () => {
    disqusService.isConfigured.mockReturnValue(true);
    disqusService.getCommentCount.mockResolvedValue(4);
    
    render(<CommentCount postId="123" />);
    
    await waitFor(() => {
      const element = screen.getByText('4').closest('.comment-count');
      expect(element).toHaveAttribute('data-disqus-identifier', 'post-123');
    });
  });

  test('cleanup prevents state updates after unmount', async () => {
    disqusService.isConfigured.mockReturnValue(true);
    
    let resolvePromise;
    const promise = new Promise((resolve) => {
      resolvePromise = resolve;
    });
    disqusService.getCommentCount.mockReturnValue(promise);
    
    const { unmount } = render(<CommentCount postId="123" />);
    
    unmount();
    
    // Resolve promise after unmount
    resolvePromise(5);
    
    // Should not cause any errors or warnings
    await waitFor(() => {
      // Just wait a bit to ensure no state updates occur
    }, { timeout: 100 });
  });
});