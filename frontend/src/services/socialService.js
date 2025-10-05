import { simpleApi as api } from './api';

// Social API endpoints
const SOCIAL_ENDPOINTS = {
  FOLLOW_USER: (userId) => `/api/auth/users/${userId}/follow/`,
  USER_FOLLOWERS: (userId) => `/api/auth/users/${userId}/followers/`,
  USER_FOLLOWING: (userId) => `/api/auth/users/${userId}/following/`,
  USER_SOCIAL_PROFILE: (userId) => `/api/auth/users/${userId}/social-profile/`,
  CHECK_FOLLOW_STATUS: (userId) => `/api/auth/users/${userId}/follow-status/`,
  MUTUAL_FOLLOWERS: (userId) => `/api/auth/users/${userId}/mutual-followers/`,
  SUGGESTED_USERS: '/api/auth/users/suggested/',
};

/**
 * Follow a user
 * @param {number} userId - ID of the user to follow
 * @returns {Promise} API response
 */
export const followUser = async (userId) => {
  try {
    const response = await api.post(SOCIAL_ENDPOINTS.FOLLOW_USER(userId));
    return response;
  } catch (error) {
    console.error('Error following user:', error);
    throw error;
  }
};

/**
 * Unfollow a user
 * @param {number} userId - ID of the user to unfollow
 * @returns {Promise} API response
 */
export const unfollowUser = async (userId) => {
  try {
    const response = await api.post(SOCIAL_ENDPOINTS.FOLLOW_USER(userId));
    return response;
  } catch (error) {
    console.error('Error unfollowing user:', error);
    throw error;
  }
};

/**
 * Get user's followers
 * @param {number} userId - ID of the user
 * @param {Object} params - Query parameters (page, limit, etc.)
 * @returns {Promise} API response with followers list
 */
export const getUserFollowers = async (userId, params = {}) => {
  try {
    const response = await api.get(SOCIAL_ENDPOINTS.USER_FOLLOWERS(userId), { params });
    return response;
  } catch (error) {
    console.error('Error fetching user followers:', error);
    throw error;
  }
};

/**
 * Get users that a user is following
 * @param {number} userId - ID of the user
 * @param {Object} params - Query parameters (page, limit, etc.)
 * @returns {Promise} API response with following list
 */
export const getUserFollowing = async (userId, params = {}) => {
  try {
    const response = await api.get(SOCIAL_ENDPOINTS.USER_FOLLOWING(userId), { params });
    return response;
  } catch (error) {
    console.error('Error fetching user following:', error);
    throw error;
  }
};

/**
 * Get user's social profile with stats
 * @param {number} userId - ID of the user
 * @returns {Promise} API response with user profile and social stats
 */
export const getUserSocialProfile = async (userId) => {
  try {
    const response = await api.get(SOCIAL_ENDPOINTS.USER_SOCIAL_PROFILE(userId));
    return response;
  } catch (error) {
    console.error('Error fetching user social profile:', error);
    throw error;
  }
};

/**
 * Check follow status between current user and another user
 * @param {number} userId - ID of the user to check
 * @returns {Promise} API response with follow status
 */
export const checkFollowStatus = async (userId) => {
  try {
    const response = await api.get(SOCIAL_ENDPOINTS.CHECK_FOLLOW_STATUS(userId));
    return response;
  } catch (error) {
    console.error('Error checking follow status:', error);
    throw error;
  }
};

/**
 * Get mutual followers between current user and another user
 * @param {number} userId - ID of the user
 * @returns {Promise} API response with mutual followers
 */
export const getMutualFollowers = async (userId) => {
  try {
    const response = await api.get(SOCIAL_ENDPOINTS.MUTUAL_FOLLOWERS(userId));
    return response;
  } catch (error) {
    console.error('Error fetching mutual followers:', error);
    throw error;
  }
};

/**
 * Get suggested users to follow
 * @param {Object} params - Query parameters (limit, etc.)
 * @returns {Promise} API response with suggested users
 */
export const getSuggestedUsers = async (params = {}) => {
  try {
    const response = await api.get(SOCIAL_ENDPOINTS.SUGGESTED_USERS, { params });
    return response;
  } catch (error) {
    console.error('Error fetching suggested users:', error);
    throw error;
  }
};

/**
 * Batch follow/unfollow multiple users
 * @param {Array} userIds - Array of user IDs
 * @param {string} action - 'follow' or 'unfollow'
 * @returns {Promise} Array of API responses
 */
export const batchFollowUsers = async (userIds, action = 'follow') => {
  try {
    const promises = userIds.map(userId => {
      if (action === 'follow') {
        return followUser(userId);
      } else {
        return unfollowUser(userId);
      }
    });
    
    const responses = await Promise.allSettled(promises);
    return responses;
  } catch (error) {
    console.error('Error in batch follow operation:', error);
    throw error;
  }
};

/**
 * Search users for following
 * @param {string} query - Search query
 * @param {Object} params - Additional parameters
 * @returns {Promise} API response with search results
 */
export const searchUsersToFollow = async (query, params = {}) => {
  try {
    const searchParams = {
      search: query,
      ...params
    };
    const response = await api.get('/api/auth/users/', { params: searchParams });
    return response;
  } catch (error) {
    console.error('Error searching users:', error);
    throw error;
  }
};

/**
 * Get user's social activity feed
 * @param {Object} params - Query parameters
 * @returns {Promise} API response with activity feed
 */
export const getSocialActivityFeed = async (params = {}) => {
  try {
    // This would be implemented when we have an activity feed endpoint
    const response = await api.get('/api/auth/activity-feed/', { params });
    return response;
  } catch (error) {
    console.error('Error fetching social activity feed:', error);
    throw error;
  }
};

/**
 * Get user's social stats
 * @param {number} userId - ID of the user (optional, defaults to current user)
 * @returns {Promise} API response with social stats
 */
export const getUserSocialStats = async (userId = null) => {
  try {
    const endpoint = userId 
      ? SOCIAL_ENDPOINTS.USER_SOCIAL_PROFILE(userId)
      : '/api/auth/me/';
    const response = await api.get(endpoint);
    return response;
  } catch (error) {
    console.error('Error fetching user social stats:', error);
    throw error;
  }
};

export default {
  followUser,
  unfollowUser,
  getUserFollowers,
  getUserFollowing,
  getUserSocialProfile,
  checkFollowStatus,
  getMutualFollowers,
  getSuggestedUsers,
  batchFollowUsers,
  searchUsersToFollow,
  getSocialActivityFeed,
  getUserSocialStats,
};