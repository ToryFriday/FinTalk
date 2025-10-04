import React, { memo, useMemo, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import './PostCard.css';

/**
 * PostCard component for displaying individual post information
 * Memoized for performance optimization
 * @param {Object} props - Component props
 * @param {Object} props.post - Post data object
 * @param {Function} props.onDelete - Delete handler function
 */
const PostCard = memo(({ post, onDelete }) => {
  const navigate = useNavigate();

  // Memoized event handlers to prevent unnecessary re-renders
  const handleView = useCallback(() => {
    navigate(`/posts/${post.id}`);
  }, [navigate, post.id]);

  const handleEdit = useCallback(() => {
    navigate(`/posts/${post.id}/edit`);
  }, [navigate, post.id]);

  const handleDelete = useCallback(() => {
    if (onDelete) {
      onDelete(post.id);
    }
  }, [onDelete, post.id]);

  // Memoized computed values to avoid recalculation on every render
  const formattedDate = useMemo(() => {
    const date = new Date(post.created_at);
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  }, [post.created_at]);

  const truncatedContent = useMemo(() => {
    const maxLength = 150;
    if (post.content.length <= maxLength) return post.content;
    return post.content.substring(0, maxLength) + '...';
  }, [post.content]);

  const formattedTags = useMemo(() => {
    if (!post.tags) return [];
    return post.tags.split(',').map(tag => tag.trim()).filter(tag => tag.length > 0);
  }, [post.tags]);

  return (
    <div className="post-card">
      {post.image_url && (
        <div className="post-card-image">
          <img src={post.image_url} alt={post.title} />
        </div>
      )}
      
      <div className="post-card-content">
        <h3 className="post-card-title">{post.title}</h3>
        
        <div className="post-card-meta">
          <span className="post-card-author">By {post.author}</span>
          <span className="post-card-date">{formattedDate}</span>
        </div>
        
        <p className="post-card-excerpt">
          {truncatedContent}
        </p>
        
        {formattedTags.length > 0 && (
          <div className="post-card-tags">
            {formattedTags.map((tag, index) => (
              <span key={index} className="post-tag">
                {tag}
              </span>
            ))}
          </div>
        )}
        
        <div className="post-card-actions">
          <button 
            className="action-button view-button" 
            onClick={handleView}
            type="button"
          >
            View
          </button>
          <button 
            className="action-button edit-button" 
            onClick={handleEdit}
            type="button"
          >
            Edit
          </button>
          <button 
            className="action-button delete-button" 
            onClick={handleDelete}
            type="button"
          >
            Delete
          </button>
        </div>
      </div>
    </div>
  );
});

// Display name for debugging
PostCard.displayName = 'PostCard';

export default PostCard;