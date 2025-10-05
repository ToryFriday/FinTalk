/**
 * Disqus Debug Utilities
 * Helper functions to debug Disqus integration issues
 */

export const disqusDebug = {
  /**
   * Check if Disqus configuration is valid
   */
  checkConfig() {
    const shortname = process.env.REACT_APP_DISQUS_SHORTNAME;
    const siteUrl = process.env.REACT_APP_SITE_URL || window.location.origin;
    
    console.group('🔍 Disqus Configuration Debug');
    console.log('Shortname:', shortname || '❌ Not set');
    console.log('Site URL:', siteUrl);
    console.log('Current Origin:', window.location.origin);
    console.log('Current Hostname:', window.location.hostname);
    
    if (!shortname) {
      console.warn('❌ REACT_APP_DISQUS_SHORTNAME is not set');
      console.log('💡 Set this in your .env file');
    } else if (shortname === 'your-disqus-shortname') {
      console.warn('❌ Using placeholder shortname');
      console.log('💡 Replace with your actual Disqus shortname');
    } else {
      console.log('✅ Shortname is configured');
    }
    
    console.groupEnd();
    
    return {
      shortname,
      siteUrl,
      isConfigured: shortname && shortname !== 'your-disqus-shortname'
    };
  },

  /**
   * Test if Disqus script can be loaded
   */
  async testScriptLoad(shortname) {
    if (!shortname) {
      console.error('No shortname provided for testing');
      return false;
    }

    return new Promise((resolve) => {
      const script = document.createElement('script');
      script.src = `https://${shortname}.disqus.com/embed.js`;
      script.onload = () => {
        console.log('✅ Disqus script loaded successfully');
        resolve(true);
      };
      script.onerror = () => {
        console.error('❌ Failed to load Disqus script');
        console.log('💡 Check if your shortname exists in Disqus');
        resolve(false);
      };
      
      // Don't actually add to DOM, just test loading
      script.style.display = 'none';
      document.head.appendChild(script);
      
      // Clean up after test
      setTimeout(() => {
        document.head.removeChild(script);
      }, 5000);
    });
  },

  /**
   * Check current page configuration
   */
  checkPageConfig(postId, postTitle) {
    const identifier = `post-${postId}`;
    const url = `${window.location.origin}/posts/${postId}`;
    
    console.group('📄 Page Configuration');
    console.log('Post ID:', postId);
    console.log('Post Title:', postTitle);
    console.log('Disqus Identifier:', identifier);
    console.log('Post URL:', url);
    console.groupEnd();
    
    return { identifier, url };
  },

  /**
   * Run full diagnostic
   */
  async runDiagnostic(postId = 'test', postTitle = 'Test Post') {
    console.log('🚀 Running Disqus Diagnostic...');
    
    const config = this.checkConfig();
    this.checkPageConfig(postId, postTitle);
    
    if (config.isConfigured) {
      console.log('🧪 Testing script load...');
      await this.testScriptLoad(config.shortname);
    }
    
    console.log('📋 Diagnostic complete. Check console output above.');
    
    return config;
  },

  /**
   * Generate setup instructions based on current state
   */
  getSetupInstructions() {
    const config = this.checkConfig();
    
    if (!config.shortname) {
      return [
        '1. Create a Disqus account at https://disqus.com/',
        '2. Create a new site (use https://example.com as placeholder URL)',
        '3. Note your shortname',
        '4. Add REACT_APP_DISQUS_SHORTNAME=your-shortname to .env',
        '5. Restart your Docker containers'
      ];
    }
    
    if (config.shortname === 'your-disqus-shortname') {
      return [
        '1. Replace placeholder shortname in .env file',
        '2. Use your actual Disqus shortname',
        '3. Restart your Docker containers'
      ];
    }
    
    return [
      '1. Check Disqus admin settings',
      '2. Add "localhost" to trusted domains',
      '3. Verify your shortname is correct',
      '4. Check browser console for errors'
    ];
  }
};

// Make available globally for easy debugging
if (typeof window !== 'undefined') {
  window.disqusDebug = disqusDebug;
}