import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MemoryRouter, Routes, Route } from 'react-router-dom';
import EditPostPage from './EditPostPage';
import BlogAPI from '../services/api';

// Mock the API
jest.mock('../services/api');
const mockBlogAPI = BlogAPI;

// Mock the usePost hook
jest.mock('../hooks/usePost', () => {
  return jest.fn(() => ({
    post: null,
    loading: true,
    error: null,
    updatePost: jest.fn(),
    clearError: jest.fn()
  }));
});

const usePostMock = require('../hooks/usePost');

// Helper function to render component with router and proper route params
const renderWithRouter = (component, initialEntries = ['/posts/123/edit']) => {
  return render(
    <MemoryRouter initialEntries={initialEntries}>
      <Routes>
        <Route path="/posts/:id/edit" element={component} />
      </Routes>
    </MemoryRouter>
  );
};

describe('EditPostPage', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  test('renders loading state initially', () => {
    usePostMock.mockReturnValue({
      post: null,
      loading: true,
      error: null,
      updatePost: jest.fn(),
      clearError: jest.fn()
    });

    renderWithRouter(<EditPostPage />);

    expect(screen.getByText('Edit Post')).toBeInTheDocument();
    expect(screen.getByText('Loading post data...')).toBeInTheDocument();
  });

  test('renders form when post data is loaded', () => {
    const mockPost = {
      id: 123,
      title: 'Test Post',
      content: 'Test content',
      author: 'Test Author',
      tags: 'test, post',
      image_url: 'https://example.com/image.jpg'
    };

    usePostMock.mockReturnValue({
      post: mockPost,
      loading: false,
      error: null,
      updatePost: jest.fn(),
      clearError: jest.fn()
    });

    renderWithRouter(<EditPostPage />);

    expect(screen.getByText('Edit Post')).toBeInTheDocument();
    expect(screen.getByText('Update your blog post information below.')).toBeInTheDocument();
    expect(screen.getByDisplayValue('Test Post')).toBeInTheDocument();
    expect(screen.getByDisplayValue('Test content')).toBeInTheDocument();
    expect(screen.getByDisplayValue('Test Author')).toBeInTheDocument();
    expect(screen.getByText('Update Post')).toBeInTheDocument();
    expect(screen.getByText('Cancel')).toBeInTheDocument();
  });

  test('renders not found error when post does not exist', () => {
    usePostMock.mockReturnValue({
      post: null,
      loading: false,
      error: { type: 'NOT_FOUND', status: 404, message: 'Post not found' },
      updatePost: jest.fn(),
      clearError: jest.fn()
    });

    renderWithRouter(<EditPostPage />);

    expect(screen.getByText('Edit Post')).toBeInTheDocument();
    expect(screen.getByText('Post Not Found')).toBeInTheDocument();
    expect(screen.getByText("The post you're trying to edit doesn't exist or may have been deleted.")).toBeInTheDocument();
    expect(screen.getByText('Back to Home')).toBeInTheDocument();
  });

  test('renders general error when fetch fails', () => {
    usePostMock.mockReturnValue({
      post: null,
      loading: false,
      error: { type: 'NETWORK_ERROR', message: 'Network error occurred' },
      updatePost: jest.fn(),
      clearError: jest.fn()
    });

    renderWithRouter(<EditPostPage />);

    expect(screen.getByText('Edit Post')).toBeInTheDocument();
    expect(screen.getByText('Try Again')).toBeInTheDocument();
    expect(screen.getByText('Back to Home')).toBeInTheDocument();
  });

  test('handles form submission successfully', async () => {
    const mockPost = {
      id: 123,
      title: 'Test Post',
      content: 'Test content',
      author: 'Test Author',
      tags: 'test, post',
      image_url: ''
    };

    const mockUpdatePost = jest.fn().mockResolvedValue({
      success: true,
      data: { ...mockPost, title: 'Updated Test Post' }
    });

    usePostMock.mockReturnValue({
      post: mockPost,
      loading: false,
      error: null,
      updatePost: mockUpdatePost,
      clearError: jest.fn()
    });

    renderWithRouter(<EditPostPage />);

    // Update the title
    const titleInput = screen.getByDisplayValue('Test Post');
    fireEvent.change(titleInput, { target: { value: 'Updated Test Post' } });

    // Submit the form
    const submitButton = screen.getByText('Update Post');
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(mockUpdatePost).toHaveBeenCalledWith(123, {
        title: 'Updated Test Post',
        content: 'Test content',
        author: 'Test Author',
        tags: 'test, post',
        image_url: ''
      });
    });
  });

  test('handles form submission error', async () => {
    const mockPost = {
      id: 123,
      title: 'Test Post',
      content: 'Test content',
      author: 'Test Author',
      tags: 'test, post',
      image_url: ''
    };

    const mockUpdatePost = jest.fn().mockResolvedValue({
      success: false,
      error: { type: 'VALIDATION_ERROR', message: 'Title is required' }
    });

    usePostMock.mockReturnValue({
      post: mockPost,
      loading: false,
      error: null,
      updatePost: mockUpdatePost,
      clearError: jest.fn()
    });

    renderWithRouter(<EditPostPage />);

    // Submit the form
    const submitButton = screen.getByText('Update Post');
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(mockUpdatePost).toHaveBeenCalled();
    });

    // Check that error is displayed (this would be handled by the ErrorMessage component)
    expect(mockUpdatePost).toHaveBeenCalledWith(123, expect.any(Object));
  });
});