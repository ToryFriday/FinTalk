import { simpleApi as api } from './api';

// User API endpoints
const USER_ENDPOINTS = {
  CURRENT_USER: '/api/auth/me/',
  USER_PROFILE: '/api/auth/profile/',
  PUBLIC_PROFILE: (userId) => `/api/auth/profile/${userId}/`,
  CHECK_USERNAME: '/api/auth/check-username/',
  CHECK_EMAIL: '/api/auth/check-email/',
  SEARCH_USERS: '/api/auth/users/',
};

/**
 * Get current authenticated user profile
 * @returns {Promise} API response with user profile data
 */
export const getCurrentUser = async () => {
  try {
    const response = await api.get(USER_ENDPOINTS.CURRENT_USER);
    return response;
  } catch (error) {
    console.error('Error fetching current user:', error);
    throw error;
  }
};

/**
 * Update current user profile
 * @param {FormData|Object} profileData - Profile data to update
 * @returns {Promise} API response with updated profile
 */
export const updateUserProfile = async (profileData) => {
  try {
    const config = {};
    
    // If profileData is FormData (for file uploads), set appropriate headers
    if (profileData instanceof FormData) {
      config.headers = {
        'Content-Type': 'multipart/form-data',
      };
    }
    
    const response = await api.put(USER_ENDPOINTS.USER_PROFILE, profileData, config);
    return response;
  } catch (error) {
    console.error('Error updating user profile:', error);
    throw error;
  }
};

/**
 * Get public user profile by ID
 * @param {number} userId - ID of the user
 * @returns {Promise} API response with public profile data
 */
export const getPublicUserProfile = async (userId) => {
  try {
    const response = await api.get(USER_ENDPOINTS.PUBLIC_PROFILE(userId));
    return response;
  } catch (error) {
    console.error('Error fetching public user profile:', error);
    throw error;
  }
};

/**
 * Check if username is available
 * @param {string} username - Username to check
 * @returns {Promise} API response with availability status
 */
export const checkUsernameAvailability = async (username) => {
  try {
    const response = await api.get(USER_ENDPOINTS.CHECK_USERNAME, {
      params: { username }
    });
    return response;
  } catch (error) {
    console.error('Error checking username availability:', error);
    throw error;
  }
};

/**
 * Check if email is available
 * @param {string} email - Email to check
 * @returns {Promise} API response with availability status
 */
export const checkEmailAvailability = async (email) => {
  try {
    const response = await api.get(USER_ENDPOINTS.CHECK_EMAIL, {
      params: { email }
    });
    return response;
  } catch (error) {
    console.error('Error checking email availability:', error);
    throw error;
  }
};

/**
 * Search users
 * @param {Object} params - Search parameters
 * @returns {Promise} API response with search results
 */
export const searchUsers = async (params = {}) => {
  try {
    const response = await api.get(USER_ENDPOINTS.SEARCH_USERS, { params });
    return response;
  } catch (error) {
    console.error('Error searching users:', error);
    throw error;
  }
};

/**
 * Get user posts
 * @param {number} userId - ID of the user
 * @param {Object} params - Query parameters
 * @returns {Promise} API response with user posts
 */
export const getUserPosts = async (userId, params = {}) => {
  try {
    const response = await api.get('/api/posts/', {
      params: {
        author_user: userId,
        ...params
      }
    });
    return response;
  } catch (error) {
    console.error('Error fetching user posts:', error);
    throw error;
  }
};

/**
 * Upload user avatar
 * @param {File} avatarFile - Avatar image file
 * @returns {Promise} API response with updated profile
 */
export const uploadAvatar = async (avatarFile) => {
  try {
    const formData = new FormData();
    formData.append('avatar', avatarFile);
    
    const response = await api.put(USER_ENDPOINTS.USER_PROFILE, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response;
  } catch (error) {
    console.error('Error uploading avatar:', error);
    throw error;
  }
};

/**
 * Delete user avatar
 * @returns {Promise} API response with updated profile
 */
export const deleteAvatar = async () => {
  try {
    const response = await api.put(USER_ENDPOINTS.USER_PROFILE, {
      avatar: null
    });
    return response;
  } catch (error) {
    console.error('Error deleting avatar:', error);
    throw error;
  }
};

/**
 * Get user activity summary
 * @param {number} userId - ID of the user (optional, defaults to current user)
 * @returns {Promise} API response with activity data
 */
export const getUserActivity = async (userId = null) => {
  try {
    const endpoint = userId 
      ? `/api/auth/users/${userId}/activity/`
      : '/api/auth/me/activity/';
    const response = await api.get(endpoint);
    return response;
  } catch (error) {
    console.error('Error fetching user activity:', error);
    throw error;
  }
};

export default {
  getCurrentUser,
  updateUserProfile,
  getPublicUserProfile,
  checkUsernameAvailability,
  checkEmailAvailability,
  searchUsers,
  getUserPosts,
  uploadAvatar,
  deleteAvatar,
  getUserActivity,
};