import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import './NotFoundPage.css';

const NotFoundPage = () => {
  const location = useLocation();

  return (
    <div className="not-found-page">
      <div className="not-found-content">
        <div className="not-found-icon">
          <span className="error-code">404</span>
        </div>
        
        <h1 className="not-found-title">Page Not Found</h1>
        
        <p className="not-found-description">
          The page you are looking for doesn't exist or has been moved.
        </p>
        
        {location.pathname && (
          <p className="not-found-path">
            Requested path: <code>{location.pathname}</code>
          </p>
        )}
        
        <div className="not-found-actions">
          <Link to="/" className="btn btn-primary">
            <span className="btn-icon">🏠</span>
            Go Back Home
          </Link>
          
          <button 
            onClick={() => window.history.back()} 
            className="btn btn-secondary"
            type="button"
          >
            <span className="btn-icon">←</span>
            Go Back
          </button>
        </div>
        
        <div className="not-found-suggestions">
          <h3>What you can do:</h3>
          <ul>
            <li>Check the URL for typos</li>
            <li>Go back to the <Link to="/">homepage</Link></li>
            <li>Browse all <Link to="/">blog posts</Link></li>
            <li>Create a <Link to="/posts/add">new blog post</Link></li>
          </ul>
        </div>
      </div>
    </div>
  );
};

export default NotFoundPage;