/**
 * Validation utilities for blog post forms
 */

// Validation rules
export const VALIDATION_RULES = {
  TITLE_MIN_LENGTH: 5,
  TITLE_MAX_LENGTH: 200,
  CONTENT_MIN_LENGTH: 10,
  AUTHOR_MIN_LENGTH: 2,
  AUTHOR_MAX_LENGTH: 100,
  TAGS_MAX_LENGTH: 500,
  URL_PATTERN: /^https?:\/\/.+/
};

/**
 * Validate post title
 * @param {string} title - Post title
 * @returns {string|null} Error message or null if valid
 */
export const validateTitle = (title) => {
  if (!title || typeof title !== 'string') {
    return 'Title is required';
  }
  
  const trimmedTitle = title.trim();
  if (trimmedTitle.length === 0) {
    return 'Title is required';
  }
  
  if (trimmedTitle.length < VALIDATION_RULES.TITLE_MIN_LENGTH) {
    return `Title must be at least ${VALIDATION_RULES.TITLE_MIN_LENGTH} characters long`;
  }
  
  if (trimmedTitle.length > VALIDATION_RULES.TITLE_MAX_LENGTH) {
    return `Title must not exceed ${VALIDATION_RULES.TITLE_MAX_LENGTH} characters`;
  }
  
  return null;
};

/**
 * Validate post content
 * @param {string} content - Post content
 * @returns {string|null} Error message or null if valid
 */
export const validateContent = (content) => {
  if (!content || typeof content !== 'string') {
    return 'Content is required';
  }
  
  const trimmedContent = content.trim();
  if (trimmedContent.length === 0) {
    return 'Content is required';
  }
  
  if (trimmedContent.length < VALIDATION_RULES.CONTENT_MIN_LENGTH) {
    return `Content must be at least ${VALIDATION_RULES.CONTENT_MIN_LENGTH} characters long`;
  }
  
  return null;
};

/**
 * Validate author name
 * @param {string} author - Author name
 * @returns {string|null} Error message or null if valid
 */
export const validateAuthor = (author) => {
  if (!author || typeof author !== 'string') {
    return 'Author is required';
  }
  
  const trimmedAuthor = author.trim();
  if (trimmedAuthor.length === 0) {
    return 'Author is required';
  }
  
  if (trimmedAuthor.length < VALIDATION_RULES.AUTHOR_MIN_LENGTH) {
    return `Author name must be at least ${VALIDATION_RULES.AUTHOR_MIN_LENGTH} characters long`;
  }
  
  if (trimmedAuthor.length > VALIDATION_RULES.AUTHOR_MAX_LENGTH) {
    return `Author name must not exceed ${VALIDATION_RULES.AUTHOR_MAX_LENGTH} characters`;
  }
  
  return null;
};

/**
 * Validate tags
 * @param {string} tags - Tags string
 * @returns {string|null} Error message or null if valid
 */
export const validateTags = (tags) => {
  if (!tags) {
    return null; // Tags are optional
  }
  
  if (typeof tags !== 'string') {
    return 'Tags must be a string';
  }
  
  if (tags.length > VALIDATION_RULES.TAGS_MAX_LENGTH) {
    return `Tags must not exceed ${VALIDATION_RULES.TAGS_MAX_LENGTH} characters`;
  }
  
  return null;
};

/**
 * Validate image URL
 * @param {string} imageUrl - Image URL
 * @returns {string|null} Error message or null if valid
 */
export const validateImageUrl = (imageUrl) => {
  if (!imageUrl) {
    return null; // Image URL is optional
  }
  
  if (typeof imageUrl !== 'string') {
    return 'Image URL must be a string';
  }
  
  const trimmedUrl = imageUrl.trim();
  if (trimmedUrl.length === 0) {
    return null; // Empty string is valid (optional field)
  }
  
  if (!VALIDATION_RULES.URL_PATTERN.test(trimmedUrl)) {
    return 'Image URL must be a valid HTTP or HTTPS URL';
  }
  
  return null;
};

/**
 * Validate entire post form data
 * @param {Object} postData - Post form data
 * @returns {Object} Validation result with errors object
 */
export const validatePostForm = (postData) => {
  const errors = {};
  
  const titleError = validateTitle(postData.title);
  if (titleError) errors.title = titleError;
  
  const contentError = validateContent(postData.content);
  if (contentError) errors.content = contentError;
  
  const authorError = validateAuthor(postData.author);
  if (authorError) errors.author = authorError;
  
  const tagsError = validateTags(postData.tags);
  if (tagsError) errors.tags = tagsError;
  
  const imageUrlError = validateImageUrl(postData.image_url);
  if (imageUrlError) errors.image_url = imageUrlError;
  
  return {
    isValid: Object.keys(errors).length === 0,
    errors
  };
};

/**
 * Get field validation error for real-time validation
 * @param {string} fieldName - Field name
 * @param {any} value - Field value
 * @returns {string|null} Error message or null if valid
 */
export const getFieldError = (fieldName, value) => {
  switch (fieldName) {
    case 'title':
      return validateTitle(value);
    case 'content':
      return validateContent(value);
    case 'author':
      return validateAuthor(value);
    case 'tags':
      return validateTags(value);
    case 'image_url':
      return validateImageUrl(value);
    default:
      return null;
  }
};