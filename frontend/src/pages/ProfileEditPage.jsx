import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import ProfileEdit from '../components/social/ProfileEdit';
import api from '../services/api';
import './ProfileEditPage.css';

/**
 * ProfileEditPage component for editing user profile
 * Handles authentication check and profile data loading
 */
const ProfileEditPage = () => {
  const navigate = useNavigate();
  const [currentUser, setCurrentUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchCurrentUser = async () => {
      try {
        setLoading(true);
        const response = await api.get('/api/auth/me/');
        setCurrentUser(response.data);
      } catch (error) {
        console.error('Error fetching current user:', error);
        if (error.response?.status === 401) {
          // User not authenticated, redirect to login
          navigate('/login');
        } else {
          setError('Failed to load user profile');
        }
      } finally {
        setLoading(false);
      }
    };

    fetchCurrentUser();
  }, [navigate]);

  const handleProfileUpdate = (updatedProfile) => {
    setCurrentUser(updatedProfile);
  };

  if (loading) {
    return (
      <div className="profile-edit-page">
        <div className="loading-container">
          <div className="loading-spinner"></div>
          <p>Loading profile...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="profile-edit-page">
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
    <div className="profile-edit-page">
      <ProfileEdit 
        currentUser={currentUser} 
        onProfileUpdate={handleProfileUpdate}
      />
    </div>
  );
};

export default ProfileEditPage;