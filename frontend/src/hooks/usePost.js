import { useState, useEffect } from 'react';
import BlogAPI from '../services/api';

/**
 * Custom hook for managing single post operations
 * @param {number} postId - The ID of the post to fetch
 * @returns {Object} Hook state and methods
 */
const usePost = (postId) => {
  const [post, setPost] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  /**
   * Fetch post by ID
   */
  const fetchPost = async (id) => {
    if (!id) return;
    
    setLoading(true);
    setError(null);
    
    try {
      const response = await BlogAPI.getPost(id);
      
      if (response.success) {
        setPost(response.data);
      } else {
        setError(response.error);
      }
    } catch (err) {
      setError({
        type: 'UNKNOWN_ERROR',
        message: 'An unexpected error occurred while fetching the post'
      });
    } finally {
      setLoading(false);
    }
  };

  /**
   * Update post
   */
  const updatePost = async (id, postData) => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await BlogAPI.updatePost(id, postData);
      
      if (response.success) {
        setPost(response.data);
        return { success: true, data: response.data };
      } else {
        setError(response.error);
        return { success: false, error: response.error };
      }
    } catch (err) {
      const error = {
        type: 'UNKNOWN_ERROR',
        message: 'An unexpected error occurred while updating the post'
      };
      setError(error);
      return { success: false, error };
    } finally {
      setLoading(false);
    }
  };

  /**
   * Delete post
   */
  const deletePost = async (id) => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await BlogAPI.deletePost(id);
      
      if (response.success) {
        setPost(null);
        return { success: true };
      } else {
        setError(response.error);
        return { success: false, error: response.error };
      }
    } catch (err) {
      const error = {
        type: 'UNKNOWN_ERROR',
        message: 'An unexpected error occurred while deleting the post'
      };
      setError(error);
      return { success: false, error };
    } finally {
      setLoading(false);
    }
  };

  /**
   * Clear error state
   */
  const clearError = () => {
    setError(null);
  };

  /**
   * Reset hook state
   */
  const reset = () => {
    setPost(null);
    setError(null);
    setLoading(false);
  };

  // Fetch post when postId changes
  useEffect(() => {
    if (postId) {
      fetchPost(postId);
    } else {
      reset();
    }
  }, [postId]);

  return {
    post,
    loading,
    error,
    fetchPost,
    updatePost,
    deletePost,
    clearError,
    reset
  };
};

export default usePost;