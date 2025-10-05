import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import FollowButton from '../FollowButton';
import * as socialService from '../../../services/socialService';

// Mock the social service
jest.mock('../../../services/socialService');

describe('FollowButton', () => {
  const mockProps = {
    userId: 1,
    username: 'testuser',
    onFollowChange: jest.fn(),
    className: 'test-class'
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders follow button when not following', async () => {
    socialService.checkFollowStatus.mockResolvedValue({
      data: {
        is_following: false,
        followers_count: 5
      }
    });

    render(<FollowButton {...mockProps} />);

    await waitFor(() => {
      expect(screen.getByText('Follow')).toBeInTheDocument();
      expect(screen.getByText('5 followers')).toBeInTheDocument();
    });
  });

  it('renders following button when already following', async () => {
    socialService.checkFollowStatus.mockResolvedValue({
      data: {
        is_following: true,
        followers_count: 6
      }
    });

    render(<FollowButton {...mockProps} />);

    await waitFor(() => {
      expect(screen.getByText('Following')).toBeInTheDocument();
      expect(screen.getByText('6 followers')).toBeInTheDocument();
    });
  });

  it('handles follow action correctly', async () => {
    socialService.checkFollowStatus.mockResolvedValue({
      data: {
        is_following: false,
        followers_count: 5
      }
    });

    socialService.followUser.mockResolvedValue({
      data: {
        is_following: true,
        followers_count: 6,
        action: 'followed'
      }
    });

    render(<FollowButton {...mockProps} />);

    await waitFor(() => {
      expect(screen.getByText('Follow')).toBeInTheDocument();
    });

    const followButton = screen.getByRole('button');
    fireEvent.click(followButton);

    await waitFor(() => {
      expect(socialService.followUser).toHaveBeenCalledWith(1);
      expect(mockProps.onFollowChange).toHaveBeenCalledWith({
        userId: 1,
        isFollowing: true,
        followersCount: 6,
        action: 'followed'
      });
    });
  });

  it('handles unfollow action correctly', async () => {
    socialService.checkFollowStatus.mockResolvedValue({
      data: {
        is_following: true,
        followers_count: 6
      }
    });

    socialService.unfollowUser.mockResolvedValue({
      data: {
        is_following: false,
        followers_count: 5,
        action: 'unfollowed'
      }
    });

    render(<FollowButton {...mockProps} />);

    await waitFor(() => {
      expect(screen.getByText('Following')).toBeInTheDocument();
    });

    const followButton = screen.getByRole('button');
    fireEvent.click(followButton);

    await waitFor(() => {
      expect(socialService.unfollowUser).toHaveBeenCalledWith(1);
      expect(mockProps.onFollowChange).toHaveBeenCalledWith({
        userId: 1,
        isFollowing: false,
        followersCount: 5,
        action: 'unfollowed'
      });
    });
  });

  it('shows loading state during API call', async () => {
    socialService.checkFollowStatus.mockResolvedValue({
      data: {
        is_following: false,
        followers_count: 5
      }
    });

    // Mock a delayed response
    socialService.followUser.mockImplementation(() => 
      new Promise(resolve => setTimeout(() => resolve({
        data: { is_following: true, followers_count: 6 }
      }), 100))
    );

    render(<FollowButton {...mockProps} />);

    await waitFor(() => {
      expect(screen.getByText('Follow')).toBeInTheDocument();
    });

    const followButton = screen.getByRole('button');
    fireEvent.click(followButton);

    // Should show loading state
    expect(followButton).toHaveClass('loading');
    expect(followButton).toBeDisabled();
  });

  it('handles API errors gracefully', async () => {
    socialService.checkFollowStatus.mockResolvedValue({
      data: {
        is_following: false,
        followers_count: 5
      }
    });

    socialService.followUser.mockRejectedValue({
      response: {
        data: {
          error: 'Failed to follow user'
        }
      }
    });

    render(<FollowButton {...mockProps} />);

    await waitFor(() => {
      expect(screen.getByText('Follow')).toBeInTheDocument();
    });

    const followButton = screen.getByRole('button');
    fireEvent.click(followButton);

    await waitFor(() => {
      expect(screen.getByText('Failed to follow user')).toBeInTheDocument();
      expect(screen.getByTitle('Retry')).toBeInTheDocument();
    });
  });

  it('retries after error', async () => {
    socialService.checkFollowStatus.mockResolvedValue({
      data: {
        is_following: false,
        followers_count: 5
      }
    });

    socialService.followUser.mockRejectedValueOnce({
      response: {
        data: {
          error: 'Network error'
        }
      }
    });

    render(<FollowButton {...mockProps} />);

    await waitFor(() => {
      expect(screen.getByText('Follow')).toBeInTheDocument();
    });

    const followButton = screen.getByRole('button');
    fireEvent.click(followButton);

    await waitFor(() => {
      expect(screen.getByText('Network error')).toBeInTheDocument();
    });

    // Click retry button
    const retryButton = screen.getByTitle('Retry');
    fireEvent.click(retryButton);

    await waitFor(() => {
      expect(screen.getByText('Follow')).toBeInTheDocument();
    });
  });

  it('displays correct follower count format', async () => {
    socialService.checkFollowStatus.mockResolvedValue({
      data: {
        is_following: false,
        followers_count: 1
      }
    });

    render(<FollowButton {...mockProps} />);

    await waitFor(() => {
      expect(screen.getByText('1 follower')).toBeInTheDocument();
    });
  });

  it('handles zero followers correctly', async () => {
    socialService.checkFollowStatus.mockResolvedValue({
      data: {
        is_following: false,
        followers_count: 0
      }
    });

    render(<FollowButton {...mockProps} />);

    await waitFor(() => {
      expect(screen.getByText('Follow')).toBeInTheDocument();
      expect(screen.queryByText('0 followers')).not.toBeInTheDocument();
    });
  });

  it('applies custom className', async () => {
    socialService.checkFollowStatus.mockResolvedValue({
      data: {
        is_following: false,
        followers_count: 5
      }
    });

    render(<FollowButton {...mockProps} />);

    await waitFor(() => {
      const container = screen.getByText('Follow').closest('.follow-button-container');
      expect(container).toHaveClass('test-class');
    });
  });

  it('handles missing onFollowChange prop', async () => {
    socialService.checkFollowStatus.mockResolvedValue({
      data: {
        is_following: false,
        followers_count: 5
      }
    });

    socialService.followUser.mockResolvedValue({
      data: {
        is_following: true,
        followers_count: 6
      }
    });

    const propsWithoutCallback = {
      userId: 1,
      username: 'testuser'
    };

    render(<FollowButton {...propsWithoutCallback} />);

    await waitFor(() => {
      expect(screen.getByText('Follow')).toBeInTheDocument();
    });

    const followButton = screen.getByRole('button');
    fireEvent.click(followButton);

    await waitFor(() => {
      expect(socialService.followUser).toHaveBeenCalledWith(1);
      // Should not throw error even without callback
    });
  });
});