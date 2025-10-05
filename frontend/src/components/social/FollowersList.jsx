import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { getUserFollowers } from '../../services/socialService';
import FollowButton from './FollowButton';
import './FollowersList.css';

const FollowersList = ({ userId }) => {
  const [followers, setFollowers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [page, setPage] = useState(1);
  const [hasMore, setHasMore] = useState(true);
  const [totalCount, setTotalCount] = useState(0);

  useEffect(() => {
    const fetchFollowers = async () => {
      try {
        setLoading(true);
        const response = await getUserFollowers(userId, { page: 1 });
        setFollowers(response.data.results || []);
        setTotalCount(response.data.count || 0);
        setHasMore(response.data.next !== null);
        setPage(1);
      } catch (error) {
        console.error('Error fetching followers:', error);
        setError('Failed to load followers');
      } finally {
        setLoading(false);
      }
    };

    if (userId) {
      fetchFollowers();
    }
  }, [userId]);

  const loadMore = async () => {
    if (loading || !hasMore) return;

    try {
      setLoading(true);
      const nextPage = page + 1;
      const response = await getUserFollowers(userId, { page: nextPage });
      setFollowers(prev => [...prev, ...(response.data.results || [])]);
      setHasMore(response.data.next !== null);
      setPage(nextPage);
    } catch (error) {
      console.error('Error loading more followers:', error);
      setError('Failed to load more followers');
    } finally {
      setLoading(false);
    }
  };

  const handleFollowChange = (followData) => {
    // Update the followers list to reflect follow status changes
    setFollowers(prev => prev.map(follower => 
      follower.user_id === followData.userId 
        ? { ...follower, is_following: followData.isFollowing }
        : follower
    ));
  };

  if (loading && followers.length === 0) {
    return (
      <div className="followers-list-loading">
        <div className="loading-spinner">Loading followers...</div>
      </div>
    );
  }

  if (error && followers.length === 0) {
    return (
      <div className="followers-list-error">
        <p>{error}</p>
        <button onClick={() => window.location.reload()}>
          Try Again
        </button>
      </div>
    );
  }

  if (followers.length === 0) {
    return (
      <div className="followers-list-empty">
        <div className="empty-state">
          <div className="empty-icon">👥</div>
          <h3>No followers yet</h3>
          <p>When people follow this user, they'll appear here.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="followers-list">
      <div className="followers-header">
        <h3>Followers ({totalCount})</h3>
      </div>
      
      <div className="followers-grid">
        {followers.map((follower) => (
          <div key={follower.id} className="follower-card">
            <Link to={`/users/${follower.user_id}`} className="follower-link">
              <div className="follower-avatar">
                {follower.avatar_url ? (
                  <img src={follower.avatar_url} alt={`${follower.full_name}'s avatar`} />
                ) : (
                  <div className="avatar-placeholder">
                    {follower.full_name.charAt(0).toUpperCase()}
                  </div>
                )}
              </div>
              
              <div className="follower-info">
                <h4 className="follower-name">{follower.full_name}</h4>
                <p className="follower-username">@{follower.username}</p>
                {follower.bio && (
                  <p className="follower-bio">{follower.bio}</p>
                )}
                
                <div className="follower-stats">
                  <span className="stat">
                    {follower.followers_count} followers
                  </span>
                  <span className="stat">
                    {follower.following_count} following
                  </span>
                </div>
              </div>
            </Link>
            
            <div className="follower-actions">
              <FollowButton
                userId={follower.user_id}
                username={follower.username}
                onFollowChange={handleFollowChange}
                className="compact"
              />
            </div>
          </div>
        ))}
      </div>
      
      {hasMore && (
        <div className="load-more-section">
          <button
            onClick={loadMore}
            disabled={loading}
            className="load-more-button"
          >
            {loading ? 'Loading...' : 'Load More'}
          </button>
        </div>
      )}
      
      {error && followers.length > 0 && (
        <div className="load-more-error">
          <p>{error}</p>
        </div>
      )}
    </div>
  );
};

export default FollowersList;