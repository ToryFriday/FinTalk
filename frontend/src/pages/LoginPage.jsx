import React, { useState, useEffect } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { login } from '../services/authService';
import { useAuth } from '../contexts/AuthContext';

import './LoginPage.css';

const LoginPage = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { login: authLogin } = useAuth();
  
  const [formData, setFormData] = useState({
    username: '',
    password: ''
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  // Check for success message from registration
  useEffect(() => {
    if (location.state?.message) {
      setSuccess(location.state.message);
      // Clear the navigation state
      window.history.replaceState({}, document.title);
    }
  }, [location.state]);

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
    
    // Clear error when user starts typing
    if (error) {
      setError('');
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!formData.username || !formData.password) {
      setError('Please fill in all fields');
      return;
    }

    setLoading(true);
    setError('');

    try {
      const response = await login(formData.username, formData.password);
      
      if (response.data) {
        // Update the auth context with user data
        authLogin(response.data);
        
        // Redirect to intended page or home
        const redirectTo = location.state?.from?.pathname || '/';
        navigate(redirectTo, { 
          replace: true,
          state: { 
            message: `Welcome back, ${response.data.username || response.data.first_name || 'User'}!`,
            type: 'success'
          }
        });
      }
    } catch (error) {
      console.error('Login error:', error);
      
      if (error.status === 403 && error.error_type === 'authentication_required') {
        setError('Invalid username or password. Please try again.');
      } else if (error.details && typeof error.details === 'object') {
        // Handle validation errors
        const errorMessages = [];
        Object.entries(error.details).forEach(([field, messages]) => {
          if (Array.isArray(messages)) {
            errorMessages.push(...messages);
          } else {
            errorMessages.push(messages);
          }
        });
        setError(errorMessages.join('. '));
      } else {
        setError(error.message || 'Login failed. Please try again.');
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-page">
      <div className="login-container">
        <div className="login-header">
          <Link to="/" className="back-to-home">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M19 12H5M12 19l-7-7 7-7"/>
            </svg>
            Back to Home
          </Link>
          <div className="brand-section">
            <h1>Welcome Back</h1>
            <p>Sign in to your FinTalk account</p>
          </div>
        </div>

        <div className="login-form-container">
          {success && (
            <div className="success-message">
              {success}
            </div>
          )}

          {error && (
            <div className="error-message">
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="login-form">
            <div className="form-group">
              <label htmlFor="username">Username or Email</label>
              <input
                type="text"
                id="username"
                name="username"
                value={formData.username}
                onChange={handleInputChange}
                placeholder="Enter your username or email"
                disabled={loading}
                autoComplete="username"
                required
              />
            </div>

            <div className="form-group">
              <label htmlFor="password">Password</label>
              <input
                type="password"
                id="password"
                name="password"
                value={formData.password}
                onChange={handleInputChange}
                placeholder="Enter your password"
                disabled={loading}
                autoComplete="current-password"
                required
              />
            </div>

            <button 
              type="submit" 
              className="btn btn-primary btn-full"
              disabled={loading}
            >
              {loading ? 'Signing In...' : 'Sign In'}
            </button>
          </form>

          <div className="login-footer">
            <div className="forgot-password">
              <Link to="/forgot-password">Forgot your password?</Link>
            </div>
            
            <div className="signup-link">
              <span>Don't have an account? </span>
              <Link to="/register">Sign up here</Link>
            </div>
          </div>

          <div className="demo-accounts">
            <h3>Demo Accounts</h3>
            <p>Try the platform with these test accounts:</p>
            <div className="demo-buttons">
              <button 
                type="button"
                className="btn btn-outline btn-small"
                onClick={() => setFormData({ username: 'testuser', password: 'password' })}
                disabled={loading}
              >
                Regular User
              </button>
              <button 
                type="button"
                className="btn btn-outline btn-small"
                onClick={() => setFormData({ username: 'admin', password: 'admin123' })}
                disabled={loading}
              >
                Admin User
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default LoginPage;