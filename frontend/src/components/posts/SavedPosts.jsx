import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import BlogAPI from '../../services/api';
import { formatErrorMessage } from '../../services/api';
import SaveButton from './SaveButton';
import './SavedPosts.css';

/**
 * SavedPosts component for displaying user's saved articles with filtering and search
 */
const SavedPosts = () => {
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();
  
  const [savedPosts, setSavedPosts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [pagination, setPagination] = useState({
    count: 0,
    next: null,
    previous: null,
    total_pages: 0,
    current_page: 1,
    page_size: 10
  });
  const [metadata, setMetadata] = useState({
    total_saved: 0,
    filters_applied: {}
  });

  // Get filter values from URL params
  const filters = useMemo(() => ({
    search: searchParams.get('search') || '',
    tag: searchParams.get('tag') || '',
    author: searchParams.get('author') || '',
    date_from: searchParams.get('date_from') || '',
    date_to: searchParams.get('date_to') || '',
    ordering: searchParams.get('ordering') || '-saved_at',
    page: parseInt(searchParams.get('page')) || 1,
    page_size: parseInt(searchParams.get('page_size')) || 10
  }), [searchParams]);

  // Load saved posts
  const loadSavedPosts = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      const response = await BlogAPI.getSavedPosts(filters);

      if (response.success) {
        setSavedPosts(response.data.results || []);
        setPagination({
          count: response.data.count || 0,
          next: response.data.next,
          previous: response.data.previous,
          total_pages: response.data.total_pages || 0,
          current_page: response.data.current_page || 1,
          page_size: response.data.page_size || 10
        });
        setMetadata(response.data.metadata || { total_saved: 0, filters_applied: {} });
      } else {
        const errorMessage = formatErrorMessage(response.error);
        setError(errorMessage);
      }
    } catch (error) {
      console.error('Error loading saved posts:', error);
      setError('Failed to load saved articles');
    } finally {
      setLoading(false);
    }
  }, [filters]);

  // Load posts when filters change
  useEffect(() => {
    loadSavedPosts();
  }, [loadSavedPosts]);

  // Update URL params when filters change
  const updateFilters = useCallback((newFilters) => {
    const params = new URLSearchParams();
    
    Object.entries({ ...filters, ...newFilters }).forEach(([key, value]) => {
      if (value && value !== '' && value !== 1) {
        params.set(key, value.toString());
      }
    });

    setSearchParams(params);
  }, [filters, setSearchParams]);

  // Handle search input
  const handleSearch = useCallback((searchTerm) => {
    updateFilters({ search: searchTerm, page: 1 });
  }, [updateFilters]);

  // Handle filter changes
  const handleFilterChange = useCallback((filterName, value) => {
    updateFilters({ [filterName]: value, page: 1 });
  }, [updateFilters]);

  // Handle pagination
  const handlePageChange = useCallback((page) => {
    updateFilters({ page });
  }, [updateFilters]);

  // Handle save status change
  const handleSaveChange = useCallback((postId, isSaved) => {
    if (!isSaved) {
      // Remove from list if unsaved
      setSavedPosts(prev => prev.filter(item => item.post !== postId));
      setPagination(prev => ({ ...prev, count: prev.count - 1 }));
      setMetadata(prev => ({ ...prev, total_saved: prev.total_saved - 1 }));
    }
  }, []);

  // Handle post click
  const handlePostClick = useCallback((postId) => {
    navigate(`/posts/${postId}`);
  }, [navigate]);

  // Format date
  const formatDate = useCallback((dateString) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  }, []);

  // Truncate content
  const truncateContent = useCallback((content, maxLength = 200) => {
    if (content.length <= maxLength) return content;
    return content.substring(0, maxLength) + '...';
  }, []);

  if (loading && savedPosts.length === 0) {
    return (
      <div className="saved-posts-container">
        <div className="loading-state">
          <div className="loading-spinner"></div>
          <p>Loading your saved articles...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="saved-posts-container">
      <div className="saved-posts-header">
        <h1>Saved Articles</h1>
        <p className="saved-count">
          {metadata.total_saved} article{metadata.total_saved !== 1 ? 's' : ''} saved
        </p>
      </div>

      {/* Filters */}
      <div className="saved-posts-filters">
        <div className="search-filter">
          <input
            type="text"
            placeholder="Search saved articles..."
            value={filters.search}
            onChange={(e) => handleSearch(e.target.value)}
            className="search-input"
          />
        </div>

        <div className="filter-row">
          <div className="filter-group">
            <label htmlFor="tag-filter">Tag:</label>
            <input
              id="tag-filter"
              type="text"
              placeholder="Filter by tag"
              value={filters.tag}
              onChange={(e) => handleFilterChange('tag', e.target.value)}
              className="filter-input"
            />
          </div>

          <div className="filter-group">
            <label htmlFor="author-filter">Author:</label>
            <input
              id="author-filter"
              type="text"
              placeholder="Filter by author"
              value={filters.author}
              onChange={(e) => handleFilterChange('author', e.target.value)}
              className="filter-input"
            />
          </div>

          <div className="filter-group">
            <label htmlFor="ordering-filter">Sort by:</label>
            <select
              id="ordering-filter"
              value={filters.ordering}
              onChange={(e) => handleFilterChange('ordering', e.target.value)}
              className="filter-select"
            >
              <option value="-saved_at">Recently Saved</option>
              <option value="saved_at">Oldest Saved</option>
              <option value="post__title">Title A-Z</option>
              <option value="-post__title">Title Z-A</option>
              <option value="-post__created_at">Newest Articles</option>
              <option value="post__created_at">Oldest Articles</option>
              <option value="-post__view_count">Most Popular</option>
            </select>
          </div>
        </div>

        <div className="date-filters">
          <div className="filter-group">
            <label htmlFor="date-from">Saved from:</label>
            <input
              id="date-from"
              type="date"
              value={filters.date_from}
              onChange={(e) => handleFilterChange('date_from', e.target.value)}
              className="filter-input"
            />
          </div>

          <div className="filter-group">
            <label htmlFor="date-to">Saved to:</label>
            <input
              id="date-to"
              type="date"
              value={filters.date_to}
              onChange={(e) => handleFilterChange('date_to', e.target.value)}
              className="filter-input"
            />
          </div>
        </div>
      </div>

      {/* Error state */}
      {error && (
        <div className="error-state" role="alert">
          <p>Error: {error}</p>
          <button onClick={loadSavedPosts} className="retry-button">
            Try Again
          </button>
        </div>
      )}

      {/* Empty state */}
      {!loading && !error && savedPosts.length === 0 && (
        <div className="empty-state">
          <div className="empty-icon">📚</div>
          <h2>No saved articles found</h2>
          <p>
            {filters.search || filters.tag || filters.author
              ? 'Try adjusting your filters or search terms.'
              : 'Start saving articles to build your reading list!'}
          </p>
          {(filters.search || filters.tag || filters.author) && (
            <button
              onClick={() => updateFilters({ search: '', tag: '', author: '', page: 1 })}
              className="clear-filters-button"
            >
              Clear Filters
            </button>
          )}
        </div>
      )}

      {/* Saved posts list */}
      {savedPosts.length > 0 && (
        <>
          <div className="saved-posts-list">
            {savedPosts.map((savedItem) => (
              <div key={savedItem.id} className="saved-post-item">
                <div className="saved-post-content" onClick={() => handlePostClick(savedItem.post)}>
                  <h3 className="saved-post-title">{savedItem.post_title}</h3>
                  
                  <div className="saved-post-meta">
                    <span className="saved-post-author">By {savedItem.post_author}</span>
                    <span className="saved-post-date">
                      Published: {formatDate(savedItem.post_created_at)}
                    </span>
                    <span className="saved-date">
                      Saved: {formatDate(savedItem.saved_at)}
                    </span>
                    {savedItem.post_view_count > 0 && (
                      <span className="view-count">{savedItem.post_view_count} views</span>
                    )}
                  </div>

                  <p className="saved-post-excerpt">
                    {truncateContent(savedItem.post_content)}
                  </p>

                  {savedItem.post_tags && (
                    <div className="saved-post-tags">
                      {savedItem.post_tags.split(',').map((tag, index) => (
                        <span key={index} className="post-tag">
                          {tag.trim()}
                        </span>
                      ))}
                    </div>
                  )}

                  {savedItem.notes && (
                    <div className="saved-notes">
                      <strong>Notes:</strong> {savedItem.notes}
                    </div>
                  )}
                </div>

                <div className="saved-post-actions">
                  <SaveButton
                    postId={savedItem.post}
                    isAuthenticated={true}
                    onSaveChange={handleSaveChange}
                  />
                </div>
              </div>
            ))}
          </div>

          {/* Pagination */}
          {pagination.total_pages > 1 && (
            <div className="pagination">
              <button
                onClick={() => handlePageChange(pagination.current_page - 1)}
                disabled={!pagination.previous}
                className="pagination-button"
              >
                Previous
              </button>
              
              <span className="pagination-info">
                Page {pagination.current_page} of {pagination.total_pages}
              </span>
              
              <button
                onClick={() => handlePageChange(pagination.current_page + 1)}
                disabled={!pagination.next}
                className="pagination-button"
              >
                Next
              </button>
            </div>
          )}
        </>
      )}

      {/* Loading overlay for subsequent loads */}
      {loading && savedPosts.length > 0 && (
        <div className="loading-overlay">
          <div className="loading-spinner"></div>
        </div>
      )}
    </div>
  );
};

export default SavedPosts;