import React, { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import usePost from '../hooks/usePost';
import PostDetail from '../components/posts/PostDetail';
import LoadingSpinner from '../components/common/LoadingSpinner';
import ErrorMessage from '../components/common/ErrorMessage';
import NotFoundPage from './NotFoundPage';
import './ViewPostPage.css';

const ViewPostPage = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const { post, loading, error, fetchPost, deletePost } = usePost(parseInt(id));
  const [isDeleting, setIsDeleting] = useState(false);

  const handleDelete = async (postId) => {
    setIsDeleting(true);
    try {
      const result = await deletePost(postId);
      if (result.success) {
        // Navigate back to home page after successful deletion
        navigate('/', { 
          state: { 
            message: 'Post deleted successfully',
            type: 'success' 
          }
        });
      } else {
        // Handle deletion error - could show an error message
        console.error('Failed to delete post:', result.error);
      }
    } finally {
      setIsDeleting(false);
    }
  };

  const handleRetry = () => {
    fetchPost(parseInt(id));
  };

  // Show loading spinner while fetching post
  if (loading) {
    return (
      <div className="view-post-page">
        <LoadingSpinner message="Loading post..." />
      </div>
    );
  }

  // Show 404 page if post not found
  if (error && error.type === 'NOT_FOUND') {
    return <NotFoundPage />;
  }

  // Show error message for other errors
  if (error) {
    return (
      <div className="view-post-page">
        <ErrorMessage 
          error={error} 
          onRetry={handleRetry}
        />
      </div>
    );
  }

  // Show 404 if no post data (shouldn't happen with proper error handling)
  if (!post) {
    return <NotFoundPage />;
  }

  return (
    <div className="view-post-page">
      <PostDetail 
        post={post} 
        onDelete={handleDelete}
        isDeleting={isDeleting}
      />
    </div>
  );
};

export default ViewPostPage;