import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import PostForm from '../components/posts/PostForm';
import LoadingSpinner from '../components/common/LoadingSpinner';
import ErrorMessage from '../components/common/ErrorMessage';
import usePost from '../hooks/usePost';
import { formatErrorMessage } from '../services/api';
import './EditPostPage.css';

const EditPostPage = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const postId = parseInt(id, 10);
  
  // Hook for managing post data
  const { post, loading, error, updatePost, clearError } = usePost(postId);
  
  // Form submission state
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState(null);
  const [successMessage, setSuccessMessage] = useState('');

  // Clear success message after 5 seconds
  useEffect(() => {
    if (successMessage) {
      const timer = setTimeout(() => {
        setSuccessMessage('');
      }, 5000);
      return () => clearTimeout(timer);
    }
  }, [successMessage]);

  /**
   * Handle form submission for updating post
   */
  const handleSubmit = async (formData) => {
    setIsSubmitting(true);
    setSubmitError(null);
    setSuccessMessage('');

    try {
      const result = await updatePost(postId, formData);
      
      if (result.success) {
        setSuccessMessage('Post updated successfully!');
        // Navigate to the post view page after successful update
        setTimeout(() => {
          navigate(`/posts/${postId}`);
        }, 1500);
      } else {
        setSubmitError({
          message: formatErrorMessage(result.error),
          details: result.error
        });
      }
    } catch (err) {
      setSubmitError({
        message: 'An unexpected error occurred while updating the post',
        details: err
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  /**
   * Handle navigation back to post view
   */
  const handleCancel = () => {
    navigate(`/posts/${postId}`);
  };

  /**
   * Handle navigation back to home
   */
  const handleBackToHome = () => {
    navigate('/');
  };

  // Show loading spinner while fetching post data
  if (loading) {
    return (
      <div className="edit-post-page">
        <div className="page-header">
          <h1>Edit Post</h1>
        </div>
        <div className="loading-container">
          <LoadingSpinner message="Loading post data..." />
        </div>
      </div>
    );
  }

  // Show error if post not found or other error occurred
  if (error) {
    const isNotFound = error.type === 'NOT_FOUND' || error.status === 404;
    
    return (
      <div className="edit-post-page">
        <div className="page-header">
          <h1>Edit Post</h1>
        </div>
        <div className="error-container">
          {isNotFound ? (
            <div className="not-found-error">
              <h2>Post Not Found</h2>
              <p>The post you're trying to edit doesn't exist or may have been deleted.</p>
              <div className="error-actions">
                <button 
                  onClick={handleBackToHome}
                  className="primary-button"
                >
                  Back to Home
                </button>
              </div>
            </div>
          ) : (
            <div className="fetch-error">
              <ErrorMessage 
                error={{
                  message: formatErrorMessage(error),
                  details: error
                }}
              />
              <div className="error-actions">
                <button 
                  onClick={() => window.location.reload()}
                  className="secondary-button"
                >
                  Try Again
                </button>
                <button 
                  onClick={handleBackToHome}
                  className="primary-button"
                >
                  Back to Home
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    );
  }

  // Show form when post data is loaded
  if (!post) {
    return (
      <div className="edit-post-page">
        <div className="page-header">
          <h1>Edit Post</h1>
        </div>
        <div className="error-container">
          <p>Post data not available.</p>
          <button onClick={handleBackToHome} className="primary-button">
            Back to Home
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="edit-post-page">
      <div className="page-header">
        <h1>Edit Post</h1>
        <p className="page-description">
          Update your blog post information below.
        </p>
      </div>

      {/* Success Message */}
      {successMessage && (
        <div className="success-message">
          <div className="success-content">
            <span className="success-icon">✓</span>
            {successMessage}
          </div>
        </div>
      )}

      {/* Post Form */}
      <div className="form-container">
        <PostForm
          initialData={{
            title: post.title || '',
            content: post.content || '',
            author: post.author || '',
            tags: post.tags || '',
            image_url: post.image_url || ''
          }}
          onSubmit={handleSubmit}
          submitButtonText="Update Post"
          isSubmitting={isSubmitting}
          submitError={submitError}
        />
        
        {/* Form Actions */}
        <div className="form-actions-secondary">
          <button
            type="button"
            onClick={handleCancel}
            className="cancel-button"
            disabled={isSubmitting}
          >
            Cancel
          </button>
        </div>
      </div>
    </div>
  );
};

export default EditPostPage;