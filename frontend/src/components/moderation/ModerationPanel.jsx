import React, { useState, useEffect } from 'react';
import axios from 'axios';

const ModerationPanel = () => {
  const [flags, setFlags] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [filters, setFilters] = useState({
    status: '',
    reason: '',
    page: 1
  });
  const [summary, setSummary] = useState({});
  const [selectedFlag, setSelectedFlag] = useState(null);

  const statusOptions = [
    { value: '', label: 'All Statuses' },
    { value: 'pending', label: 'Pending' },
    { value: 'under_review', label: 'Under Review' },
    { value: 'resolved_valid', label: 'Resolved (Valid)' },
    { value: 'resolved_invalid', label: 'Resolved (Invalid)' },
    { value: 'dismissed', label: 'Dismissed' }
  ];

  const reasonOptions = [
    { value: '', label: 'All Reasons' },
    { value: 'spam', label: 'Spam' },
    { value: 'inappropriate', label: 'Inappropriate Content' },
    { value: 'harassment', label: 'Harassment' },
    { value: 'hate_speech', label: 'Hate Speech' },
    { value: 'violence', label: 'Violence' },
    { value: 'copyright', label: 'Copyright Violation' },
    { value: 'misinformation', label: 'Misinformation' },
    { value: 'off_topic', label: 'Off Topic' },
    { value: 'other', label: 'Other' }
  ];

  useEffect(() => {
    fetchFlags();
  }, [filters]);

  const fetchFlags = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (filters.status) params.append('status', filters.status);
      if (filters.reason) params.append('reason', filters.reason);
      params.append('page', filters.page);

      const response = await axios.get(`/api/moderation/flags/?${params}`);
      setFlags(response.data.results);
      setSummary(response.data.summary);
      setError('');
    } catch (err) {
      setError('Failed to load flags. Please try again.');
      console.error('Error fetching flags:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleStatusChange = async (flagId, newStatus, resolutionNotes = '', actionTaken = '') => {
    try {
      const response = await axios.put(`/api/moderation/flags/${flagId}/`, {
        status: newStatus,
        resolution_notes: resolutionNotes,
        action_taken: actionTaken
      });

      // Update the flag in the list
      setFlags(flags.map(flag => 
        flag.id === flagId ? response.data : flag
      ));

      setSelectedFlag(null);
      fetchFlags(); // Refresh to update summary
    } catch (err) {
      setError('Failed to update flag status. Please try again.');
      console.error('Error updating flag:', err);
    }
  };

  const getStatusBadgeClass = (status) => {
    const baseClass = "px-2 py-1 rounded-full text-xs font-medium";
    switch (status) {
      case 'pending':
        return `${baseClass} bg-yellow-100 text-yellow-800`;
      case 'under_review':
        return `${baseClass} bg-blue-100 text-blue-800`;
      case 'resolved_valid':
        return `${baseClass} bg-red-100 text-red-800`;
      case 'resolved_invalid':
        return `${baseClass} bg-green-100 text-green-800`;
      case 'dismissed':
        return `${baseClass} bg-gray-100 text-gray-800`;
      default:
        return `${baseClass} bg-gray-100 text-gray-800`;
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
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Content Moderation</h1>
        <p className="mt-2 text-gray-600">Review and manage flagged content</p>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-5 gap-4 mb-8">
        <div className="bg-white p-4 rounded-lg shadow">
          <div className="text-2xl font-bold text-gray-900">{summary.total_flags || 0}</div>
          <div className="text-sm text-gray-600">Total Flags</div>
        </div>
        <div className="bg-white p-4 rounded-lg shadow">
          <div className="text-2xl font-bold text-yellow-600">{summary.pending_flags || 0}</div>
          <div className="text-sm text-gray-600">Pending</div>
        </div>
        <div className="bg-white p-4 rounded-lg shadow">
          <div className="text-2xl font-bold text-blue-600">{summary.under_review_flags || 0}</div>
          <div className="text-sm text-gray-600">Under Review</div>
        </div>
        <div className="bg-white p-4 rounded-lg shadow">
          <div className="text-2xl font-bold text-red-600">{summary.resolved_flags || 0}</div>
          <div className="text-sm text-gray-600">Resolved</div>
        </div>
        <div className="bg-white p-4 rounded-lg shadow">
          <div className="text-2xl font-bold text-gray-600">{summary.dismissed_flags || 0}</div>
          <div className="text-sm text-gray-600">Dismissed</div>
        </div>
      </div>

      {/* Filters */}
      <div className="bg-white p-4 rounded-lg shadow mb-6">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Status</label>
            <select
              value={filters.status}
              onChange={(e) => setFilters({ ...filters, status: e.target.value, page: 1 })}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              {statusOptions.map(option => (
                <option key={option.value} value={option.value}>{option.label}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Reason</label>
            <select
              value={filters.reason}
              onChange={(e) => setFilters({ ...filters, reason: e.target.value, page: 1 })}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              {reasonOptions.map(option => (
                <option key={option.value} value={option.value}>{option.label}</option>
              ))}
            </select>
          </div>
          <div className="flex items-end">
            <button
              onClick={() => setFilters({ status: '', reason: '', page: 1 })}
              className="px-4 py-2 bg-gray-500 text-white rounded-md hover:bg-gray-600"
            >
              Clear Filters
            </button>
          </div>
        </div>
      </div>

      {error && (
        <div className="mb-6 p-4 bg-red-100 border border-red-400 text-red-700 rounded">
          {error}
        </div>
      )}

      {/* Flags List */}
      <div className="bg-white shadow rounded-lg overflow-hidden">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Post
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Reason
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Status
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Flagged By
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Date
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {flags.map((flag) => (
                <tr key={flag.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm font-medium text-gray-900">
                      {flag.post_title}
                    </div>
                    <div className="text-sm text-gray-500">
                      by {flag.post_author}
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm text-gray-900">{flag.reason_display}</div>
                    {flag.description && (
                      <div className="text-sm text-gray-500 truncate max-w-xs">
                        {flag.description}
                      </div>
                    )}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={getStatusBadgeClass(flag.status)}>
                      {flag.status_display}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {flag.flagged_by_name}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {formatDate(flag.created_at)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                    {flag.can_review && (flag.status === 'pending' || flag.status === 'under_review') && (
                      <button
                        onClick={() => setSelectedFlag(flag)}
                        className="text-blue-600 hover:text-blue-900 mr-3"
                      >
                        Review
                      </button>
                    )}
                    <button
                      onClick={() => window.open(`/posts/${flag.post}`, '_blank')}
                      className="text-gray-600 hover:text-gray-900"
                    >
                      View Post
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {flags.length === 0 && (
          <div className="text-center py-12">
            <div className="text-gray-500">No flags found matching your criteria.</div>
          </div>
        )}
      </div>

      {/* Review Modal */}
      {selectedFlag && (
        <FlagReviewModal
          flag={selectedFlag}
          onClose={() => setSelectedFlag(null)}
          onUpdate={handleStatusChange}
        />
      )}
    </div>
  );
};

const FlagReviewModal = ({ flag, onClose, onUpdate }) => {
  const [status, setStatus] = useState(flag.status);
  const [resolutionNotes, setResolutionNotes] = useState(flag.resolution_notes || '');
  const [actionTaken, setActionTaken] = useState(flag.action_taken || '');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsSubmitting(true);
    
    try {
      await onUpdate(flag.id, status, resolutionNotes, actionTaken);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 w-full max-w-2xl mx-4 max-h-screen overflow-y-auto">
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-lg font-semibold text-gray-900">Review Flag</h3>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600"
          >
            ✕
          </button>
        </div>

        <div className="mb-6 p-4 bg-gray-50 rounded-lg">
          <h4 className="font-medium text-gray-900 mb-2">Flagged Content</h4>
          <div className="text-sm text-gray-600">
            <div><strong>Post:</strong> {flag.post_title}</div>
            <div><strong>Author:</strong> {flag.post_author}</div>
            <div><strong>Reason:</strong> {flag.reason_display}</div>
            <div><strong>Flagged by:</strong> {flag.flagged_by_name}</div>
            <div><strong>Date:</strong> {new Date(flag.created_at).toLocaleString()}</div>
            {flag.description && (
              <div className="mt-2">
                <strong>Description:</strong>
                <div className="mt-1 p-2 bg-white rounded border">
                  {flag.description}
                </div>
              </div>
            )}
          </div>
        </div>

        <form onSubmit={handleSubmit}>
          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Status
            </label>
            <select
              value={status}
              onChange={(e) => setStatus(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              required
            >
              <option value="under_review">Under Review</option>
              <option value="resolved_valid">Resolved (Valid Flag)</option>
              <option value="resolved_invalid">Resolved (Invalid Flag)</option>
              <option value="dismissed">Dismissed</option>
            </select>
          </div>

          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Resolution Notes
            </label>
            <textarea
              value={resolutionNotes}
              onChange={(e) => setResolutionNotes(e.target.value)}
              placeholder="Explain your decision and any actions taken..."
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              rows="4"
              required={status !== 'under_review'}
            />
          </div>

          {status === 'resolved_valid' && (
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Action Taken
              </label>
              <input
                type="text"
                value={actionTaken}
                onChange={(e) => setActionTaken(e.target.value)}
                placeholder="e.g., content_removed, warning_issued, user_suspended"
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                required
              />
            </div>
          )}

          <div className="flex justify-end space-x-3">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-gray-600 border border-gray-300 rounded-md hover:bg-gray-50"
              disabled={isSubmitting}
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isSubmitting}
              className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isSubmitting ? 'Updating...' : 'Update Flag'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default ModerationPanel;