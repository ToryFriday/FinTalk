import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import '@testing-library/jest-dom';
import SavedPosts from './SavedPosts';
import BlogAPI from '../../services/api';

// Mock the BlogAPI
jest.mock('../../services/api');

// Mock react-router-dom hooks
const mockNavigate = jest.fn();
jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  useNavigate: () => mockNavigate,
  useSearchParams: () => [new URLSearchParams(), jest.fn()]
}));

// Mock SaveButton component
jest.mock('./SaveButton', () => {
  return function MockSaveButton({ postId, onSaveChange }) {
    return (
      <button
        data-testid={`save-button-${postId}`}
        onClick={() => onSaveChange && onSaveChange(postId, false)}
      >
        Mock Save Button
      </button>
    );
  };
});

const mockSavedPostsResponse = {
  success: true,
  data: {
    results: [
      {
        id: 1,
        post: 101,
        post_title: 'Test Article 1',
        post_content: 'This is the content of test article 1',
        post_author: 'John Doe',
        post_created_at: '2023-01-01T10:00:00Z',
        saved_at: '2023-01-02T10:00:00Z',
        post_tags: 'tech, programming',
        post_view_count: 150,
        notes: 'Interesting article about tech'
      },
      {
        id: 2,
        post: 102,
        post_title: 'Test Article 2',
        post_content: 'This is the content of test article 2',
        post_author: 'Jane Smith',
        post_created_at: '2023-01-03T10:00:00Z',
        saved_at: '2023-01-04T10:00:00Z',
        post_tags: 'design, ui',
        post_view_count: 75,
        notes: ''
      }
    ],
    count: 2,
    total_pages: 1,
    current_page: 1,
    page_size: 10,
    metadata: {
      total_saved: 2,
      filters_applied: {}
    }
  }
};

const renderSavedPosts = () => {
  return render(
    <BrowserRouter>
      <SavedPosts />
    </BrowserRouter>
  );
};

describe('SavedPosts', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    BlogAPI.getSavedPosts.mockResolvedValue(mockSavedPostsResponse);
  });

  it('should render loading state initially', () => {
    renderSavedPosts();
    
    expect(screen.getByText('Loading your saved articles...')).toBeInTheDocument();
  });

  it('should render saved posts after loading', async () => {
    renderSavedPosts();

    await waitFor(() => {
      expect(screen.getByText('Saved Articles')).toBeInTheDocument();
    });

    expect(screen.getByText('2 articles saved')).toBeInTheDocument();
    expect(screen.getByText('Test Article 1')).toBeInTheDocument();
    expect(screen.getByText('Test Article 2')).toBeInTheDocument();
    expect(screen.getByText('By John Doe')).toBeInTheDocument();
    expect(screen.getByText('By Jane Smith')).toBeInTheDocument();
  });

  it('should display post metadata correctly', async () => {
    renderSavedPosts();

    await waitFor(() => {
      expect(screen.getByText('Test Article 1')).toBeInTheDocument();
    });

    expect(screen.getByText('150 views')).toBeInTheDocument();
    expect(screen.getByText('75 views')).toBeInTheDocument();
    expect(screen.getByText('Notes: Interesting article about tech')).toBeInTheDocument();
  });

  it('should display tags correctly', async () => {
    renderSavedPosts();

    await waitFor(() => {
      expect(screen.getByText('Test Article 1')).toBeInTheDocument();
    });

    expect(screen.getByText('tech')).toBeInTheDocument();
    expect(screen.getByText('programming')).toBeInTheDocument();
    expect(screen.getByText('design')).toBeInTheDocument();
    expect(screen.getByText('ui')).toBeInTheDocument();
  });

  it('should handle search input', async () => {
    renderSavedPosts();

    await waitFor(() => {
      expect(screen.getByPlaceholderText('Search saved articles...')).toBeInTheDocument();
    });

    const searchInput = screen.getByPlaceholderText('Search saved articles...');
    fireEvent.change(searchInput, { target: { value: 'test search' } });

    expect(searchInput.value).toBe('test search');
  });

  it('should handle filter changes', async () => {
    renderSavedPosts();

    await waitFor(() => {
      expect(screen.getByLabelText('Tag:')).toBeInTheDocument();
    });

    const tagFilter = screen.getByLabelText('Tag:');
    fireEvent.change(tagFilter, { target: { value: 'tech' } });

    expect(tagFilter.value).toBe('tech');
  });

  it('should handle sorting changes', async () => {
    renderSavedPosts();

    await waitFor(() => {
      expect(screen.getByLabelText('Sort by:')).toBeInTheDocument();
    });

    const sortSelect = screen.getByLabelText('Sort by:');
    fireEvent.change(sortSelect, { target: { value: 'post__title' } });

    expect(sortSelect.value).toBe('post__title');
  });

  it('should navigate to post when clicked', async () => {
    renderSavedPosts();

    await waitFor(() => {
      expect(screen.getByText('Test Article 1')).toBeInTheDocument();
    });

    const postTitle = screen.getByText('Test Article 1');
    fireEvent.click(postTitle);

    expect(mockNavigate).toHaveBeenCalledWith('/posts/101');
  });

  it('should handle save button click and remove post from list', async () => {
    renderSavedPosts();

    await waitFor(() => {
      expect(screen.getByTestId('save-button-101')).toBeInTheDocument();
    });

    const saveButton = screen.getByTestId('save-button-101');
    fireEvent.click(saveButton);

    await waitFor(() => {
      expect(screen.queryByText('Test Article 1')).not.toBeInTheDocument();
    });

    expect(screen.getByText('Test Article 2')).toBeInTheDocument();
  });

  it('should display empty state when no saved posts', async () => {
    BlogAPI.getSavedPosts.mockResolvedValue({
      success: true,
      data: {
        results: [],
        count: 0,
        total_pages: 0,
        current_page: 1,
        page_size: 10,
        metadata: {
          total_saved: 0,
          filters_applied: {}
        }
      }
    });

    renderSavedPosts();

    await waitFor(() => {
      expect(screen.getByText('No saved articles found')).toBeInTheDocument();
    });

    expect(screen.getByText('Start saving articles to build your reading list!')).toBeInTheDocument();
  });

  it('should display error state when API fails', async () => {
    BlogAPI.getSavedPosts.mockResolvedValue({
      success: false,
      error: {
        type: 'API_ERROR',
        message: 'Failed to load saved articles',
        status: 500
      }
    });

    renderSavedPosts();

    await waitFor(() => {
      expect(screen.getByText('Error: Failed to load saved articles')).toBeInTheDocument();
    });

    expect(screen.getByText('Try Again')).toBeInTheDocument();
  });

  it('should handle retry button click', async () => {
    BlogAPI.getSavedPosts
      .mockResolvedValueOnce({
        success: false,
        error: {
          type: 'API_ERROR',
          message: 'Failed to load saved articles',
          status: 500
        }
      })
      .mockResolvedValueOnce(mockSavedPostsResponse);

    renderSavedPosts();

    await waitFor(() => {
      expect(screen.getByText('Try Again')).toBeInTheDocument();
    });

    const retryButton = screen.getByText('Try Again');
    fireEvent.click(retryButton);

    await waitFor(() => {
      expect(screen.getByText('Test Article 1')).toBeInTheDocument();
    });
  });

  it('should display pagination when multiple pages', async () => {
    const paginatedResponse = {
      ...mockSavedPostsResponse,
      data: {
        ...mockSavedPostsResponse.data,
        total_pages: 3,
        current_page: 2,
        next: 'http://example.com/api/posts/saved/?page=3',
        previous: 'http://example.com/api/posts/saved/?page=1'
      }
    };

    BlogAPI.getSavedPosts.mockResolvedValue(paginatedResponse);

    renderSavedPosts();

    await waitFor(() => {
      expect(screen.getByText('Page 2 of 3')).toBeInTheDocument();
    });

    expect(screen.getByText('Previous')).toBeInTheDocument();
    expect(screen.getByText('Next')).toBeInTheDocument();
  });

  it('should handle pagination button clicks', async () => {
    const paginatedResponse = {
      ...mockSavedPostsResponse,
      data: {
        ...mockSavedPostsResponse.data,
        total_pages: 3,
        current_page: 2,
        next: 'http://example.com/api/posts/saved/?page=3',
        previous: 'http://example.com/api/posts/saved/?page=1'
      }
    };

    BlogAPI.getSavedPosts.mockResolvedValue(paginatedResponse);

    renderSavedPosts();

    await waitFor(() => {
      expect(screen.getByText('Next')).toBeInTheDocument();
    });

    const nextButton = screen.getByText('Next');
    fireEvent.click(nextButton);

    // The component should call the API with updated page parameter
    await waitFor(() => {
      expect(BlogAPI.getSavedPosts).toHaveBeenCalledWith(
        expect.objectContaining({ page: 3 })
      );
    });
  });

  it('should truncate long content', async () => {
    const longContentResponse = {
      ...mockSavedPostsResponse,
      data: {
        ...mockSavedPostsResponse.data,
        results: [
          {
            ...mockSavedPostsResponse.data.results[0],
            post_content: 'A'.repeat(300) // Long content
          }
        ]
      }
    };

    BlogAPI.getSavedPosts.mockResolvedValue(longContentResponse);

    renderSavedPosts();

    await waitFor(() => {
      expect(screen.getByText(/A{200}\.{3}/)).toBeInTheDocument();
    });
  });
});