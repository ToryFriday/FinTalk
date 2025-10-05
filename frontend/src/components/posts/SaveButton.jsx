import React, { useState, useEffect, useCallback } from 'react';
import BlogAPI from '../../services/api';
import { formatErrorMessage } from '../../services/api';
import './SaveButton.css';

/**
 * SaveButton component for saving/unsaving articles
 * @param {Object} props - Component props
 * @param {number} props.postId - Post ID
 * @param {boolean} props.isAuthenticated - Whether user is authenticated
 * @param {string} props.className - Additional CSS classes
 * @param {Function} props.onSaveChange - Callback when save status changes
 */
const SaveButton = ({ postId, isAuthenticated, className = '', onSaveChange }) => {
  const [isSaved, setIsSaved] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  // Check if post is saved when component mounts
  useEffect(() => {
    if (isAuthenticated && postId) {
      checkSavedStatus();
    } else {
      setIsLoading(false);
    }
  }, [postId, isAuthenticated]);

  const checkSavedStatus = useCallback(async () => {
    try {
      setIsLoading(true);
      const response = await BlogAPI.checkSavedStatus(postId);
      
      if (response.success) {
        setIsSaved(response.data.is_saved);
        setError(null);
      } else {
        console.error('Failed to check saved status:', response.error);
        setError('Failed to check saved status');
      }
    } catch (error) {
      console.error('Error checking saved status:', error);
      setError('Failed to check saved status');
    } finally {
      setIsLoading(false);
    }
  }, [postId]);

  const handleSaveToggle = useCallback(async () => {
    if (!isAuthenticated) {
      setError('Please log in to save articles');
      return;
    }

    try {
      setIsLoading(true);
      setError(null);

      let response;
      if (isSaved) {
        response = await BlogAPI.unsavePost(postId);
      } else {
        response = await BlogAPI.savePost(postId);
      }

      if (response.success) {
        const newSavedState = !isSaved;
        setIsSaved(newSavedState);
        
        // Call callback if provided
        if (onSaveChange) {
          onSaveChange(postId, newSavedState);
        }
      } else {
        const errorMessage = formatErrorMessage(response.error);
        setError(errorMessage);
      }
    } catch (error) {
      console.error('Error toggling save status:', error);
      setError('Failed to update save status');
    } finally {
      setIsLoading(false);
    }
  }, [postId, isSaved, isAuthenticated, onSaveChange]);

  // Don't render if user is not authenticated
  if (!isAuthenticated) {
    return null;
  }

  return (
    <div className={`save-button-container ${className}`}>
      <button
        className={`save-button ${isSaved ? 'saved' : 'unsaved'} ${isLoading ? 'loading' : ''}`}
        onClick={handleSaveToggle}
        disabled={isLoading}
        type="button"
        title={isSaved ? 'Remove from saved articles' : 'Save for later reading'}
      >
        <span className="save-icon">
          {isLoading ? '⏳' : isSaved ? '❤️' : '🤍'}
        </span>
        <span className="save-text">
          {isLoading ? 'Saving...' : isSaved ? 'Saved' : 'Save'}
        </span>
      </button>
      
      {error && (
        <div className="save-error" role="alert">
          {error}
        </div>
      )}
    </div>
  );
};

export default SaveButton;