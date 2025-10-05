import axios from 'axios';
import { 
  API_BASE_URL, 
  API_ENDPOINTS, 
  HTTP_STATUS, 
  ERROR_TYPES, 
  REQUEST_TIMEOUT, 
  DEFAULT_HEADERS 
} from './apiConfig';

// Create axios instance with base configuration
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: REQUEST_TIMEOUT,
  headers: DEFAULT_HEADERS,
  withCredentials: true, // Enable sending cookies for CSRF
});

// Utility function to get CSRF token from cookies
const getCSRFToken = () => {
  const name = 'csrftoken';
  let cookieValue = null;
  if (document.cookie && document.cookie !== '') {
    const cookies = document.cookie.split(';');
    for (let i = 0; i < cookies.length; i++) {
      const cookie = cookies[i].trim();
      if (cookie.substring(0, name.length + 1) === (name + '=')) {
        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
        break;
      }
    }
  }
  return cookieValue;
};

// Request interceptor for adding CSRF token and logging
apiClient.interceptors.request.use(
  (config) => {
    // Add CSRF token for non-GET requests
    if (config.method !== 'get') {
      const csrfToken = getCSRFToken();
      if (csrfToken) {
        config.headers['X-CSRFToken'] = csrfToken;
      }
    }
    
    // Log request for debugging (development only)
    if (process.env.NODE_ENV === 'development') {
      console.log(`Making ${config.method?.toUpperCase()} request to ${config.url}`);
    }
    return config;
  },
  (error) => {
    console.error('Request interceptor error:', error);
    return Promise.reject(error);
  }
);

// Response interceptor for error handling
apiClient.interceptors.response.use(
  (response) => {
    // Log successful response (development only)
    if (process.env.NODE_ENV === 'development') {
      console.log(`Response received: ${response.status} ${response.statusText}`);
    }
    return response;
  },
  (error) => {
    // Handle response errors
    if (process.env.NODE_ENV === 'development') {
      console.error('Response interceptor error:', error);
    }
    
    // If we get a 401 or 403 with authentication_required, clear stored auth
    if (error.response?.status === 401 || error.response?.status === 403) {
      const errorData = error.response.data;
      if (errorData?.error_type === 'authentication_required') {
        // Clear stored user data
        localStorage.removeItem('user');
      }
    }
    
    return Promise.reject(handleApiError(error));
  }
);

// Utility function for API error processing
export const handleApiError = (error) => {
  if (error.response) {
    // Server responded with error status
    const { status, data } = error.response;
    switch (status) {
      case HTTP_STATUS.BAD_REQUEST:
        return {
          type: ERROR_TYPES.VALIDATION_ERROR,
          message: 'Invalid data provided',
          details: data,
          status
        };
      case HTTP_STATUS.NOT_FOUND:
        return {
          type: ERROR_TYPES.NOT_FOUND,
          message: 'Resource not found',
          details: data,
          status
        };
      case HTTP_STATUS.INTERNAL_SERVER_ERROR:
        return {
          type: ERROR_TYPES.SERVER_ERROR,
          message: 'Internal server error occurred',
          details: data,
          status
        };
      default:
        return {
          type: ERROR_TYPES.API_ERROR,
          message: `Request failed with status ${status}`,
          details: data,
          status
        };
    }
  } else if (error.request) {
    // Network error - no response received
    return {
      type: ERROR_TYPES.NETWORK_ERROR,
      message: 'Network error - please check your connection',
      details: null,
      status: null
    };
  } else {
    // Something else happened
    return {
      type: ERROR_TYPES.UNKNOWN_ERROR,
      message: error.message || 'An unexpected error occurred',
      details: null,
      status: null
    };
  }
};

// Utility function to format API error for display
export const formatErrorMessage = (error) => {
  if (error.type === ERROR_TYPES.VALIDATION_ERROR && error.details) {
    // Extract validation error messages
    const messages = [];
    if (typeof error.details === 'object') {
      Object.entries(error.details).forEach(([field, fieldErrors]) => {
        if (Array.isArray(fieldErrors)) {
          fieldErrors.forEach(msg => messages.push(`${field}: ${msg}`));
        } else {
          messages.push(`${field}: ${fieldErrors}`);
        }
      });
    }
    return messages.length > 0 ? messages.join(', ') : error.message;
  }
  return error.message;
};

// BlogAPI class with all CRUD operations
class BlogAPI {
  /**
   * Get all blog posts
   * @param {Object} params - Query parameters (page, page_size, etc.)
   * @returns {Promise<Object>} Response with posts array and pagination info
   */
  static async getAllPosts(params = {}) {
    try {
      const response = await apiClient.get(API_ENDPOINTS.POSTS, { params });
      return {
        success: true,
        data: response.data,
        status: response.status
      };
    } catch (error) {
      // If backend is not available, return mock data for development
      if (error.type === ERROR_TYPES.NETWORK_ERROR) {
        console.warn('Backend not available, using mock data');
        return {
          success: true,
          data: [
            {
              id: 1,
              title: 'Welcome to Blog Manager',
              content: 'This is a sample blog post. The backend server is not running, so you\'re seeing mock data.',
              author: 'Demo User',
              tags: 'welcome, demo',
              image_url: '',
              created_at: new Date().toISOString(),
              updated_at: new Date().toISOString()
            },
            {
              id: 2,
              title: 'Getting Started',
              content: 'To see real data, start the Django backend server by running: python manage.py runserver',
              author: 'System',
              tags: 'setup, backend',
              image_url: '',
              created_at: new Date().toISOString(),
              updated_at: new Date().toISOString()
            }
          ],
          status: 200
        };
      }
      
      return {
        success: false,
        error: error,
        status: error.status
      };
    }
  }

  /**
   * Get a single blog post by ID
   * @param {number} id - Post ID
   * @returns {Promise<Object>} Response with post data
   */
  static async getPost(id) {
    try {
      const response = await apiClient.get(API_ENDPOINTS.POST_DETAIL(id));
      return {
        success: true,
        data: response.data,
        status: response.status
      };
    } catch (error) {
      return {
        success: false,
        error: error,
        status: error.status
      };
    }
  }

  /**
   * Create a new blog post
   * @param {Object} postData - Post data (title, content, author, tags, image_url)
   * @returns {Promise<Object>} Response with created post data
   */
  static async createPost(postData) {
    try {
      const response = await apiClient.post(API_ENDPOINTS.POSTS, postData);
      return {
        success: true,
        data: response.data,
        status: response.status
      };
    } catch (error) {
      return {
        success: false,
        error: error,
        status: error.status
      };
    }
  }

  /**
   * Update an existing blog post
   * @param {number} id - Post ID
   * @param {Object} postData - Updated post data
   * @returns {Promise<Object>} Response with updated post data
   */
  static async updatePost(id, postData) {
    try {
      const response = await apiClient.put(API_ENDPOINTS.POST_DETAIL(id), postData);
      return {
        success: true,
        data: response.data,
        status: response.status
      };
    } catch (error) {
      return {
        success: false,
        error: error,
        status: error.status
      };
    }
  }

  /**
   * Delete a blog post
   * @param {number} id - Post ID
   * @returns {Promise<Object>} Response indicating success/failure
   */
  static async deletePost(id) {
    try {
      const response = await apiClient.delete(API_ENDPOINTS.POST_DETAIL(id));
      return {
        success: true,
        data: null,
        status: response.status
      };
    } catch (error) {
      return {
        success: false,
        error: error,
        status: error.status
      };
    }
  }

  /**
   * Partial update of a blog post (PATCH)
   * @param {number} id - Post ID
   * @param {Object} partialData - Partial post data to update
   * @returns {Promise<Object>} Response with updated post data
   */
  static async patchPost(id, partialData) {
    try {
      const response = await apiClient.patch(API_ENDPOINTS.POST_DETAIL(id), partialData);
      return {
        success: true,
        data: response.data,
        status: response.status
      };
    } catch (error) {
      return {
        success: false,
        error: error,
        status: error.status
      };
    }
  }

  /**
   * Get draft posts for the authenticated user
   * @param {Object} params - Query parameters (page, page_size, etc.)
   * @returns {Promise<Object>} Response with draft posts array and pagination info
   */
  static async getDraftPosts(params = {}) {
    try {
      const response = await apiClient.get('/api/posts/drafts/', { params });
      return {
        success: true,
        data: response.data,
        status: response.status
      };
    } catch (error) {
      return {
        success: false,
        error: error,
        status: error.status
      };
    }
  }

  /**
   * Schedule a post for future publication
   * @param {number} id - Post ID
   * @param {Object} scheduleData - Schedule data with scheduled_publish_date
   * @returns {Promise<Object>} Response with updated post data
   */
  static async schedulePost(id, scheduleData) {
    try {
      const response = await apiClient.post(`/api/posts/${id}/schedule/`, scheduleData);
      return {
        success: true,
        data: response.data,
        status: response.status
      };
    } catch (error) {
      return {
        success: false,
        error: error,
        status: error.status
      };
    }
  }

  /**
   * Publish a draft or scheduled post immediately
   * @param {number} id - Post ID
   * @returns {Promise<Object>} Response with updated post data
   */
  static async publishPost(id) {
    try {
      const response = await apiClient.post(`/api/posts/${id}/publish/`);
      return {
        success: true,
        data: response.data,
        status: response.status
      };
    } catch (error) {
      return {
        success: false,
        error: error,
        status: error.status
      };
    }
  }

  /**
   * Save an article for later reading
   * @param {number} id - Post ID
   * @param {string} notes - Optional notes about why the article was saved
   * @returns {Promise<Object>} Response with saved article data
   */
  static async savePost(id, notes = '') {
    try {
      const response = await apiClient.post(API_ENDPOINTS.SAVE_POST(id), { notes });
      return {
        success: true,
        data: response.data,
        status: response.status
      };
    } catch (error) {
      return {
        success: false,
        error: error,
        status: error.status
      };
    }
  }

  /**
   * Unsave an article
   * @param {number} id - Post ID
   * @returns {Promise<Object>} Response indicating success/failure
   */
  static async unsavePost(id) {
    try {
      const response = await apiClient.delete(API_ENDPOINTS.SAVE_POST(id));
      return {
        success: true,
        data: response.data,
        status: response.status
      };
    } catch (error) {
      return {
        success: false,
        error: error,
        status: error.status
      };
    }
  }

  /**
   * Check if an article is saved by the current user
   * @param {number} id - Post ID
   * @returns {Promise<Object>} Response with saved status
   */
  static async checkSavedStatus(id) {
    try {
      const response = await apiClient.get(API_ENDPOINTS.CHECK_SAVED(id));
      return {
        success: true,
        data: response.data,
        status: response.status
      };
    } catch (error) {
      return {
        success: false,
        error: error,
        status: error.status
      };
    }
  }

  /**
   * Get all saved articles for the authenticated user
   * @param {Object} params - Query parameters (search, tag, author, date_from, date_to, ordering, page, page_size)
   * @returns {Promise<Object>} Response with saved articles array and pagination info
   */
  static async getSavedPosts(params = {}) {
    try {
      const response = await apiClient.get(API_ENDPOINTS.SAVED_POSTS, { params });
      return {
        success: true,
        data: response.data,
        status: response.status
      };
    } catch (error) {
      return {
        success: false,
        error: error,
        status: error.status
      };
    }
  }

  /**
   * Upload a media file (image or video)
   * @param {File} file - File to upload
   * @param {string} altText - Alternative text for accessibility
   * @returns {Promise<Object>} Response with uploaded media data
   */
  static async uploadMedia(file, altText = '') {
    try {
      const formData = new FormData();
      formData.append('file', file);
      if (altText) {
        formData.append('alt_text', altText);
      }

      const response = await apiClient.post(API_ENDPOINTS.MEDIA_UPLOAD, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      
      return {
        success: true,
        data: response.data,
        status: response.status
      };
    } catch (error) {
      return {
        success: false,
        error: error,
        status: error.status
      };
    }
  }

  /**
   * Get list of uploaded media files
   * @param {Object} params - Query parameters (file_type, page, page_size)
   * @returns {Promise<Object>} Response with media files array and pagination info
   */
  static async getMediaFiles(params = {}) {
    try {
      const response = await apiClient.get(API_ENDPOINTS.MEDIA_LIST, { params });
      return {
        success: true,
        data: response.data,
        status: response.status
      };
    } catch (error) {
      return {
        success: false,
        error: error,
        status: error.status
      };
    }
  }

  /**
   * Get a specific media file by ID
   * @param {number} id - Media file ID
   * @returns {Promise<Object>} Response with media file data
   */
  static async getMediaFile(id) {
    try {
      const response = await apiClient.get(API_ENDPOINTS.MEDIA_DETAIL(id));
      return {
        success: true,
        data: response.data,
        status: response.status
      };
    } catch (error) {
      return {
        success: false,
        error: error,
        status: error.status
      };
    }
  }

  /**
   * Delete a media file
   * @param {number} id - Media file ID
   * @returns {Promise<Object>} Response indicating success/failure
   */
  static async deleteMediaFile(id) {
    try {
      const response = await apiClient.delete(API_ENDPOINTS.MEDIA_DETAIL(id));
      return {
        success: true,
        data: null,
        status: response.status
      };
    } catch (error) {
      return {
        success: false,
        error: error,
        status: error.status
      };
    }
  }

  /**
   * Get media files attached to a specific post
   * @param {number} postId - Post ID
   * @returns {Promise<Object>} Response with attached media files
   */
  static async getPostMedia(postId) {
    try {
      const response = await apiClient.get(API_ENDPOINTS.POST_MEDIA(postId));
      return {
        success: true,
        data: response.data,
        status: response.status
      };
    } catch (error) {
      return {
        success: false,
        error: error,
        status: error.status
      };
    }
  }

  /**
   * Attach media files to a post
   * @param {number} postId - Post ID
   * @param {Array} mediaFileIds - Array of media file IDs to attach
   * @param {Object} captions - Object mapping media file IDs to captions
   * @returns {Promise<Object>} Response with attached media data
   */
  static async attachMediaToPost(postId, mediaFileIds, captions = {}) {
    try {
      const response = await apiClient.post(API_ENDPOINTS.POST_MEDIA(postId), {
        media_file_ids: mediaFileIds,
        captions: captions
      });
      return {
        success: true,
        data: response.data,
        status: response.status
      };
    } catch (error) {
      return {
        success: false,
        error: error,
        status: error.status
      };
    }
  }

  /**
   * Remove media file from a post
   * @param {number} postId - Post ID
   * @param {number} mediaId - Media file ID to remove
   * @returns {Promise<Object>} Response indicating success/failure
   */
  static async removeMediaFromPost(postId, mediaId) {
    try {
      const response = await apiClient.delete(API_ENDPOINTS.POST_MEDIA_DETAIL(postId, mediaId));
      return {
        success: true,
        data: null,
        status: response.status
      };
    } catch (error) {
      return {
        success: false,
        error: error,
        status: error.status
      };
    }
  }
}

// Export both the BlogAPI class and the axios client
export default BlogAPI;
export { apiClient as api };

// Also create a simple API object for direct use
export const simpleApi = {
  get: (url, config) => apiClient.get(url, config),
  post: (url, data, config) => apiClient.post(url, data, config),
  put: (url, data, config) => apiClient.put(url, data, config),
  delete: (url, config) => apiClient.delete(url, config),
  patch: (url, data, config) => apiClient.patch(url, data, config),
};