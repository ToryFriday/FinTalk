import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import ErrorBoundary from './components/common/ErrorBoundary';
import Layout from './components/layout/Layout';
import { AuthProvider } from './contexts/AuthContext';
import ProtectedRoute from './components/auth/ProtectedRoute';

import LandingPage from './pages/LandingPage';
import LoginPage from './pages/LoginPage';
import RegisterPage from './pages/RegisterPage';
import HomePage from './pages/HomePage';
import AddPostPage from './pages/AddPostPage';
import EditPostPage from './pages/EditPostPage';
import ViewPostPage from './pages/ViewPostPage';
import DisqusTestPage from './pages/DisqusTestPage';
import UserProfilePage from './pages/UserProfilePage';
import ProfileEditPage from './pages/ProfileEditPage';
import UserDirectoryPage from './pages/UserDirectoryPage';
import NotFoundPage from './pages/NotFoundPage';
import { useAccessibility } from './hooks/useAccessibility';
import './App.css';

// Accessibility announcement component
const AccessibilityAnnouncements = () => {
  const { announcements, announcementRef } = useAccessibility();

  return (
    <div
      ref={announcementRef}
      aria-live="polite"
      aria-atomic="true"
      className="sr-only"
      role="status"
    >
      {announcements.map((announcement) => (
        <div key={announcement.id}>
          {announcement.message}
        </div>
      ))}
    </div>
  );
};

function App() {
  return (
    <ErrorBoundary>
      <AuthProvider>
        <Router>
          <div className="app" lang="en">
            {/* Accessibility announcements */}
            <AccessibilityAnnouncements />
            

            
            <Routes>
              {/* Public routes without layout */}
              <Route path="/landing" element={<LandingPage />} />
              <Route path="/login" element={<LoginPage />} />
              <Route path="/register" element={<RegisterPage />} />
              
              {/* Routes with layout */}
              <Route path="/*" element={
                <Layout>
                  <ErrorBoundary>
                    <Routes>
                      <Route path="/" element={<HomePage />} />
                      <Route path="/posts" element={<HomePage />} />
                      <Route path="/posts/:id" element={<ViewPostPage />} />
                      <Route path="/users" element={<UserDirectoryPage />} />
                      
                      {/* Protected routes */}
                      <Route path="/posts/add" element={
                        <ProtectedRoute>
                          <AddPostPage />
                        </ProtectedRoute>
                      } />
                      <Route path="/posts/:id/edit" element={
                        <ProtectedRoute>
                          <EditPostPage />
                        </ProtectedRoute>
                      } />
                      <Route path="/profile/:userId" element={
                        <ProtectedRoute>
                          <UserProfilePage />
                        </ProtectedRoute>
                      } />
                      <Route path="/profile/edit" element={
                        <ProtectedRoute>
                          <ProfileEditPage />
                        </ProtectedRoute>
                      } />
                      <Route path="/test-disqus" element={
                        <ProtectedRoute requireRoles={['admin', 'editor']}>
                          <DisqusTestPage />
                        </ProtectedRoute>
                      } />
                      
                      <Route path="*" element={<NotFoundPage />} />
                    </Routes>
                  </ErrorBoundary>
                </Layout>
              } />
            </Routes>
          </div>
        </Router>
      </AuthProvider>
    </ErrorBoundary>
  );
}

export default App;
