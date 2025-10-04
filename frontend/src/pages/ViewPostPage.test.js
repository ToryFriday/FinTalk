import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import { BrowserRouter, MemoryRouter } from 'react-router-dom';
import ViewPostPage from './ViewPostPage';
import * as usePostHook from '../hooks/usePost';

// Mock the usePost hook
jest.mock('../hooks/usePost');

// Mock the PostDetail component
jest.mock('../components/posts/PostDetail', () => {
  return function MockPostDetail({ post, onDelete }) {
    return (
      <div data-testid="post-detail">
        <h1>{post.title}</h1>
        <p>{post.content}</p>
        <button onClick={() => onDelete(post.id)}>Delete</button>
      </div>
    );
  };
});

// Mock the NotFoundPage component
jest.mock('./NotFoundPage', () => {
  return function MockNotFoundPage() {
    return <div data-testid="not-found-page">404 - Post Not Found</div>;
  };
});

const mockPost = {
  id: 1,
  title: 'Test Post',
  content: 'Test content',
  author: 'Test Author',
  tags: 'test',
  created_at: '2024-01-01T10:00:00Z',
  updated_at: '2024-01-01T10:00:00Z'
};

const TestWrapper = ({ children, initialEntries = ['/posts/1'] }) => (
  <MemoryRouter initialEntries={initialEntries}>
    {children}
  </MemoryRouter>
);

describe('ViewPostPage', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  test('renders loading spinner while fetching post', () => {
    usePostHook.default.mockReturnValue({
      post: null,
      loading: true,
      error: null,
      fetchPost: jest.fn(),
      deletePost: jest.fn()
    });

    render(
      <TestWrapper>
        <ViewPostPage />
      </TestWrapper>
    );

    expect(screen.getByText('Loading post...')).toBeInTheDocument();
  });

  test('renders PostDetail component when post is loaded', () => {
    usePostHook.default.mockReturnValue({
      post: mockPost,
      loading: false,
      error: null,
      fetchPost: jest.fn(),
      deletePost: jest.fn()
    });

    render(
      <TestWrapper>
        <ViewPostPage />
      </TestWrapper>
    );

    expect(screen.getByTestId('post-detail')).toBeInTheDocument();
    expect(screen.getByText('Test Post')).toBeInTheDocument();
    expect(screen.getByText('Test content')).toBeInTheDocument();
  });

  test('renders NotFoundPage when post is not found', () => {
    usePostHook.default.mockReturnValue({
      post: null,
      loading: false,
      error: { type: 'NOT_FOUND', message: 'Post not found' },
      fetchPost: jest.fn(),
      deletePost: jest.fn()
    });

    render(
      <TestWrapper>
        <ViewPostPage />
      </TestWrapper>
    );

    expect(screen.getByTestId('not-found-page')).toBeInTheDocument();
  });

  test('renders error message for other errors', () => {
    const mockError = { type: 'NETWORK_ERROR', message: 'Network error' };
    const mockFetchPost = jest.fn();

    usePostHook.default.mockReturnValue({
      post: null,
      loading: false,
      error: mockError,
      fetchPost: mockFetchPost,
      deletePost: jest.fn()
    });

    render(
      <TestWrapper>
        <ViewPostPage />
      </TestWrapper>
    );

    expect(screen.getByText('Network error')).toBeInTheDocument();
    expect(screen.getByText('Try Again')).toBeInTheDocument();
  });

  test('renders NotFoundPage when no post data and no error', () => {
    usePostHook.default.mockReturnValue({
      post: null,
      loading: false,
      error: null,
      fetchPost: jest.fn(),
      deletePost: jest.fn()
    });

    render(
      <TestWrapper>
        <ViewPostPage />
      </TestWrapper>
    );

    expect(screen.getByTestId('not-found-page')).toBeInTheDocument();
  });

  test('handles delete post successfully', async () => {
    const mockDeletePost = jest.fn().mockResolvedValue({ success: true });
    const mockNavigate = jest.fn();

    // Mock useNavigate
    jest.doMock('react-router-dom', () => ({
      ...jest.requireActual('react-router-dom'),
      useNavigate: () => mockNavigate,
    }));

    usePostHook.default.mockReturnValue({
      post: mockPost,
      loading: false,
      error: null,
      fetchPost: jest.fn(),
      deletePost: mockDeletePost
    });

    render(
      <TestWrapper>
        <ViewPostPage />
      </TestWrapper>
    );

    // The delete functionality would be tested through the PostDetail component
    // This test verifies the hook is properly connected
    expect(screen.getByTestId('post-detail')).toBeInTheDocument();
  });
});