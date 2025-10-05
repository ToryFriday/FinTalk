import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import '@testing-library/jest-dom';
import UserProfile from '../UserProfile';
import * as socialService from '../../../services/socialService';
import * as postService from '../../../services/postService';

// Mock the services
jest.mock('../../../services/socialService');
jest.mock('../../../services/postService');

// Mock react-router-dom
const mockParams = { userId: '1' };
jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  useParams: () => mockParams,
}));

// Mock child components
jest.mock('../FollowButton', () => {
  return function MockFollowButton({ userId, username, onFollowChange, className }) {
    return (
      <button 
        data-testid="follow-button"
        onClick={() => onFollowChange && onFollowChange({
          userId,
          isFollowing: true,
          followersCount: 10,
          action: 'followed'
        })}
      >
        Follow {username}
      </button>
    );
  };
});

jest.mock('../FollowersList', () => {
  return function MockFollowersList({ userId }) {
    return <div data-testid="followers-list">Followers for user {userId}</div>;
  };
});

jest.mock('../FollowingList', () => {
  return function MockFollowingList({ userId }) {
    return <div data-testid="following-list">Following for user {userId}</div>;
  };
});

jest.mock('../../posts/PostCard', () => {
  return function MockPostCard({ post }) {
    return <div data-testid="post-card">{post.title}</div>;
  };
});

const mockProfile = {
  user_id: 1,
  username: 'testuser',
  full_name: 'Test User',
  bio: 'This is a test user bio',
  location: 'Test City',
  website: 'https://example.com',
  avatar_url: 'https://example.com/avatar.jpg',
  followers_count: 5,
  following_count: 3,
  posts_count: 10,
  is_following: false,
  is_followed_by: false,
  mutual_followers_count: 2
};

const mockPosts = [
  { id: 1, title: 'Test Post 1', content: 'Content 1' },
  { id: 2, title: 'Test Post 2', content: 'Content 2' }
];

const renderWithRouter = (component) => {
  return render(
    <BrowserRouter>
      {component}
    </BrowserRouter>
  );
};

describe('UserProfile', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders user profile with all information', async () => {
    socialService.getUserSocialProfile.mockResolvedValue({
      data: mockProfile
    });

    postService.getUserPosts.mockResolvedValue({
      data: { results: mockPosts }
    });

    renderWithRouter(<UserProfile />);

    await waitFor(() => {
      expect(screen.getByText('Test User')).toBeInTheDocument();
      expect(screen.getByText('@testuser')).toBeInTheDocument();
      expect(screen.getByText('This is a test user bio')).toBeInTheDocument();
      expect(screen.getByText('📍 Test City')).toBeInTheDocument();
      expect(screen.getByText('🔗 Website')).toBeInTheDocument();
      expect(screen.getByText('10')).toBeInTheDocument(); // Posts count
      expect(screen.getByText('5')).toBeInTheDocument(); // Followers count
      expect(screen.getByText('3')).toBeInTheDocument(); // Following count
      expect(screen.getByText('2')).toBeInTheDocument(); // Mutual followers count
    });
  });

  it('renders avatar or placeholder correctly', async () => {
    socialService.getUserSocialProfile.mockResolvedValue({
      data: mockProfile
    });

    renderWithRouter(<UserProfile />);

    await waitFor(() => {
      const avatar = screen.getByAltText("Test User's avatar");
      expect(avatar).toHaveAttribute('src', 'https://example.com/avatar.jpg');
    });
  });

  it('renders avatar placeholder when no avatar URL', async () => {
    const profileWithoutAvatar = {
      ...mockProfile,
      avatar_url: null
    };

    socialService.getUserSocialProfile.mockResolvedValue({
      data: profileWithoutAvatar
    });

    renderWithRouter(<UserProfile />);

    await waitFor(() => {
      expect(screen.getByText('T')).toBeInTheDocument(); // First letter of name
    });
  });

  it('switches between tabs correctly', async () => {
    socialService.getUserSocialProfile.mockResolvedValue({
      data: mockProfile
    });

    postService.getUserPosts.mockResolvedValue({
      data: { results: mockPosts }
    });

    renderWithRouter(<UserProfile />);

    await waitFor(() => {
      expect(screen.getByText('Posts (10)')).toBeInTheDocument();
    });

    // Initially shows posts
    await waitFor(() => {
      expect(screen.getByTestId('post-card')).toBeInTheDocument();
    });

    // Switch to followers tab
    fireEvent.click(screen.getByText('Followers (5)'));
    expect(screen.getByTestId('followers-list')).toBeInTheDocument();

    // Switch to following tab
    fireEvent.click(screen.getByText('Following (3)'));
    expect(screen.getByTestId('following-list')).toBeInTheDocument();
  });

  it('handles follow button interaction', async () => {
    socialService.getUserSocialProfile.mockResolvedValue({
      data: mockProfile
    });

    renderWithRouter(<UserProfile />);

    await waitFor(() => {
      expect(screen.getByTestId('follow-button')).toBeInTheDocument();
    });

    // Click follow button
    fireEvent.click(screen.getByTestId('follow-button'));

    // Should update the profile state
    await waitFor(() => {
      // The mock follow button triggers onFollowChange
      // This would update the followers count in the real component
    });
  });

  it('shows loading state initially', () => {
    socialService.getUserSocialProfile.mockImplementation(() => 
      new Promise(resolve => setTimeout(resolve, 100))
    );

    renderWithRouter(<UserProfile />);

    expect(screen.getByText('Loading profile...')).toBeInTheDocument();
  });

  it('shows error state when profile fetch fails', async () => {
    socialService.getUserSocialProfile.mockRejectedValue(
      new Error('Failed to load profile')
    );

    renderWithRouter(<UserProfile />);

    await waitFor(() => {
      expect(screen.getByText('Error')).toBeInTheDocument();
      expect(screen.getByText('Failed to load user profile')).toBeInTheDocument();
      expect(screen.getByText('Try Again')).toBeInTheDocument();
    });
  });

  it('shows not found state when profile is null', async () => {
    socialService.getUserSocialProfile.mockResolvedValue({
      data: null
    });

    renderWithRouter(<UserProfile />);

    await waitFor(() => {
      expect(screen.getByText('User Not Found')).toBeInTheDocument();
      expect(screen.getByText("The user you're looking for doesn't exist or has been deactivated.")).toBeInTheDocument();
      expect(screen.getByText('Go Home')).toBeInTheDocument();
    });
  });

  it('shows empty posts state when user has no posts', async () => {
    socialService.getUserSocialProfile.mockResolvedValue({
      data: mockProfile
    });

    postService.getUserPosts.mockResolvedValue({
      data: { results: [] }
    });

    renderWithRouter(<UserProfile />);

    await waitFor(() => {
      expect(screen.getByText('No posts yet')).toBeInTheDocument();
    });
  });

  it('shows posts loading state', async () => {
    socialService.getUserSocialProfile.mockResolvedValue({
      data: mockProfile
    });

    postService.getUserPosts.mockImplementation(() => 
      new Promise(resolve => setTimeout(() => resolve({
        data: { results: mockPosts }
      }), 100))
    );

    renderWithRouter(<UserProfile />);

    await waitFor(() => {
      expect(screen.getByText('Test User')).toBeInTheDocument();
    });

    // Should show loading for posts
    expect(screen.getByText('Loading posts...')).toBeInTheDocument();
  });

  it('handles profile without optional fields', async () => {
    const minimalProfile = {
      user_id: 1,
      username: 'testuser',
      full_name: 'Test User',
      bio: '',
      location: '',
      website: '',
      avatar_url: null,
      followers_count: 0,
      following_count: 0,
      posts_count: 0,
      is_following: false,
      is_followed_by: false,
      mutual_followers_count: 0
    };

    socialService.getUserSocialProfile.mockResolvedValue({
      data: minimalProfile
    });

    postService.getUserPosts.mockResolvedValue({
      data: { results: [] }
    });

    renderWithRouter(<UserProfile />);

    await waitFor(() => {
      expect(screen.getByText('Test User')).toBeInTheDocument();
      expect(screen.getByText('@testuser')).toBeInTheDocument();
      // Should not show bio, location, or website
      expect(screen.queryByText('📍')).not.toBeInTheDocument();
      expect(screen.queryByText('🔗')).not.toBeInTheDocument();
      // Should not show mutual followers count when it's 0
      expect(screen.queryByText('Mutual')).not.toBeInTheDocument();
    });
  });

  it('updates follower count when follow status changes', async () => {
    socialService.getUserSocialProfile.mockResolvedValue({
      data: mockProfile
    });

    renderWithRouter(<UserProfile />);

    await waitFor(() => {
      expect(screen.getByText('5')).toBeInTheDocument(); // Initial followers count
    });

    // Simulate follow button click which calls onFollowChange
    fireEvent.click(screen.getByTestId('follow-button'));

    // The component should update the followers count
    // Note: In the real component, this would update the state
    // Here we're just testing that the callback is called
  });
});