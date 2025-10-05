import React, { useEffect } from 'react';
import DisqusComments from '../components/common/DisqusComments';
import CommentCount from '../components/common/CommentCount';
import DisqusTest from '../components/common/DisqusTest';
import { disqusDebug } from '../utils/disqusDebug';
import './DisqusTestPage.css';

/**
 * Test page for Disqus integration
 * This page can be used to manually test the Disqus components
 */
const DisqusTestPage = () => {
  const testPost = {
    id: 'test-123',
    title: 'Test Blog Post for Disqus Integration',
    content: 'This is a test post to verify that the Disqus commenting system is working correctly.'
  };

  useEffect(() => {
    // Run diagnostic on page load
    disqusDebug.runDiagnostic(testPost.id, testPost.title);
  }, [testPost.id, testPost.title]);

  const handleRunDiagnostic = () => {
    disqusDebug.runDiagnostic(testPost.id, testPost.title);
  };

  return (
    <div className="disqus-test-page">
      <header className="test-header">
        <h1>Disqus Integration Test</h1>
        <p>This page is used to test the Disqus commenting system integration.</p>
      </header>

      <main className="test-content">
        <article className="test-post">
          <header className="post-header">
            <h2>{testPost.title}</h2>
            <div className="post-meta">
              <span>Post ID: {testPost.id}</span>
              <CommentCount 
                postId={testPost.id} 
                className="test-comment-count"
                showZero={true}
              />
            </div>
          </header>
          
          <div className="post-content">
            <p>{testPost.content}</p>
          </div>
        </article>

        <section className="comments-section">
          <h3>Comments</h3>
          <DisqusComments
            postId={testPost.id}
            postTitle={testPost.title}
            postUrl={`${window.location.origin}/test-disqus`}
          />
        </section>
      </main>

      <aside className="test-info">
        <h3>Configuration Info</h3>
        <ul>
          <li>
            <strong>Disqus Shortname:</strong> {process.env.REACT_APP_DISQUS_SHORTNAME || 'Not configured'}
          </li>
          <li>
            <strong>Site URL:</strong> {process.env.REACT_APP_SITE_URL || window.location.origin}
          </li>
          <li>
            <strong>Post URL:</strong> {window.location.origin}/test-disqus
          </li>
          <li>
            <strong>Post Identifier:</strong> post-{testPost.id}
          </li>
        </ul>
        
        <DisqusTest shortname={process.env.REACT_APP_DISQUS_SHORTNAME} />
        
        <div className="test-instructions">
          <h4>Setup Status:</h4>
          {!process.env.REACT_APP_DISQUS_SHORTNAME || process.env.REACT_APP_DISQUS_SHORTNAME === 'your-disqus-shortname' ? (
            <div className="setup-warning">
              <p><strong>⚠️ Disqus Not Configured</strong></p>
              <p>You need to set up a real Disqus account. See <code>DISQUS_SETUP.md</code> for instructions.</p>
            </div>
          ) : (
            <div className="setup-success">
              <p><strong>✅ Disqus Configured</strong></p>
              <p>Shortname: <code>{process.env.REACT_APP_DISQUS_SHORTNAME}</code></p>
            </div>
          )}
          
          <h4>Testing Instructions:</h4>
          <ol>
            <li>Follow the setup guide in <code>DISQUS_SETUP.md</code></li>
            <li>Create a Disqus account and get your shortname</li>
            <li>Update the <code>.env</code> file with your shortname</li>
            <li>Restart Docker containers</li>
            <li>Refresh this page to test</li>
          </ol>
          
          <div className="debug-section">
            <h4>Debug Tools:</h4>
            <button 
              onClick={handleRunDiagnostic}
              className="debug-button"
              type="button"
            >
              Run Diagnostic
            </button>
            <p><small>Check browser console for detailed output</small></p>
          </div>
        </div>
      </aside>
    </div>
  );
};

export default DisqusTestPage;