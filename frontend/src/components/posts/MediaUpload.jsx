import React, { useState, useCallback, useRef } from 'react';
import BlogAPI from '../../services/api';
import { ALLOWED_FILE_TYPES, ALLOWED_EXTENSIONS, VALIDATION_LIMITS } from '../../services/apiConfig';
import { formatErrorMessage } from '../../services/api';
import './MediaUpload.css';

const MediaUpload = ({ onUploadSuccess, onUploadError, multiple = true, accept = 'image/*,video/*' }) => {
  const [isDragOver, setIsDragOver] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState({});
  const fileInputRef = useRef(null);

  // Validate file type and size
  const validateFile = (file) => {
    const errors = [];
    
    // Check file type
    const isImage = ALLOWED_FILE_TYPES.IMAGES.includes(file.type);
    const isVideo = ALLOWED_FILE_TYPES.VIDEOS.includes(file.type);
    
    if (!isImage && !isVideo) {
      errors.push(`File type "${file.type}" is not supported. Allowed types: ${[...ALLOWED_FILE_TYPES.IMAGES, ...ALLOWED_FILE_TYPES.VIDEOS].join(', ')}`);
    }
    
    // Check file size
    const maxSize = isImage ? VALIDATION_LIMITS.MAX_IMAGE_SIZE : VALIDATION_LIMITS.MAX_VIDEO_SIZE;
    if (file.size > maxSize) {
      const maxSizeMB = maxSize / (1024 * 1024);
      errors.push(`File size (${(file.size / (1024 * 1024)).toFixed(2)}MB) exceeds maximum allowed size of ${maxSizeMB}MB`);
    }
    
    return errors;
  };

  // Handle file upload
  const uploadFile = async (file, altText = '') => {
    const fileId = `${file.name}-${Date.now()}`;
    
    try {
      setUploadProgress(prev => ({ ...prev, [fileId]: 0 }));
      
      const result = await BlogAPI.uploadMedia(file, altText);
      
      if (result.success) {
        setUploadProgress(prev => ({ ...prev, [fileId]: 100 }));
        onUploadSuccess && onUploadSuccess(result.data);
        
        // Remove progress after a delay
        setTimeout(() => {
          setUploadProgress(prev => {
            const newProgress = { ...prev };
            delete newProgress[fileId];
            return newProgress;
          });
        }, 2000);
      } else {
        throw new Error(formatErrorMessage(result.error));
      }
    } catch (error) {
      setUploadProgress(prev => {
        const newProgress = { ...prev };
        delete newProgress[fileId];
        return newProgress;
      });
      onUploadError && onUploadError(error.message || 'Upload failed');
    }
  };

  // Handle files selection/drop
  const handleFiles = useCallback(async (files) => {
    const fileArray = Array.from(files);
    
    if (!multiple && fileArray.length > 1) {
      onUploadError && onUploadError('Only one file can be uploaded at a time');
      return;
    }
    
    setUploading(true);
    
    for (const file of fileArray) {
      const validationErrors = validateFile(file);
      
      if (validationErrors.length > 0) {
        onUploadError && onUploadError(`${file.name}: ${validationErrors.join(', ')}`);
        continue;
      }
      
      await uploadFile(file);
    }
    
    setUploading(false);
  }, [multiple, onUploadError, onUploadSuccess]);

  // Drag and drop handlers
  const handleDragEnter = useCallback((e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragOver(true);
  }, []);

  const handleDragLeave = useCallback((e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragOver(false);
  }, []);

  const handleDragOver = useCallback((e) => {
    e.preventDefault();
    e.stopPropagation();
  }, []);

  const handleDrop = useCallback((e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragOver(false);
    
    const files = e.dataTransfer.files;
    if (files.length > 0) {
      handleFiles(files);
    }
  }, [handleFiles]);

  // File input change handler
  const handleFileInputChange = useCallback((e) => {
    const files = e.target.files;
    if (files.length > 0) {
      handleFiles(files);
    }
    // Reset input value to allow selecting the same file again
    e.target.value = '';
  }, [handleFiles]);

  // Click to select files
  const handleClick = () => {
    fileInputRef.current?.click();
  };

  const hasActiveUploads = Object.keys(uploadProgress).length > 0;

  return (
    <div className="media-upload">
      <div
        className={`media-upload__dropzone ${isDragOver ? 'media-upload__dropzone--drag-over' : ''} ${uploading ? 'media-upload__dropzone--uploading' : ''}`}
        onDragEnter={handleDragEnter}
        onDragLeave={handleDragLeave}
        onDragOver={handleDragOver}
        onDrop={handleDrop}
        onClick={handleClick}
        role="button"
        tabIndex={0}
        onKeyDown={(e) => {
          if (e.key === 'Enter' || e.key === ' ') {
            e.preventDefault();
            handleClick();
          }
        }}
        aria-label="Upload media files"
      >
        <input
          ref={fileInputRef}
          type="file"
          multiple={multiple}
          accept={accept}
          onChange={handleFileInputChange}
          className="media-upload__input"
          aria-hidden="true"
        />
        
        <div className="media-upload__content">
          {uploading ? (
            <div className="media-upload__uploading">
              <div className="media-upload__spinner"></div>
              <p>Uploading files...</p>
            </div>
          ) : (
            <>
              <div className="media-upload__icon">
                <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
                  <polyline points="7,10 12,15 17,10" />
                  <line x1="12" y1="15" x2="12" y2="3" />
                </svg>
              </div>
              <h3 className="media-upload__title">
                {isDragOver ? 'Drop files here' : 'Upload Media Files'}
              </h3>
              <p className="media-upload__description">
                Drag and drop files here, or click to select files
              </p>
              <p className="media-upload__formats">
                Supported formats: Images (JPG, PNG, GIF, WebP) up to 10MB, Videos (MP4, WebM, OGG, MOV, AVI) up to 50MB
              </p>
            </>
          )}
        </div>
      </div>
      
      {hasActiveUploads && (
        <div className="media-upload__progress">
          <h4>Upload Progress</h4>
          {Object.entries(uploadProgress).map(([fileId, progress]) => {
            const fileName = fileId.split('-')[0];
            return (
              <div key={fileId} className="media-upload__progress-item">
                <span className="media-upload__progress-name">{fileName}</span>
                <div className="media-upload__progress-bar">
                  <div 
                    className="media-upload__progress-fill"
                    style={{ width: `${progress}%` }}
                  ></div>
                </div>
                <span className="media-upload__progress-percent">{progress}%</span>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};

export default MediaUpload;