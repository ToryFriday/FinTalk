import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import PostConfirmDelete from './PostConfirmDelete';
import './PostDetail.css';

/**
 * PostDetail component for displaying complete post information
 * @param {Object} props - Component props
 * @param {Object} props.post - Post data object
 * @param {Function} props.onDelete - Optional delete handler function
 * @param {boolean} props.isDeleting - Whether deletion is in progress
 */
const PostDetail = ({ post, onDelete, isDeleting = false }) => {
  const [showDeleteDialog, setShowDeleteDialog] = useState(false);

  const formatDate = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const formatTags = (tags) => {
    if (!tags) return [];
    return tags.split(',').map(tag => tag.trim()).filter(tag => tag.length > 0);
  };

  const handleDeleteRequest = () => {
    setShowDeleteDialog(true);
  };

  const handleDeleteConfirm = (postId) => {
    if (onDelete) {
      onDelete(postId);
    }
  };

  const handleDeleteCancel = () => {
    setShowDeleteDialog(false);
  };

  return (
    <article className="post-detail">
      {post.image_url && (
        <div className="post-detail-image">
          <img src={post.image_url} alt={post.title} />
        </div>
      )}
      
      <header className="post-detail-header">
        <h1 className="post-detail-title">{post.title}</h1>
        
        <div className="post-detail-meta">
          <div className="post-detail-author">
            <span className="author-label">By</span>
            <span className="author-name">{post.author}</span>
          </div>
          
          <div className="post-detail-dates">
            <div className="date-item">
              <span className="date-label">Published:</span>
              <span className="date-value">{formatDate(post.created_at)}</span>
            </div>
            {post.updated_at !== post.created_at && (
              <div className="date-item">
                <span className="date-label">Updated:</span>
                <span className="date-value">{formatDate(post.updated_at)}</span>
              </div>
            )}
          </div>
        </div>
        
        {post.tags && formatTags(post.tags).length > 0 && (
          <div className="post-detail-tags">
            {formatTags(post.tags).map((tag, index) => (
              <span key={index} className="post-detail-tag">
                {tag}
              </span>
            ))}
          </div>
        )}
      </header>
      
      <div className="post-detail-content">
        {post.content.split('\n').map((paragraph, index) => (
          paragraph.trim() ? (
            <p key={index} className="post-paragraph">
              {paragraph}
            </p>
          ) : (
            <br key={index} />
          )
        ))}
      </div>
      
      <footer className="post-detail-actions">
        <div className="navigation-actions">
          <Link to="/" className="action-button secondary-button">
            ← Back to Home
          </Link>
        </div>
        
        <div className="post-actions">
          <Link 
            to={`/posts/${post.id}/edit`} 
            className="action-button primary-button"
          >
            Edit Post
          </Link>
          {onDelete && (
            <button 
              className="action-button danger-button" 
              onClick={handleDeleteRequest}
              disabled={isDeleting}
              type="button"
            >
              {isDeleting ? 'Deleting...' : 'Delete Post'}
            </button>
          )}
        </div>
      </footer>

      {/* Delete Confirmation Dialog */}
      <PostConfirmDelete
        post={post}
        isOpen={showDeleteDialog}
        isDeleting={isDeleting}
        onConfirm={handleDeleteConfirm}
        onCancel={handleDeleteCancel}
      />
    </article>
  );
};

export default PostDetail;