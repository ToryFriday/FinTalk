import React from 'react';
import { Link } from 'react-router-dom';
import './LandingPage.css';

const LandingPage = () => {
  return (
    <div className="landing-page">
      {/* Hero Section */}
      <section className="hero-section">
        <div className="hero-content">
          <div className="hero-text">
            <h1 className="hero-title">
              Welcome to <span className="brand-name">FinTalk</span>
            </h1>
            <p className="hero-subtitle">
              Your premier destination for financial insights, market analysis, and investment discussions
            </p>
            <p className="hero-description">
              Join our community of financial professionals, investors, and enthusiasts. 
              Share your expertise, discover new perspectives, and stay ahead of market trends 
              with our comprehensive blogging platform.
            </p>
            <div className="hero-actions">
              <Link to="/register" className="btn btn-primary btn-large">
                Get Started
              </Link>
              <Link to="/login" className="btn btn-secondary btn-large">
                Sign In
              </Link>
            </div>
          </div>
          <div className="hero-image">
            <div className="hero-graphic">
              <div className="financial-icon">
                <svg viewBox="0 0 100 100" className="chart-icon">
                  <path d="M20 80 L30 60 L40 70 L50 40 L60 50 L70 30 L80 20" 
                        stroke="#2563eb" 
                        strokeWidth="3" 
                        fill="none" 
                        strokeLinecap="round"/>
                  <circle cx="20" cy="80" r="3" fill="#2563eb"/>
                  <circle cx="30" cy="60" r="3" fill="#2563eb"/>
                  <circle cx="40" cy="70" r="3" fill="#2563eb"/>
                  <circle cx="50" cy="40" r="3" fill="#2563eb"/>
                  <circle cx="60" cy="50" r="3" fill="#2563eb"/>
                  <circle cx="70" cy="30" r="3" fill="#2563eb"/>
                  <circle cx="80" cy="20" r="3" fill="#2563eb"/>
                </svg>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="features-section">
        <div className="container">
          <h2 className="section-title">Why Choose FinTalk?</h2>
          <div className="features-grid">
            <div className="feature-card">
              <div className="feature-icon">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M12 2L2 7l10 5 10-5-10-5z"/>
                  <path d="M2 17l10 5 10-5"/>
                  <path d="M2 12l10 5 10-5"/>
                </svg>
              </div>
              <h3>Expert Insights</h3>
              <p>Access in-depth analysis from financial professionals and industry experts.</p>
            </div>
            
            <div className="feature-card">
              <div className="feature-icon">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/>
                  <circle cx="9" cy="7" r="4"/>
                  <path d="M23 21v-2a4 4 0 0 0-3-3.87"/>
                  <path d="M16 3.13a4 4 0 0 1 0 7.75"/>
                </svg>
              </div>
              <h3>Community Driven</h3>
              <p>Connect with like-minded investors and share your financial journey.</p>
            </div>
            
            <div className="feature-card">
              <div className="feature-icon">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z"/>
                </svg>
              </div>
              <h3>Real-time Updates</h3>
              <p>Stay informed with the latest market trends and breaking financial news.</p>
            </div>
            
            <div className="feature-card">
              <div className="feature-icon">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M9 12l2 2 4-4"/>
                  <path d="M21 12c-1 0-3-1-3-3s2-3 3-3 3 1 3 3-2 3-3 3"/>
                  <path d="M3 12c1 0 3-1 3-3s-2-3-3-3-3 1-3 3 2 3 3 3"/>
                  <path d="M13 12h1"/>
                </svg>
              </div>
              <h3>Trusted Platform</h3>
              <p>Built with security and reliability in mind for professional use.</p>
            </div>
          </div>
        </div>
      </section>

      {/* About Section */}
      <section className="about-section">
        <div className="container">
          <div className="about-content">
            <div className="about-text">
              <h2>About FinTalk</h2>
              <p>
                FinTalk is a cutting-edge financial blogging platform developed by <strong>Fintrellis</strong>, 
                a leading financial technology company dedicated to democratizing access to financial knowledge 
                and investment insights.
              </p>
              <p>
                Our platform brings together financial professionals, analysts, investors, and enthusiasts 
                in a collaborative environment where knowledge sharing drives better financial decisions.
              </p>
              <div className="about-stats">
                <div className="stat">
                  <div className="stat-number">1000+</div>
                  <div className="stat-label">Active Users</div>
                </div>
                <div className="stat">
                  <div className="stat-number">500+</div>
                  <div className="stat-label">Expert Articles</div>
                </div>
                <div className="stat">
                  <div className="stat-number">50+</div>
                  <div className="stat-label">Market Topics</div>
                </div>
              </div>
            </div>
            <div className="about-image">
              <div className="company-logo">
                <div className="logo-placeholder">
                  <span className="logo-text">Fintrellis</span>
                  <span className="logo-tagline">Financial Intelligence</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="cta-section">
        <div className="container">
          <div className="cta-content">
            <h2>Ready to Join the Financial Conversation?</h2>
            <p>
              Start sharing your insights, discover new perspectives, and connect with 
              the financial community today.
            </p>
            <div className="cta-actions">
              <Link to="/register" className="btn btn-primary btn-large">
                Create Account
              </Link>
              <Link to="/posts" className="btn btn-outline btn-large">
                Browse Articles
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="landing-footer">
        <div className="container">
          <div className="footer-content">
            <div className="footer-brand">
              <h3>FinTalk</h3>
              <p>Powered by Fintrellis</p>
            </div>
            <div className="footer-links">
              <div className="footer-section">
                <h4>Platform</h4>
                <ul>
                  <li><Link to="/posts">Articles</Link></li>
                  <li><Link to="/users">Authors</Link></li>
                  <li><Link to="/register">Join Us</Link></li>
                </ul>
              </div>
              <div className="footer-section">
                <h4>Company</h4>
                <ul>
                  <li><a href="#about">About Fintrellis</a></li>
                  <li><a href="#contact">Contact</a></li>
                  <li><a href="#careers">Careers</a></li>
                </ul>
              </div>
              <div className="footer-section">
                <h4>Legal</h4>
                <ul>
                  <li><a href="#privacy">Privacy Policy</a></li>
                  <li><a href="#terms">Terms of Service</a></li>
                  <li><a href="#cookies">Cookie Policy</a></li>
                </ul>
              </div>
            </div>
          </div>
          <div className="footer-bottom">
            <p>&copy; 2025 Fintrellis. All rights reserved.</p>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default LandingPage;