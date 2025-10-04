import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import '@testing-library/jest-dom';
import AddPostPage from './AddPostPage';
import BlogAPI from '../services/api';

// Mock the BlogAPI
jest.mock('../services/api');

// Mock react-router-dom
const mockNavigate = jest.fn();
jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  useNavigate: () => mockNavigate,
}));

// Mock PostForm component
jest.mock('../components/posts/PostForm', () => {
  return function MockPostForm({ onSubmit, isSubmitting, submitError }) {
    return (
      <div data-testid="post-form">
        <button 
          onClick={() => onSubmit({
            title: 'Test Post',
            content: 'Test content',
            author: 'Test Author',
            tags: 'test',
            image_url: ''
          })}
          disabled={isSubmitting}
        >
          {isSubmitting ? 'Submitting...' : 'Create Post'}
        </button>
        {submitError && <div data-testid="submit-error">{submitError.message}</div>}
      </div>
    );
  };
});

const renderWithRouter = (component) => {
  return render(
    <BrowserRouter>
      {component}
    </BrowserRouter>
  );
};

describe('AddPostPage', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  test('renders page header and form', () => {
    renderWithRouter(<AddPostPage />);

    expect(screen.getByText('Create New Blog Post')).toBeInTheDocument();
    expect(screen.getByText(/share your insights and knowledge/i)).toBeInTheDocument();
    expect(screen.getByTestId('post-form')).toBeInTheDocument();
    expect(screen.getByText('Cancel')).toBeInTheDocument();
  });

  test('handles successful post creation', async () => {
    BlogAPI.createPost.mockResolvedValue({
      success: true,
      data: { id: 1, title: 'Test Post' }
    });

    renderWithRouter(<AddPostPage />);

    const createButton = screen.getByText('Create Post');
    fireEvent.click(createButton);

    await waitFor(() => {
      expect(BlogAPI.createPost).toHaveBeenCalledWith({
        title: 'Test Post',
        content: 'Test content',
        author: 'Test Author',
        tags: 'test',
        image_url: ''
      });
    });

    await waitFor(() => {
      expect(screen.getByText(/blog post created successfully/i)).toBeInTheDocument();
      expect(screen.getByText(/redirecting to homepage/i)).toBeInTheDocument();
    });

    // Wait for navigation
    await waitFor(() => {
      expect(mockNavigate).toHaveBeenCalledWith('/', {
        state: {
          message: 'Blog post created successfully!',
          type: 'success'
        }
      });
    }, { timeout: 2000 });
  });

  test('handles API error during post creation', async () => {
    const errorResponse = {
      success: false,
      error: {
        type: 'VALIDATION_ERROR',
        message: 'Title is required'
      }
    };

    BlogAPI.createPost.mockResolvedValue(errorResponse);

    renderWithRouter(<AddPostPage />);

    const createButton = screen.getByText('Create Post');
    fireEvent.click(createButton);

    await waitFor(() => {
      expect(screen.getByTestId('submit-error')).toBeInTheDocument();
      expect(screen.getByText('Title is required')).toBeInTheDocument();
    });

    expect(mockNavigate).not.toHaveBeenCalled();
  });

  test('handles network error during post creation', async () => {
    BlogAPI.createPost.mockRejectedValue(new Error('Network error'));

    renderWithRouter(<AddPostPage />);

    const createButton = screen.getByText('Create Post');
    fireEvent.click(createButton);

    await waitFor(() => {
      expect(screen.getByTestId('submit-error')).toBeInTheDocument();
      expect(screen.getByText(/unexpected error occurred/i)).toBeInTheDocument();
    });

    expect(mockNavigate).not.toHaveBeenCalled();
  });

  test('shows loading state during submission', async () => {
    BlogAPI.createPost.mockImplementation(() => new Promise(resolve => setTimeout(resolve, 100)));

    renderWithRouter(<AddPostPage />);

    const createButton = screen.getByText('Create Post');
    fireEvent.click(createButton);

    await waitFor(() => {
      expect(screen.getByText('Submitting...')).toBeInTheDocument();
    });
  });

  test('handles cancel button click', () => {
    renderWithRouter(<AddPostPage />);

    const cancelButton = screen.getByText('Cancel');
    fireEvent.click(cancelButton);

    expect(mockNavigate).toHaveBeenCalledWith('/');
  });

  test('disables cancel button during submission', async () => {
    BlogAPI.createPost.mockImplementation(() => new Promise(resolve => setTimeout(resolve, 100)));

    renderWithRouter(<AddPostPage />);

    const createButton = screen.getByText('Create Post');
    fireEvent.click(createButton);

    await waitFor(() => {
      const cancelButton = screen.getByText('Cancel');
      expect(cancelButton).toBeDisabled();
    });
  });
});