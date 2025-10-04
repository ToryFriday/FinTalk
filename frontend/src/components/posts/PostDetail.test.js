import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import PostDetail from './PostDetail';

// Mock data for testing
const mockPost = {
  id: 1,
  title: 'Test Blog Post',
  content: 'This is a test blog post content.\n\nThis is a second paragraph.',
  author: 'Test Author',
  tags: 'test, blog, react',
  image_url: 'https://example.com/image.jpg',
  created_at: '2024-01-01T10:00:00Z',
  updated_at: '2024-01-02T10:00:00Z'
};

const mockPostWithoutImage = {
  id: 2,
  title: 'Post Without Image',
  content: 'This post has no image.',
  author: 'Another Author',
  tags: '',
  image_url: '',
  created_at: '2024-01-01T10:00:00Z',
  updated_at: '2024-01-01T10:00:00Z'
};

// Wrapper component for router context
const TestWrapper = ({ children }) => (
  <BrowserRouter>
    {children}
  </BrowserRouter>
);

describe('PostDetail Component', () => {
  test('renders post details correctly', () => {
    render(
      <TestWrapper>
        <PostDetail post={mockPost} />
      </TestWrapper>
    );

    // Check if title is rendered
    expect(screen.getByText('Test Blog Post')).toBeInTheDocument();
    
    // Check if author is rendered
    expect(screen.getByText('Test Author')).toBeInTheDocument();
    
    // Check if content is rendered (first paragraph)
    expect(screen.getByText('This is a test blog post content.')).toBeInTheDocument();
    
    // Check if tags are rendered
    expect(screen.getByText('test')).toBeInTheDocument();
    expect(screen.getByText('blog')).toBeInTheDocument();
    expect(screen.getByText('react')).toBeInTheDocument();
    
    // Check if image is rendered
    const image = screen.getByAltText('Test Blog Post');
    expect(image).toBeInTheDocument();
    expect(image).toHaveAttribute('src', 'https://example.com/image.jpg');
  });

  test('renders post without image correctly', () => {
    render(
      <TestWrapper>
        <PostDetail post={mockPostWithoutImage} />
      </TestWrapper>
    );

    // Check if title is rendered
    expect(screen.getByText('Post Without Image')).toBeInTheDocument();
    
    // Check if author is rendered
    expect(screen.getByText('Another Author')).toBeInTheDocument();
    
    // Check that no image is rendered
    expect(screen.queryByAltText('Post Without Image')).not.toBeInTheDocument();
    
    // Check that no tags section is rendered when tags are empty
    expect(screen.queryByText('test')).not.toBeInTheDocument();
  });

  test('shows updated date when different from created date', () => {
    render(
      <TestWrapper>
        <PostDetail post={mockPost} />
      </TestWrapper>
    );

    // Check if both published and updated dates are shown
    expect(screen.getByText('Published:')).toBeInTheDocument();
    expect(screen.getByText('Updated:')).toBeInTheDocument();
  });

  test('does not show updated date when same as created date', () => {
    render(
      <TestWrapper>
        <PostDetail post={mockPostWithoutImage} />
      </TestWrapper>
    );

    // Check if only published date is shown
    expect(screen.getByText('Published:')).toBeInTheDocument();
    expect(screen.queryByText('Updated:')).not.toBeInTheDocument();
  });

  test('renders navigation and action buttons', () => {
    render(
      <TestWrapper>
        <PostDetail post={mockPost} />
      </TestWrapper>
    );

    // Check if navigation button is rendered
    const backButton = screen.getByText('← Back to Home');
    expect(backButton).toBeInTheDocument();
    expect(backButton.closest('a')).toHaveAttribute('href', '/');

    // Check if edit button is rendered
    const editButton = screen.getByText('Edit Post');
    expect(editButton).toBeInTheDocument();
    expect(editButton.closest('a')).toHaveAttribute('href', '/posts/1/edit');
  });

  test('renders delete button when onDelete prop is provided', () => {
    const mockOnDelete = jest.fn();
    
    render(
      <TestWrapper>
        <PostDetail post={mockPost} onDelete={mockOnDelete} />
      </TestWrapper>
    );

    // Check if delete button is rendered
    const deleteButton = screen.getByText('Delete Post');
    expect(deleteButton).toBeInTheDocument();
  });

  test('does not render delete button when onDelete prop is not provided', () => {
    render(
      <TestWrapper>
        <PostDetail post={mockPost} />
      </TestWrapper>
    );

    // Check if delete button is not rendered
    expect(screen.queryByText('Delete Post')).not.toBeInTheDocument();
  });

  test('calls onDelete with confirmation when delete button is clicked', () => {
    const mockOnDelete = jest.fn();
    
    // Mock window.confirm to return true
    window.confirm = jest.fn(() => true);
    
    render(
      <TestWrapper>
        <PostDetail post={mockPost} onDelete={mockOnDelete} />
      </TestWrapper>
    );

    // Click delete button
    const deleteButton = screen.getByText('Delete Post');
    fireEvent.click(deleteButton);

    // Check if confirmation was shown and onDelete was called
    expect(window.confirm).toHaveBeenCalledWith('Are you sure you want to delete this post?');
    expect(mockOnDelete).toHaveBeenCalledWith(1);
  });

  test('does not call onDelete when confirmation is cancelled', () => {
    const mockOnDelete = jest.fn();
    
    // Mock window.confirm to return false
    window.confirm = jest.fn(() => false);
    
    render(
      <TestWrapper>
        <PostDetail post={mockPost} onDelete={mockOnDelete} />
      </TestWrapper>
    );

    // Click delete button
    const deleteButton = screen.getByText('Delete Post');
    fireEvent.click(deleteButton);

    // Check if confirmation was shown but onDelete was not called
    expect(window.confirm).toHaveBeenCalledWith('Are you sure you want to delete this post?');
    expect(mockOnDelete).not.toHaveBeenCalled();
  });

  test('handles content with multiple paragraphs correctly', () => {
    render(
      <TestWrapper>
        <PostDetail post={mockPost} />
      </TestWrapper>
    );

    // Check if both paragraphs are rendered
    expect(screen.getByText('This is a test blog post content.')).toBeInTheDocument();
    expect(screen.getByText('This is a second paragraph.')).toBeInTheDocument();
  });
});