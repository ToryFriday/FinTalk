import React from 'react';
import DraftsList from '../components/posts/DraftsList';
import './DraftsPage.css';

/**
 * DraftsPage component - Page for managing draft posts
 */
const DraftsPage = () => {
  return (
    <div className="drafts-page">
      <div className="page-header">
        <h1>Draft Management</h1>
        <p>Manage your unpublished posts and schedule them for publication</p>
      </div>
      
      <main className="page-content">
        <DraftsList />
      </main>
    </div>
  );
};

export default DraftsPage;