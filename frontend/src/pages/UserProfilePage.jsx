import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { getUserSocialProfile } from '../services/socialService';
import { getUserPosts } from '../services/postService';
import UserProfile from '../components/social/UserProfile';
import './UserProfilePage.css';

/**
 * UserProfilePage component for displaying comprehensive user profiles
 * Shows user information, articles, followers, and activity
 */
const UserProfilePage = () => {
  const { userId } = useParams();
  const navigate = useNavigate();
  const [profile, setProfile] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchProfile = async () => {
      try {
        setLoading(true);
        setError(null);
        
        const response = await getUserSocialProfile(userId);
        setProfile(response.data);
      } catch (error) {
        console.error('Error fetching user profile:', error);
        if (error.response?.status === 404) {
          setError('User not found');
        } else {
          setError('Failed to load user profile');
        }
      } finally {
        setLoading(false);
      }
    };

    if (userId) {
      fetchProfile();
    } else {
      setError('Invalid user ID');
      setLoading(false);
    }
  }, [userId]);

  if (loading) {
    return (
      <div className="user-profile-page">
        <div className="loading-container">
          <div className="loading-spinner"></div>
          <p>Loading profile...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="user-profile-page">
        <div className="error-container">
          <h2>Error</h2>
          <p>{error}</p>
          <div className="error-actions">
            <button onClick={() => window.location.reload()}>
              Try Again
            </button>
            <button onClick={() => navigate('/')}>
              Go Home
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="user-profile-page">
      <UserProfile />
    </div>
  );
};

export default UserProfilePage;