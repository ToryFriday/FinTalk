import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import SaveButton from './SaveButton';
import BlogAPI from '../../services/api';

// Mock the BlogAPI
jest.mock('../../services/api');

describe('SaveButton', () => {
  const mockPostId = 1;
  const mockOnSaveChange = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('when user is not authenticated', () => {
    it('should not render anything', () => {
      render(
        <SaveButton
          postId={mockPostId}
          isAuthenticated={false}
          onSaveChange={mockOnSaveChange}
        />
      );

      expect(screen.queryByRole('button')).not.toBeInTheDocument();
    });
  });

  describe('when user is authenticated', () => {
    beforeEach(() => {
      BlogAPI.checkSavedStatus.mockResolvedValue({
        success: true,
        data: { is_saved: false }
      });
    });

    it('should render save button for unsaved post', async () => {
      render(
        <SaveButton
          postId={mockPostId}
          isAuthenticated={true}
          onSaveChange={mockOnSaveChange}
        />
      );

      await waitFor(() => {
        expect(screen.getByRole('button')).toBeInTheDocument();
        expect(screen.getByRole('button')).not.toHaveClass('loading');
      });

      const button = screen.getByRole('button');
      expect(button).toHaveTextContent('Save');
      expect(button).toHaveClass('unsaved');
    });

    it('should render saved button for saved post', async () => {
      BlogAPI.checkSavedStatus.mockResolvedValue({
        success: true,
        data: { is_saved: true }
      });

      render(
        <SaveButton
          postId={mockPostId}
          isAuthenticated={true}
          onSaveChange={mockOnSaveChange}
        />
      );

      await waitFor(() => {
        expect(screen.getByRole('button')).toBeInTheDocument();
      });

      const button = screen.getByRole('button');
      expect(button).toHaveTextContent('Saved');
      expect(button).toHaveClass('saved');
    });

    it('should handle save action successfully', async () => {
      BlogAPI.savePost.mockResolvedValue({
        success: true,
        data: { message: 'Article saved successfully.' }
      });

      render(
        <SaveButton
          postId={mockPostId}
          isAuthenticated={true}
          onSaveChange={mockOnSaveChange}
        />
      );

      await waitFor(() => {
        expect(screen.getByRole('button')).toBeInTheDocument();
      });

      const button = screen.getByRole('button');
      fireEvent.click(button);

      await waitFor(() => {
        expect(BlogAPI.savePost).toHaveBeenCalledWith(mockPostId);
        expect(mockOnSaveChange).toHaveBeenCalledWith(mockPostId, true);
      });

      expect(button).toHaveTextContent('Saved');
      expect(button).toHaveClass('saved');
    });

    it('should handle unsave action successfully', async () => {
      BlogAPI.checkSavedStatus.mockResolvedValue({
        success: true,
        data: { is_saved: true }
      });

      BlogAPI.unsavePost.mockResolvedValue({
        success: true,
        data: { message: 'Article unsaved successfully.' }
      });

      render(
        <SaveButton
          postId={mockPostId}
          isAuthenticated={true}
          onSaveChange={mockOnSaveChange}
        />
      );

      await waitFor(() => {
        expect(screen.getByRole('button')).toBeInTheDocument();
        expect(screen.getByRole('button')).not.toHaveClass('loading');
      });

      const button = screen.getByRole('button');
      expect(button).toHaveTextContent('Saved');
      
      fireEvent.click(button);

      await waitFor(() => {
        expect(BlogAPI.unsavePost).toHaveBeenCalledWith(mockPostId);
        expect(mockOnSaveChange).toHaveBeenCalledWith(mockPostId, false);
      });

      await waitFor(() => {
        expect(button).toHaveTextContent('Save');
        expect(button).toHaveClass('unsaved');
      });
    });

    it('should display error when save fails', async () => {
      BlogAPI.savePost.mockResolvedValue({
        success: false,
        error: {
          type: 'API_ERROR',
          message: 'Failed to save article',
          status: 500
        }
      });

      render(
        <SaveButton
          postId={mockPostId}
          isAuthenticated={true}
          onSaveChange={mockOnSaveChange}
        />
      );

      await waitFor(() => {
        expect(screen.getByRole('button')).toBeInTheDocument();
        expect(screen.getByRole('button')).not.toHaveClass('loading');
      });

      const button = screen.getByRole('button');
      fireEvent.click(button);

      await waitFor(() => {
        expect(screen.getByRole('alert')).toBeInTheDocument();
      });

      expect(screen.getByRole('alert')).toHaveTextContent('Failed to save article');
    });

    it('should show loading state during save operation', async () => {
      let resolvePromise;
      const savePromise = new Promise((resolve) => {
        resolvePromise = resolve;
      });

      BlogAPI.savePost.mockReturnValue(savePromise);

      render(
        <SaveButton
          postId={mockPostId}
          isAuthenticated={true}
          onSaveChange={mockOnSaveChange}
        />
      );

      await waitFor(() => {
        expect(screen.getByRole('button')).toBeInTheDocument();
      });

      const button = screen.getByRole('button');
      fireEvent.click(button);

      expect(button).toHaveTextContent('Saving...');
      expect(button).toHaveClass('loading');
      expect(button).toBeDisabled();

      // Resolve the promise
      resolvePromise({
        success: true,
        data: { message: 'Article saved successfully.' }
      });

      await waitFor(() => {
        expect(button).not.toHaveClass('loading');
        expect(button).not.toBeDisabled();
      });
    });

    it('should handle network error gracefully', async () => {
      BlogAPI.checkSavedStatus.mockRejectedValue(new Error('Network error'));

      render(
        <SaveButton
          postId={mockPostId}
          isAuthenticated={true}
          onSaveChange={mockOnSaveChange}
        />
      );

      await waitFor(() => {
        expect(screen.getByRole('alert')).toBeInTheDocument();
      });

      expect(screen.getByRole('alert')).toHaveTextContent('Failed to check saved status');
    });

    it('should apply custom className', async () => {
      render(
        <SaveButton
          postId={mockPostId}
          isAuthenticated={true}
          className="custom-class"
          onSaveChange={mockOnSaveChange}
        />
      );

      await waitFor(() => {
        expect(screen.getByRole('button')).toBeInTheDocument();
      });

      const container = screen.getByRole('button').closest('.save-button-container');
      expect(container).toHaveClass('custom-class');
    });

    it('should have proper accessibility attributes', async () => {
      render(
        <SaveButton
          postId={mockPostId}
          isAuthenticated={true}
          onSaveChange={mockOnSaveChange}
        />
      );

      await waitFor(() => {
        expect(screen.getByRole('button')).toBeInTheDocument();
      });

      const button = screen.getByRole('button');
      expect(button).toHaveAttribute('type', 'button');
      expect(button).toHaveAttribute('title', 'Save for later reading');
    });
  });
});