import React, { useState, useEffect } from 'react';
import { followUser, unfollowUser, checkFollowStatus } from '../../services/socialService';
import './FollowButton.css';

const FollowButton = ({ userId, username, onFollowChange, className = '' }) => {
  const [isFollowing, setIsFollowing] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [followersCount, setFollowersCount] = useState(0);
  const [error, setError] = useState(null);

  useEffect(() => {
    const checkStatus = async () => {
      try {
        const response = await checkFollowStatus(userId);
        setIsFollowing(response.data.is_following);
        setFollowersCount(response.data.followers_count);
      } catch (error) {
        console.error('Error checking follow status:', error);
        setError('Failed to load follow status');
      }
    };

    if (userId) {
      checkStatus();
    }
  }, [userId]);

  const handleFollowToggle = async () => {
    if (isLoading) return;

    setIsLoading(true);
    setError(null);

    try {
      let response;
      if (isFollowing) {
        response = await unfollowUser(userId);
      } else {
        response = await followUser(userId);
      }

      const newIsFollowing = response.data.is_following;
      const newFollowersCount = response.data.followers_count;

      setIsFollowing(newIsFollowing);
      setFollowersCount(newFollowersCount);

      // Notify parent component of the change
      if (onFollowChange) {
        onFollowChange({
          userId,
          isFollowing: newIsFollowing,
          followersCount: newFollowersCount,
          action: newIsFollowing ? 'followed' : 'unfollowed'
        });
      }

    } catch (error) {
      console.error('Error toggling follow status:', error);
      setError(error.response?.data?.error || 'Failed to update follow status');
    } finally {
      setIsLoading(false);
    }
  };

  if (error) {
    return (
      <div className={`follow-button-error ${className}`}>
        <span className="error-message">{error}</span>
        <button 
          onClick={() => setError(null)}
          className="retry-button"
          title="Retry"
        >
          ↻
        </button>
      </div>
    );
  }

  return (
    <div className={`follow-button-container ${className}`}>
      <button
        onClick={handleFollowToggle}
        disabled={isLoading}
        className={`follow-button ${isFollowing ? 'following' : 'not-following'} ${isLoading ? 'loading' : ''}`}
        title={isFollowing ? `Unfollow ${username}` : `Follow ${username}`}
      >
        {isLoading ? (
          <span className="loading-spinner">⟳</span>
        ) : (
          <>
            <span className="follow-icon">
              {isFollowing ? '✓' : '+'}
            </span>
            <span className="follow-text">
              {isFollowing ? 'Following' : 'Follow'}
            </span>
          </>
        )}
      </button>
      
      {followersCount > 0 && (
        <span className="followers-count" title={`${followersCount} followers`}>
          {followersCount} {followersCount === 1 ? 'follower' : 'followers'}
        </span>
      )}
    </div>
  );
};

export default FollowButton;