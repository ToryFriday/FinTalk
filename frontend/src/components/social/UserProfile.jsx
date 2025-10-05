import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { getUserSocialProfile } from '../../services/socialService';
import { getUserPosts } from '../../services/postService';
import FollowButton from './FollowButton';
import PostCard from '../posts/PostCard';
import FollowersList from './FollowersList';
import FollowingList from './FollowingList';
import './UserProfile.css';

const UserProfile = () => {
  const { userId } = useParams();
  const [profile, setProfile] = useState(null);
  const [posts, setPosts] = useState([]);
  const [activeTab, setActiveTab] = useState('posts');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [postsLoading, setPostsLoading] = useState(false);

  useEffect(() => {
    const fetchProfile = async () => {
      try {
        setLoading(true);
        const response = await getUserSocialProfile(userId);
        setProfile(response.data);
      } catch (error) {
        console.error('Error fetching user profile:', error);
        setError('Failed to load user profile');
      } finally {
        setLoading(false);
      }
    };

    if (userId) {
      fetchProfile();
    }
  }, [userId]);

  useEffect(() => {
    const fetchPosts = async () => {
      if (activeTab === 'posts' && profile) {
        try {
          setPostsLoading(true);
          const response = await getUserPosts(userId);
          setPosts(response.data.results || []);
        } catch (error) {
          console.error('Error fetching user posts:', error);
        } finally {
          setPostsLoading(false);
        }
      }
    };

    fetchPosts();
  }, [activeTab, profile, userId]);

  const handleFollowChange = (followData) => {
    setProfile(prev => ({
      ...prev,
      followers_count: followData.followersCount,
      is_following: followData.isFollowing
    }));
  };

  const renderTabContent = () => {
    switch (activeTab) {
      case 'posts':
        if (postsLoading) {
          return <div className="loading">Loading posts...</div>;
        }
        return (
          <div className="posts-grid">
            {posts.length > 0 ? (
              posts.map(post => (
                <PostCard key={post.id} post={post} />
              ))
            ) : (
              <div className="no-posts">
                <p>No posts yet</p>
              </div>
            )}
          </div>
        );
      
      case 'followers':
        return <FollowersList userId={userId} />;
      
      case 'following':
        return <FollowingList userId={userId} />;
      
      default:
        return null;
    }
  };

  if (loading) {
    return (
      <div className="user-profile-loading">
        <div className="loading-spinner">Loading profile...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="user-profile-error">
        <h2>Error</h2>
        <p>{error}</p>
        <button onClick={() => window.location.reload()}>
          Try Again
        </button>
      </div>
    );
  }

  if (!profile) {
    return (
      <div className="user-profile-not-found">
        <h2>User Not Found</h2>
        <p>The user you're looking for doesn't exist or has been deactivated.</p>
        <Link to="/">Go Home</Link>
      </div>
    );
  }

  return (
    <div className="user-profile">
      <div className="profile-header">
        <div className="profile-avatar">
          {profile.avatar_url ? (
            <img src={profile.avatar_url} alt={`${profile.full_name}'s avatar`} />
          ) : (
            <div className="avatar-placeholder">
              {profile.full_name.charAt(0).toUpperCase()}
            </div>
          )}
        </div>
        
        <div className="profile-info">
          <div className="profile-name-section">
            <h1 className="profile-name">{profile.full_name}</h1>
            <p className="profile-username">@{profile.username}</p>
          </div>
          
          {profile.bio && (
            <p className="profile-bio">{profile.bio}</p>
          )}
          
          <div className="profile-meta">
            {profile.location && (
              <span className="profile-location">
                📍 {profile.location}
              </span>
            )}
            {profile.website && (
              <a 
                href={profile.website} 
                target="_blank" 
                rel="noopener noreferrer"
                className="profile-website"
              >
                🔗 Website
              </a>
            )}
          </div>
          
          <div className="profile-stats">
            <div className="stat">
              <span className="stat-number">{profile.posts_count}</span>
              <span className="stat-label">Posts</span>
            </div>
            <div className="stat">
              <span className="stat-number">{profile.followers_count}</span>
              <span className="stat-label">Followers</span>
            </div>
            <div className="stat">
              <span className="stat-number">{profile.following_count}</span>
              <span className="stat-label">Following</span>
            </div>
            {profile.mutual_followers_count > 0 && (
              <div className="stat">
                <span className="stat-number">{profile.mutual_followers_count}</span>
                <span className="stat-label">Mutual</span>
              </div>
            )}
          </div>
        </div>
        
        <div className="profile-actions">
          <FollowButton
            userId={profile.user_id}
            username={profile.username}
            onFollowChange={handleFollowChange}
            className="large"
          />
        </div>
      </div>
      
      <div className="profile-tabs">
        <button
          className={`tab ${activeTab === 'posts' ? 'active' : ''}`}
          onClick={() => setActiveTab('posts')}
        >
          Posts ({profile.posts_count})
        </button>
        <button
          className={`tab ${activeTab === 'followers' ? 'active' : ''}`}
          onClick={() => setActiveTab('followers')}
        >
          Followers ({profile.followers_count})
        </button>
        <button
          className={`tab ${activeTab === 'following' ? 'active' : ''}`}
          onClick={() => setActiveTab('following')}
        >
          Following ({profile.following_count})
        </button>
      </div>
      
      <div className="profile-content">
        {renderTabContent()}
      </div>
    </div>
  );
};

export default UserProfile;