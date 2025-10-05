/**
 * Disqus service for handling comment counts and integration
 */

class DisqusService {
  constructor() {
    this.shortname = process.env.REACT_APP_DISQUS_SHORTNAME;
    this.siteUrl = process.env.REACT_APP_SITE_URL || window.location.origin;
    this.commentCounts = new Map();
    this.isCountScriptLoaded = false;
  }

  /**
   * Get the full URL for a post
   * @param {string|number} postId - Post ID
   * @returns {string} Full URL for the post
   */
  getPostUrl(postId) {
    return `${this.siteUrl}/posts/${postId}`;
  }

  /**
   * Get the identifier for a post
   * @param {string|number} postId - Post ID
   * @param {string} postSlug - Optional post slug
   * @returns {string} Disqus identifier
   */
  getPostIdentifier(postId, postSlug = null) {
    return postSlug || `post-${postId}`;
  }

  /**
   * Load Disqus comment count script
   * @returns {Promise<boolean>} Promise that resolves when script is loaded
   */
  loadCommentCountScript() {
    return new Promise((resolve, reject) => {
      if (!this.shortname) {
        console.warn('Disqus shortname not configured');
        resolve(false);
        return;
      }

      if (this.isCountScriptLoaded) {
        resolve(true);
        return;
      }

      // Check if script already exists
      const existingScript = document.querySelector('script[src*="count.js"]');
      if (existingScript) {
        this.isCountScriptLoaded = true;
        resolve(true);
        return;
      }

      const script = document.createElement('script');
      script.id = 'dsq-count-scr';
      script.src = `https://${this.shortname}.disqus.com/count.js`;
      script.async = true;
      
      script.onload = () => {
        this.isCountScriptLoaded = true;
        resolve(true);
      };
      
      script.onerror = () => {
        console.error('Failed to load Disqus comment count script');
        reject(new Error('Failed to load Disqus count script'));
      };

      document.head.appendChild(script);
    });
  }

  /**
   * Get comment count for a specific post
   * @param {string|number} postId - Post ID
   * @param {string} postSlug - Optional post slug
   * @returns {Promise<number>} Promise that resolves to comment count
   */
  async getCommentCount(postId, postSlug = null) {
    if (!this.shortname) {
      return 0;
    }

    const identifier = this.getPostIdentifier(postId, postSlug);
    
    // Check if we have cached count
    if (this.commentCounts.has(identifier)) {
      return this.commentCounts.get(identifier);
    }

    try {
      await this.loadCommentCountScript();
      
      // Wait for DISQUSWIDGETS to be available
      return new Promise((resolve) => {
        const checkDisqusWidgets = () => {
          if (window.DISQUSWIDGETS) {
            // Use Disqus API to get comment count
            window.DISQUSWIDGETS.getCount({
              reset: true
            });
            
            // Listen for count updates
            const checkCount = () => {
              const countElement = document.querySelector(`[data-disqus-identifier="${identifier}"]`);
              if (countElement && countElement.textContent) {
                const count = parseInt(countElement.textContent) || 0;
                this.commentCounts.set(identifier, count);
                resolve(count);
              } else {
                // Default to 0 if no count found
                resolve(0);
              }
            };
            
            // Check immediately and after a short delay
            setTimeout(checkCount, 100);
          } else {
            // Retry after a short delay
            setTimeout(checkDisqusWidgets, 100);
          }
        };
        
        checkDisqusWidgets();
      });
    } catch (error) {
      console.error('Error getting comment count:', error);
      return 0;
    }
  }

  /**
   * Get comment counts for multiple posts
   * @param {Array} posts - Array of post objects with id property
   * @returns {Promise<Map>} Promise that resolves to Map of postId -> count
   */
  async getCommentCounts(posts) {
    if (!this.shortname || !posts || posts.length === 0) {
      return new Map();
    }

    try {
      await this.loadCommentCountScript();
      
      const counts = new Map();
      
      // Create temporary elements for each post to get counts
      const tempContainer = document.createElement('div');
      tempContainer.style.display = 'none';
      document.body.appendChild(tempContainer);
      
      posts.forEach(post => {
        const identifier = this.getPostIdentifier(post.id);
        const url = this.getPostUrl(post.id);
        
        const link = document.createElement('a');
        link.href = url;
        link.setAttribute('data-disqus-identifier', identifier);
        link.className = 'disqus-comment-count';
        link.textContent = '0';
        tempContainer.appendChild(link);
      });
      
      return new Promise((resolve) => {
        const getCountsFromElements = () => {
          posts.forEach(post => {
            const identifier = this.getPostIdentifier(post.id);
            const element = tempContainer.querySelector(`[data-disqus-identifier="${identifier}"]`);
            if (element) {
              const count = parseInt(element.textContent) || 0;
              counts.set(post.id, count);
              this.commentCounts.set(identifier, count);
            }
          });
          
          // Clean up temporary container
          document.body.removeChild(tempContainer);
          resolve(counts);
        };
        
        if (window.DISQUSWIDGETS) {
          window.DISQUSWIDGETS.getCount({ reset: true });
          setTimeout(getCountsFromElements, 500);
        } else {
          // If DISQUSWIDGETS is not available, return empty counts
          setTimeout(() => {
            document.body.removeChild(tempContainer);
            resolve(counts);
          }, 100);
        }
      });
    } catch (error) {
      console.error('Error getting comment counts:', error);
      return new Map();
    }
  }

  /**
   * Clear cached comment counts
   */
  clearCache() {
    this.commentCounts.clear();
  }

  /**
   * Check if Disqus is properly configured
   * @returns {boolean} True if Disqus is configured
   */
  isConfigured() {
    return !!this.shortname;
  }
}

// Export singleton instance
export default new DisqusService();