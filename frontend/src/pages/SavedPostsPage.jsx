import React from 'react';
import SavedPosts from '../components/posts/SavedPosts';

/**
 * SavedPostsPage - Page component for displaying user's saved articles
 */
const SavedPostsPage = () => {
  return (
    <div className="saved-posts-page">
      <SavedPosts />
    </div>
  );
};

export default SavedPostsPage;