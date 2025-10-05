import React, { useEffect, useRef, useState } from 'react';
import './DisqusComments.css';

/**
 * DisqusComments component for integrating Disqus commenting system
 * @param {Object} props - Component props
 * @param {string|number} props.postId - Unique identifier for the post
 * @param {string} props.postTitle - Title of the post for Disqus
 * @param {string} props.postUrl - URL of the post page
 * @param {string} props.postSlug - Optional slug for the post (defaults to postId)
 */
const DisqusComments = ({ postId, postTitle, postUrl, postSlug }) => {
  const disqusRef = useRef(null);
  const [isLoaded, setIsLoaded] = useState(false);
  const [hasError, setHasError] = useState(false);
  const [isLoading, setIsLoading] = useState(true);

  // Get Disqus configuration from environment variables
  const disqusShortname = process.env.REACT_APP_DISQUS_SHORTNAME;
  const siteUrl = process.env.REACT_APP_SITE_URL || window.location.origin;

  // Generate full URL for the post
  const fullPostUrl = postUrl || `${siteUrl}/posts/${postId}`;
  const identifier = postSlug || `post-${postId}`;

  useEffect(() => {
    // Don't load if no shortname is configured
    if (!disqusShortname) {
      setHasError(true);
      setIsLoading(false);
      console.warn('Disqus shortname not configured. Please set REACT_APP_DISQUS_SHORTNAME environment variable.');
      return;
    }

    // Don't load if required props are missing
    if (!postId || !postTitle) {
      setHasError(true);
      setIsLoading(false);
      console.error('DisqusComments: postId and postTitle are required props');
      return;
    }

    const loadDisqus = () => {
      // Reset Disqus if it's already loaded
      if (window.DISQUS) {
        window.DISQUS.reset({
          reload: true,
          config: function () {
            this.page.identifier = identifier;
            this.page.url = fullPostUrl;
            this.page.title = postTitle;
          }
        });
        setIsLoaded(true);
        setIsLoading(false);
        return;
      }

      // Configure Disqus
      window.disqus_config = function () {
        this.page.url = fullPostUrl;
        this.page.identifier = identifier;
        this.page.title = postTitle;
        
        // Optional: Configure additional settings
        this.callbacks.onReady = [function () {
          setIsLoaded(true);
          setIsLoading(false);
        }];
        
        this.callbacks.onError = [function () {
          setHasError(true);
          setIsLoading(false);
        }];
      };

      // Load Disqus script
      const script = document.createElement('script');
      script.src = `https://${disqusShortname}.disqus.com/embed.js`;
      script.setAttribute('data-timestamp', +new Date());
      script.async = true;
      script.onerror = () => {
        setHasError(true);
        setIsLoading(false);
      };

      // Add script to document
      document.head.appendChild(script);
    };

    // Small delay to ensure DOM is ready
    const timer = setTimeout(loadDisqus, 100);

    return () => {
      clearTimeout(timer);
    };
  }, [postId, postTitle, fullPostUrl, identifier, disqusShortname]);

  // Don't render if no shortname is configured
  if (!disqusShortname) {
    return (
      <div className="disqus-comments disqus-error">
        <div className="disqus-fallback">
          <h3>Comments</h3>
          <p>
            <strong>Disqus Not Configured</strong><br/>
            To enable comments, you need to:
          </p>
          <ol style={{ textAlign: 'left', margin: '1rem 0' }}>
            <li>Create a Disqus account at <a href="https://disqus.com" target="_blank" rel="noopener noreferrer">disqus.com</a></li>
            <li>Register your site and get a shortname</li>
            <li>Set REACT_APP_DISQUS_SHORTNAME in your .env file</li>
            <li>Add localhost:3000 to your Disqus trusted domains</li>
          </ol>
          <p><small>Current shortname: {process.env.REACT_APP_DISQUS_SHORTNAME || 'Not set'}</small></p>
        </div>
      </div>
    );
  }

  return (
    <div className="disqus-comments">
      {isLoading && (
        <div className="disqus-loading">
          <div className="loading-spinner" data-testid="loading-spinner"></div>
          <p>Loading comments...</p>
        </div>
      )}
      
      {hasError && !isLoading && (
        <div className="disqus-fallback">
          <h3>Comments</h3>
          <p>
            Comments are temporarily unavailable. Please try refreshing the page or check back later.
          </p>
          <button 
            className="retry-button"
            onClick={() => window.location.reload()}
            type="button"
          >
            Retry
          </button>
        </div>
      )}
      
      <div 
        id="disqus_thread" 
        ref={disqusRef}
        style={{ display: hasError ? 'none' : 'block' }}
      ></div>
      
      {isLoaded && (
        <div className="disqus-noscript-fallback" style={{ display: 'none' }}>
          <noscript>
            Please enable JavaScript to view the{' '}
            <a href="https://disqus.com/?ref_noscript">
              comments powered by Disqus.
            </a>
          </noscript>
          <p data-testid="noscript-message">
            Please enable JavaScript to view the comments powered by Disqus.
          </p>
        </div>
      )}
    </div>
  );
};

export default DisqusComments;