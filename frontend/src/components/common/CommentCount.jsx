import React, { useState, useEffect } from 'react';
import disqusService from '../../services/disqusService';
import './CommentCount.css';

/**
 * CommentCount component for displaying Disqus comment counts
 * @param {Object} props - Component props
 * @param {string|number} props.postId - Post ID
 * @param {string} props.postSlug - Optional post slug
 * @param {string} props.className - Additional CSS classes
 * @param {boolean} props.showZero - Whether to show "0 comments" or hide when zero
 */
const CommentCount = ({ postId, postSlug, className = '', showZero = true }) => {
  const [count, setCount] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [hasError, setHasError] = useState(false);

  useEffect(() => {
    // Don't fetch if Disqus is not configured
    if (!disqusService.isConfigured()) {
      setIsLoading(false);
      setHasError(true);
      return;
    }
    let isMounted = true;

    const fetchCommentCount = async () => {

      try {
        setIsLoading(true);
        setHasError(false);
        
        const commentCount = await disqusService.getCommentCount(postId, postSlug);
        
        if (isMounted) {
          setCount(commentCount);
          setIsLoading(false);
        }
      } catch (error) {
        console.error('Error fetching comment count:', error);
        if (isMounted) {
          setHasError(true);
          setIsLoading(false);
          setCount(0);
        }
      }
    };

    fetchCommentCount();

    return () => {
      isMounted = false;
    };
  }, [postId, postSlug]);

  // Don't render if Disqus is not configured
  if (!disqusService.isConfigured()) {
    return null;
  }

  // Don't render if loading and no count yet
  if (isLoading && count === null) {
    return (
      <span className={`comment-count loading ${className}`}>
        <span className="comment-count-spinner" data-testid="comment-count-spinner"></span>
      </span>
    );
  }

  // Don't render if count is 0 and showZero is false
  if (!showZero && count === 0) {
    return null;
  }

  // Handle error state
  if (hasError && count === null) {
    return null; // Silently fail for comment counts
  }

  const displayCount = count || 0;
  const commentText = displayCount === 1 ? 'comment' : 'comments';

  return (
    <span 
      className={`comment-count ${className}`}
      data-disqus-identifier={disqusService.getPostIdentifier(postId, postSlug)}
    >
      <span className="comment-count-number">{displayCount}</span>
      <span className="comment-count-text">{commentText}</span>
    </span>
  );
};

export default CommentCount;