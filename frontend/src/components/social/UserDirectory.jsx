import React, { useState, useEffect, useCallback } from 'react';
import { Link } from 'react-router-dom';
import { searchUsersToFollow, getSuggestedUsers } from '../../services/socialService';
import FollowButton from './FollowButton';
import './UserDirectory.css';

/**
 * UserDirectory component for discovering and searching writers
 * Includes search functionality, filters, and suggested users
 */
const UserDirectory = () => {
  const [users, setUsers] = useState([]);
  const [suggestedUsers, setSuggestedUsers] = useState([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [suggestedLoading, setSuggestedLoading] = useState(false);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('suggested');
  const [filters, setFilters] = useState({
    role: 'all',
    sortBy: 'followers'
  });

  // Debounced search function
  const debounce = (func, wait) => {
    let timeout;
    return function executedFunction(...args) {
      const later = () => {
        clearTimeout(timeout);
        func(...args);
      };
      clearTimeout(timeout);
      timeout = setTimeout(later, wait);
    };
  };

  const searchUsers = useCallback(
    debounce(async (query, filterOptions) => {
      if (!query.trim()) {
        setUsers([]);
        return;
      }

      setLoading(true);
      setError(null);

      try {
        const params = {
          search: query,
          role: filterOptions.role !== 'all' ? filterOptions.role : undefined,
          ordering: filterOptions.sortBy === 'followers' ? '-followers_count' : 
                   filterOptions.sortBy === 'posts' ? '-posts_count' : 
                   filterOptions.sortBy === 'recent' ? '-date_joined' : undefined,
          limit: 20
        };

        const response = await searchUsersToFollow(query, params);
        setUsers(response.data.results || []);
      } catch (error) {
        console.error('Error searching users:', error);
        setError('Failed to search users. Please try again.');
      } finally {
        setLoading(false);
      }
    }, 300),
    []
  );

  const fetchSuggestedUsers = async () => {
    setSuggestedLoading(true);
    setError(null);

    try {
      const response = await getSuggestedUsers({ limit: 12 });
      setSuggestedUsers(response.data.results || []);
    } catch (error) {
      console.error('Error fetching suggested users:', error);
      setError('Failed to load suggested users.');
    } finally {
      setSuggestedLoading(false);
    }
  };

  useEffect(() => {
    fetchSuggestedUsers();
  }, []);

  useEffect(() => {
    if (activeTab === 'search' && searchQuery) {
      searchUsers(searchQuery, filters);
    }
  }, [searchQuery, filters, activeTab, searchUsers]);

  const handleSearchChange = (e) => {
    const query = e.target.value;
    setSearchQuery(query);
    
    if (activeTab !== 'search') {
      setActiveTab('search');
    }
  };

  const handleFilterChange = (filterType, value) => {
    setFilters(prev => ({
      ...prev,
      [filterType]: value
    }));
  };

  const handleFollowChange = (userId, followData) => {
    // Update user in both lists
    const updateUserInList = (userList) => 
      userList.map(user => 
        user.user_id === userId 
          ? { ...user, is_following: followData.isFollowing, followers_count: followData.followersCount }
          : user
      );

    setUsers(updateUserInList);
    setSuggestedUsers(updateUserInList);
  };

  const renderUserCard = (user) => (
    <div key={user.user_id} className="user-card">
      <div className="user-card-header">
        <Link to={`/profile/${user.user_id}`} className="user-avatar-link">
          {user.avatar_url ? (
            <img src={user.avatar_url} alt={`${user.full_name}'s avatar`} className="user-avatar" />
          ) : (
            <div className="user-avatar-placeholder">
              {user.full_name.charAt(0).toUpperCase()}
            </div>
          )}
        </Link>
        <div className="user-info">
          <Link to={`/profile/${user.user_id}`} className="user-name-link">
            <h3 className="user-name">{user.full_name}</h3>
          </Link>
          <p className="user-username">@{user.username}</p>
          {user.role && user.role !== 'reader' && (
            <span className={`user-role role-${user.role}`}>
              {user.role.charAt(0).toUpperCase() + user.role.slice(1)}
            </span>
          )}
        </div>
        <div className="user-actions">
          <FollowButton
            userId={user.user_id}
            username={user.username}
            onFollowChange={(followData) => handleFollowChange(user.user_id, followData)}
            size="small"
          />
        </div>
      </div>
      
      {user.bio && (
        <div className="user-bio">
          <p>{user.bio}</p>
        </div>
      )}
      
      <div className="user-stats">
        <div className="stat">
          <span className="stat-number">{user.posts_count || 0}</span>
          <span className="stat-label">Posts</span>
        </div>
        <div className="stat">
          <span className="stat-number">{user.followers_count || 0}</span>
          <span className="stat-label">Followers</span>
        </div>
        {user.mutual_followers_count > 0 && (
          <div className="stat">
            <span className="stat-number">{user.mutual_followers_count}</span>
            <span className="stat-label">Mutual</span>
          </div>
        )}
      </div>
    </div>
  );

  return (
    <div className="user-directory">
      <div className="user-directory-header">
        <h1>Discover Writers</h1>
        <p>Find and follow interesting writers in the FinTalk community</p>
      </div>

      <div className="search-section">
        <div className="search-input-container">
          <input
            type="text"
            placeholder="Search for writers..."
            value={searchQuery}
            onChange={handleSearchChange}
            className="search-input"
          />
          <div className="search-icon">🔍</div>
        </div>

        <div className="filters">
          <div className="filter-group">
            <label>Role:</label>
            <select
              value={filters.role}
              onChange={(e) => handleFilterChange('role', e.target.value)}
            >
              <option value="all">All Users</option>
              <option value="writer">Writers</option>
              <option value="editor">Editors</option>
              <option value="admin">Admins</option>
            </select>
          </div>
          <div className="filter-group">
            <label>Sort by:</label>
            <select
              value={filters.sortBy}
              onChange={(e) => handleFilterChange('sortBy', e.target.value)}
            >
              <option value="followers">Most Followers</option>
              <option value="posts">Most Posts</option>
              <option value="recent">Recently Joined</option>
            </select>
          </div>
        </div>
      </div>

      <div className="directory-tabs">
        <button
          className={`tab ${activeTab === 'suggested' ? 'active' : ''}`}
          onClick={() => setActiveTab('suggested')}
        >
          Suggested for You
        </button>
        <button
          className={`tab ${activeTab === 'search' ? 'active' : ''}`}
          onClick={() => setActiveTab('search')}
        >
          Search Results {searchQuery && `(${users.length})`}
        </button>
      </div>

      <div className="directory-content">
        {error && (
          <div className="error-message">
            <p>{error}</p>
            <button onClick={() => window.location.reload()}>
              Try Again
            </button>
          </div>
        )}

        {activeTab === 'suggested' && (
          <div className="suggested-users">
            {suggestedLoading ? (
              <div className="loading-container">
                <div className="loading-spinner"></div>
                <p>Loading suggested users...</p>
              </div>
            ) : suggestedUsers.length > 0 ? (
              <div className="users-grid">
                {suggestedUsers.map(renderUserCard)}
              </div>
            ) : (
              <div className="empty-state">
                <h3>No suggestions available</h3>
                <p>Try following some users or check back later for personalized suggestions.</p>
              </div>
            )}
          </div>
        )}

        {activeTab === 'search' && (
          <div className="search-results">
            {loading ? (
              <div className="loading-container">
                <div className="loading-spinner"></div>
                <p>Searching users...</p>
              </div>
            ) : searchQuery ? (
              users.length > 0 ? (
                <div className="users-grid">
                  {users.map(renderUserCard)}
                </div>
              ) : (
                <div className="empty-state">
                  <h3>No users found</h3>
                  <p>Try adjusting your search terms or filters.</p>
                </div>
              )
            ) : (
              <div className="empty-state">
                <h3>Start searching</h3>
                <p>Enter a name or username to find writers to follow.</p>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default UserDirectory;