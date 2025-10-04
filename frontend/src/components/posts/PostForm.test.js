import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import PostForm from './PostForm';
import { INITIAL_POST_FORM } from '../../utils/constants';

// Mock the LoadingSpinner and ErrorMessage components
jest.mock('../common/LoadingSpinner', () => {
  return function MockLoadingSpinner({ size, message }) {
    return <div data-testid="loading-spinner">{message}</div>;
  };
});

jest.mock('../common/ErrorMessage', () => {
  return function MockErrorMessage({ error }) {
    return <div data-testid="error-message">{error.message || error}</div>;
  };
});

describe('PostForm', () => {
  const mockOnSubmit = jest.fn();

  beforeEach(() => {
    mockOnSubmit.mockClear();
  });

  test('renders all form fields', () => {
    render(<PostForm onSubmit={mockOnSubmit} />);

    expect(screen.getByLabelText(/title/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/content/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/author/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/tags/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/image url/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /create post/i })).toBeInTheDocument();
  });

  test('shows validation errors for required fields', async () => {
    render(<PostForm onSubmit={mockOnSubmit} />);

    const submitButton = screen.getByRole('button', { name: /create post/i });
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText(/title is required/i)).toBeInTheDocument();
      expect(screen.getByText(/content is required/i)).toBeInTheDocument();
      expect(screen.getByText(/author is required/i)).toBeInTheDocument();
    });

    expect(mockOnSubmit).not.toHaveBeenCalled();
  });

  test('validates field lengths', async () => {
    render(<PostForm onSubmit={mockOnSubmit} />);

    const titleInput = screen.getByLabelText(/title/i);
    const contentInput = screen.getByLabelText(/content/i);
    const authorInput = screen.getByLabelText(/author/i);

    // Test minimum lengths
    fireEvent.change(titleInput, { target: { value: 'Hi' } });
    fireEvent.blur(titleInput);
    fireEvent.change(contentInput, { target: { value: 'Short' } });
    fireEvent.blur(contentInput);
    fireEvent.change(authorInput, { target: { value: 'A' } });
    fireEvent.blur(authorInput);

    await waitFor(() => {
      expect(screen.getByText(/title must be at least 5 characters/i)).toBeInTheDocument();
      expect(screen.getByText(/content must be at least 10 characters/i)).toBeInTheDocument();
      expect(screen.getByText(/author name must be at least 2 characters/i)).toBeInTheDocument();
    });
  });

  test('validates image URL format', async () => {
    render(<PostForm onSubmit={mockOnSubmit} />);

    const imageUrlInput = screen.getByLabelText(/image url/i);
    fireEvent.change(imageUrlInput, { target: { value: 'invalid-url' } });
    fireEvent.blur(imageUrlInput);

    await waitFor(() => {
      expect(screen.getByText(/image url must be a valid http or https url/i)).toBeInTheDocument();
    });
  });

  test('submits form with valid data', async () => {
    render(<PostForm onSubmit={mockOnSubmit} />);

    const validData = {
      title: 'Test Blog Post Title',
      content: 'This is a test blog post content that is long enough to pass validation.',
      author: 'Test Author',
      tags: 'test, blog, post',
      image_url: 'https://example.com/image.jpg'
    };

    fireEvent.change(screen.getByLabelText(/title/i), { target: { value: validData.title } });
    fireEvent.change(screen.getByLabelText(/content/i), { target: { value: validData.content } });
    fireEvent.change(screen.getByLabelText(/author/i), { target: { value: validData.author } });
    fireEvent.change(screen.getByLabelText(/tags/i), { target: { value: validData.tags } });
    fireEvent.change(screen.getByLabelText(/image url/i), { target: { value: validData.image_url } });

    const submitButton = screen.getByRole('button', { name: /create post/i });
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(mockOnSubmit).toHaveBeenCalledWith(validData);
    });
  });

  test('shows loading state when submitting', () => {
    render(<PostForm onSubmit={mockOnSubmit} isSubmitting={true} />);

    expect(screen.getByText(/submitting/i)).toBeInTheDocument();
    expect(screen.getByTestId('loading-spinner')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /submitting/i })).toBeDisabled();
  });

  test('shows submit error', () => {
    const error = { message: 'Failed to create post' };
    render(<PostForm onSubmit={mockOnSubmit} submitError={error} />);

    expect(screen.getByTestId('error-message')).toBeInTheDocument();
    expect(screen.getByText('Failed to create post')).toBeInTheDocument();
  });

  test('clears field errors when user starts typing', async () => {
    render(<PostForm onSubmit={mockOnSubmit} />);

    const titleInput = screen.getByLabelText(/title/i);
    
    // Trigger validation error
    fireEvent.blur(titleInput);
    await waitFor(() => {
      expect(screen.getByText(/title is required/i)).toBeInTheDocument();
    });

    // Start typing to clear error
    fireEvent.change(titleInput, { target: { value: 'New title' } });
    
    await waitFor(() => {
      expect(screen.queryByText(/title is required/i)).not.toBeInTheDocument();
    });
  });

  test('uses initial data for editing', () => {
    const initialData = {
      title: 'Existing Post',
      content: 'Existing content',
      author: 'Existing Author',
      tags: 'existing, tags',
      image_url: 'https://example.com/existing.jpg'
    };

    render(<PostForm onSubmit={mockOnSubmit} initialData={initialData} />);

    expect(screen.getByDisplayValue('Existing Post')).toBeInTheDocument();
    expect(screen.getByDisplayValue('Existing content')).toBeInTheDocument();
    expect(screen.getByDisplayValue('Existing Author')).toBeInTheDocument();
    expect(screen.getByDisplayValue('existing, tags')).toBeInTheDocument();
    expect(screen.getByDisplayValue('https://example.com/existing.jpg')).toBeInTheDocument();
  });
});