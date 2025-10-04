import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import PostConfirmDelete from './PostConfirmDelete';

// Mock post data
const mockPost = {
  id: 1,
  title: 'Test Post',
  content: 'This is a test post content',
  author: 'Test Author',
  created_at: '2023-01-01T00:00:00Z',
  updated_at: '2023-01-01T00:00:00Z'
};

describe('PostConfirmDelete', () => {
  const mockOnConfirm = jest.fn();
  const mockOnCancel = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
  });

  test('renders nothing when isOpen is false', () => {
    render(
      <PostConfirmDelete
        post={mockPost}
        isOpen={false}
        onConfirm={mockOnConfirm}
        onCancel={mockOnCancel}
      />
    );

    expect(screen.queryByText('Confirm Deletion')).not.toBeInTheDocument();
  });

  test('renders dialog when isOpen is true', () => {
    render(
      <PostConfirmDelete
        post={mockPost}
        isOpen={true}
        onConfirm={mockOnConfirm}
        onCancel={mockOnCancel}
      />
    );

    expect(screen.getByText('Confirm Deletion')).toBeInTheDocument();
    expect(screen.getByText('Are you sure you want to delete this post?')).toBeInTheDocument();
    expect(screen.getByText('"Test Post"')).toBeInTheDocument();
    expect(screen.getByText(/By.*Test Author/)).toBeInTheDocument();
    expect(screen.getByText('This action cannot be undone.')).toBeInTheDocument();
  });

  test('calls onConfirm when Delete Post button is clicked', () => {
    render(
      <PostConfirmDelete
        post={mockPost}
        isOpen={true}
        onConfirm={mockOnConfirm}
        onCancel={mockOnCancel}
      />
    );

    const deleteButton = screen.getByText('Delete Post');
    fireEvent.click(deleteButton);

    expect(mockOnConfirm).toHaveBeenCalledWith(1);
  });

  test('calls onCancel when Cancel button is clicked', () => {
    render(
      <PostConfirmDelete
        post={mockPost}
        isOpen={true}
        onConfirm={mockOnConfirm}
        onCancel={mockOnCancel}
      />
    );

    const cancelButton = screen.getByText('Cancel');
    fireEvent.click(cancelButton);

    expect(mockOnCancel).toHaveBeenCalled();
  });

  test('calls onCancel when close button (×) is clicked', () => {
    render(
      <PostConfirmDelete
        post={mockPost}
        isOpen={true}
        onConfirm={mockOnConfirm}
        onCancel={mockOnCancel}
      />
    );

    const closeButton = screen.getByLabelText('Close dialog');
    fireEvent.click(closeButton);

    expect(mockOnCancel).toHaveBeenCalled();
  });

  test('calls onCancel when backdrop is clicked', () => {
    render(
      <PostConfirmDelete
        post={mockPost}
        isOpen={true}
        onConfirm={mockOnConfirm}
        onCancel={mockOnCancel}
      />
    );

    const overlay = screen.getByRole('dialog').parentElement;
    fireEvent.click(overlay);

    expect(mockOnCancel).toHaveBeenCalled();
  });

  test('shows loading state when isDeleting is true', () => {
    render(
      <PostConfirmDelete
        post={mockPost}
        isOpen={true}
        isDeleting={true}
        onConfirm={mockOnConfirm}
        onCancel={mockOnCancel}
      />
    );

    expect(screen.getByText('Deleting...')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /deleting/i })).toBeDisabled();
    expect(screen.getByRole('button', { name: /cancel/i })).toBeDisabled();
  });

  test('disables buttons when isDeleting is true', () => {
    render(
      <PostConfirmDelete
        post={mockPost}
        isOpen={true}
        isDeleting={true}
        onConfirm={mockOnConfirm}
        onCancel={mockOnCancel}
      />
    );

    const deleteButton = screen.getByRole('button', { name: /deleting/i });
    const cancelButton = screen.getByRole('button', { name: /cancel/i });

    expect(deleteButton).toBeDisabled();
    expect(cancelButton).toBeDisabled();
  });

  test('handles keyboard navigation - Escape key calls onCancel', () => {
    render(
      <PostConfirmDelete
        post={mockPost}
        isOpen={true}
        onConfirm={mockOnConfirm}
        onCancel={mockOnCancel}
      />
    );

    const overlay = screen.getByRole('dialog').parentElement;
    fireEvent.keyDown(overlay, { key: 'Escape' });

    expect(mockOnCancel).toHaveBeenCalled();
  });

  test('handles keyboard navigation - Enter key calls onConfirm', () => {
    render(
      <PostConfirmDelete
        post={mockPost}
        isOpen={true}
        onConfirm={mockOnConfirm}
        onCancel={mockOnCancel}
      />
    );

    const overlay = screen.getByRole('dialog').parentElement;
    fireEvent.keyDown(overlay, { key: 'Enter' });

    expect(mockOnConfirm).toHaveBeenCalledWith(1);
  });

  test('does not call onConfirm when isDeleting is true and button is clicked', () => {
    render(
      <PostConfirmDelete
        post={mockPost}
        isOpen={true}
        isDeleting={true}
        onConfirm={mockOnConfirm}
        onCancel={mockOnCancel}
      />
    );

    const deleteButton = screen.getByRole('button', { name: /deleting/i });
    fireEvent.click(deleteButton);

    expect(mockOnConfirm).not.toHaveBeenCalled();
  });

  test('does not call onCancel when isDeleting is true and cancel is attempted', () => {
    render(
      <PostConfirmDelete
        post={mockPost}
        isOpen={true}
        isDeleting={true}
        onConfirm={mockOnConfirm}
        onCancel={mockOnCancel}
      />
    );

    const cancelButton = screen.getByRole('button', { name: /cancel/i });
    fireEvent.click(cancelButton);

    expect(mockOnCancel).not.toHaveBeenCalled();
  });
});