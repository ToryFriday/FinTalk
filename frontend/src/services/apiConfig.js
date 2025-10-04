// API Configuration constants and utilities

// Base URL configuration
export const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

// API endpoints
export const API_ENDPOINTS = {
  POSTS: '/api/posts/',
  POST_DETAIL: (id) => `/api/posts/${id}/`,
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