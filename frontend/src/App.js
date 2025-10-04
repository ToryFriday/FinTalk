import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import ErrorBoundary from './components/common/ErrorBoundary';
import Layout from './components/layout/Layout';
import HomePage from './pages/HomePage';
import AddPostPage from './pages/AddPostPage';
import EditPostPage from './pages/EditPostPage';
import ViewPostPage from './pages/ViewPostPage';
import NotFoundPage from './pages/NotFoundPage';
import './App.css';

function App() {
  return (
    <ErrorBoundary>
      <Router>
        <Layout>
          <ErrorBoundary>
            <Routes>
              <Route path="/" element={<HomePage />} />
              <Route path="/posts/add" element={<AddPostPage />} />
              <Route path="/posts/:id/edit" element={<EditPostPage />} />
              <Route path="/posts/:id" element={<ViewPostPage />} />
              <Route path="*" element={<NotFoundPage />} />
            </Routes>
          </ErrorBoundary>
        </Layout>
      </Router>
    </ErrorBoundary>
  );
}

export default App;
