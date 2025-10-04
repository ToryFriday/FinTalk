import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import Layout from './Layout';

describe('Layout Component', () => {
  test('renders header with navigation links', () => {
    render(
      <MemoryRouter>
        <Layout>
          <div>Test Content</div>
        </Layout>
      </MemoryRouter>
    );

    expect(screen.getByText('FinTalk')).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Home' })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Add Post' })).toBeInTheDocument();
    expect(screen.getByText('Test Content')).toBeInTheDocument();
  });

  test('applies active class to current route', () => {
    render(
      <MemoryRouter initialEntries={['/add']}>
        <Layout>
          <div>Test Content</div>
        </Layout>
      </MemoryRouter>
    );

    const addPostLink = screen.getByRole('link', { name: 'Add Post' });
    const homeLink = screen.getByRole('link', { name: 'Home' });
    
    expect(addPostLink).toHaveClass('active');
    expect(homeLink).not.toHaveClass('active');
  });

  test('renders footer', () => {
    render(
      <MemoryRouter>
        <Layout>
          <div>Test Content</div>
        </Layout>
      </MemoryRouter>
    );

    expect(screen.getByText('© 2024 FinTalk. All rights reserved.')).toBeInTheDocument();
  });
});