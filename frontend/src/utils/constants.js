/**
 * Application constants
 */

// Form field names
export const FORM_FIELDS = {
  TITLE: 'title',
  CONTENT: 'content',
  AUTHOR: 'author',
  TAGS: 'tags',
  IMAGE_URL: 'image_url',
  STATUS: 'status',
  SCHEDULED_PUBLISH_DATE: 'scheduled_publish_date'
};

// Form validation messages
export const VALIDATION_MESSAGES = {
  REQUIRED: 'This field is required',
  TITLE_TOO_SHORT: 'Title must be at least 5 characters long',
  TITLE_TOO_LONG: 'Title must not exceed 200 characters',
  CONTENT_TOO_SHORT: 'Content must be at least 10 characters long',
  AUTHOR_TOO_SHORT: 'Author name must be at least 2 characters long',
  AUTHOR_TOO_LONG: 'Author name must not exceed 100 characters',
  TAGS_TOO_LONG: 'Tags must not exceed 500 characters',
  INVALID_URL: 'Please enter a valid HTTP or HTTPS URL'
};

// Success messages
export const SUCCESS_MESSAGES = {
  POST_CREATED: 'Blog post created successfully!',
  POST_UPDATED: 'Blog post updated successfully!',
  POST_DELETED: 'Blog post deleted successfully!'
};

// Error messages
export const ERROR_MESSAGES = {
  NETWORK_ERROR: 'Network error - please check your connection',
  SERVER_ERROR: 'Server error occurred - please try again later',
  VALIDATION_ERROR: 'Please fix the validation errors below',
  UNKNOWN_ERROR: 'An unexpected error occurred'
};

// Form states
export const FORM_STATES = {
  IDLE: 'idle',
  SUBMITTING: 'submitting',
  SUCCESS: 'success',
  ERROR: 'error'
};

// Post form initial values
export const INITIAL_POST_FORM = {
  title: '',
  content: '',
  author: '',
  tags: '',
  image_url: '',
  status: 'draft',
  scheduled_publish_date: ''
};

// Post status options
export const POST_STATUS = {
  DRAFT: 'draft',
  PUBLISHED: 'published',
  SCHEDULED: 'scheduled'
};

// Post status display names
export const POST_STATUS_DISPLAY = {
  [POST_STATUS.DRAFT]: 'Draft',
  [POST_STATUS.PUBLISHED]: 'Published',
  [POST_STATUS.SCHEDULED]: 'Scheduled'
};