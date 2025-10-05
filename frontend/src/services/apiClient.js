import axios from 'axios';
import { API_BASE_URL, REQUEST_TIMEOUT, DEFAULT_HEADERS } from './apiConfig';

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
  
  // Debug logging in development
  if (process.env.NODE_ENV === 'development') {
    console.log('🔍 CSRF Token Check:', {
      allCookies: document.cookie,
      csrfToken: cookieValue ? cookieValue.substring(0, 20) + '...' : 'None'
    });
  }
  
  return cookieValue;
};

// Simple function to get CSRF token with a direct request
const fetchCSRFToken = async () => {
  try {
    // Use fetch instead of axios to avoid interceptor loops
    const response = await fetch(`${API_BASE_URL}/admin/`, {
      method: 'GET',
      credentials: 'include', // Include cookies
    });
    
    // The CSRF token should now be in the cookies
    return getCSRFToken();
  } catch (error) {
    console.warn('Could not fetch CSRF token:', error);
    return null;
  }
};

// Request interceptor for adding CSRF token and logging
apiClient.interceptors.request.use(
  (config) => {
    // Add CSRF token for non-GET requests
    if (config.method !== 'get') {
      const csrfToken = getCSRFToken();
      
      if (csrfToken) {
        config.headers['X-CSRFToken'] = csrfToken;
        
        if (process.env.NODE_ENV === 'development') {
          console.log('✅ CSRF token added to request:', csrfToken.substring(0, 20) + '...');
        }
      } else {
        if (process.env.NODE_ENV === 'development') {
          console.warn('⚠️ No CSRF token available for request!');
        }
      }
    }
    
    // Log request for debugging (development only)
    if (process.env.NODE_ENV === 'development') {
      console.log(`Making ${config.method?.toUpperCase()} request to ${config.url}`);
      console.log('Request headers:', config.headers);
    }
    return config;
  },
  (error) => {
    if (process.env.NODE_ENV === 'development') {
      console.error('Request interceptor error:', error);
    }
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
    
    return Promise.reject(error);
  }
);

export default apiClient;
export { fetchCSRFToken };