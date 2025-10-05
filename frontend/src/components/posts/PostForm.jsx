import React, { useState, useEffect } from 'react';
import { validatePostForm, getFieldError } from '../../utils/validation';
import { FORM_FIELDS, INITIAL_POST_FORM } from '../../utils/constants';
import ErrorMessage from '../common/ErrorMessage';
import FormErrorDisplay from '../common/FormErrorDisplay';
import NetworkErrorHandler from '../common/NetworkErrorHandler';
import LoadingSpinner from '../common/LoadingSpinner';
import MediaManager from './MediaManager';
import BlogAPI from '../../services/api';
import './PostForm.css';

/**
 * PostForm component for creating and editing blog posts
 * @param {Object} props - Component props
 * @param {Object} props.initialData - Initial form data for editing
 * @param {Function} props.onSubmit - Form submission handler
 * @param {string} props.submitButtonText - Text for submit button
 * @param {boolean} props.isSubmitting - Whether form is being submitted
 * @param {Object} props.submitError - Error from form submission
 */
const PostForm = ({ 
  initialData = INITIAL_POST_FORM, 
  onSubmit, 
  submitButtonText = 'Create Post',
  isSubmitting = false,
  submitError = null
}) => {
  // Form state
  const [formData, setFormData] = useState(initialData);
  const [fieldErrors, setFieldErrors] = useState({});
  const [touchedFields, setTouchedFields] = useState({});
  const [selectedMedia, setSelectedMedia] = useState([]);
  const [showMediaManager, setShowMediaManager] = useState(false);
  const [attachedMedia, setAttachedMedia] = useState([]);

  // Update form data when initialData changes (for edit mode)
  useEffect(() => {
    setFormData(initialData);
    
    // Load attached media if editing existing post
    if (initialData.id) {
      loadPostMedia(initialData.id);
    }
  }, [initialData]);

  // Load media files attached to the post
  const loadPostMedia = async (postId) => {
    try {
      const result = await BlogAPI.getPostMedia(postId);
      if (result.success) {
        setAttachedMedia(result.data);
      }
    } catch (error) {
      console.error('Failed to load post media:', error);
    }
  };

  /**
   * Handle input field changes
   */
  const handleInputChange = (e) => {
    const { name, value } = e.target;
    
    // Update form data
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));

    // Clear field error when user starts typing
    if (fieldErrors[name]) {
      setFieldErrors(prev => ({
        ...prev,
        [name]: null
      }));
    }
  };

  /**
   * Handle field blur for validation
   */
  const handleFieldBlur = (e) => {
    const { name, value } = e.target;
    
    // Mark field as touched
    setTouchedFields(prev => ({
      ...prev,
      [name]: true
    }));

    // Validate field
    const error = getFieldError(name, value);
    setFieldErrors(prev => ({
      ...prev,
      [name]: error
    }));
  };

  /**
   * Handle form submission
   */
  const handleSubmit = (e) => {
    e.preventDefault();

    // Validate entire form
    const validation = validatePostForm(formData);
    
    if (!validation.isValid) {
      setFieldErrors(validation.errors);
      // Mark all fields as touched to show errors
      const allFieldsTouched = Object.keys(FORM_FIELDS).reduce((acc, key) => {
        acc[FORM_FIELDS[key]] = true;
        return acc;
      }, {});
      setTouchedFields(allFieldsTouched);
      return;
    }

    // Clear field errors
    setFieldErrors({});

    // Trim string values before submission
    const trimmedData = {
      ...formData,
      title: formData.title.trim(),
      content: formData.content.trim(),
      author: formData.author.trim(),
      tags: formData.tags.trim(),
      image_url: formData.image_url.trim()
    };

    // Handle scheduled_publish_date formatting
    if (trimmedData.status === 'scheduled' && trimmedData.scheduled_publish_date) {
      // Convert datetime-local format to ISO format for backend
      const dateValue = new Date(trimmedData.scheduled_publish_date);
      if (!isNaN(dateValue.getTime())) {
        trimmedData.scheduled_publish_date = dateValue.toISOString();
      } else {
        // Invalid date, remove the field
        delete trimmedData.scheduled_publish_date;
      }
    } else {
      // Remove scheduled_publish_date if status is not 'scheduled' or if it's empty
      delete trimmedData.scheduled_publish_date;
    }

    // Call parent submit handler
    onSubmit(trimmedData);
  };

  /**
   * Get field error message for display
   */
  const getDisplayError = (fieldName) => {
    return touchedFields[fieldName] ? fieldErrors[fieldName] : null;
  };

  /**
   * Check if field has error
   */
  const hasFieldError = (fieldName) => {
    return touchedFields[fieldName] && fieldErrors[fieldName];
  };

  /**
   * Handle media selection from MediaManager
   */
  const handleMediaSelect = (media) => {
    setSelectedMedia(media);
  };

  /**
   * Attach selected media to post
   */
  const attachMediaToPost = async (postId) => {
    if (selectedMedia.length === 0) return;

    try {
      const mediaFileIds = selectedMedia.map(media => media.id);
      const result = await BlogAPI.attachMediaToPost(postId, mediaFileIds);
      
      if (result.success) {
        setAttachedMedia(prev => [...prev, ...result.data]);
        setSelectedMedia([]);
        setShowMediaManager(false);
      }
    } catch (error) {
      console.error('Failed to attach media to post:', error);
    }
  };

  /**
   * Remove media from post
   */
  const removeMediaFromPost = async (postId, mediaId) => {
    try {
      const result = await BlogAPI.removeMediaFromPost(postId, mediaId);
      
      if (result.success) {
        setAttachedMedia(prev => prev.filter(media => media.media_file.id !== mediaId));
      }
    } catch (error) {
      console.error('Failed to remove media from post:', error);
    }
  };

  return (
    <div className="post-form-container">
      <form onSubmit={handleSubmit} className="post-form" noValidate>
        {/* Title Field */}
        <div className="form-group">
          <label htmlFor={FORM_FIELDS.TITLE} className="form-label">
            Title <span className="required">*</span>
          </label>
          <input
            type="text"
            id={FORM_FIELDS.TITLE}
            name={FORM_FIELDS.TITLE}
            value={formData.title}
            onChange={handleInputChange}
            onBlur={handleFieldBlur}
            className={`form-input ${hasFieldError(FORM_FIELDS.TITLE) ? 'error' : ''}`}
            placeholder="Enter post title..."
            maxLength={200}
            disabled={isSubmitting}
            required
          />
          {getDisplayError(FORM_FIELDS.TITLE) && (
            <span className="field-error">{getDisplayError(FORM_FIELDS.TITLE)}</span>
          )}
          <div className="character-count">
            {formData.title.length}/200
          </div>
        </div>

        {/* Content Field */}
        <div className="form-group">
          <label htmlFor={FORM_FIELDS.CONTENT} className="form-label">
            Content <span className="required">*</span>
          </label>
          <textarea
            id={FORM_FIELDS.CONTENT}
            name={FORM_FIELDS.CONTENT}
            value={formData.content}
            onChange={handleInputChange}
            onBlur={handleFieldBlur}
            className={`form-textarea ${hasFieldError(FORM_FIELDS.CONTENT) ? 'error' : ''}`}
            placeholder="Write your blog post content..."
            rows={10}
            disabled={isSubmitting}
            required
          />
          {getDisplayError(FORM_FIELDS.CONTENT) && (
            <span className="field-error">{getDisplayError(FORM_FIELDS.CONTENT)}</span>
          )}
          <div className="character-count">
            {formData.content.length} characters
          </div>
        </div>

        {/* Author Field */}
        <div className="form-group">
          <label htmlFor={FORM_FIELDS.AUTHOR} className="form-label">
            Author <span className="required">*</span>
          </label>
          <input
            type="text"
            id={FORM_FIELDS.AUTHOR}
            name={FORM_FIELDS.AUTHOR}
            value={formData.author}
            onChange={handleInputChange}
            onBlur={handleFieldBlur}
            className={`form-input ${hasFieldError(FORM_FIELDS.AUTHOR) ? 'error' : ''}`}
            placeholder="Enter author name..."
            maxLength={100}
            disabled={isSubmitting}
            required
          />
          {getDisplayError(FORM_FIELDS.AUTHOR) && (
            <span className="field-error">{getDisplayError(FORM_FIELDS.AUTHOR)}</span>
          )}
          <div className="character-count">
            {formData.author.length}/100
          </div>
        </div>

        {/* Tags Field */}
        <div className="form-group">
          <label htmlFor={FORM_FIELDS.TAGS} className="form-label">
            Tags
          </label>
          <input
            type="text"
            id={FORM_FIELDS.TAGS}
            name={FORM_FIELDS.TAGS}
            value={formData.tags}
            onChange={handleInputChange}
            onBlur={handleFieldBlur}
            className={`form-input ${hasFieldError(FORM_FIELDS.TAGS) ? 'error' : ''}`}
            placeholder="Enter tags separated by commas..."
            maxLength={500}
            disabled={isSubmitting}
          />
          {getDisplayError(FORM_FIELDS.TAGS) && (
            <span className="field-error">{getDisplayError(FORM_FIELDS.TAGS)}</span>
          )}
          <div className="character-count">
            {formData.tags.length}/500
          </div>
          <small className="field-help">
            Separate multiple tags with commas (e.g., finance, investing, stocks)
          </small>
        </div>

        {/* Image URL Field */}
        <div className="form-group">
          <label htmlFor={FORM_FIELDS.IMAGE_URL} className="form-label">
            Image URL
          </label>
          <input
            type="url"
            id={FORM_FIELDS.IMAGE_URL}
            name={FORM_FIELDS.IMAGE_URL}
            value={formData.image_url}
            onChange={handleInputChange}
            onBlur={handleFieldBlur}
            className={`form-input ${hasFieldError(FORM_FIELDS.IMAGE_URL) ? 'error' : ''}`}
            placeholder="https://example.com/image.jpg"
            disabled={isSubmitting}
          />
          {getDisplayError(FORM_FIELDS.IMAGE_URL) && (
            <span className="field-error">{getDisplayError(FORM_FIELDS.IMAGE_URL)}</span>
          )}
          <small className="field-help">
            Optional: Enter a URL for the post's featured image
          </small>
        </div>

        {/* Media Attachments */}
        <div className="form-group">
          <label className="form-label">
            Media Attachments
          </label>
          
          {/* Attached Media Display */}
          {attachedMedia.length > 0 && (
            <div className="attached-media">
              <h4>Attached Files ({attachedMedia.length})</h4>
              <div className="attached-media-grid">
                {attachedMedia.map((postMedia) => (
                  <div key={postMedia.id} className="attached-media-item">
                    <div className="attached-media-preview">
                      {postMedia.media_file.file_type === 'image' ? (
                        <img
                          src={postMedia.media_file.thumbnail_url || postMedia.media_file.file_url}
                          alt={postMedia.media_file.alt_text || postMedia.media_file.original_name}
                          className="attached-media-image"
                        />
                      ) : (
                        <div className="attached-media-video">
                          <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
                            <path d="M8 5v14l11-7z"/>
                          </svg>
                        </div>
                      )}
                    </div>
                    <div className="attached-media-info">
                      <span className="attached-media-name" title={postMedia.media_file.original_name}>
                        {postMedia.media_file.original_name}
                      </span>
                      <span className="attached-media-type">
                        {postMedia.media_file.file_type}
                      </span>
                    </div>
                    {formData.id && (
                      <button
                        type="button"
                        onClick={() => removeMediaFromPost(formData.id, postMedia.media_file.id)}
                        className="attached-media-remove"
                        aria-label={`Remove ${postMedia.media_file.original_name}`}
                        disabled={isSubmitting}
                      >
                        ×
                      </button>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Media Manager Toggle */}
          <div className="media-manager-controls">
            <button
              type="button"
              onClick={() => setShowMediaManager(!showMediaManager)}
              className="media-manager-toggle"
              disabled={isSubmitting}
            >
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <rect x="3" y="3" width="18" height="18" rx="2" ry="2" />
                <circle cx="8.5" cy="8.5" r="1.5" />
                <polyline points="21,15 16,10 5,21" />
              </svg>
              {showMediaManager ? 'Hide Media Manager' : 'Manage Media Files'}
            </button>
            
            {selectedMedia.length > 0 && formData.id && (
              <button
                type="button"
                onClick={() => attachMediaToPost(formData.id)}
                className="attach-media-button"
                disabled={isSubmitting}
              >
                Attach Selected ({selectedMedia.length})
              </button>
            )}
          </div>

          {/* Media Manager */}
          {showMediaManager && (
            <div className="media-manager-container">
              <MediaManager
                onMediaSelect={handleMediaSelect}
                selectedMedia={selectedMedia}
                multiple={true}
                showUpload={true}
                showGallery={true}
              />
            </div>
          )}

          <small className="field-help">
            Upload and attach images or videos to enhance your post content
          </small>
        </div>

        {/* Status Field */}
        <div className="form-group">
          <label htmlFor="status" className="form-label">
            Status
          </label>
          <select
            id="status"
            name="status"
            value={formData.status || 'draft'}
            onChange={handleInputChange}
            onBlur={handleFieldBlur}
            className={`form-select ${hasFieldError('status') ? 'error' : ''}`}
            disabled={isSubmitting}
          >
            <option value="draft">Draft</option>
            <option value="published">Published</option>
            <option value="scheduled">Scheduled</option>
          </select>
          {getDisplayError('status') && (
            <span className="field-error">{getDisplayError('status')}</span>
          )}
          <small className="field-help">
            Choose the publication status for this post
          </small>
        </div>

        {/* Scheduled Publish Date Field - Only show when status is 'scheduled' */}
        {(formData.status === 'scheduled') && (
          <div className="form-group">
            <label htmlFor="scheduled_publish_date" className="form-label">
              Scheduled Publish Date <span className="required">*</span>
            </label>
            <input
              type="datetime-local"
              id="scheduled_publish_date"
              name="scheduled_publish_date"
              value={formData.scheduled_publish_date ? 
                new Date(formData.scheduled_publish_date).toISOString().slice(0, 16) : 
                ''
              }
              onChange={handleInputChange}
              onBlur={handleFieldBlur}
              className={`form-input ${hasFieldError('scheduled_publish_date') ? 'error' : ''}`}
              disabled={isSubmitting}
              min={new Date().toISOString().slice(0, 16)}
              required
            />
            {getDisplayError('scheduled_publish_date') && (
              <span className="field-error">{getDisplayError('scheduled_publish_date')}</span>
            )}
            <small className="field-help">
              Select when this post should be automatically published
            </small>
          </div>
        )}



        {/* Submit Error */}
        {submitError && (
          <div className="form-group">
            {submitError.type ? (
              <NetworkErrorHandler 
                error={submitError} 
                operation="saving post"
                showDetails={false}
              />
            ) : (
              <ErrorMessage error={submitError} />
            )}
          </div>
        )}

        {/* Form Actions */}
        <div className="form-actions">
          <button
            type="submit"
            className="submit-button"
            disabled={isSubmitting}
          >
            {isSubmitting ? (
              <>
                <LoadingSpinner size="small" message="" />
                Submitting...
              </>
            ) : (
              submitButtonText
            )}
          </button>
        </div>
      </form>
    </div>
  );
};

export default PostForm;