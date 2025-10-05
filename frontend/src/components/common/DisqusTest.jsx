import React, { useState, useEffect } from 'react';

/**
 * Simple Disqus test component to verify if shortname exists
 */
const DisqusTest = ({ shortname = 'fintalk-blog' }) => {
  const [status, setStatus] = useState('testing');
  const [error, setError] = useState(null);

  useEffect(() => {
    const testDisqusShortname = async () => {
      try {
        setStatus('testing');
        setError(null);

        // Test if we can load the Disqus embed script
        const script = document.createElement('script');
        script.src = `https://${shortname}.disqus.com/embed.js`;
        script.async = true;
        
        script.onload = () => {
          setStatus('success');
          console.log(`✅ Disqus shortname "${shortname}" exists and script loaded`);
        };
        
        script.onerror = () => {
          setStatus('error');
          setError(`Shortname "${shortname}" does not exist or cannot be loaded`);
          console.error(`❌ Disqus shortname "${shortname}" failed to load`);
        };

        // Add script to test loading
        document.head.appendChild(script);

        // Clean up after 10 seconds
        setTimeout(() => {
          try {
            document.head.removeChild(script);
          } catch (e) {
            // Script might already be removed
          }
        }, 10000);

      } catch (err) {
        setStatus('error');
        setError(err.message);
      }
    };

    if (shortname && shortname !== 'your-disqus-shortname') {
      testDisqusShortname();
    } else {
      setStatus('not-configured');
    }
  }, [shortname]);

  const getStatusColor = () => {
    switch (status) {
      case 'success': return '#28a745';
      case 'error': return '#dc3545';
      case 'testing': return '#ffc107';
      default: return '#6c757d';
    }
  };

  const getStatusText = () => {
    switch (status) {
      case 'success': return '✅ Shortname Valid';
      case 'error': return '❌ Shortname Invalid';
      case 'testing': return '🔄 Testing...';
      case 'not-configured': return '⚠️ Not Configured';
      default: return 'Unknown';
    }
  };

  return (
    <div style={{
      padding: '1rem',
      border: '1px solid #ddd',
      borderRadius: '4px',
      margin: '1rem 0',
      backgroundColor: '#f8f9fa'
    }}>
      <h4>Disqus Shortname Test</h4>
      <p>
        <strong>Testing shortname:</strong> <code>{shortname}</code>
      </p>
      <p style={{ color: getStatusColor(), fontWeight: 'bold' }}>
        {getStatusText()}
      </p>
      {error && (
        <div style={{
          padding: '0.5rem',
          backgroundColor: '#f8d7da',
          border: '1px solid #f5c6cb',
          borderRadius: '4px',
          color: '#721c24',
          marginTop: '0.5rem'
        }}>
          <strong>Error:</strong> {error}
        </div>
      )}
      {status === 'error' && (
        <div style={{ marginTop: '1rem', fontSize: '0.9rem' }}>
          <p><strong>Possible solutions:</strong></p>
          <ul>
            <li>Create a Disqus account at <a href="https://disqus.com" target="_blank" rel="noopener noreferrer">disqus.com</a></li>
            <li>Register a new site with shortname "{shortname}"</li>
            <li>Or use a different shortname that you've already registered</li>
            <li>Add "localhost" to your Disqus trusted domains</li>
          </ul>
        </div>
      )}
      {status === 'success' && (
        <div style={{ marginTop: '1rem', fontSize: '0.9rem', color: '#155724' }}>
          <p><strong>Great!</strong> Your Disqus shortname is valid. If comments still don't work:</p>
          <ul>
            <li>Add "localhost" to your Disqus trusted domains</li>
            <li>Check browser console for additional errors</li>
            <li>Wait a few minutes for Disqus settings to propagate</li>
          </ul>
        </div>
      )}
    </div>
  );
};

export default DisqusTest;