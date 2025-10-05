import React, { useEffect, useState } from 'react';
import { useLocation, Navigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import PostList from '../components/posts/PostList';
import './HomePage.css';

const HomePage = () => {
  const location = useLocation();
  const { isAuthenticated, loading } = useAuth();
  const [navigationMessage, setNavigationMessage] = useState(null);

  useEffect(() => {
    // Check if there's a success message from navigation
    if (location.state?.message) {
      setNavigationMessage({
        message: location.state.message,
        type: location.state.type || 'success'
      });
      
      // Clear the message after 3 seconds
      setTimeout(() => {
        setNavigationMessage(null);
      }, 3000);
      
      // Clear the navigation state to prevent showing the message on refresh
      window.history.replaceState({}, document.title);
    }
  }, [location.state]);

  // Show loading while checking authentication
  if (loading) {
    return (
      <div className="home-page">
        <div className="loading-container">
          <div className="loading-spinner">
            <div className="spinner"></div>
            <p>Loading...</p>
          </div>
        </div>
      </div>
    );
  }

  // Redirect to landing page if not authenticated
  if (!isAuthenticated) {
    return <Navigate to="/landing" replace />;
  }

  return (
    <div className="home-page">
      {navigationMessage && (
        <div className={`navigation-message ${navigationMessage.type}-message`}>
          {navigationMessage.message}
        </div>
      )}
      <PostList />
    </div>
  );
};

export default HomePage;