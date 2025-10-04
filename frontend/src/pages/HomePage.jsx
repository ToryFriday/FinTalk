import React, { useEffect, useState } from 'react';
import { useLocation } from 'react-router-dom';
import PostList from '../components/posts/PostList';
import './HomePage.css';

const HomePage = () => {
  const location = useLocation();
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