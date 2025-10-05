import React, { useState, useEffect } from 'react';
import BlogAPI from '../../services/api';
import { formatErrorMessage } from '../../services/api';
import './MediaGallery.css';

const MediaGallery = ({ 
  onMediaSelect, 
  onMediaDelete, 
  selectedMedia = [], 
  selectable = true,
  deletable = true,
  fileType = null // 'image', 'video', or null for all
}) => {
  const [mediaFiles, setMediaFiles] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [page, setPage] = useState(1);
  const [hasMore, setHasMore] = useState(false);
  const [totalCount, setTotalCount] = useState(0);

  // Load media files
  const loadMediaFiles = async (pageNum = 1, append = false) => {
    try {
      setLoading(true);
      setError(null);
      
      const params = {
        page: pageNum,
        page_size: 12
      };
      
      if (fileType) {
        params.file_type = fileType;
      }
      
      const result = await BlogAPI.getMediaFiles(params);
      
      if (result.success) {
        const newMediaFiles = result.data.results || result.data;
        
        if (append) {
          setMediaFiles(prev => [...prev, ...newMediaFiles]);
        } else {
          setMediaFiles(newMediaFiles);
        }
        
        // Handle pagination info
        if (result.data.count !== undefined) {
          setTotalCount(result.data.count);
          setHasMore(result.data.next !== null);
        } else {
          setTotalCount(newMediaFiles.length);
          setHasMore(false);
        }
      } else {
        throw new Error(formatErrorMessage(result.error));
      }
    } catch (err) {
      setError(err.message || 'Failed to load media files');
    } finally {
      setLoading(false);
    }
  };

  // Load more media files
  const loadMore = () => {
    const nextPage = page + 1;
    setPage(nextPage);
    loadMediaFiles(nextPage, true);
  };

  // Delete media file
  const handleDelete = async (mediaFile) => {
    if (!window.confirm(`Are you sure you want to delete "${mediaFile.original_name}"?`)) {
      return;
    }
    
    try {
      const result = await BlogAPI.deleteMediaFile(mediaFile.id);
      
      if (result.success) {
        setMediaFiles(prev => prev.filter(file => file.id !== mediaFile.id));
        setTotalCount(prev => prev - 1);
        onMediaDelete && onMediaDelete(mediaFile);
      } else {
        throw new Error(formatErrorMessage(result.error));
      }
    } catch (err) {
      setError(err.message || 'Failed to delete media file');
    }
  };

  // Handle media selection
  const handleSelect = (mediaFile) => {
    if (!selectable) return;
    
    const isSelected = selectedMedia.some(selected => selected.id === mediaFile.id);
    
    if (isSelected) {
      const newSelection = selectedMedia.filter(selected => selected.id !== mediaFile.id);
      onMediaSelect && onMediaSelect(newSelection);
    } else {
      onMediaSelect && onMediaSelect([...selectedMedia, mediaFile]);
    }
  };

  // Format file size
  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  // Format date
  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString();
  };

  useEffect(() => {
    loadMediaFiles();
  }, [fileType]);

  if (loading && mediaFiles.length === 0) {
    return (
      <div className="media-gallery">
        <div className="media-gallery__loading">
          <div className="media-gallery__spinner"></div>
          <p>Loading media files...</p>
        </div>
      </div>
    );
  }

  if (error && mediaFiles.length === 0) {
    return (
      <div className="media-gallery">
        <div className="media-gallery__error">
          <p>Error: {error}</p>
          <button 
            onClick={() => loadMediaFiles()}
            className="media-gallery__retry-btn"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="media-gallery">
      {error && (
        <div className="media-gallery__error-banner">
          <p>{error}</p>
          <button 
            onClick={() => setError(null)}
            className="media-gallery__close-error"
            aria-label="Close error message"
          >
            ×
          </button>
        </div>
      )}
      
      <div className="media-gallery__header">
        <h3>Media Library</h3>
        <p className="media-gallery__count">
          {totalCount} {totalCount === 1 ? 'file' : 'files'}
        </p>
      </div>
      
      {mediaFiles.length === 0 ? (
        <div className="media-gallery__empty">
          <p>No media files found.</p>
          <p>Upload some files to get started!</p>
        </div>
      ) : (
        <>
          <div className="media-gallery__grid">
            {mediaFiles.map((mediaFile) => {
              const isSelected = selectedMedia.some(selected => selected.id === mediaFile.id);
              
              return (
                <div
                  key={mediaFile.id}
                  className={`media-gallery__item ${isSelected ? 'media-gallery__item--selected' : ''} ${selectable ? 'media-gallery__item--selectable' : ''}`}
                  onClick={() => handleSelect(mediaFile)}
                  role={selectable ? 'button' : 'img'}
                  tabIndex={selectable ? 0 : -1}
                  onKeyDown={(e) => {
                    if (selectable && (e.key === 'Enter' || e.key === ' ')) {
                      e.preventDefault();
                      handleSelect(mediaFile);
                    }
                  }}
                  aria-label={`${mediaFile.file_type} file: ${mediaFile.original_name}`}
                >
                  <div className="media-gallery__preview">
                    {mediaFile.file_type === 'image' ? (
                      <img
                        src={mediaFile.thumbnail_url || mediaFile.file_url}
                        alt={mediaFile.alt_text || mediaFile.original_name}
                        className="media-gallery__image"
                        loading="lazy"
                      />
                    ) : (
                      <div className="media-gallery__video-preview">
                        <video
                          src={mediaFile.file_url}
                          className="media-gallery__video"
                          muted
                          preload="metadata"
                        />
                        <div className="media-gallery__video-overlay">
                          <svg width="24" height="24" viewBox="0 0 24 24" fill="white">
                            <path d="M8 5v14l11-7z"/>
                          </svg>
                        </div>
                      </div>
                    )}
                    
                    {selectable && isSelected && (
                      <div className="media-gallery__selected-indicator">
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="white">
                          <path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z"/>
                        </svg>
                      </div>
                    )}
                  </div>
                  
                  <div className="media-gallery__info">
                    <h4 className="media-gallery__filename" title={mediaFile.original_name}>
                      {mediaFile.original_name}
                    </h4>
                    <div className="media-gallery__meta">
                      <span className="media-gallery__size">
                        {formatFileSize(mediaFile.file_size)}
                      </span>
                      <span className="media-gallery__date">
                        {formatDate(mediaFile.created_at)}
                      </span>
                    </div>
                    {mediaFile.width && mediaFile.height && (
                      <div className="media-gallery__dimensions">
                        {mediaFile.width} × {mediaFile.height}
                      </div>
                    )}
                  </div>
                  
                  {deletable && (
                    <button
                      className="media-gallery__delete-btn"
                      onClick={(e) => {
                        e.stopPropagation();
                        handleDelete(mediaFile);
                      }}
                      aria-label={`Delete ${mediaFile.original_name}`}
                      title="Delete file"
                    >
                      <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
                        <path d="M6 19c0 1.1.9 2 2 2h8c1.1 0 2-.9 2-2V7H6v12zM19 4h-3.5l-1-1h-5l-1 1H5v2h14V4z"/>
                      </svg>
                    </button>
                  )}
                </div>
              );
            })}
          </div>
          
          {hasMore && (
            <div className="media-gallery__load-more">
              <button
                onClick={loadMore}
                disabled={loading}
                className="media-gallery__load-more-btn"
              >
                {loading ? 'Loading...' : 'Load More'}
              </button>
            </div>
          )}
        </>
      )}
    </div>
  );
};

export default MediaGallery;