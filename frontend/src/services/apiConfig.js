// API Configuration constants and utilities

// Base URL configuration
export const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

// API endpoints
export const API_ENDPOINTS = {
  // Authentication endpoints
  LOGIN: '/api/auth/login/',
  LOGOUT: '/api/auth/logout/',
  REGISTER: '/api/auth/register/',
  VERIFY_EMAIL: '/api/auth/verify-email/',
  RESEND_VERIFICATION: '/api/auth/resend-verification/',
  CURRENT_USER: '/api/auth/me/',
  PROFILE: '/api/auth/profile/',
  
  // Posts endpoints
  POSTS: '/api/posts/',
  POST_DETAIL: (id) => `/api/posts/${id}/`,
  SAVE_POST: (id) => `/api/posts/${id}/save/`,
  CHECK_SAVED: (id) => `/api/posts/${id}/saved/`,
  SAVED_POSTS: '/api/posts/saved/',
  
  // Media endpoints
  MEDIA_UPLOAD: '/api/posts/media/upload/',
  MEDIA_LIST: '/api/posts/media/',
  MEDIA_DETAIL: (id) => `/api/posts/media/${id}/`,
  POST_MEDIA: (id) => `/api/posts/${id}/media/`,
  POST_MEDIA_DETAIL: (postId, mediaId) => `/api/posts/${postId}/media/${mediaId}/`,
};

// HTTP status codes
export const HTTP_STATUS = {
  OK: 200,
  CREATED: 201,
  NO_CONTENT: 204,
  BAD_REQUEST: 400,
  NOT_FOUND: 404,
  INTERNAL_SERVER_ERROR: 500,
};

// Error types
export const ERROR_TYPES = {
  VALIDATION_ERROR: 'VALIDATION_ERROR',
  NOT_FOUND: 'NOT_FOUND',
  SERVER_ERROR: 'SERVER_ERROR',
  NETWORK_ERROR: 'NETWORK_ERROR',
  API_ERROR: 'API_ERROR',
  UNKNOWN_ERROR: 'UNKNOWN_ERROR',
};

// Request timeout in milliseconds
export const REQUEST_TIMEOUT = 10000;

// Default headers
export const DEFAULT_HEADERS = {
  'Content-Type': 'application/json',
  'X-Requested-With': 'XMLHttpRequest',
};

// Pagination defaults
export const PAGINATION_DEFAULTS = {
  PAGE_SIZE: 10,
  INITIAL_PAGE: 1,
};

// Validation constants
export const VALIDATION_LIMITS = {
  TITLE_MIN_LENGTH: 5,
  TITLE_MAX_LENGTH: 200,
  CONTENT_MIN_LENGTH: 10,
  AUTHOR_MAX_LENGTH: 100,
  TAGS_MAX_LENGTH: 500,
  
  // Media validation limits
  MAX_IMAGE_SIZE: 10 * 1024 * 1024, // 10MB
  MAX_VIDEO_SIZE: 50 * 1024 * 1024, // 50MB
  ALT_TEXT_MAX_LENGTH: 255,
  CAPTION_MAX_LENGTH: 1000,
};

// Allowed file types
export const ALLOWED_FILE_TYPES = {
  IMAGES: ['image/jpeg', 'image/png', 'image/gif', 'image/webp'],
  VIDEOS: ['video/mp4', 'video/webm', 'video/ogg', 'video/quicktime', 'video/x-msvideo'],
};

// File extensions
export const ALLOWED_EXTENSIONS = {
  IMAGES: ['.jpg', '.jpeg', '.png', '.gif', '.webp'],
  VIDEOS: ['.mp4', '.webm', '.ogg', '.mov', '.avi'],
};

export default {
  API_BASE_URL,
  API_ENDPOINTS,
  HTTP_STATUS,
  ERROR_TYPES,
  REQUEST_TIMEOUT,
  DEFAULT_HEADERS,
  PAGINATION_DEFAULTS,
  VALIDATION_LIMITS,
};