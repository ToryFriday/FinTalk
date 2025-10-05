import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import BlogAPI from '../../services/api';
import LoadingSpinner from '../common/LoadingSpinner';
import ErrorMessage from '../common/ErrorMessage';
import { POST_STATUS_DISPLAY } from '../../utils/constants';
import './DraftsList.css';

/**
 * DraftsList component for displaying user's draft posts
 */
const DraftsList = () => {
  const [drafts, setDrafts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [pagination, setPagination] = useState({
    count: 0,
    next: null,
    previous: null,
    current_page: 1,
    total_pages: 1
  });

  useEffect(() => {
    loadDrafts();
  }, []);

  const loadDrafts = async (page = 1) => {
    setLoading(true);
    setError(null);

    try {
      const response = await BlogAPI.getDraftPosts({ page });
      
      if (response.success) {
        setDrafts(response.data.results || response.data);
        if (response.data.count !== undefined) {
          setPagination({
            count: response.data.count,
            next: response.data.next,
            previous: response.data.previous,
            current_page: response.data.current_page || page,
            total_pages: response.data.total_pages || 1
          });
        }
      } else {
        setError(response.error);
      }
    } catch (err) {
      setError({
        type: 'UNKNOWN_ERROR',
        message: 'Failed to load drafts'
      });
    } finally {
      setLoading(false);
    }
  };

  const handlePublishDraft = async (postId) => {
    try {
      const response = await BlogAPI.publishPost(postId);
      
      if (response.success) {
        // Remove the published post from drafts list
        setDrafts(prev => prev.filter(draft => draft.id !== postId));
        // Show success message (you might want to add a toast notification here)
        console.log('Post published successfully');
      } else {
        setError(response.error);
      }
    } catch (err) {
      setError({
        type: 'UNKNOWN_ERROR',
        message: 'Failed to publish post'
      });
    }
  };

  const handleSchedulePost = async (postId, scheduledDate) => {
    try {
      const response = await BlogAPI.schedulePost(postId, { scheduled_publish_date: scheduledDate });
      
      if (response.success) {
        // Update the post in the drafts list
        setDrafts(prev => prev.map(draft => 
          draft.id === postId ? response.data : draft
        ));
        console.log('Post scheduled successfully');
      } else {
        setError(response.error);
      }
    } catch (err) {
      setError({
        type: 'UNKNOWN_ERROR',
        message: 'Failed to schedule post'
      });
    }
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  if (loading) {
    return (
      <div className="drafts-list-container">
        <LoadingSpinner message="Loading drafts..." />
      </div>
    );
  }

  return (
    <div className="drafts-list-container">
      <div className="drafts-header">
        <h2>My Drafts</h2>
        <Link to="/posts/new" className="btn btn-primary">
          Create New Post
        </Link>
      </div>

      {error && (
        <div className="error-container">
          <ErrorMessage error={error} />
        </div>
      )}

      {drafts.length === 0 ? (
        <div className="no-drafts">
          <p>You don't have any draft posts yet.</p>
          <Link to="/posts/new" className="btn btn-primary">
            Create Your First Post
          </Link>
        </div>
      ) : (
        <>
          <div className="drafts-grid">
            {drafts.map(draft => (
              <DraftCard
                key={draft.id}
                draft={draft}
                onPublish={handlePublishDraft}
                onSchedule={handleSchedulePost}
                formatDate={formatDate}
              />
            ))}
          </div>

          {pagination.total_pages > 1 && (
            <div className="pagination">
              <button
                onClick={() => loadDrafts(pagination.current_page - 1)}
                disabled={!pagination.previous}
                className="btn btn-secondary"
              >
                Previous
              </button>
              <span className="page-info">
                Page {pagination.current_page} of {pagination.total_pages}
              </span>
              <button
                onClick={() => loadDrafts(pagination.current_page + 1)}
                disabled={!pagination.next}
                className="btn btn-secondary"
              >
                Next
              </button>
            </div>
          )}
        </>
      )}
    </div>
  );
};

/**
 * Individual draft card component
 */
const DraftCard = ({ draft, onPublish, onSchedule, formatDate }) => {
  const [showScheduleForm, setShowScheduleForm] = useState(false);
  const [scheduledDate, setScheduledDate] = useState('');
  const [isPublishing, setIsPublishing] = useState(false);
  const [isScheduling, setIsScheduling] = useState(false);

  const handlePublish = async () => {
    setIsPublishing(true);
    await onPublish(draft.id);
    setIsPublishing(false);
  };

  const handleScheduleSubmit = async (e) => {
    e.preventDefault();
    if (!scheduledDate) return;

    setIsScheduling(true);
    await onSchedule(draft.id, scheduledDate);
    setIsScheduling(false);
    setShowScheduleForm(false);
    setScheduledDate('');
  };

  const getMinDateTime = () => {
    const now = new Date();
    now.setMinutes(now.getMinutes() + 5); // Minimum 5 minutes from now
    return now.toISOString().slice(0, 16);
  };

  return (
    <div className="draft-card">
      <div className="draft-content">
        <h3 className="draft-title">
          <Link to={`/posts/${draft.id}`}>
            {draft.title}
          </Link>
        </h3>
        
        <div className="draft-meta">
          <span className={`status-badge status-${draft.status}`}>
            {POST_STATUS_DISPLAY[draft.status] || draft.status}
          </span>
          <span className="draft-date">
            Updated: {formatDate(draft.updated_at)}
          </span>
          {draft.scheduled_publish_date && (
            <span className="scheduled-date">
              Scheduled: {formatDate(draft.scheduled_publish_date)}
            </span>
          )}
        </div>

        <p className="draft-excerpt">
          {draft.content.length > 150 
            ? `${draft.content.substring(0, 150)}...` 
            : draft.content
          }
        </p>

        <div className="draft-actions">
          <Link to={`/posts/${draft.id}/edit`} className="btn btn-secondary btn-sm">
            Edit
          </Link>
          
          <button
            onClick={handlePublish}
            disabled={isPublishing}
            className="btn btn-success btn-sm"
          >
            {isPublishing ? 'Publishing...' : 'Publish Now'}
          </button>
          
          <button
            onClick={() => setShowScheduleForm(!showScheduleForm)}
            className="btn btn-info btn-sm"
          >
            Schedule
          </button>
        </div>

        {showScheduleForm && (
          <form onSubmit={handleScheduleSubmit} className="schedule-form">
            <div className="form-group">
              <label htmlFor={`schedule-${draft.id}`}>
                Schedule for:
              </label>
              <input
                type="datetime-local"
                id={`schedule-${draft.id}`}
                value={scheduledDate}
                onChange={(e) => setScheduledDate(e.target.value)}
                min={getMinDateTime()}
                required
                className="form-input"
              />
            </div>
            <div className="schedule-actions">
              <button
                type="submit"
                disabled={isScheduling || !scheduledDate}
                className="btn btn-primary btn-sm"
              >
                {isScheduling ? 'Scheduling...' : 'Schedule'}
              </button>
              <button
                type="button"
                onClick={() => {
                  setShowScheduleForm(false);
                  setScheduledDate('');
                }}
                className="btn btn-secondary btn-sm"
              >
                Cancel
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  );
};

export default DraftsList;