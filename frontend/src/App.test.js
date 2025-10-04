import React from 'react';
import { render, screen } from '@testing-library/react';
import { MemoryRouter, Routes, Route } from 'react-router-dom';
import Layout from './components/layout/Layout';
import HomePage from './pages/HomePage';
import AddPostPage from './pages/AddPostPage';
import EditPostPage from './pages/EditPostPage';
import ViewPostPage from './pages/ViewPostPage';
import NotFoundPage from './pages/NotFoundPage';

// Create a test component that mimics App structure but allows for MemoryRouter
const TestApp = ({ initialEntries = ['/'] }) => (
  <MemoryRouter initialEntries={initialEntries}>
    <Layout>
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/add" element={<AddPostPage />} />
        <Route path="/edit/:id" element={<EditPostPage />} />
        <Route path="/view/:id" element={<ViewPostPage />} />
        <Route path="*" element={<NotFoundPage />} />
      </Routes>
    </Layout>
  </MemoryRouter>
);

// Test routing functionality
describe('App Routing', () => {
  test('renders home page by default', () => {
    render(<TestApp />);
    
    expect(screen.getByText('FinTalk')).toBeInTheDocument();
    expect(screen.getByText('Loading posts...')).toBeInTheDocument();
  });

  test('renders add post page', () => {
    render(<TestApp initialEntries={['/add']} />);
    
    expect(screen.getByText('Create New Blog Post')).toBeInTheDocument();
  });

  test('renders edit post page with ID parameter', () => {
    render(<TestApp initialEntries={['/edit/123']} />);
    
    expect(screen.getByText('Edit Post')).toBeInTheDocument();
    expect(screen.getByText('Loading post data...')).toBeInTheDocument();
  });

  test('renders view post page with ID parameter', () => {
    render(<TestApp initialEntries={['/view/456']} />);
    
    expect(screen.getByText('Loading post...')).toBeInTheDocument();
  });

  test('renders 404 page for unknown routes', () => {
    render(<TestApp initialEntries={['/unknown-route']} />);
    
    expect(screen.getByText('Page Not Found')).toBeInTheDocument();
    expect(screen.getByText('404')).toBeInTheDocument();
  });

  test('navigation links are present', () => {
    render(<TestApp />);
    
    expect(screen.getByRole('link', { name: 'FinTalk' })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Home' })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Add Post' })).toBeInTheDocument();
  });
});