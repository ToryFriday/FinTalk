import React, { useState, useEffect } from 'react';
import { validatePostForm, getFieldError } from '../../utils/validation';
import { FORM_FIELDS, INITIAL_POST_FORM } from '../../utils/constants';
import ErrorMessage from '../common/ErrorMessage';
import FormErrorDisplay from '../common/FormErrorDisplay';
import NetworkErrorHandler from '../common/NetworkErrorHandler';
import LoadingSpinner from '../common/LoadingSpinner';
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

  // Update form data when initialData changes (for edit mode)
  useEffect(() => {
    setFormData(initialData);
  }, [initialData]);

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