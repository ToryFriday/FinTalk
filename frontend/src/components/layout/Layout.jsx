import React, { useState } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { useResponsive } from '../../hooks/useResponsive';
import { useAccessibility } from '../../hooks/useAccessibility';
import { useAuth } from '../../contexts/AuthContext';
import { logout } from '../../services/authService';
import Button from '../common/Button';
import './Layout.css';

const Layout = ({ children }) => {
  const location = useLocation();
  const navigate = useNavigate();
  const { isMobile } = useResponsive();
  const { announce } = useAccessibility();
  const { isAuthenticated, user, logout: authLogout, canCreatePosts } = useAuth();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const toggleMobileMenu = () => {
    setMobileMenuOpen(!mobileMenuOpen);
    announce(mobileMenuOpen ? 'Menu closed' : 'Menu opened', 'polite');
  };

  const handleNavClick = () => {
    if (isMobile) {
      setMobileMenuOpen(false);
    }
  };

  const handleLogout = async () => {
    try {
      await logout();
      authLogout();
      navigate('/', { 
        state: { 
          message: 'You have been logged out successfully.',
          type: 'success'
        }
      });
      announce('Logged out successfully', 'polite');
    } catch (error) {
      console.error('Logout error:', error);
      // Even if logout API fails, clear local auth state
      authLogout();
      navigate('/');
    }
  };

  // Dynamic navigation items based on authentication
  const getNavigationItems = () => {
    const items = [
      { path: '/', label: 'Home', ariaLabel: 'Go to home page' },
      { path: '/users', label: 'Authors', ariaLabel: 'Browse user directory' }
    ];

    if (isAuthenticated) {
      if (canCreatePosts()) {
        items.push({ path: '/posts/add', label: 'Write', ariaLabel: 'Create a new post' });
      }
      items.push({ path: `/profile/${user?.user_id}`, label: 'Profile', ariaLabel: 'View your profile' });
    }

    return items;
  };

  const navigationItems = getNavigationItems();

  return (
    <div className="layout">
      {/* Skip to main content link for accessibility */}
      <a href="#main-content" className="skip-link">
        Skip to main content
      </a>
      
      <header className="header" role="banner">
        <div className="header-content">
          <h1 className="logo">
            <Link 
              to="/" 
              aria-label="FinTalk - Go to homepage"
              onClick={handleNavClick}
            >
              FinTalk
            </Link>
          </h1>
          
          {/* Mobile menu button */}
          {isMobile && (
            <Button
              variant="outline-primary"
              size="sm"
              onClick={toggleMobileMenu}
              className="mobile-menu-toggle"
              ariaLabel={mobileMenuOpen ? 'Close navigation menu' : 'Open navigation menu'}
              aria-expanded={mobileMenuOpen}
              aria-controls="main-navigation"
            >
              <span className="hamburger-icon">
                <span></span>
                <span></span>
                <span></span>
              </span>
            </Button>
          )}
          
          <nav 
            id="main-navigation"
            className={`nav ${mobileMenuOpen ? 'nav-mobile-open' : ''}`}
            role="navigation"
            aria-label="Main navigation"
          >
            <ul className="nav-list" role="menubar">
              {navigationItems.map((item) => (
                <li key={item.path} className="nav-item" role="none">
                  <Link 
                    to={item.path}
                    className={location.pathname === item.path ? 'nav-link active' : 'nav-link'}
                    onClick={handleNavClick}
                    role="menuitem"
                    aria-label={item.ariaLabel}
                    aria-current={location.pathname === item.path ? 'page' : undefined}
                  >
                    {item.label}
                  </Link>
                </li>
              ))}
            </ul>
            
            {/* Authentication section */}
            <div className="auth-section">
              {isAuthenticated ? (
                <div className="user-menu">
                  <span className="user-greeting">
                    Hello, {user?.first_name || user?.username || 'User'}
                  </span>
                  <Button
                    variant="outline-primary"
                    size="sm"
                    onClick={handleLogout}
                    className="logout-btn"
                    ariaLabel="Log out of your account"
                  >
                    Logout
                  </Button>
                </div>
              ) : (
                <div className="auth-buttons">
                  <Link 
                    to="/login" 
                    className="btn btn-outline-primary btn-sm"
                    onClick={handleNavClick}
                  >
                    Sign In
                  </Link>
                  <Link 
                    to="/register" 
                    className="btn btn-primary btn-sm"
                    onClick={handleNavClick}
                  >
                    Sign Up
                  </Link>
                </div>
              )}
            </div>
          </nav>
        </div>
      </header>
      
      <main 
        id="main-content" 
        className="main-content" 
        role="main"
        tabIndex="-1"
      >
        {children}
      </main>
      
      <footer className="footer" role="contentinfo">
        <div className="footer-content">
          <p>&copy; 2024 FinTalk. All rights reserved.</p>
          <nav className="footer-nav" aria-label="Footer navigation">
            <Link to="/privacy" className="footer-link">Privacy Policy</Link>
            <Link to="/terms" className="footer-link">Terms of Service</Link>
            <Link to="/contact" className="footer-link">Contact</Link>
          </nav>
        </div>
      </footer>
    </div>
  );
};

export default Layout;