import React, { useState, useCallback } from 'react';
import MediaUpload from './MediaUpload';
import MediaGallery from './MediaGallery';
import './MediaManager.css';

const MediaManager = ({ 
  onMediaSelect, 
  selectedMedia = [], 
  multiple = true,
  fileType = null, // 'image', 'video', or null for all
  showUpload = true,
  showGallery = true
}) => {
  const [activeTab, setActiveTab] = useState(showUpload ? 'upload' : 'gallery');
  const [uploadError, setUploadError] = useState(null);
  const [uploadSuccess, setUploadSuccess] = useState(null);
  const [refreshGallery, setRefreshGallery] = useState(0);

  // Handle successful upload
  const handleUploadSuccess = useCallback((mediaFile) => {
    setUploadSuccess(`Successfully uploaded "${mediaFile.original_name}"`);
    setUploadError(null);
    
    // Refresh gallery to show new file
    setRefreshGallery(prev => prev + 1);
    
    // Auto-select uploaded file if in selection mode
    if (onMediaSelect) {
      const newSelection = multiple 
        ? [...selectedMedia, mediaFile]
        : [mediaFile];
      onMediaSelect(newSelection);
    }
    
    // Clear success message after 3 seconds
    setTimeout(() => {
      setUploadSuccess(null);
    }, 3000);
    
    // Switch to gallery tab to show uploaded file
    if (showGallery) {
      setActiveTab('gallery');
    }
  }, [selectedMedia, multiple, onMediaSelect, showGallery]);

  // Handle upload error
  const handleUploadError = useCallback((error) => {
    setUploadError(error);
    setUploadSuccess(null);
  }, []);

  // Handle media selection from gallery
  const handleMediaSelect = useCallback((newSelection) => {
    onMediaSelect && onMediaSelect(newSelection);
  }, [onMediaSelect]);

  // Handle media deletion from gallery
  const handleMediaDelete = useCallback((deletedMedia) => {
    // Remove deleted media from selection if it was selected
    if (selectedMedia.some(media => media.id === deletedMedia.id)) {
      const newSelection = selectedMedia.filter(media => media.id !== deletedMedia.id);
      onMediaSelect && onMediaSelect(newSelection);
    }
  }, [selectedMedia, onMediaSelect]);

  // Clear messages
  const clearMessages = () => {
    setUploadError(null);
    setUploadSuccess(null);
  };

  const showTabs = showUpload && showGallery;

  return (
    <div className="media-manager">
      {showTabs && (
        <div className="media-manager__tabs">
          <button
            className={`media-manager__tab ${activeTab === 'upload' ? 'media-manager__tab--active' : ''}`}
            onClick={() => {
              setActiveTab('upload');
              clearMessages();
            }}
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
              <polyline points="7,10 12,15 17,10" />
              <line x1="12" y1="15" x2="12" y2="3" />
            </svg>
            Upload Files
          </button>
          <button
            className={`media-manager__tab ${activeTab === 'gallery' ? 'media-manager__tab--active' : ''}`}
            onClick={() => {
              setActiveTab('gallery');
              clearMessages();
            }}
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <rect x="3" y="3" width="18" height="18" rx="2" ry="2" />
              <circle cx="8.5" cy="8.5" r="1.5" />
              <polyline points="21,15 16,10 5,21" />
            </svg>
            Media Library
          </button>
        </div>
      )}

      {/* Messages */}
      {(uploadError || uploadSuccess) && (
        <div className="media-manager__messages">
          {uploadError && (
            <div className="media-manager__message media-manager__message--error">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
                <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/>
              </svg>
              <span>{uploadError}</span>
              <button 
                onClick={() => setUploadError(null)}
                className="media-manager__message-close"
                aria-label="Close error message"
              >
                ×
              </button>
            </div>
          )}
          
          {uploadSuccess && (
            <div className="media-manager__message media-manager__message--success">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
                <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/>
              </svg>
              <span>{uploadSuccess}</span>
              <button 
                onClick={() => setUploadSuccess(null)}
                className="media-manager__message-close"
                aria-label="Close success message"
              >
                ×
              </button>
            </div>
          )}
        </div>
      )}

      {/* Content */}
      <div className="media-manager__content">
        {(activeTab === 'upload' && showUpload) && (
          <div className="media-manager__upload">
            <MediaUpload
              onUploadSuccess={handleUploadSuccess}
              onUploadError={handleUploadError}
              multiple={multiple}
              accept={fileType === 'image' ? 'image/*' : fileType === 'video' ? 'video/*' : 'image/*,video/*'}
            />
          </div>
        )}

        {(activeTab === 'gallery' && showGallery) && (
          <div className="media-manager__gallery">
            <MediaGallery
              key={refreshGallery} // Force refresh when new files are uploaded
              onMediaSelect={handleMediaSelect}
              onMediaDelete={handleMediaDelete}
              selectedMedia={selectedMedia}
              selectable={!!onMediaSelect}
              deletable={true}
              fileType={fileType}
            />
          </div>
        )}
      </div>

      {/* Selection summary */}
      {onMediaSelect && selectedMedia.length > 0 && (
        <div className="media-manager__selection">
          <div className="media-manager__selection-header">
            <h4>Selected Files ({selectedMedia.length})</h4>
            <button
              onClick={() => onMediaSelect([])}
              className="media-manager__clear-selection"
            >
              Clear All
            </button>
          </div>
          <div className="media-manager__selection-list">
            {selectedMedia.map((media) => (
              <div key={media.id} className="media-manager__selection-item">
                <div className="media-manager__selection-preview">
                  {media.file_type === 'image' ? (
                    <img
                      src={media.thumbnail_url || media.file_url}
                      alt={media.alt_text || media.original_name}
                      className="media-manager__selection-image"
                    />
                  ) : (
                    <div className="media-manager__selection-video">
                      <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
                        <path d="M8 5v14l11-7z"/>
                      </svg>
                    </div>
                  )}
                </div>
                <div className="media-manager__selection-info">
                  <span className="media-manager__selection-name" title={media.original_name}>
                    {media.original_name}
                  </span>
                  <span className="media-manager__selection-type">
                    {media.file_type}
                  </span>
                </div>
                <button
                  onClick={() => {
                    const newSelection = selectedMedia.filter(m => m.id !== media.id);
                    onMediaSelect(newSelection);
                  }}
                  className="media-manager__selection-remove"
                  aria-label={`Remove ${media.original_name} from selection`}
                >
                  ×
                </button>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default MediaManager;