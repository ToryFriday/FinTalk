import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { getUserFollowing } from '../../services/socialService';
import FollowButton from './FollowButton';
import './FollowingList.css';

const FollowingList = ({ userId }) => {
  const [following, setFollowing] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [page, setPage] = useState(1);
  const [hasMore, setHasMore] = useState(true);
  const [totalCount, setTotalCount] = useState(0);

  useEffect(() => {
    const fetchFollowing = async () => {
      try {
        setLoading(true);
        const response = await getUserFollowing(userId, { page: 1 });
        setFollowing(response.data.results || []);
        setTotalCount(response.data.count || 0);
        setHasMore(response.data.next !== null);
        setPage(1);
      } catch (error) {
        console.error('Error fetching following:', error);
        setError('Failed to load following');
      } finally {
        setLoading(false);
      }
    };

    if (userId) {
      fetchFollowing();
    }
  }, [userId]);

  const loadMore = async () => {
    if (loading || !hasMore) return;

    try {
      setLoading(true);
      const nextPage = page + 1;
      const response = await getUserFollowing(userId, { page: nextPage });
      setFollowing(prev => [...prev, ...(response.data.results || [])]);
      setHasMore(response.data.next !== null);
      setPage(nextPage);
    } catch (error) {
      console.error('Error loading more following:', error);
      setError('Failed to load more following');
    } finally {
      setLoading(false);
    }
  };

  const handleFollowChange = (followData) => {
    // Update the following list to reflect follow status changes
    setFollowing(prev => prev.map(user => 
      user.user_id === followData.userId 
        ? { ...user, is_following: followData.isFollowing }
        : user
    ));
  };

  if (loading && following.length === 0) {
    return (
      <div className="following-list-loading">
        <div className="loading-spinner">Loading following...</div>
      </div>
    );
  }

  if (error && following.length === 0) {
    return (
      <div className="following-list-error">
        <p>{error}</p>
        <button onClick={() => window.location.reload()}>
          Try Again
        </button>
      </div>
    );
  }

  if (following.length === 0) {
    return (
      <div className="following-list-empty">
        <div className="empty-state">
          <div className="empty-icon">👤</div>
          <h3>Not following anyone yet</h3>
          <p>When this user follows people, they'll appear here.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="following-list">
      <div className="following-header">
        <h3>Following ({totalCount})</h3>
      </div>
      
      <div className="following-grid">
        {following.map((user) => (
          <div key={user.id} className="following-card">
            <Link to={`/users/${user.user_id}`} className="following-link">
              <div className="following-avatar">
                {user.avatar_url ? (
                  <img src={user.avatar_url} alt={`${user.full_name}'s avatar`} />
                ) : (
                  <div className="avatar-placeholder">
                    {user.full_name.charAt(0).toUpperCase()}
                  </div>
                )}
              </div>
              
              <div className="following-info">
                <h4 className="following-name">{user.full_name}</h4>
                <p className="following-username">@{user.username}</p>
                {user.bio && (
                  <p className="following-bio">{user.bio}</p>
                )}
                
                <div className="following-stats">
                  <span className="stat">
                    {user.followers_count} followers
                  </span>
                  <span className="stat">
                    {user.following_count} following
                  </span>
                </div>
              </div>
            </Link>
            
            <div className="following-actions">
              <FollowButton
                userId={user.user_id}
                username={user.username}
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
      
      {error && following.length > 0 && (
        <div className="load-more-error">
          <p>{error}</p>
        </div>
      )}
    </div>
  );
};

export default FollowingList;