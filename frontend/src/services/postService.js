import { simpleApi as api } from './api';

/**
 * Get posts by a specific user
 * @param {number} userId - ID of the user
 * @param {Object} params - Query parameters
 * @returns {Promise} API response with user's posts
 */
export const getUserPosts = async (userId, params = {}) => {
  try {
    const response = await api.get(`/api/posts/`, { 
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

export default {
  getUserPosts,
};