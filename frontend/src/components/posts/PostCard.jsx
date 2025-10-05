import React, { memo, useMemo, useCallback } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { POST_STATUS_DISPLAY } from '../../utils/constants';
import { useResponsive } from '../../hooks/useResponsive';
import { useAccessibility } from '../../hooks/useAccessibility';
import SaveButton from './SaveButton';
import CommentCount from '../common/CommentCount';
import Button from '../common/Button';
import './PostCard.css';

/**
 * PostCard component for displaying individual post information
 * Memoized for performance optimization
 * @param {Object} props - Component props
 * @param {Object} props.post - Post data object
 * @param {Function} props.onDelete - Delete handler function
 * @param {boolean} props.isAuthenticated - Whether user is authenticated
 * @param {Function} props.onSaveChange - Callback when save status changes
 */
const PostCard = memo(({ post, onDelete, isAuthenticated = false, onSaveChange }) => {
  const navigate = useNavigate();
  const { isMobile } = useResponsive();
  const { announce } = useAccessibility();

  // Memoized event handlers to prevent unnecessary re-renders
  const handleView = useCallback(() => {
    navigate(`/posts/${post.id}`);
    announce(`Navigating to post: ${post.title}`, 'polite');
  }, [navigate, post.id, post.title, announce]);

  const handleEdit = useCallback(() => {
    navigate(`/posts/${post.id}/edit`);
    announce(`Editing post: ${post.title}`, 'polite');
  }, [navigate, post.id, post.title, announce]);

  const handleDelete = useCallback(() => {
    if (onDelete) {
      onDelete(post.id);
      announce(`Delete requested for post: ${post.title}`, 'polite');
    }
  }, [onDelete, post.id, post.title, announce]);

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

  const cardClasses = [
    'post-card',
    isMobile && 'post-card-mobile'
  ].filter(Boolean).join(' ');

  return (
    <article 
      className={cardClasses}
      role="article"
      aria-labelledby={`post-title-${post.id}`}
      aria-describedby={`post-excerpt-${post.id}`}
    >
      {post.image_url && (
        <div className="post-card-image">
          <img 
            src={post.image_url} 
            alt={`Featured image for ${post.title}`}
            loading="lazy"
            onError={(e) => {
              e.target.style.display = 'none';
            }}
          />
        </div>
      )}
      
      <div className="post-card-content">
        <h3 id={`post-title-${post.id}`} className="post-card-title">
          <Link 
            to={`/posts/${post.id}`}
            className="post-title-link"
            aria-label={`Read full post: ${post.title}`}
          >
            {post.title}
          </Link>
        </h3>
        
        <div className="post-card-meta" role="group" aria-label="Post metadata">
          <div className="post-card-author">
            <span className="author-label sr-only">Author:</span>
            {post.author_user ? (
              <Link 
                to={`/profile/${post.author_user}`} 
                className="author-link"
                aria-label={`View profile of ${post.author}`}
              >
                {post.author}
              </Link>
            ) : (
              <span>{post.author}</span>
            )}
          </div>
          
          <time 
            className="post-card-date" 
            dateTime={post.created_at}
            aria-label={`Published on ${formattedDate}`}
          >
            {formattedDate}
          </time>
          
          {post.status === 'published' && (
            <CommentCount 
              postId={post.id} 
              className="compact" 
              showZero={false}
            />
          )}
          
          {post.status && (
            <span 
              className={`status-badge status-${post.status}`}
              aria-label={`Post status: ${POST_STATUS_DISPLAY[post.status] || post.status}`}
            >
              {POST_STATUS_DISPLAY[post.status] || post.status}
            </span>
          )}
        </div>
        
        <p 
          id={`post-excerpt-${post.id}`}
          className="post-card-excerpt"
        >
          {truncatedContent}
        </p>
        
        {formattedTags.length > 0 && (
          <div className="post-card-tags" role="group" aria-label="Post tags">
            {formattedTags.map((tag, index) => (
              <span 
                key={index} 
                className="post-tag"
                role="button"
                tabIndex="0"
                aria-label={`Tag: ${tag}`}
              >
                {tag}
              </span>
            ))}
          </div>
        )}
        
        <div className="post-card-actions" role="group" aria-label="Post actions">
          <Button
            variant="primary"
            size={isMobile ? 'sm' : 'md'}
            onClick={handleView}
            ariaLabel={`View full post: ${post.title}`}
          >
            View
          </Button>
          
          <Button
            variant="secondary"
            size={isMobile ? 'sm' : 'md'}
            onClick={handleEdit}
            ariaLabel={`Edit post: ${post.title}`}
          >
            Edit
          </Button>
          
          <Button
            variant="danger"
            size={isMobile ? 'sm' : 'md'}
            onClick={handleDelete}
            ariaLabel={`Delete post: ${post.title}`}
          >
            Delete
          </Button>
          
          {post.status === 'published' && (
            <SaveButton
              postId={post.id}
              isAuthenticated={isAuthenticated}
              className="compact"
              onSaveChange={onSaveChange}
              size={isMobile ? 'sm' : 'md'}
            />
          )}
        </div>
      </div>
    </article>
  );
});

// Display name for debugging
PostCard.displayName = 'PostCard';

export default PostCard;