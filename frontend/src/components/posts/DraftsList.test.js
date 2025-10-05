import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import DraftsList from './DraftsList';
import BlogAPI from '../../services/api';

// Mock the API
jest.mock('../../services/api');

// Mock the common components
jest.mock('../common/LoadingSpinner', () => {
  return function LoadingSpinner({ message }) {
    return <div data-testid="loading-spinner">{message}</div>;
  };
});

jest.mock('../common/ErrorMessage', () => {
  return function ErrorMessage({ error }) {
    return <div data-testid="error-message">{error.message}</div>;
  };
});

const renderWithRouter = (component) => {
  return render(
    <BrowserRouter>
      {component}
    </BrowserRouter>
  );
};

describe('DraftsList Component', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  test('renders loading state initially', () => {
    BlogAPI.getDraftPosts.mockImplementation(() => new Promise(() => {})); // Never resolves
    
    renderWithRouter(<DraftsList />);
    
    expect(screen.getByTestId('loading-spinner')).toBeInTheDocument();
    expect(screen.getByText('Loading drafts...')).toBeInTheDocument();
  });

  test('renders empty state when no drafts', async () => {
    BlogAPI.getDraftPosts.mockResolvedValue({
      success: true,
      data: {
        results: [],
        count: 0
      }
    });

    renderWithRouter(<DraftsList />);

    await waitFor(() => {
      expect(screen.getByText("You don't have any draft posts yet.")).toBeInTheDocument();
    });
  });

  test('renders drafts when data is available', async () => {
    const mockDrafts = [
      {
        id: 1,
        title: 'Test Draft',
        content: 'This is a test draft content',
        status: 'draft',
        updated_at: '2023-01-01T00:00:00Z'
      }
    ];

    BlogAPI.getDraftPosts.mockResolvedValue({
      success: true,
      data: {
        results: mockDrafts,
        count: 1
      }
    });

    renderWithRouter(<DraftsList />);

    await waitFor(() => {
      expect(screen.getByText('Test Draft')).toBeInTheDocument();
      expect(screen.getByText('This is a test draft content')).toBeInTheDocument();
    });
  });

  test('renders error state when API fails', async () => {
    const mockError = {
      type: 'API_ERROR',
      message: 'Failed to load drafts'
    };

    BlogAPI.getDraftPosts.mockResolvedValue({
      success: false,
      error: mockError
    });

    renderWithRouter(<DraftsList />);

    await waitFor(() => {
      expect(screen.getByTestId('error-message')).toBeInTheDocument();
      expect(screen.getByText('Failed to load drafts')).toBeInTheDocument();
    });
  });

  test('calls API on component mount', () => {
    BlogAPI.getDraftPosts.mockResolvedValue({
      success: true,
      data: { results: [], count: 0 }
    });

    renderWithRouter(<DraftsList />);

    expect(BlogAPI.getDraftPosts).toHaveBeenCalledWith({ page: 1 });
  });
});