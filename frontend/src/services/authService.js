import apiClient from './apiClient';
import { API_ENDPOINTS } from './apiConfig';

/**
 * Initialize CSRF token by making a request to get it
 * @returns {Promise} Promise that resolves when CSRF token is obtained
 */
export const initializeCSRF = async () => {
  try {
    // Use fetch to avoid interceptor issues
    const response = await fetch(`${process.env.REACT_APP_API_URL || 'http://localhost:8000'}/admin/`, {
      method: 'GET',
      credentials: 'include',
    });
    
    if (process.env.NODE_ENV === 'development') {
      console.log('CSRF token initialized');
    }
  } catch (error) {
    console.warn('Could not initialize CSRF token:', error);
  }
};

/**
 * Login user with username/email and password
 * @param {string} username - Username or email
 * @param {string} password - Password
 * @returns {Promise} API response with user data
 */
export const login = async (username, password) => {
  try {
    // Ensure CSRF token is available before login
    await initializeCSRF();
    
    // Wait a bit for the cookie to be set
    await new Promise(resolve => setTimeout(resolve, 100));
    
    // Double-check that we have a CSRF token
    const csrfToken = document.cookie.split(';').find(cookie => cookie.trim().startsWith('csrftoken='));
    
    if (process.env.NODE_ENV === 'development') {
      console.log('🔍 Pre-login CSRF check:', {
        hasCsrfCookie: !!csrfToken,
        allCookies: document.cookie
      });
    }
    
    const response = await apiClient.post(API_ENDPOINTS.LOGIN, {
      username,
      password
    });
    
    // Store user data in localStorage if login successful
    if (response.data) {
      localStorage.setItem('user', JSON.stringify(response.data));
    }
    
    return response;
  } catch (error) {
    console.error('Login error:', error);
    throw error;
  }
};

/**
 * Register new user
 * @param {Object} userData - User registration data
 * @returns {Promise} API response with registration result
 */
export const register = async (userData) => {
  try {
    const response = await apiClient.post(API_ENDPOINTS.REGISTER, userData);
    return response;
  } catch (error) {
    console.error('Registration error:', error);
    throw error;
  }
};

/**
 * Logout current user
 * @returns {Promise} API response
 */
export const logout = async () => {
  try {
    const response = await apiClient.post(API_ENDPOINTS.LOGOUT);
    
    // Clear user data from localStorage
    localStorage.removeItem('user');
    
    return response;
  } catch (error) {
    console.error('Logout error:', error);
    // Clear localStorage even if API call fails
    localStorage.removeItem('user');
    throw error;
  }
};

/**
 * Get current authenticated user
 * @returns {Promise} API response with user data
 */
export const getCurrentUser = async () => {
  try {
    const response = await apiClient.get(API_ENDPOINTS.CURRENT_USER);
    
    // Update localStorage with fresh user data
    if (response.data) {
      localStorage.setItem('user', JSON.stringify(response.data));
    }
    
    return response;
  } catch (error) {
    console.error('Get current user error:', error);
    // Clear localStorage if user is not authenticated
    if (error.status === 401 || error.status === 403) {
      localStorage.removeItem('user');
    }
    throw error;
  }
};

/**
 * Verify email with token
 * @param {string} token - Email verification token
 * @returns {Promise} API response
 */
export const verifyEmail = async (token) => {
  try {
    const response = await apiClient.post(API_ENDPOINTS.VERIFY_EMAIL, { token });
    return response;
  } catch (error) {
    console.error('Email verification error:', error);
    throw error;
  }
};

/**
 * Resend email verification
 * @param {string} email - Email address
 * @returns {Promise} API response
 */
export const resendVerification = async (email) => {
  try {
    const response = await apiClient.post(API_ENDPOINTS.RESEND_VERIFICATION, { email });
    return response;
  } catch (error) {
    console.error('Resend verification error:', error);
    throw error;
  }
};

/**
 * Check if user is authenticated (from localStorage)
 * @returns {Object|null} User data or null
 */
export const getStoredUser = () => {
  try {
    const userData = localStorage.getItem('user');
    return userData ? JSON.parse(userData) : null;
  } catch (error) {
    console.error('Error parsing stored user data:', error);
    localStorage.removeItem('user');
    return null;
  }
};

/**
 * Check if user is authenticated
 * @returns {boolean} Authentication status
 */
export const isAuthenticated = () => {
  return getStoredUser() !== null;
};

/**
 * Clear authentication data
 */
export const clearAuth = () => {
  localStorage.removeItem('user');
};

/**
 * Update stored user data
 * @param {Object} userData - Updated user data
 */
export const updateStoredUser = (userData) => {
  localStorage.setItem('user', JSON.stringify(userData));
};

export default {
  login,
  register,
  logout,
  getCurrentUser,
  verifyEmail,
  resendVerification,
  getStoredUser,
  isAuthenticated,
  clearAuth,
  updateStoredUser,
  initializeCSRF,
};