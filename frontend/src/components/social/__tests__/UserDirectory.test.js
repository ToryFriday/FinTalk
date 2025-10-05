import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import UserDirectory from '../UserDirectory';
import { searchUsersToFollow, getSuggestedUsers } from '../../../services/socialService';

// Mock the social service
jest.mock('../../../services/socialService');

const mockUsers = [
  {
    user_id: 1,
    username: 'writer1',
    full_name: 'John Writer',
    bio: 'Financial writer and analyst',
    avatar_url: null,
    role: 'writer',
    posts_count: 15,
    followers_count: 120,
    is_following: false,
    mutual_followers_count: 5
  },
  {
    user_id: 2,
    username: 'editor1',
    full_name: 'Jane Editor',
    bio: 'Senior financial editor',
    avatar_url: 'https://example.com/avatar.jpg',
    role: 'editor',
    posts_count: 8,
    followers_count: 200,
    is_following: true,
    mutual_followers_count: 0
  }
];

const renderUserDirectory = () => {
  return render(
    <BrowserRouter>
      <UserDirectory />
    </BrowserRouter>
  );
};

describe('UserDirectory Component', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    getSuggestedUsers.mockResolvedValue({ data: { results: mockUsers } });
    searchUsersToFollow.mockResolvedValue({ data: { results: mockUsers } });
  });

  test('renders user directory with header', () => {
    renderUserDirectory();
    
    expect(screen.getByText('Discover Writers')).toBeInTheDocument();
    expect(screen.getByText('Find and follow interesting writers in the FinTalk community')).toBeInTheDocument();
  });

  test('loads suggested users on mount', async () => {
    renderUserDirectory();
    
    await waitFor(() => {
      expect(getSuggestedUsers).toHaveBeenCalledWith({ limit: 12 });
    });
    
    expect(screen.getByText('John Writer')).toBeInTheDocument();
    expect(screen.getByText('Jane Editor')).toBeInTheDocument();
  });

  test('switches to search tab when typing in search input', async () => {
    renderUserDirectory();
    
    const searchInput = screen.getByPlaceholderText('Search for writers...');
    fireEvent.change(searchInput, { target: { value: 'john' } });
    
    // Should automatically switch to search tab
    await waitFor(() => {
      expect(screen.getByText('Search Results (2)')).toBeInTheDocument();
    });
  });

  test('performs search with debouncing', async () => {
    renderUserDirectory();
    
    const searchInput = screen.getByPlaceholderText('Search for writers...');
    fireEvent.change(searchInput, { target: { value: 'writer' } });
    
    // Should debounce the search
    await waitFor(() => {
      expect(searchUsersToFollow).toHaveBeenCalledWith('writer', expect.any(Object));
    }, { timeout: 500 });
  });

  test('applies role filter', async () => {
    renderUserDirectory();
    
    const roleSelect = screen.getByDisplayValue('All Users');
    fireEvent.change(roleSelect, { target: { value: 'writer' } });
    
    const searchInput = screen.getByPlaceholderText('Search for writers...');
    fireEvent.change(searchInput, { target: { value: 'test' } });
    
    await waitFor(() => {
      expect(searchUsersToFollow).toHaveBeenCalledWith('test', 
        expect.objectContaining({ role: 'writer' })
      );
    });
  });

  test('applies sort filter', async () => {
    renderUserDirectory();
    
    const sortSelect = screen.getByDisplayValue('Most Followers');
    fireEvent.change(sortSelect, { target: { value: 'posts' } });
    
    const searchInput = screen.getByPlaceholderText('Search for writers...');
    fireEvent.change(searchInput, { target: { value: 'test' } });
    
    await waitFor(() => {
      expect(searchUsersToFollow).toHaveBeenCalledWith('test', 
        expect.objectContaining({ ordering: '-posts_count' })
      );
    });
  });

  test('displays user cards with correct information', async () => {
    renderUserDirectory();
    
    await waitFor(() => {
      expect(screen.getByText('John Writer')).toBeInTheDocument();
    });
    
    expect(screen.getByText('@writer1')).toBeInTheDocument();
    expect(screen.getByText('Financial writer and analyst')).toBeInTheDocument();
    expect(screen.getByText('Writer')).toBeInTheDocument();
    expect(screen.getByText('15')).toBeInTheDocument(); // Posts count
    expect(screen.getByText('120')).toBeInTheDocument(); // Followers count
  });

  test('shows mutual followers when available', async () => {
    renderUserDirectory();
    
    await waitFor(() => {
      expect(screen.getByText('5')).toBeInTheDocument(); // Mutual followers for first user
    });
    
    expect(screen.getByText('Mutual')).toBeInTheDocument();
  });

  test('handles loading state', () => {
    getSuggestedUsers.mockImplementation(() => new Promise(() => {})); // Never resolves
    
    renderUserDirectory();
    
    expect(screen.getByText('Loading suggested users...')).toBeInTheDocument();
  });

  test('handles error state', async () => {
    getSuggestedUsers.mockRejectedValue(new Error('Failed to load'));
    
    renderUserDirectory();
    
    await waitFor(() => {
      expect(screen.getByText('Failed to load suggested users.')).toBeInTheDocument();
    });
  });

  test('shows empty state for no suggestions', async () => {
    getSuggestedUsers.mockResolvedValue({ data: { results: [] } });
    
    renderUserDirectory();
    
    await waitFor(() => {
      expect(screen.getByText('No suggestions available')).toBeInTheDocument();
    });
  });

  test('shows empty state for no search results', async () => {
    searchUsersToFollow.mockResolvedValue({ data: { results: [] } });
    
    renderUserDirectory();
    
    const searchInput = screen.getByPlaceholderText('Search for writers...');
    fireEvent.change(searchInput, { target: { value: 'nonexistent' } });
    
    await waitFor(() => {
      expect(screen.getByText('No users found')).toBeInTheDocument();
    });
  });

  test('navigates to user profile when clicking user name', async () => {
    renderUserDirectory();
    
    await waitFor(() => {
      expect(screen.getByText('John Writer')).toBeInTheDocument();
    });
    
    const userLink = screen.getByText('John Writer').closest('a');
    expect(userLink).toHaveAttribute('href', '/profile/1');
  });

  test('displays avatar or placeholder correctly', async () => {
    renderUserDirectory();
    
    await waitFor(() => {
      // First user has no avatar, should show placeholder
      expect(screen.getByText('J')).toBeInTheDocument(); // First letter of name
      
      // Second user has avatar
      const avatarImg = screen.getByAltText("Jane Editor's avatar");
      expect(avatarImg).toHaveAttribute('src', 'https://example.com/avatar.jpg');
    });
  });

  test('switches between tabs correctly', async () => {
    renderUserDirectory();
    
    // Should start on suggested tab
    expect(screen.getByText('Suggested for You')).toHaveClass('active');
    
    // Click search tab
    fireEvent.click(screen.getByText(/Search Results/));
    
    expect(screen.getByText(/Search Results/)).toHaveClass('active');
    expect(screen.getByText('Suggested for You')).not.toHaveClass('active');
  });
});