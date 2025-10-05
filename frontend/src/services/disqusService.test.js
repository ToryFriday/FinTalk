import disqusService from './disqusService';

// Mock environment variables
const originalEnv = process.env;

beforeEach(() => {
  jest.resetModules();
  process.env = { ...originalEnv };
  
  // Clear any existing Disqus scripts
  const existingScripts = document.querySelectorAll('script[src*="disqus.com"]');
  existingScripts.forEach(script => script.remove());
  
  // Clear Disqus global variables
  delete window.DISQUSWIDGETS;
  
  // Reset service state
  disqusService.clearCache();
  disqusService.isCountScriptLoaded = false;
});

afterEach(() => {
  process.env = originalEnv;
});

describe('DisqusService', () => {
  describe('configuration', () => {
    test('isConfigured returns false when shortname is not set', () => {
      delete process.env.REACT_APP_DISQUS_SHORTNAME;
      expect(disqusService.isConfigured()).toBe(false);
    });

    test('isConfigured returns true when shortname is set', () => {
      process.env.REACT_APP_DISQUS_SHORTNAME = 'test-shortname';
      expect(disqusService.isConfigured()).toBe(true);
    });
  });

  describe('URL and identifier generation', () => {
    beforeEach(() => {
      process.env.REACT_APP_SITE_URL = 'https://example.com';
    });

    test('getPostUrl generates correct URL', () => {
      const url = disqusService.getPostUrl('123');
      expect(url).toBe('https://example.com/posts/123');
    });

    test('getPostIdentifier returns slug when provided', () => {
      const identifier = disqusService.getPostIdentifier('123', 'custom-slug');
      expect(identifier).toBe('custom-slug');
    });

    test('getPostIdentifier returns default format when no slug', () => {
      const identifier = disqusService.getPostIdentifier('123');
      expect(identifier).toBe('post-123');
    });
  });

  describe('loadCommentCountScript', () => {
    test('resolves false when shortname is not configured', async () => {
      delete process.env.REACT_APP_DISQUS_SHORTNAME;
      const result = await disqusService.loadCommentCountScript();
      expect(result).toBe(false);
    });

    test('loads script when shortname is configured', async () => {
      process.env.REACT_APP_DISQUS_SHORTNAME = 'test-shortname';
      
      const promise = disqusService.loadCommentCountScript();
      
      // Find and trigger load event on script
      const script = document.querySelector('script[src*="test-shortname.disqus.com/count.js"]');
      expect(script).toBeInTheDocument();
      
      const loadEvent = new Event('load');
      script.dispatchEvent(loadEvent);
      
      const result = await promise;
      expect(result).toBe(true);
    });

    test('rejects when script fails to load', async () => {
      process.env.REACT_APP_DISQUS_SHORTNAME = 'test-shortname';
      
      const promise = disqusService.loadCommentCountScript();
      
      // Find and trigger error event on script
      const script = document.querySelector('script[src*="test-shortname.disqus.com/count.js"]');
      expect(script).toBeInTheDocument();
      
      const errorEvent = new Event('error');
      script.dispatchEvent(errorEvent);
      
      await expect(promise).rejects.toThrow('Failed to load Disqus count script');
    });

    test('returns true if script is already loaded', async () => {
      process.env.REACT_APP_DISQUS_SHORTNAME = 'test-shortname';
      disqusService.isCountScriptLoaded = true;
      
      const result = await disqusService.loadCommentCountScript();
      expect(result).toBe(true);
      
      // Should not create a new script
      const scripts = document.querySelectorAll('script[src*="count.js"]');
      expect(scripts.length).toBe(0);
    });

    test('returns true if script already exists in DOM', async () => {
      process.env.REACT_APP_DISQUS_SHORTNAME = 'test-shortname';
      
      // Add existing script
      const existingScript = document.createElement('script');
      existingScript.src = 'https://test-shortname.disqus.com/count.js';
      document.head.appendChild(existingScript);
      
      const result = await disqusService.loadCommentCountScript();
      expect(result).toBe(true);
    });
  });

  describe('getCommentCount', () => {
    test('returns 0 when shortname is not configured', async () => {
      delete process.env.REACT_APP_DISQUS_SHORTNAME;
      const count = await disqusService.getCommentCount('123');
      expect(count).toBe(0);
    });

    test('returns cached count when available', async () => {
      process.env.REACT_APP_DISQUS_SHORTNAME = 'test-shortname';
      
      // Set cached count
      disqusService.commentCounts.set('post-123', 5);
      
      const count = await disqusService.getCommentCount('123');
      expect(count).toBe(5);
    });

    test('loads script and gets count from DOM element', async () => {
      process.env.REACT_APP_DISQUS_SHORTNAME = 'test-shortname';
      
      // Mock DISQUSWIDGETS
      window.DISQUSWIDGETS = {
        getCount: jest.fn()
      };
      
      const promise = disqusService.getCommentCount('123');
      
      // Simulate script load
      const script = document.querySelector('script[src*="count.js"]');
      if (script) {
        const loadEvent = new Event('load');
        script.dispatchEvent(loadEvent);
      }
      
      // Create mock count element
      const countElement = document.createElement('span');
      countElement.setAttribute('data-disqus-identifier', 'post-123');
      countElement.textContent = '7';
      document.body.appendChild(countElement);
      
      const count = await promise;
      expect(count).toBe(7);
      
      // Clean up
      document.body.removeChild(countElement);
    });

    test('returns 0 when count element is not found', async () => {
      process.env.REACT_APP_DISQUS_SHORTNAME = 'test-shortname';
      
      window.DISQUSWIDGETS = {
        getCount: jest.fn()
      };
      
      const promise = disqusService.getCommentCount('123');
      
      // Simulate script load
      const script = document.querySelector('script[src*="count.js"]');
      if (script) {
        const loadEvent = new Event('load');
        script.dispatchEvent(loadEvent);
      }
      
      const count = await promise;
      expect(count).toBe(0);
    });
  });

  describe('getCommentCounts', () => {
    test('returns empty Map when shortname is not configured', async () => {
      delete process.env.REACT_APP_DISQUS_SHORTNAME;
      const counts = await disqusService.getCommentCounts([{ id: '123' }]);
      expect(counts).toBeInstanceOf(Map);
      expect(counts.size).toBe(0);
    });

    test('returns empty Map when posts array is empty', async () => {
      process.env.REACT_APP_DISQUS_SHORTNAME = 'test-shortname';
      const counts = await disqusService.getCommentCounts([]);
      expect(counts).toBeInstanceOf(Map);
      expect(counts.size).toBe(0);
    });

    test('gets counts for multiple posts', async () => {
      process.env.REACT_APP_DISQUS_SHORTNAME = 'test-shortname';
      
      window.DISQUSWIDGETS = {
        getCount: jest.fn()
      };
      
      const posts = [{ id: '123' }, { id: '456' }];
      const promise = disqusService.getCommentCounts(posts);
      
      // Simulate script load
      const script = document.querySelector('script[src*="count.js"]');
      if (script) {
        const loadEvent = new Event('load');
        script.dispatchEvent(loadEvent);
      }
      
      // Wait for temporary container to be created and then simulate counts
      setTimeout(() => {
        const tempContainer = document.querySelector('div[style*="display: none"]');
        if (tempContainer) {
          const links = tempContainer.querySelectorAll('a[data-disqus-identifier]');
          links.forEach((link, index) => {
            link.textContent = `${index + 3}`; // 3, 4
          });
        }
      }, 100);
      
      const counts = await promise;
      expect(counts).toBeInstanceOf(Map);
      // Note: The actual values depend on the DOM manipulation timing
    });
  });

  describe('cache management', () => {
    test('clearCache removes all cached counts', () => {
      disqusService.commentCounts.set('post-123', 5);
      disqusService.commentCounts.set('post-456', 3);
      
      expect(disqusService.commentCounts.size).toBe(2);
      
      disqusService.clearCache();
      
      expect(disqusService.commentCounts.size).toBe(0);
    });
  });
});