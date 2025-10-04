import React, { useState, useCallback, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import usePosts from '../../hooks/usePosts';
import PostCard from './PostCard';
import PostConfirmDelete from './PostConfirmDelete';
import LoadingSpinner from '../common/LoadingSpinner';
import ErrorMessage from '../common/ErrorMessage';
import NetworkErrorHandler from '../common/NetworkErrorHandler';
import Pagination from '../common/Pagination';
import BlogAPI from '../../services/api';
import './PostList.css';

/**
 * PostList component for displaying all blog posts
 * Handles loading, error states, and post deletion
 * Optimized with memoization for better performance
 */
const PostList = () => {
  const navigate = useNavigate();
  const { 
    posts, 
    loading, 
    error, 
    pagination, 
    refreshPosts, 
    removePost, 
    goToPage, 
    goToNextPage, 
    goToPreviousPage, 
    changePageSize 
  } = usePosts();
  const [deletingPostId, setDeletingPostId] = useState(null);
  const [postToDelete, setPostToDelete] = useState(null);
  const [showDeleteDialog, setShowDeleteDialog] = useState(false);
  const [deleteError, setDeleteError] = useState(null);
  const [successMessage, setSuccessMessage] = useState(null);

  // Memoized computed values
  const isValidPostsArray = useMemo(() => Array.isArray(posts), [posts]);
  const hasNoPosts = useMemo(() => !isValidPostsArray || posts.length === 0, [isValidPostsArray, posts.length]);
  
  // Debug logging (only in development)
  if (process.env.NODE_ENV === 'development') {
    console.log('PostList render - posts:', posts, 'type:', typeof posts, 'isArray:', isValidPostsArray);
  }

  // Memoized handlers to prevent unnecessary re-renders
  const handleAddPost = useCallback(() => {
    navigate('/posts/add');
  }, [navigate]);

  const handleDeleteRequest = useCallback((postId) => {
    const post = posts.find(p => p.id === postId);
    if (post) {
      setPostToDelete(post);
      setShowDeleteDialog(true);
      setDeleteError(null);
    }
  }, [posts]);

  const handleDeleteConfirm = useCallback(async (postId) => {
    try {
      setDeletingPostId(postId);
      setDeleteError(null);
      
      const response = await BlogAPI.deletePost(postId);
      
      if (response.success) {
        removePost(postId);
        setShowDeleteDialog(false);
        setPostToDelete(null);
        setSuccessMessage('Post deleted successfully');
        
        // Clear success message after 3 seconds
        setTimeout(() => {
          setSuccessMessage(null);
        }, 3000);
      } else {
        setDeleteError(response.error?.message || 'Failed to delete post. Please try again.');
      }
    } catch (err) {
      setDeleteError('An error occurred while deleting the post.');
    } finally {
      setDeletingPostId(null);
    }
  }, [removePost]);

  const handleDeleteCancel = useCallback(() => {
    setShowDeleteDialog(false);
    setPostToDelete(null);
    setDeleteError(null);
    setDeletingPostId(null);
  }, []);

  if (loading) {
    return <LoadingSpinner message="Loading posts..." />;
  }

  if (error) {
    return (
      <div className="post-list-container">
        <NetworkErrorHandler 
          error={error} 
          onRetry={refreshPosts}
          operation="loading posts"
          showDetails={true}
        />
      </div>
    );
  }

  return (
    <div className="post-list-container">
      {/* Success Message */}
      {successMessage && (
        <div className="success-message">
          {successMessage}
        </div>
      )}

      {/* Delete Error Message */}
      {deleteError && (
        <div className="delete-error-message">
          {deleteError}
          <button 
            className="close-error-button"
            onClick={() => setDeleteError(null)}
            type="button"
          >
            ×
          </button>
        </div>
      )}

      <div className="post-list-header">
        <h2>Blog Posts</h2>
        <button 
          className="add-post-button" 
          onClick={handleAddPost}
          type="button"
        >
          Add New Post
        </button>
      </div>

      {hasNoPosts ? (
        <div className="no-posts">
          <p>{!isValidPostsArray ? 'Error loading posts.' : 'No blog posts found.'}</p>
          <button 
            className="add-first-post-button" 
            onClick={handleAddPost}
            type="button"
          >
            Create Your First Post
          </button>
        </div>
      ) : (
        <div className="post-list-grid">
          {posts.map((post) => (
            <div key={post.id} className="post-list-item">
              {deletingPostId === post.id && (
                <div className="deleting-overlay">
                  <LoadingSpinner size="small" message="Deleting..." />
                </div>
              )}
              <PostCard 
                post={post} 
                onDelete={handleDeleteRequest}
              />
            </div>
          ))}
        </div>
      )}

      {/* Pagination */}
      {!hasNoPosts && !loading && (
        <Pagination
          currentPage={pagination.currentPage}
          totalPages={pagination.totalPages}
          totalItems={pagination.totalPosts}
          pageSize={pagination.pageSize}
          hasNext={pagination.hasNext}
          hasPrevious={pagination.hasPrevious}
          onPageChange={goToPage}
          onPageSizeChange={changePageSize}
          pageSizeOptions={[5, 10, 20, 50]}
          showPageSizeSelector={true}
          showInfo={true}
        />
      )}

      {/* Delete Confirmation Dialog */}
      <PostConfirmDelete
        post={postToDelete}
        isOpen={showDeleteDialog}
        isDeleting={deletingPostId !== null}
        onConfirm={handleDeleteConfirm}
        onCancel={handleDeleteCancel}
      />
    </div>
  );
};

export default PostList;