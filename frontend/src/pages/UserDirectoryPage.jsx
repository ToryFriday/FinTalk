import React from 'react';
import UserDirectory from '../components/social/UserDirectory';
import './UserDirectoryPage.css';

/**
 * UserDirectoryPage component for the user directory/search page
 * Wrapper page for the UserDirectory component
 */
const UserDirectoryPage = () => {
  return (
    <div className="user-directory-page">
      <UserDirectory />
    </div>
  );
};

export default UserDirectoryPage;