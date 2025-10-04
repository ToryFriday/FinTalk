import React from 'react';
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import PostList from './PostList';

// Mock the usePosts hook
jest.mock('../../hooks/usePosts', () => ({
  __esModule: true,
  default: () => ({
    posts: [],
    loading: false,
    error: null,
    refreshPosts: jest.fn(),
    removePost: jest.fn()
  })
}));

// Mock the BlogAPI
jest.mock('../../services/api', () => ({
  __esModule: true,
  default: {
    deletePost: jest.fn()
  }
}));

describe('PostList Component', () => {
  const renderWithRouter = (component) => {
    return render(
      <MemoryRouter>
        {component}
      </MemoryRouter>
    );
  };

  test('renders PostList component with no posts message', () => {
    renderWithRouter(<PostList />);
    
    expect(screen.getByText('Blog Posts')).toBeInTheDocument();
    expect(screen.getByText('No blog posts found.')).toBeInTheDocument();
    expect(screen.getByText('Create Your First Post')).toBeInTheDocument();
  });

  test('renders add new post button', () => {
    renderWithRouter(<PostList />);
    
    expect(screen.getByText('Add New Post')).toBeInTheDocument();
  });
});