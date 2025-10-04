import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import PostForm from '../components/posts/PostForm';
import BlogAPI from '../services/api';
import { SUCCESS_MESSAGES, INITIAL_POST_FORM } from '../utils/constants';
import './AddPostPage.css';

/**
 * AddPostPage component for creating new blog posts
 */
const AddPostPage = () => {
  const navigate = useNavigate();
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState(null);
  const [successMessage, setSuccessMessage] = useState('');

  /**
   * Handle form submission
   */
  const handleSubmit = async (postData) => {
    setIsSubmitting(true);
    setSubmitError(null);
    setSuccessMessage('');

    try {
      const response = await BlogAPI.createPost(postData);
      
      if (response.success) {
        // Show success message
        setSuccessMessage(SUCCESS_MESSAGES.POST_CREATED);
        
        // Redirect to homepage after a short delay
        setTimeout(() => {
          navigate('/', { 
            state: { 
              message: SUCCESS_MESSAGES.POST_CREATED,
              type: 'success'
            }
          });
        }, 1500);
      } else {
        // Handle API error
        setSubmitError(response.error);
      }
    } catch (error) {
      // Handle unexpected errors
      console.error('Error creating post:', error);
      setSubmitError({
        type: 'UNKNOWN_ERROR',
        message: 'An unexpected error occurred while creating the post'
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  /**
   * Handle cancel action
   */
  const handleCancel = () => {
    navigate('/');
  };

  return (
    <div className="add-post-page">
      <div className="page-header">
        <h1>Create New Blog Post</h1>
        <p className="page-description">
          Share your insights and knowledge with the community by creating a new blog post.
        </p>
      </div>

      {/* Success Message */}
      {successMessage && (
        <div className="success-message">
          <div className="success-content">
            <span className="success-icon">✅</span>
            <span className="success-text">{successMessage}</span>
          </div>
          <p className="redirect-message">Redirecting to homepage...</p>
        </div>
      )}

      {/* Post Form */}
      {!successMessage && (
        <>
          <PostForm
            initialData={INITIAL_POST_FORM}
            onSubmit={handleSubmit}
            submitButtonText="Create Post"
            isSubmitting={isSubmitting}
            submitError={submitError}
          />

          {/* Cancel Button */}
          <div className="page-actions">
            <button
              type="button"
              className="cancel-button"
              onClick={handleCancel}
              disabled={isSubmitting}
            >
              Cancel
            </button>
          </div>
        </>
      )}
    </div>
  );
};

export default AddPostPage;