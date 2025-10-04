import React, { useState } from 'react';
import './PostConfirmDelete.css';

/**
 * PostConfirmDelete component for confirming post deletion
 * @param {Object} props - Component props
 * @param {Object} props.post - Post data object to be deleted
 * @param {Function} props.onConfirm - Function called when deletion is confirmed
 * @param {Function} props.onCancel - Function called when deletion is cancelled
 * @param {boolean} props.isOpen - Whether the dialog is open
 * @param {boolean} props.isDeleting - Whether deletion is in progress
 */
const PostConfirmDelete = ({ 
  post, 
  onConfirm, 
  onCancel, 
  isOpen, 
  isDeleting = false 
}) => {
  const [isClosing, setIsClosing] = useState(false);

  const handleConfirm = () => {
    if (onConfirm && !isDeleting) {
      onConfirm(post.id);
    }
  };

  const handleCancel = () => {
    if (isDeleting) return; // Prevent cancellation during deletion
    
    if (onCancel) {
      onCancel();
    }
  };

  const handleBackdropClick = (e) => {
    if (e.target === e.currentTarget) {
      handleCancel();
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Escape') {
      handleCancel();
    } else if (e.key === 'Enter') {
      handleConfirm();
    }
  };

  if (!isOpen) return null;

  return (
    <div 
      className={`confirm-delete-overlay ${isClosing ? 'closing' : ''}`}
      onClick={handleBackdropClick}
      onKeyDown={handleKeyDown}
      tabIndex={-1}
    >
      <div className="confirm-delete-dialog" role="dialog" aria-modal="true" aria-labelledby="dialog-title">
        <div className="confirm-delete-header">
          <h3 id="dialog-title">Confirm Deletion</h3>
          {!isDeleting && (
            <button 
              className="close-button"
              onClick={handleCancel}
              aria-label="Close dialog"
              type="button"
            >
              ×
            </button>
          )}
        </div>
        
        <div className="confirm-delete-content">
          <div className="warning-icon">
            ⚠️
          </div>
          <p className="confirm-message">
            Are you sure you want to delete this post?
          </p>
          
          {post && (
            <div className="post-preview">
              <h4 className="post-title-preview">"{post.title}"</h4>
              <p className="post-meta-preview">
                By {post.author} • {new Date(post.created_at).toLocaleDateString()}
              </p>
            </div>
          )}
          
          <p className="warning-text">
            This action cannot be undone.
          </p>
        </div>
        
        <div className="confirm-delete-actions">
          <button 
            className="cancel-button"
            onClick={handleCancel}
            disabled={isDeleting}
            type="button"
          >
            Cancel
          </button>
          <button 
            className="confirm-button"
            onClick={handleConfirm}
            disabled={isDeleting}
            type="button"
          >
            {isDeleting ? (
              <>
                <span className="spinner"></span>
                Deleting...
              </>
            ) : (
              'Delete Post'
            )}
          </button>
        </div>
      </div>
    </div>
  );
};

export default PostConfirmDelete;